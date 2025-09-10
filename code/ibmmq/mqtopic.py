"""Topic class: for MQOPEN, MQSUB, MQPUT (ie publish), MQCLOSE
"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqerrors import *
from ibmmq import CMQC, OD, PMO, ibmmqc, MQObject
from mqqargs import common_q_args
from mqsub import *

from mqqmgr import *

unicode = str

# Publish Subscribe support - Hannes Wagener 2011
class Topic(MQObject):
    """ Topic encapsulates all the Topic I/O operations, including
    publish/subscribe.  A QueueManager object must be already
    connected. The Topic may be opened implicitly on construction, or
    the open may be deferred until a call to open(), pub() or sub()
    The same as for Queue.

    The Topic to open is identified by a topic name and/or a topic
    string (in which case a default MQOD structure is created using
    those names), or by passing a ready constructed MQOD class.

    Refer to the 'Using topic strings' section in the MQ documentation
    for an explanation of how the topic name and topic string are combined
    to identify a particular topic.
    """

    def __real_open(self):
        """ Really open the topic.  Only do this in pub()?
        """
        if self.__topic_desc is None:
            raise PYIFError('The Topic Descriptor has not been set.')

        rv = ibmmqc.MQOPEN(self.__queue_manager.getHandle(),
                          self.__topic_desc.pack(), self.__open_opts)
        if rv[-2]:
            raise MQMIError(rv[-2], rv[-1])

        _ = self.__topic_handle = rv[0]
        _ = self.__topic_desc.unpack(rv[1])

    def __init__(self, queue_manager, topic_name=None, topic_string=None, topic_desc=None, open_opts=None):
        """ Associate a Topic instance with the QueueManager object 'queue_manager'
        and optionally open the Topic.

        If topic_desc is passed ignore topic_string and topic_name.

        If open_opts is passed, it specifies topic open options, and
        the topic is opened immediately. If open_opts is not passed,
        the queue open is deferred to a subsequent call to open(),
        pub().

        The following table clarifies when the Topic is opened:

        topic_desc  open_opts   When opened
             N       N       open()
             Y       N       open() or pub()
             Y       Y       Immediately
        """

        queue_manager = ensure_strings_are_bytes(queue_manager)
        topic_name = ensure_strings_are_bytes(topic_name)
        topic_string = ensure_strings_are_bytes(topic_string)

        self.__queue_manager = queue_manager
        self.__topic_handle = None
        self.__topic_desc = topic_desc
        self.__open_opts = open_opts

        self.topic_name = topic_name
        self.topic_string = topic_string

        if self.__topic_desc:
            if self.__topic_desc['ObjectType'] is not CMQC.MQOT_TOPIC:
                raise PYIFError('The Topic Descriptor ObjectType is not MQOT_TOPIC.')
            if self.__topic_desc['Version'] < CMQC.MQOD_VERSION_4:
                raise PYIFError('The Topic Descriptor Version must be at least MQOD_VERSION_4.')
        else:
            self.__topic_desc = self.__create_topic_desc(topic_name, topic_string)

        if self.__open_opts:
            self.__real_open()
        object_name = None
        if topic_name:
            object_name  = topic_name
        if topic_string:
            if object_name:
                object_name = object_name + "/" + topic_string
            else:
                object_name = topic_string
        super().__init__(object_name)

    @staticmethod
    def __create_topic_desc(topic_name, topic_string):
        """ Creates a topic object descriptor from a given topic_name/topic_string.
        """
        topic_name = ensure_strings_are_bytes(topic_name)
        topic_string = ensure_strings_are_bytes(topic_string)

        topic_desc = OD()
        topic_desc['ObjectType'] = CMQC.MQOT_TOPIC
        topic_desc['Version'] = CMQC.MQOD_VERSION_4

        if topic_name:
            topic_desc['ObjectName'] = topic_name

        if topic_string:
            topic_desc.set_vs('ObjectString', topic_string, 0, 0, 0)

        return topic_desc

    def __del__(self):
        """ Close the Topic, if it has been opened.
        """
        try:
            if self.__topic_handle:
                self.close()
        except (PYIFError, MQMIError):
            pass

    def open(self, topic_name=None, topic_string=None, topic_desc=None, open_opts=None):
        """ Open the Topic specified by topic_desc or create a object descriptor
        from topic_name and topic_string.
        If open_opts is passed, it defines the
        Topic open options, and the Topic is opened immediately. If
        open_opts is not passed, the Topic open is deferred until a
        subsequent pub() call.
        """
        topic_name = ensure_strings_are_bytes(topic_name)
        topic_string = ensure_strings_are_bytes(topic_string)

        if self.__topic_handle:
            raise PYIFError('The Topic is already open.')

        if topic_name:
            self.topic_name = topic_name

        if topic_string:
            self.topic_string = topic_string

        if topic_desc:
            self.__topic_desc = topic_desc
        else:
            self.__topic_desc = self.__create_topic_desc(self.topic_name, self.topic_string)

        if open_opts:
            self.__open_opts = open_opts
            self.__real_open()

    def pub(self, msg, *opts):
        """ Publish the string buffer 'msg' to the Topic. If the Topic is not
        already open, it is opened now. with the option 'MQOO_OUTPUT'.

        msg_desc is the MD() Message Descriptor for the
        message. If it is not passed, or is None, then a default md()
        object is used.

        put_opts is the PMO() Put Message Options structure
        for the put call. If it is not passed, or is None, then a
        default pmo() object is used.

        If msg_desc and/or put_opts arguments were supplied, they may be
        updated by the put operation.
        """

        msg_desc, put_opts = common_q_args(*opts)

        if not isinstance(msg, bytes):
            if isinstance(msg, str):
                msg = msg.encode(self.__queue_manager.bytes_encoding)
                msg_desc.CodedCharSetId = self.__queue_manager.default_ccsid
                msg_desc.Format = CMQC.MQFMT_STRING
            else:
                error_message = 'Message type is {0}. Convert to bytes.'
                raise TypeError(error_message.format(type(msg)))

        if put_opts is None:
            put_opts = PMO()

        # If queue open was deferred, open it for put now
        if not self.__topic_handle:
            self.__open_opts = CMQC.MQOO_OUTPUT
            self.__real_open()
        # Now send the message
        rv = ibmmqc.MQPUT(self.__queue_manager.getHandle(), self.__topic_handle, msg_desc.pack(), put_opts.pack(), msg)
        if rv[-2]:
            raise MQMIError(rv[-2], rv[-1])

        _ = msg_desc.unpack(rv[0])
        _ = put_opts.unpack(rv[1])

    # Create an alias as the underlying MQ verb is MQPUT
    put = pub

    def pub_rfh2(self, msg, *opts):
        """pub_rfh2(msg[, msgDesc, putOpts, [rfh2_header, ]])
        Put a RFH2 message. opts[2] is a list of RFH2 headers.
        MQMD and RFH2's must be correct.
        """

        rfh2_buff = b''
        if len(opts) >= 3:
            if opts[2] is not None:
                if not isinstance(opts[2], list):
                    raise TypeError('Third item of opts should be a list.')
                encoding = CMQC.MQENC_NATIVE
                if opts[0] is not None:
                    mqmd = opts[0]
                    encoding = mqmd['Encoding']

                for rfh2_header in opts[2]:
                    if rfh2_header is not None:
                        rfh2_buff = rfh2_buff + rfh2_header.pack(encoding)
                        encoding = rfh2_header['Encoding']

                msg = rfh2_buff + ensure_strings_are_bytes(msg)
            self.pub(msg, *opts[0:2])
        else:
            self.pub(msg, *opts)

    # Create an alias as the underlying MQ verb is MQPUT
    put_rfh2 = pub_rfh2

    def sub(self, *opts):
        """ Subscribe to the topic and return a Subscription object.
        A subscription to a topic can be made using an existing queue, either
        by pasing a Queue object or a string at which case the queue will
        be opened with default options.
        """
        sub_desc = None
        if len(opts) > 0:
            sub_desc = opts[0]

        sub_queue = None
        if len(opts) > 1:
            sub_queue = ensure_strings_are_bytes(opts[1])

        sub = Subscription(self.__queue_manager)
        sub.sub(sub_desc=sub_desc, sub_queue=sub_queue, topic_name=self.topic_name, topic_string=self.topic_string)

        return sub

    def close(self, options=CMQC.MQCO_NONE):
        """ Close the topic, using options.
        """
        if not self.__topic_handle:
            raise PYIFError('Topic not open.')

        rv = ibmmqc.MQCLOSE(self.__queue_manager.getHandle(), self.__topic_handle, options)
        if rv[0]:
            raise MQMIError(rv[-2], rv[-1])

        self.__topic_handle = None
        self.__topic_desc = None
        self.__open_opts = None
