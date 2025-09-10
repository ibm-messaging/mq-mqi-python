# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows a simple execution of a PCF command to display connections
and extract the program names. It uses the ByteString constructor for PCF elements.

The "admin" credentials are used to avoid needing to grant application users
additional privileges. We use the CSP class to provide those credentials.
"""

import ibmmq as mq

no_queues=False
queue_manager = 'QM1'
channel = 'DEV.ADMIN.SVRCONN'
host = '127.0.0.1'
port = '1414'

conn_info = '%s(%s)' % (host, port)

csp = mq.CSP()
csp.CSPUserId = 'admin'
csp.CSPPassword = 'password'


# The parameters needed for the INQUIRE CONNECTIONS command
argsName   = {mq.CMQCFC.MQBACF_GENERIC_CONNECTION_ID: mq.ByteString('')}


qmgr = mq.connect(queue_manager, channel, conn_info, csp=csp)
pcf = mq.PCFExecute(qmgr, response_wait_interval=15000)

print()
print("Listing connections...")
try:
    response = pcf.MQCMD_INQUIRE_CONNECTION(argsName)
except mq.MQMIError as e:
    if e.comp == mq.CMQC.MQCC_FAILED and e.reason == mq.CMQCFC.MQRCCF_CONNECTION_ID_ERROR:
        no_conns=True
        print('No connections matched.') # Should never happen!
    else:
        raise
else:
    for conn_info in response:
        try:
            appl_tag = conn_info[mq.CMQCFC.MQCACF_APPL_TAG]
            # Convert the byte-form of the app name to a Python string.
            s_appl_tag = mq.to_string(appl_tag)
            print(f'Found application \"{s_appl_tag}\"')
            if s_appl_tag.startswith("python"):
                stashed_conn_tag = conn_info[mq.CMQCFC.MQBACF_CONN_TAG]
        except UnicodeError:
            print(f'Failure to decode msg: {appl_tag}')
        except KeyError:
            print('Cannot find queue name in response: ', conn_info)

qmgr.disconnect()

print("Done.")
