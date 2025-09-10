# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows how to set an option for a channel connection. Though
since these are negotiated with the qmgr, it will only take effect if both
sides agree.
"""

import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
queue_name = 'DEV.QUEUE.1'
message = 'Hello from Python!' * 10000
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

cd = mq.CD()
cd.MsgCompList[0] = mq.CMQXC.MQCOMPRESS_ZLIBHIGH

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

queue = mq.Queue(qmgr, queue_name)
queue.put(message)
queue.close()

qmgr.disconnect()

print("Done.")
