# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example generates an error when connecting. It shows both how the exception
can be caught and inspected, and how the values can be converted to readable text.
"""

import ibmmq as mq
from ibmmq import CMQC, CMQSTRC

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = 'localhost.invalid' # Note the hostname that should never be resolvable
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

try:
    qmgr = mq.connect(queue_manager, channel, conn_info, user, password)
except mq.MQMIError as e:
    if e.comp == CMQC.MQCC_FAILED and e.reason == CMQC.MQRC_HOST_NOT_AVAILABLE:
        print(f'Host `{host}` does not exist.')
    print(f"MQI Error is CC:{e.comp} [{CMQSTRC.MQCC_DICT[e.comp]}] RC:{e.reason} [{CMQSTRC.MQRC_DICT[e.reason]}]")
