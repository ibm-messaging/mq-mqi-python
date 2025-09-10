# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows how asynchronous consume works. A function is passed
to the MQ library and invoked for message arrival and for certain events
"""

import time
import ibmmq as mq

class Status:
    """A simple way of holding the state without using explicit global variables"""
    ok = True
    connBroken = False

def cb_func(**kwargs):
    """
    The callback function is called with parameters:
       queue_manager, queue, md, gmo, msg, cbc
    The CallbackContext (cbd) structure holds the reasons for invocation, along with
    object and connection-related correlation buffers. Which we print out here
    """
    msg=kwargs['msg']
    cbc=kwargs['cbc']
    obj=kwargs['queue']
    qmgr=kwargs['queue_manager']

    print(f"In CB Func: QMgr={qmgr.get_name()} Q={obj.get_name() if obj else '<<None>>'} Msg={msg[:cbc.DataLength] if msg else '<<NONE>>'}")
    print(f"    CallType      = {cbc.CallType} [{mq.CMQSTRC.MQCBCT_DICT[cbc.CallType]}]")
    print(f"    CallbackArea  = {cbc.CallbackArea}")
    print(f"    ConnectionArea= {cbc.ConnectionArea}")

    if cbc.Reason != mq.CMQC.MQRC_NONE:
        print(f"Reason: {cbc.Reason} [{mq.CMQSTRC.MQRC_DICT[cbc.Reason]}]")

        # Going to assume for now that any event (other than Reason == 2033) is due to the connection
        # ending. A real program might need to be more specific as this assumption is
        # not always true.
        if cbc.CallType == mq.CMQC.MQCBCT_EVENT_CALL and cbc.Reason != mq.CMQC.MQRC_NO_MSG_AVAILABLE:
            Status.connBroken = True
        else:
            pass
        Status.ok = False

# Define the connection to the queue manager
queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

queue_name = 'DEV.QUEUE.1'
print("Using package version: ", mq.get_versions())

csp = mq.CSP()
csp.CSPUserId = user
csp.CSPPassword = password

qmgr = mq.connect(queue_manager, channel, conn_info, csp=csp)

od = mq.OD()
od.ObjectName = queue_name

q = mq.Queue(qmgr, od, mq.CMQC.MQOO_INPUT_AS_Q_DEF)

# Looking for any message on the queue
md = mq.MD()
gmo = mq.GMO()
gmo.Options = mq.CMQC.MQGMO_NO_SYNCPOINT
gmo.Options |= mq.CMQC.MQGMO_WAIT
gmo.WaitInterval = 3 * 1000 # convert to milliseconds

# Register a callback for the queue
cbd = mq.CBD()
cbd.CallbackFunction = cb_func
cbd.CallbackArea = b'My CB Area'
cbd.CallbackType = mq.CMQC.MQCBT_MESSAGE_CONSUMER
q.cb(operation=mq.CMQC.MQOP_REGISTER, cbd=cbd, md=md, gmo=gmo)

# Also register a callback for qmgr-wide events
cbd.CallbackFunction = cb_func
cbd.CallbackType = mq.CMQC.MQCBT_EVENT_HANDLER
cbd.CallbackArea = b'MY QGMGR CB AREA'
qmgr.cb(operation=mq.CMQC.MQOP_REGISTER, cbd=cbd)

# Start the async processing
ctlo = mq.CTLO()
ctlo.ConnectionArea = b'My Connection Area'
qmgr.ctl(mq.CMQC.MQOP_START, ctlo)

# Now wait for messages to be put to the queue or for qmgr events
# such as endmqm
while Status.ok:
    print("Sleeping ...")
    time.sleep(2)

if not Status.connBroken:
    qmgr.ctl(mq.CMQC.MQOP_STOP,ctlo)
    q.cb(operation=mq.CMQC.MQOP_DEREGISTER)

    q.close()
    qmgr.disconnect()

print("Done.")
