""" A very simple basic test of the python package.
It does a local bindings connection to QM1, puts and gets a message.
"""

from datetime import datetime
import ibmmq

od = ibmmq.OD()
md = ibmmq.MD()

od.ObjectName="DEV.QUEUE.1"

qmgr = ibmmq.connect('QM1')
q = ibmmq.Queue(qmgr, od, ibmmq.CMQC.MQOO_OUTPUT | ibmmq.CMQC.MQOO_INPUT_EXCLUSIVE)

now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
msg_out='Hello from Python at ' + now
q.put(msg_out,md)
print("Message put:", msg_out)

#msg_in=""
msg_in = q.get()
print('Message got:', msg_in)

q.close()
qmgr.disconnect()
