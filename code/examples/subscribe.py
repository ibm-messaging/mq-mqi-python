# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows subscribing to a topic and reading publications sent to it. Use this
in conjunction with the publish_message example.
"""

import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
topic_string = 'dev/'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

# Message Descriptor
md = mq.MD()

# Get Message Options
gmo = mq.GMO()
gmo.Options = mq.CMQC.MQGMO_WAIT | mq.CMQC.MQGMO_FAIL_IF_QUIESCING
gmo.MatchOptions = mq.CMQC.MQMO_NONE
gmo.WaitInterval = 5000 # 5 seconds

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

sub_desc = mq.SD()
sub_desc.Options = mq.CMQC.MQSO_CREATE
sub_desc.Options |= mq.CMQC.MQSO_MANAGED
sub_desc.set_vs("ObjectString", topic_string)

sub = mq.Subscription(qmgr)
sub.sub(sub_desc=sub_desc)

keep_running = True

while keep_running:
    try:
        # Wait up to to gmo.WaitInterval for a new message.
        message = sub.get(None, md, gmo)

        # Process the message here..
        print("Received publication: ", message)

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

sub.close()
qmgr.disconnect()
