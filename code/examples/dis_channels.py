# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows a simple execution of a PCF command to display channels matching a pattern. The PCF
parameters are passed as a dictionary of attribute name and value pairs. Compare with the style used in the
dis_queues example.

The "admin" credentials are used to avoid needing to grant application users
additional privileges.
"""

import logging

import ibmmq as mq

logging.basicConfig(level=logging.INFO)

queue_manager = 'QM1'
channel = 'DEV.ADMIN.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'admin'
password = 'password'

prefix = 'SYSTEM.*'

args = {mq.CMQCFC.MQCACH_CHANNEL_NAME: prefix}

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)
pcf = mq.PCFExecute(qmgr)

try:
    response = pcf.MQCMD_INQUIRE_CHANNEL(args)
except mq.MQMIError as e:
    if e.comp == mq.CMQC.MQCC_FAILED and e.reason == mq.CMQC.MQRC_UNKNOWN_OBJECT_NAME:
        logging.info('No channels matched prefix `%s`', prefix)
    else:
        raise
else:
    for channel_info in response:
        channel_name = channel_info[mq.CMQCFC.MQCACH_CHANNEL_NAME]
        logging.info('Found channel `%s`', channel_name)

qmgr.disconnect()

print("Done.")
