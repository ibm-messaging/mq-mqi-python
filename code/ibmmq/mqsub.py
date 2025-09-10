"""Subscription class: for MQSUB, MQSUBRQ, MQCLOSE.
Will reference a managed queue for the MQGET if that has been requested.
"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from typing import Union

from mqcommon import *
from mqerrors import *
from ibmmq import CMQC, SD, SRO, MQObject, Queue, ibmmqc

class Subscription(MQObject):
    """ Encapsulates a subscription to a topic.
    """
    def __init__(self, queue_manager, sub_desc=None, sub_name=None,
                 sub_queue=None, sub_opts=None, topic_name=None, topic_string=None):

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
            object_name  = topic_name
        if topic_string:
            if object_name:
                object_name = object_name + "/" + topic_string
            else:
                object_name = topic_string
        super().__init__(object_name)

    def get_sub_queue(self) -> Queue:
        """ Return the subscription queue.
        """
        return self.sub_queue

    def get(self, max_length: Union[None, int] = None, *opts):  # pylint: disable=keyword-arg-before-vararg
        """ Get a publication from the Queue.
        """
        return self.sub_queue.get(max_length, *opts)

    def get_rfh2(self, max_length:Union[None, int] = None, *opts) -> bytes:  # pylint: disable=keyword-arg-before-vararg
        """ Get a publication from the Queue.
        """
        return self.sub_queue.get_rfh2(max_length, *opts)

    def sub(self, sub_desc=None, sub_queue=None, sub_name=None, sub_opts=None,
            topic_name=None, topic_string=None):
        """ Subscribe to a topic, alter or resume a subscription.
        Executes the MQSUB call with parameters.
        The subscription queue can be either passed as a Queue object or a
        Queue object handle.
        """
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
            raise MQMIError(rv[-2], rv[-1])

        sub_desc.unpack(rv[0])
        self.__sub_desc = sub_desc
        self.sub_queue = Queue(self.__queue_manager)
        self.sub_queue.set_handle(rv[1])
        self.__sub_handle = rv[2]

    def close(self, sub_close_options=CMQC.MQCO_NONE, close_sub_queue=False, close_sub_queue_options=CMQC.MQCO_NONE):
        """Close the subscription"""

        if not self.__sub_handle:
            raise PYIFError('Subscription not open.')

        rv = ibmmqc.MQCLOSE(self.__queue_manager.getHandle(), self.__sub_handle, sub_close_options)
        if rv[0]:
            raise MQMIError(rv[-2], rv[-1])

        self.__sub_handle = None
        self.__sub_desc = None

        if close_sub_queue:
            _ = self.sub_queue.close(close_sub_queue_options)

    def subrq(self, sub_action:int = CMQC.MQSR_ACTION_PUBLICATION, sro=None) -> None:
        """Call the MQSUBRQ function. If the SRO object is supplied then it
        may be updated by the operation.
        """
        if sro:
            if not isinstance(sro, SRO):
                raise TypeError('sro must be an SRO(sub request options) object.')
        else:
            sro = SRO()

        rv = ibmmqc.MQSUBRQ(self.__queue_manager.getHandle(), self.__sub_handle, sub_action, sro.pack())

        if rv[-2]:
            raise MQMIError(rv[-2], rv[-1])

        _ = sro.unpack(rv[0])

    def __del__(self):
        """ Close the Subscription, if it has been opened.
        """
        try:
            if self.__sub_handle:
                self.close()
        except PYIFError:
            pass
