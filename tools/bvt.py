""" A very simple basic test of the python package.
It does a local bindings connection to QM1, puts and gets a message.
"""

from datetime import datetime
import ibmmq as mq

od = mq.OD()
md = mq.MD()

od.ObjectName="DEV.QUEUE.1"

qmgr = mq.connect('QM1')
q = mq.Queue(qmgr, od, mq.CMQC.MQOO_OUTPUT | mq.CMQC.MQOO_INPUT_EXCLUSIVE)

msg_out='Hello from Python at ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
q.put(msg_out,md)
print("Message put:", msg_out)

msg_in = q.get()
print('Message got:', msg_in)

q.close()
qmgr.disconnect()
