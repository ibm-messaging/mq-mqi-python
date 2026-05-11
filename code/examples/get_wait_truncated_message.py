# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows reading a single message from a queue, waiting
for up to 5 seconds before giving up. In this scenario, we allow
the message to be truncated by giving a tiny buffer.
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
WAIT_INTERVAL = 5  # seconds

# Message Descriptor
md = mq.MD()

# Get Message Options
gmo = mq.GMO()
gmo.Options = mq.CMQC.MQGMO_WAIT | mq.CMQC.MQGMO_FAIL_IF_QUIESCING
gmo.Options |= mq.CMQC.MQGMO_ACCEPT_TRUNCATED_MSG
gmo.WaitInterval = WAIT_INTERVAL * 1000

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

queue = mq.Queue(qmgr, queue_name)
print("Waiting for message ...")
try:
    max_length = 2  # Something tiny to demonstrate that truncated messages can be handled
    message = queue.get(max_length, md, gmo)
except mq.MQMIError as e:
    if e.comp == mq.CMQC.MQCC_WARNING and e.reason == mq.CMQC.MQRC_TRUNCATED_MSG_ACCEPTED:
        print(e)
        print(f'Original length: {e.get('original_length')}')
        message = e.get('message')
    else:
        raise e

print("Message: ", message)
queue.close()

qmgr.disconnect()
