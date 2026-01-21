"""Queue class: implements Queue-based MQI verbs including
MQOPEN, MQPUT, MQGET, MQCLOSE, MQCB, MQINQ, MQSET
"""

# Copyright (c) 2025, 2026 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.
from mqcommon import *
from mqerrors import *
from ibmmq import CMQC, PMO, GMO, RFH2, ibmmqc, MQObject
from mqqmgr import *

import mqinq
import mqqargs

import mqcallback

import mqlog

# unicode = str

class Queue(MQObject):
    """ Queue encapsulates all the Queue I/O operations, including
    open/close and get/put. A QueueManager object must be already
    connected. The Queue may be opened implicitly on construction, or
    the open may be deferred until a call to open(), put() or
    get(). The Queue to open is identified either by a queue name
    string (in which case a default MQOD structure is created using
    that name), or by passing a ready constructed MQOD class.
    """
    def __real_open(self):
        """Really open the queue."""
        mqlog.trace_entry("queue:__real_open")
        if self.__q_desc is None:
            mqlog.trace_exit("queue:__real_open", ep=1)
            raise PYIFError('The Queue Descriptor has not been set.')
        rv = ibmmqc.MQOPEN(self.__q_mgr.get_handle(), self.__q_desc.pack(), self.__open_opts)
        if rv[-2]:
            mqlog.trace_exit("queue:__real_open", ep=2, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1])

        self.__q_handle = rv[0]
        self.__q_desc.unpack(rv[1])

        if OTelFunctions.open:
            OTelFunctions.open(self, self.__q_desc, self.__open_opts, None)
        mqlog.trace_exit("queue:__real_open")

    def __init__(self, qmgr: QueueManager, *opts):
        """ Associate a Queue instance with the QueueManager object 'qmgr'
        and optionally open the Queue.

        If q_desc is passed, it identifies the Queue either by name (if
        its a string), or by MQOD (if its a OD() instance). If
        q_desc is not defined, then the Queue is not opened
        immediately, but deferred to a subsequent call to open().

        If openOpts is passed, it specifies queue open options, and
        the queue is opened immediately. If open_opts is not passed,
        the queue open is deferred to a subsequent call to open(),
        put() or get().

        The following table clarifies when the Queue is opened:

           qDesc  openOpts   When opened
             N       N       open()
             Y       N       open() or get() or put()
             Y       Y       Immediately
        """
        mqlog.trace_entry("queue:__init__")

        self.__q_mgr = qmgr
        self.__q_handle = self.__q_desc = self.__open_opts = None
        ln = len(opts)
        if ln > 2:
            mqlog.trace_exit("queue:__init__", ep=1)
            raise TypeError('Too many args')
        if ln > 0:
            self.__q_desc = mqqargs._make_q_desc(opts[0])
        if ln == 2:
            self.__open_opts = opts[1]
            self.__real_open()

        if self.__q_desc:
            try:
                q_name = self.__q_desc.ObjectName
            except AttributeError:
                q_name = ""
        else:
            q_name = ""
        super().__init__(q_name)
        mqlog.trace_exit("queue:__init__")

    def __del__(self):
        """ Close the queue, if it has been opened.
        """
        mqlog.trace_entry("queue:__del__")
        if self.__q_handle:
            try:
                self.close()
            except (PYIFError, MQMIError):
                pass
        mqlog.trace_exit("queue:__del__")

    def open(self, q_desc, *opts):
        """ Open the queue specified by q_desc. q_desc identifies the Queue
        either by name (if its a string), or by MQOD (if its a
        OD() instance). If openOpts is passed, it defines the
        queue open options, and the Queue is opened immediately. If
        openOpts is not passed, the Queue open is deferred until a
        subsequent put() or get() call.
        """
        mqlog.trace_entry("queue:open")

        ln = len(opts)
        if ln > 1:
            mqlog.trace_exit("queue:open", ep=1)
            raise TypeError('Too many args')
        if self.__q_handle:
            mqlog.trace_exit("queue:open", ep=2)
            raise PYIFError('The Queue is already open')
        self.__q_desc = mqqargs._make_q_desc(q_desc)
        if ln == 1:
            self.__open_opts = opts[0]
            self.__real_open()
        mqlog.trace_exit("queue:open")

    def put(self, msg, *opts):
        """ Put the string buffer 'msg' on the queue. If the queue is not
        already open, it is opened now with the option 'MQOO_OUTPUT'.

        m_desc is the MQ() Message Descriptor for the
        message. If it is not passed, or is None, then a default md()
        object is used.

        put_opts is the PMO() Put Message Options structure
        for the put call. If it is not passed, or is None, then a
        default pmo() object is used.

        If m_desc and/or put_opts arguments were supplied, they may be
        updated by the put operation.
        """

        mqlog.trace_entry("queue:put")

        m_desc, put_opts = mqqargs.common_q_args(*opts)
        if not isinstance(msg, bytes):
            if isinstance(msg, str):
                msg = msg.encode(self.__q_mgr.bytes_encoding)
                m_desc.CodedCharSetId = self.__q_mgr.default_ccsid
                m_desc.Format = CMQC.MQFMT_STRING
            else:
                error_message = 'Message type is {0}. Convert to bytes.'
                mqlog.trace_exit("queue:put", ep=1)
                raise TypeError(error_message.format(type(msg)))

        if put_opts is None:
            put_opts = PMO()

        # If queue open was deferred, open it for put now
        if not self.__q_handle:
            self.__open_opts = CMQC.MQOO_OUTPUT
            self.__real_open()

        if OTelFunctions.put_trace_before:
            OTelFunctions.put_trace_before(self.__q_mgr, m_desc, put_opts, msg)

        # Now send the message
        rv = ibmmqc.MQPUT(self.__q_mgr.get_handle(), self.__q_handle, m_desc.pack(), put_opts.pack(), msg)
        if rv[-2]:
            mqlog.trace_exit("queue:put", ep=2, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1])
        _ = m_desc.unpack(rv[0])
        _ = put_opts.unpack(rv[1])

        if OTelFunctions.put_trace_after:
            OTelFunctions.put_trace_after(self.__q_mgr, put_opts)
        mqlog.trace_exit("queue:put")

    def put_rfh2(self, msg, *opts):
        """ Put a RFH2 message. opts[2] is a list of RFH2 headers. MQMD and RFH2's must be correct.
        """
        mqlog.trace_entry("queue:put_rfh2")

        ensure_not_unicode(msg)  # Python 3 bytes check

        rfh2_buff = b''
        if len(opts) >= 3:
            if opts[2] is not None:
                if not isinstance(opts[2], list):
                    mqlog.trace_exit("queue:put_rfh2", ep=1)
                    raise TypeError('Third item of opts should be a list.')
                encoding = CMQC.MQENC_NATIVE
                if opts[0] is not None:
                    mqmd = opts[0]
                    encoding = mqmd['Encoding']

                for rfh2_header in opts[2]:
                    if rfh2_header is not None:
                        rfh2_buff = rfh2_buff + rfh2_header.pack(encoding)
                        encoding = rfh2_header['Encoding']

                msg = rfh2_buff + msg
            self.put(msg, *opts[0:2])
        else:
            self.put(msg, *opts)
        mqlog.trace_exit("queue:put_rfh2")

    # pylint complains about a couple of things here which we will ignore in order to maintain
    # backwards compatibility
    def get(self, maxLength=None, *opts, **kwargs):  # pylint: disable=invalid-name,keyword-arg-before-vararg
        """ Return a message from the queue. If the queue is not already
        open, it is opened now with the option 'MQOO_INPUT_AS_Q_DEF'.

        maxLength, if present, specifies the maximum length for the
        message. If the message received exceeds maxLength, then the
        behavior is as defined by MQI and the get_opts argument.

        If maxLength is not specified, or is None, then the entire
        message is returned regardless of its size. This may require
        multiple calls to the underlying MQGET API. Other get() variants
        use max_length as the parameter, but this one has to stay in camelCase
        for backwards compatibility.

        m_desc is the MD() Message Descriptor for receiving
        the message. If it is not passed, or is None, then a default
        MD() object is used.

        get_opts is the GMO() Get Message Options
        structure for the get call. If it is not passed, or is None,
        then a default GMO() object is used.

        If m_desc and/or get_opts arguments were supplied, they may be
        updated by the get operation.

        If you want to supply the MD or GMO values, then you must also
        supply a maxLength value.
        """
        mqlog.trace_entry("queue:get")

        removed = 0

        otel_options = kwargs['otel_options'] if 'otel_options' in kwargs else None
        if otel_options and not isinstance(otel_options, OTelOptions):
            mqlog.trace_exit("queue:get", ep=1)
            raise TypeError('otel_options must be instance of OTelOptions.')

        max_length = maxLength  # Work with the "right" name style from here on
        m_desc, get_opts = mqqargs.common_q_args(*opts)
        if get_opts is None:
            get_opts = GMO()

        # If queue open was deferred, open it for put now
        if not self.__q_handle:
            self.__open_opts = CMQC.MQOO_INPUT_AS_Q_DEF
            self.__real_open()

        if max_length is None:
            if get_opts.Options & CMQC.MQGMO_ACCEPT_TRUNCATED_MSG:
                length = 0
            else:
                length = 4096  # Try to read short message in one call
        else:
            length = max_length

        if OTelFunctions.get_trace_before:
            OTelFunctions.get_trace_before(self.__q_mgr, self, get_opts, False)

        rv = ibmmqc.MQGET(self.__q_mgr.get_handle(), self.__q_handle, m_desc.pack(), get_opts.pack(), length)

        if not rv[-2]:
            # Everything is OK
            _ = m_desc.unpack(rv[1])
            _ = get_opts.unpack(rv[2])

            if OTelFunctions.get_trace_after:
                removed = OTelFunctions.get_trace_after(self, get_opts, m_desc, otel_options, rv[0], False)
            # This is the most common route, so no "ep" on this trace point
            mqlog.trace_exit("queue:get")
            return rv[0][removed:]

        # Accept truncated message
        if ((rv[-1] == CMQC.MQRC_TRUNCATED_MSG_ACCEPTED) or
                # Do not reread message with original length
                (rv[-1] == CMQC.MQRC_TRUNCATED_MSG_FAILED and max_length is not None) or
                # Other errors
                (rv[-1] != CMQC.MQRC_TRUNCATED_MSG_FAILED)):
            if rv[-2] == CMQC.MQCC_WARNING:
                _ = m_desc.unpack(rv[1])
                _ = get_opts.unpack(rv[2])
            mqlog.trace_exit("queue:get", ep=3, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1], message=rv[0], original_length=rv[-3])

        # Message truncated, but we know its size. Do another MQGET
        # to retrieve it from the queue.
        rv = ibmmqc.MQGET(self.__q_mgr.get_handle(), self.__q_handle, m_desc.pack(), get_opts.pack(), rv[-3])
        if rv[-2]:
            mqlog.trace_exit("queue:get", ep=4, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1])

        _ = m_desc.unpack(rv[1])
        _ = get_opts.unpack(rv[2])

        # Only process OTel tracing if we actually got a message
        if rv[-2] == CMQC.MQCC_OK or rv[-1] == CMQC.MQRC_TRUNCATED_MSG_ACCEPTED:
            if OTelFunctions.get_trace_after:
                removed = OTelFunctions.get_trace_after(self, get_opts, m_desc, otel_options, rv[0], False)

        if rv[0]:
            mqlog.trace_exit("queue:get", ep=5)
            return rv[0][removed:]

        mqlog.trace_exit("queue:get", ep=6)
        return rv[0]

    def get_no_jms(self, max_length=None, *args, **kwargs):  # pylint: disable=keyword-arg-before-vararg
        """Get a message but force there to be no properties returned."""
        mqlog.trace_entry("queue:get_no_jms")

        md, gmo = mqqargs.common_q_args(*args)
        if not gmo:
            gmo = GMO()
        gmo.Options = gmo.Options | CMQC.MQGMO_NO_PROPERTIES | CMQC.MQGMO_FAIL_IF_QUIESCING

        rv = self.get(max_length, md, gmo, kwargs)
        mqlog.trace_exit("queue:get_no_jms")
        return rv

    get_no_rfh2 = get_no_jms

    def get_rfh2(self, max_length=None, *opts, **kwargs):  # pylint: disable=keyword-arg-before-vararg
        """ Get a message and attempt to unpack the rfh2 headers.
        opts[2] should be a empty list.
        Unpacking only attempted if Format in previous header is
        CMQC.MQFMT_RF_HEADER_2.
        """
        mqlog.trace_entry("queue:get_rfh2")

        if len(opts) >= 3:
            if opts[2] is not None:
                if not isinstance(opts[2], list):
                    mqlog.trace_exit("queue:get_rfh2", ep=1)
                    raise TypeError('Third item of opts should be a list.')

                msg = self.get(max_length, *opts[0:2], kwargs)
                mqmd = opts[0]
                rfh2_headers = []
                # If format is not CMQC.MQFMT_RF_HEADER_2 then do not parse.
                frmt = mqmd['Format']
                while frmt == CMQC.MQFMT_RF_HEADER_2:
                    rfh2_header = RFH2()
                    rfh2_header.unpack(msg)
                    rfh2_headers.append(rfh2_header)
                    msg = msg[rfh2_header['StrucLength']:]
                    frmt = rfh2_header['Format']
                opts[2].extend(rfh2_headers)
            else:
                mqlog.trace_exit("queue:get_rfh2", ep=2)
                raise AttributeError('get_opts cannot be None if passed.')
        else:
            msg = self.get(max_length, *opts, kwargs)

        mqlog.trace_exit("queue:get_rfh2")

        return msg

    def close(self, options: int = CMQC.MQCO_NONE) -> None:
        """ Close a queue, using options.
        """
        mqlog.trace_entry("queue:close")

        if not self.__q_handle:
            mqlog.trace_exit("queue:close", ep=1)
            raise PYIFError('not open')
        rv = ibmmqc.MQCLOSE(self.__q_mgr.get_handle(), self.__q_handle, options)
        if rv[0]:
            mqlog.trace_exit("queue:close", ep=1, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1])

        if OTelFunctions.close:
            OTelFunctions.close(self)

        self.__q_handle = self.__q_desc = self.__open_opts = None
        mqlog.trace_exit("queue:close")

    def inquire(self, selectors: Union[int, list[int]]) -> Union[Any, dict[int, Any]]:
        """ Inquire on queue attributes. If the queue is not already
        open, it is opened for Inquire.

        If the selectors parameter is a single value, then that specific
        attribute's value is returned (string or int).

        If the selectors parameter is a list of values, then a dict is returned
        where all the values are stored using each element of the selectors as the keys.
        """

        if not self.__q_handle:
            self.__open_opts = CMQC.MQOO_INQUIRE
            self.__real_open()
        # mqinq.inq will throw the exception if necessary
        rv = mqinq.common_inq(self.__q_mgr.get_handle(), self.__q_handle, selectors)
        return rv

    # Create an alias that is closer to the real MQI function name
    inq = inquire

    def set(self, *args) -> None:
        """ Sets a queue's attributes

        Old-style interface has two parameters, selector and value.
        Newer interface has a single parameter, a dict that maps between selectors and values.
        """
        mqlog.trace_entry("queue:set")

        if not self.__q_handle:
            self.__open_opts = CMQC.MQOO_SET
            self.__real_open()
        rv = mqinq.common_set(self.__q_mgr.get_handle(), self.__q_handle, args)

        if rv[1]:
            mqlog.trace_exit("queue:set", ep=1, rc=rv[-1])
            raise MQMIError(rv[-2], rv[-1])
        mqlog.trace_exit("queue:set")

    def set_handle(self, queue_handle):
        """ Sets the queue handle in the case when a handle was returned from a previous MQ call.
        """
        self.__q_handle = queue_handle

    def get_handle(self) -> int:
        """ Get the queue handle.
        """
        return self.__q_handle

    def get_name(self) -> str:
        """Return the name of the queue as a stripped string"""
        v = self.__q_desc.ObjectName
        return self.to_string(v)

    def get_queue_manager(self) -> QueueManager:
        """ Get the queue manager object.
        """
        return self.__q_mgr

    # Setting up a callback - pass it to the function
    # common to both Queues and QMgrs
    def cb(self, **kwargs: dict[str, Any]) -> None:
        """cb(operation=operation, md=mqmd,gmo=mqgmo,cbd=mqcbd)
        Register or Deregister a Callback function for asynchronous
        message consumption.

        The cbd.CallbackFunction must be defined as (dict[str,Any]) with
        entries for queue_manager,queue,md,gmo,cbc,msg.
        """
        mqlog.trace_entry("queue:cb")
        mqcallback.real_cb(self, kwargs)
        mqlog.trace_exit("queue:cb")
