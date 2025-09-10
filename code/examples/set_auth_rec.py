# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows how to build a PCF command to set a user's authority.
The "principal" is set and will always work on systems where UserExternal is configured, allowing
unknown userids to be used in these commands. Otherwise, additional configuration would
be required on the queue manager to define users or groups; something we want to avoid in
examples wherever possible.
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

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)
pcf = mq.PCFExecute(qmgr)

principal_entity = [b'app']
authorities = [mq.CMQCFC.MQAUTH_BROWSE,
               mq.CMQCFC.MQAUTH_INQUIRE]

args = {mq.CMQCFC.MQCACF_AUTH_PROFILE_NAME: 'DEV.QUEUE.1',
        mq.CMQCFC.MQIACF_OBJECT_TYPE: mq.CMQC.MQOT_Q,
        mq.CMQCFC.MQIACF_AUTH_ADD_AUTHS: authorities,
        mq.CMQCFC.MQCACF_PRINCIPAL_ENTITY_NAMES: principal_entity}

result = pcf.MQCMD_SET_AUTH_REC(args)

qmgr.disconnect()

print("Done.")
