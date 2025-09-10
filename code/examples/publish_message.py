# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows publishing a message to a topic
"""

from datetime import datetime
import ibmmq as mq

queue_manager = "QM1"
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

topic_string = 'dev/'

now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
message = 'Hello from Python! Published at ' + now

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

topic = mq.Topic(qmgr, topic_string = topic_string)
topic.open(open_opts=mq.CMQC.MQOO_OUTPUT)
topic.pub(message)
print("Message published OK")
topic.close()

qmgr.disconnect()

print("Done.")
