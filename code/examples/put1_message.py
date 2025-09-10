# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows putting a message to a queue using the put1 (MQPUT1) method
"""

import ibmmq as mq

queue_manager = "QM1"
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

queue_name = 'DEV.QUEUE.1'
message = 'Hello from Python!'

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

qmgr.put1(queue_name,message)

qmgr.disconnect()

print("Done.")
