# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and

"""
This example shows a way to connect to a remote queue manager using
the CSP class to provide credentials
"""
import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

csp = mq.CSP()
csp.CSPUserId = user
csp.CSPPassword = password

qmgr = mq.connect(queue_manager, channel, conn_info, csp=csp)
print("Connection succeeded.")
qmgr.disconnect()
