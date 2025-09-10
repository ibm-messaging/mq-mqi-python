# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows how to put a message with an alternate userid. It will
fail (2035) if the real user does not have the authority to use the option, and
if the alternate user does not have the authority to put to the queue.
"""
import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
queue_name = 'DEV.QUEUE.1'
message = 'Hello from Python!'
alternate_user_id = 'altusr'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

od = mq.OD()
od.ObjectName = queue_name
od.AlternateUserId = alternate_user_id

queue = mq.Queue(qmgr)
queue.open(od, mq.CMQC.MQOO_OUTPUT | mq.CMQC.MQOO_ALTERNATE_USER_AUTHORITY)
queue.put(message)

queue.close()
qmgr.disconnect()

print("Done.")
