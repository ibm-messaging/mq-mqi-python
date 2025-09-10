# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows reading all the messages on a queue.
"""

import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
queue_name = 'DEV.QUEUE.1'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

# Message Descriptor
md = mq.MD()

# Get Message Options
gmo = mq.GMO()
gmo.Options = mq.CMQC.MQGMO_WAIT | mq.CMQC.MQGMO_FAIL_IF_QUIESCING
gmo.MatchOptions = mq.CMQC.MQMO_NONE
gmo.WaitInterval = 3000 # 3 seconds

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)
queue = mq.Queue(qmgr, queue_name)

keep_running = True

while keep_running:
    try:
        # Wait up to to gmo.WaitInterval for a new message.
        message = queue.get(None, md, gmo)

        # Process the message here..
        print("Message: ", message)

        # Reset the MsgId, CorrelId & GroupId so that we can reuse
        # the same 'md' object again.
        md.MsgId = mq.CMQC.MQMI_NONE
        md.CorrelId = mq.CMQC.MQCI_NONE
        md.GroupId = mq.CMQC.MQGI_NONE

    except mq.MQMIError as e:
        if e.comp == mq.CMQC.MQCC_FAILED and e.reason == mq.CMQC.MQRC_NO_MSG_AVAILABLE:
            # No messages, that's OK, we can ignore it.
            print("No more messages.")
            keep_running = False
        else:
            # Some other error condition.
            raise

queue.close()
qmgr.disconnect()
