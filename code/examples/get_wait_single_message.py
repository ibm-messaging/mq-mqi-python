# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows reading a single message from a queue, waiting
for up to 5 seconds before giving up.
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
gmo.WaitInterval = 5000 # 5 seconds

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

queue = mq.Queue(qmgr, queue_name)
print("Waiting for message ...")
message = queue.get(None, md, gmo)
print("Message: ", message)
queue.close()

qmgr.disconnect()
