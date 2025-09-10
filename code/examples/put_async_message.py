# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows putting several messages to a queue using the ASYNC put option and
then using the MQSTAT operation to see if they all succeeded. The queue is toggled between
PUT(ENABLED) and PUT(DISABLED) to show when and how the error is reported. It is NOT generated
at MQPUT time.
"""

import ibmmq as mq

queue_manager = "QM1"
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)

cd = mq.CD()
cd.ConnectionName = conn_info
cd.ChannelName = channel


cno = mq.CNO()
cno.Options = mq.CMQC.MQCNO_CLIENT_BINDING

csp = mq.CSP()
csp.CSPUserId = 'app'
csp.CSPPassword = 'password'

queue_name = 'DEV.QUEUE.1'
message = 'Hello from Python: message '

qmgr = mq.connect(queue_manager, cd=cd, csp=csp, cno=cno)

od = mq.OD()
od.ObjectName = queue_name
queue = mq.Queue(qmgr, od, mq.CMQC.MQOO_SET | mq.CMQC.MQOO_OUTPUT)

pmo = mq.PMO()
pmo.Options = mq.CMQC.MQPMO_NO_SYNCPOINT | mq.CMQC.MQPMO_ASYNC_RESPONSE

for opt in (mq.CMQC.MQQA_PUT_ALLOWED,mq.CMQC.MQQA_PUT_INHIBITED):
    selectors={mq.CMQC.MQIA_INHIBIT_PUT:opt}
    queue.set(selectors)
    for i in range(0,10):
        md = mq.MD()
        queue.put(message + str(i),md, pmo)

    sts = qmgr.stat(mq.CMQC.MQSTAT_TYPE_ASYNC_ERROR)
    print("Queue: ",mq.CMQSTRC.MQQA_PUT_DICT[opt])
    print(f"Put Success: {sts.PutSuccessCount}")
    print(f"Put Failure: {sts.PutFailureCount}")
    print()

# Make sure the queue is back in "allowed" state when we end
selectors={mq.CMQC.MQIA_INHIBIT_PUT:mq.CMQC.MQQA_PUT_ALLOWED}
queue.set(selectors)

queue.close()
qmgr.disconnect()

print("Done.")
