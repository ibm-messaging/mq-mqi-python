# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example demonstrates the "is_connected" property of a qmgr.
"""

import logging

import ibmmq as mq

logging.basicConfig(level=logging.INFO)

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)
logging.info('qmgr.is_connected=`%s`', qmgr.is_connected)

qmgr.disconnect()
