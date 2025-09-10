# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

""""
This example shows a way to connect as a client to a remote queue manager, passing
credentials as explicit positional parameters to the connect() method.
"""
import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)
print("Connection succeeded.")

qmgr.disconnect()
