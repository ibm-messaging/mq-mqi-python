# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows a simple execution of a PCF command to define a channel.
The "replace" option is used in case the object already exists. If you remove
that line and rerun the example, an error is generated.

The PCF parameters are passed as a dictionary of attribute name and value pairs. Compare with
the style used in the def_queue example.

The "admin" credentials are used to avoid needing to grant application users
additional privileges.
"""

import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.ADMIN.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'admin'
password = 'password'

channel_name = 'MYCHANNEL.1'
channel_type = mq.CMQXC.MQCHT_SVRCONN

args = {
    mq.CMQCFC.MQCACH_CHANNEL_NAME: channel_name,
    mq.CMQCFC.MQIACH_CHANNEL_TYPE: channel_type,
    mq.CMQCFC.MQIACF_REPLACE: mq.CMQCFC.MQRP_YES
}

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

pcf = mq.PCFExecute(qmgr)
pcf.MQCMD_CREATE_CHANNEL(args)

qmgr.disconnect()

print("Done.")
