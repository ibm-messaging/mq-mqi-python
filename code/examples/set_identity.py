# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows how to put a message with a specific context value. It will
fail (2035) if the user does not have the authority to use the option.
"""
import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
queue_name = 'DEV.QUEUE.1'
message = 'Hello from Python!'
context_applid = 'MyApplId'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

qmgr = mq.connect(queue_manager, channel, conn_info) # , user, password)

od = mq.OD()
od.ObjectName = queue_name

queue = mq.Queue(qmgr)
queue.open(od, mq.CMQC.MQOO_OUTPUT | mq.CMQC.MQOO_SET_IDENTITY_CONTEXT)

md = mq.MD()
md.ApplIdentityData = context_applid

pmo = mq.PMO()
pmo.Options = mq.CMQC.MQPMO_SET_IDENTITY_CONTEXT

queue.put(message,md,pmo)

queue.close()
qmgr.disconnect()

print("Done.")
