# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows a request/reply pattern, with the requester waiting for
a reply message that has a CorrelId matching the request's MsgId. This is
one common pattern for linking requests and responses.
The program continues indefinitely, until interrupted from the keyboard.
"""

import logging
import threading
import time
import uuid

import ibmmq as mq

logging.basicConfig(level=logging.INFO)

# Queue manager name
queue_manager = 'QM1'

# Connection host and port
conn_info = '127.0.0.1(1414)'

# Channel to transfer data through
channel = 'DEV.APP.SVRCONN'

# Request Queue
request_queue_name = 'DEV.QUEUE.1'

# ReplyTo Queue
replyto_queue_name = 'DEV.QUEUE.2'

message_prefix = 'Test Data. '

class Producer(threading.Thread):
    """ A base class for any producer used in this example.
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True

        cd = mq.CD()
        cd.ChannelName = channel
        cd.ConnectionName = conn_info
        cd.ChannelType = mq.CMQXC.MQCHT_CLNTCONN
        cd.TransportType = mq.CMQXC.MQXPT_TCP
        self.qm = mq.QueueManager(None)
        self.qm.connect_with_options(queue_manager, opts=mq.CMQC.MQCNO_HANDLE_SHARE_NO_BLOCK,
                                   cd=cd)

        self.req_queue = mq.Queue(self.qm, request_queue_name)
        self.replyto_queue = mq.Queue(self.qm, replyto_queue_name)


class RequestProducer(Producer):
    """ Instances of this class produce an infinite stream of request messages
    and wait for appropriate responses on reply-to queues.
    """

    def run(self):

        while True:
            # Put the request message.
            put_mqmd = mq.MD()

            # Set the MsgType to request.
            put_mqmd['MsgType'] = mq.CMQC.MQMT_REQUEST

            # Set up the ReplyTo QUeue/Queue Manager (Queue Manager is automatically
            # set by MQ).
            put_mqmd['ReplyToQ'] = replyto_queue_name
            put_mqmd['ReplyToQMgr'] = queue_manager

            # Set up the put options - do it with NO_SYNCPOINT so that the request
            # message is committed immediately.
            put_opts = mq.PMO(Options=mq.CMQC.MQPMO_NO_SYNCPOINT + mq.CMQC.MQPMO_FAIL_IF_QUIESCING)

            # Create a random message.
            message = message_prefix + uuid.uuid4().hex

            self.req_queue.put(message, put_mqmd, put_opts)
            logging.info('Put request message.  Message: [%s]', message)

            # Set up message descriptor for get.
            get_mqmd = mq.MD()

            # Set the get CorrelId to the put MsgId (which was set by MQ on the put1).
            get_mqmd['CorrelId'] = put_mqmd['MsgId']

            # Set up the get options.
            get_opts = mq.GMO(
                Options=mq.CMQC.MQGMO_NO_SYNCPOINT + mq.CMQC.MQGMO_FAIL_IF_QUIESCING + mq.CMQC.MQGMO_WAIT)

            # Version must be set to at least 2 to use the GMO MatchOptions field.
            get_opts['Version'] = mq.CMQC.MQGMO_VERSION_2

            # Tell MQ that we are matching on CorrelId.
            get_opts['MatchOptions'] = mq.CMQC.MQMO_MATCH_CORREL_ID

            # Set the wait timeout of half a second.
            get_opts['WaitInterval'] = 500

            # Open the replyto queue and get response message,
            replyto_queue = mq.Queue(self.qm, replyto_queue_name, mq.CMQC.MQOO_INPUT_SHARED)
            response_message = replyto_queue.get(None, get_mqmd, get_opts)

            logging.info('Got response message `%s`', response_message)

            time.sleep(1)

class ResponseProducer(Producer):
    """ Instances of this class wait for request messages and produce responses.
    """

    def run(self):

        # Request message descriptor, will be reset after processing each
        # request message.
        request_md = mq.MD()

        # Get Message Options
        gmo = mq.GMO()
        gmo.Options = mq.CMQC.MQGMO_WAIT | mq.CMQC.MQGMO_FAIL_IF_QUIESCING
        gmo.WaitInterval = 500 # Half a second

        queue = mq.Queue(self.qm, request_queue_name)

        keep_running = True

        while keep_running:
            try:
                # Wait up to to gmo.WaitInterval for a new message.
                request_message = queue.get(None, request_md, gmo)

                # Create a response message descriptor with the CorrelId
                # set to the value of MsgId of the original request message.
                response_md = mq.MD()
                response_md.CorrelId = request_md.MsgId

                response_message = 'Response to message %s' % request_message
                self.replyto_queue.put(response_message, response_md)

                # Reset the MsgId, CorrelId & GroupId so that we can reuse
                # the same 'md' object again.
                request_md.MsgId = mq.CMQC.MQMI_NONE
                request_md.CorrelId = mq.CMQC.MQCI_NONE
                request_md.GroupId = mq.CMQC.MQGI_NONE

            except mq.MQMIError as e:
                if e.comp == mq.CMQC.MQCC_FAILED and e.reason == mq.CMQC.MQRC_NO_MSG_AVAILABLE:
                    # No messages, that's OK, we can ignore it.
                    pass
                else:
                    # Some other error condition.
                    raise

req = RequestProducer()
resp = ResponseProducer()

req.start()
resp.start()

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    req.qm.disconnect()
