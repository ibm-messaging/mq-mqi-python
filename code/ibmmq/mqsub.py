"""Subscription class: for MQSUB, MQSUBRQ, MQCLOSE.
Will reference a managed queue for the MQGET if that has been requested.
"""

# Copyright (c) 2025, 2026 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from typing import Union

from mqcommon import *
from mqerrors import *
from ibmmq import CMQC, SD, SRO, MQObject, Queue, ibmmqc
import mqlog

class Subscription(MQObject):
    """ Encapsulates a subscription to a topic.
    """
    def __init__(self, queue_manager, sub_desc=None, sub_name=None,
                 sub_queue=None, sub_opts=None, topic_name=None, topic_string=None):

        mqlog.trace_entry("sub:__init__")

        queue_manager = ensure_strings_are_bytes(queue_manager)
        sub_name = ensure_strings_are_bytes(sub_name)
        topic_name = ensure_strings_are_bytes(topic_name)
        topic_string = ensure_strings_are_bytes(topic_string)

        self.__queue_manager = queue_manager
        self.sub_queue = sub_queue
        self.__sub_desc = sub_desc
        self.sub_name = sub_name
        self.sub_opts = sub_opts
        self.topic_name = topic_name
        self.topic_string = topic_string
        self.__sub_handle = None

        if self.__sub_desc:
            self.sub(sub_desc=self.__sub_desc)

        object_name = None
        if topic_name:
            object_name = topic_name
        if topic_string:
            if object_name:
                object_name = object_name + "/" + topic_string
            else:
                object_name = topic_string
        super().__init__(object_name)
        mqlog.trace_exit("sub:__init__")

    def get_handle(self):
        """Return the subscription's hObj object"""
        return self.__sub_handle

    def get_queue_manager(self):
        """Return the subscriptions hConn object"""
        return self.__queue_manager

    def get_sub_queue(self) -> Queue:
        """ Return the subscription queue.
        """
        return self.sub_queue

    def get(self, max_length: Union[None, int] = None, *opts):  # pylint: disable=keyword-arg-before-vararg
        """ Get a publication from the Queue.
        """
        mqlog.trace_entry("sub:get")
        rv = self.sub_queue.get(max_length, *opts)
        mqlog.trace_exit("sub:get")

        return rv

    def get_rfh2(self, max_length: Union[None, int] = None, *opts) -> bytes:  # pylint: disable=keyword-arg-before-vararg
        """ Get a publication from the Queue.
        """
        mqlog.trace_entry("sub:get_rfh2")
        rv = self.sub_queue.get_rfh2(max_length, *opts)
        mqlog.trace_exit("sub:get_rfh2")
        return rv

    def sub(self, sub_desc=None, sub_queue=None, sub_name=None, sub_opts=None,
            topic_name=None, topic_string=None):
        """ Subscribe to a topic, alter or resume a subscription.
        Executes the MQSUB call with parameters.
        The subscription queue can be either passed as a Queue object or a
        Queue object handle.
        """
        mqlog.trace_entry("sub:sub")

        sub_queue = ensure_strings_are_bytes(sub_queue)
        sub_name = ensure_strings_are_bytes(sub_name)
        topic_name = ensure_strings_are_bytes(topic_name)
        topic_string = ensure_strings_are_bytes(topic_string)

        if topic_name:
            self.topic_name = topic_name
        if topic_string:
            self.topic_string = topic_string
        if sub_name:
            self.sub_name = sub_name

        if sub_desc:
            if not isinstance(sub_desc, SD):
                mqlog.trace_exit("sub:sub", ep=1)
                raise TypeError('sub_desc must be a SD(sub descriptor) object.')
        else:
            sub_desc = SD()
            if sub_opts:
                sub_desc['Options'] = sub_opts
            else:
                sub_desc['Options'] = CMQC.MQSO_CREATE + CMQC.MQSO_NON_DURABLE + CMQC.MQSO_MANAGED
            if self.sub_name:
                sub_desc.set_vs('SubName', self.sub_name)
            if self.topic_name:
                sub_desc['ObjectName'] = self.topic_name
            if self.topic_string:
                sub_desc.set_vs('ObjectString', self.topic_string)
        self.__sub_desc = sub_desc

        sub_queue_handle = CMQC.MQHO_NONE
        if sub_queue:
            if isinstance(sub_queue, Queue):
                sub_queue_handle = sub_queue.get_handle()
            else:
                sub_queue_handle = sub_queue

        rv = ibmmqc.MQSUB(self.__queue_manager.getHandle(), sub_desc.pack(), sub_queue_handle)

        if rv[-2]:
            mqlog.trace_exit("sub:sub", ep=2, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1])

        sub_desc.unpack(rv[0])
        self.__sub_desc = sub_desc
        self.sub_queue = Queue(self.__queue_manager)
        self.sub_queue.set_handle(rv[1])
        self.__sub_handle = rv[2]

        if OTelFunctions.open and (sub_desc.Options & CMQC.MQSO_MANAGED) != 0:
            OTelFunctions.open(self, None, 0, self.sub_queue)
        mqlog.trace_exit("sub:sub")

    def close(self, sub_close_options=CMQC.MQCO_NONE, close_sub_queue=False, close_sub_queue_options=CMQC.MQCO_NONE):
        """Close the subscription"""
        mqlog.trace_entry("sub:close")

        if not self.__sub_handle:
            mqlog.trace_exit("sub:close", ep=1)
            raise PYIFError('Subscription not open.')

        rv = ibmmqc.MQCLOSE(self.__queue_manager.getHandle(), self.__sub_handle, sub_close_options)
        if rv[0]:
            mqlog.trace_exit("sub:close", ep=2, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1])

        if OTelFunctions.close:
            OTelFunctions.close(self)

        self.__sub_handle = None
        self.__sub_desc = None

        if close_sub_queue:
            _ = self.sub_queue.close(close_sub_queue_options)

        mqlog.trace_exit("sub:close")

    def subrq(self, sub_action: int = CMQC.MQSR_ACTION_PUBLICATION, sro=None) -> None:
        """Call the MQSUBRQ function. If the SRO object is supplied then it
        may be updated by the operation.
        """
        mqlog.trace_entry("sub:subrq")

        if sro:
            if not isinstance(sro, SRO):
                mqlog.trace_exit("sub:subrq", ep=1)
                raise TypeError('sro must be an SRO(sub request options) object.')
        else:
            sro = SRO()

        rv = ibmmqc.MQSUBRQ(self.__queue_manager.getHandle(), self.__sub_handle, sub_action, sro.pack())

        if rv[-2]:
            mqlog.trace_exit("sub:subrq", ep=2, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1])

        _ = sro.unpack(rv[0])
        mqlog.trace_exit("sub:subrq")

    def __del__(self):
        """ Close the Subscription, if it has been opened.
        """
        mqlog.trace_entry("sub:__del__")

        try:
            if self.__sub_handle:
                self.close()
        except PYIFError:
            pass

        mqlog.trace_exit("sub:__del__")
