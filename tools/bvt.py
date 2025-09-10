"""
A very simple basic test of the python package.
It does a local bindings connection to QM1, puts and gets a message.
"""

import ibmmq

qn="DEV.QUEUE.1"

od = ibmmq.OD()
md = ibmmq.MD()
md.MsgId=b'ThisIsAMsgId'

# Different styles of setting the fields
od.ObjectName=qn
od['ObjectName']=qn
od.set(ObjectName=qn)

queue_manager = ibmmq.connect('QM1')

q = ibmmq.Queue(queue_manager, od, ibmmq.CMQC.MQOO_OUTPUT | ibmmq.CMQC.MQOO_INPUT_EXCLUSIVE)
q.put('Hello from Python!',md)

odr = od.to_string()
print("QName = ", odr['ObjectName'])

msg = q.get()
print('Here is the message:', msg)

q.close()
queue_manager.disconnect()
