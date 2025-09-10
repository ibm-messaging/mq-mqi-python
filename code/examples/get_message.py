# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows a simple and single immediate message retrieval. The message body
is the returned value from the get() function if it is successful. There is no waiting
for any message to arrive on the queue.
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

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

queue = mq.Queue(qmgr, queue_name)
message = queue.get()
print("Message:", message)
queue.close()

qmgr.disconnect()

print("Done.")
