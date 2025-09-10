# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows a simple execution of a PCF command to define a queue.
The "replace" option is used in case the object already exists. If you remove
that line and rerun the example, an error is generated.

The PCF parameters are built as a list of separate elements. Compare with the the dict-based approach
in the def_channel example.

The "admin" credentials are used to avoid needing to grant application users
additional privileges.
"""

import random
import ibmmq as mq

queue_manager = 'QM1'
channel = 'DEV.ADMIN.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'admin'
password = 'password'

queue_name = 'MYQUEUE.1'
queue_type = mq.CMQC.MQQT_LOCAL
# Set a random max depth so it will change on each execution
max_depth = random.randint(100,1000) * 100

args = []
args.append(mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME, String=queue_name))
args.append(mq.CFIN(Parameter=mq.CMQC.MQIA_Q_TYPE, Value=queue_type))
args.append(mq.CFIN(Parameter=mq.CMQC.MQIA_MAX_Q_DEPTH, Value=max_depth))
args.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_REPLACE, Value=mq.CMQCFC.MQRP_YES))

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

pcf = mq.PCFExecute(qmgr)
pcf.MQCMD_CREATE_Q(args)

qmgr.disconnect()

print("Done.")
