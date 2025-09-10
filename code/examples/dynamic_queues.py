# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows use of a dynamic queue as a reply destination. It sends
a message but the code to wait for and read the reply messaage would have to be
added. Alongside working with another application that does the actual reply.
See the reply_to_queues example for one such.

Note that the user must have "get" and "dsp" authorities against the model queue.
"""

import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'
message = 'Please reply to a dynamic queue, thanks.'
dynamic_queue_prefix = 'MY.REPLIES.*'
request_queue = 'DEV.QUEUE.1'

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

# Dynamic queue's object descriptor.
dyn_od = mq.OD()
dyn_od.ObjectName = 'SYSTEM.DEFAULT.MODEL.QUEUE'
dyn_od.DynamicQName = dynamic_queue_prefix

# Open the dynamic queue.
dyn_input_open_options = mq.CMQC.MQOO_INPUT_EXCLUSIVE
dyn_queue = mq.Queue(qmgr, dyn_od, dyn_input_open_options)
dyn_queue_name = dyn_od.ObjectName.strip()

# Prepare a Message Descriptor for the request message.
md = mq.MD()
md.ReplyToQ = dyn_queue_name

# Send the message.
queue = mq.Queue(qmgr, request_queue)
queue.put(message, md)

# Get and process the response here...

dyn_queue.close()
queue.close()
qmgr.disconnect()

print("Done.")
