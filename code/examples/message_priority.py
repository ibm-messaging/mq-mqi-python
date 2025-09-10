# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example demonstrates setting and viewing the priority of a message. A
random number in the valid range is set in the message.
"""

import logging
import random
import ibmmq as mq

logging.basicConfig(level=logging.INFO)

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
queue_name = 'DEV.QUEUE.1'
message = 'Hello from Python!'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

priority = random.randint(0,9)

put_md = mq.MD()
put_md.Priority = priority

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

put_queue = mq.Queue(qmgr, queue_name)
put_queue.put(message, put_md)

get_md = mq.MD()
get_queue = mq.Queue(qmgr, queue_name)
message_body = get_queue.get(None, get_md)

logging.info('Received a message, priority `%s`.', get_md.Priority)

put_queue.close()
get_queue.close()
qmgr.disconnect()

print("Done.")
