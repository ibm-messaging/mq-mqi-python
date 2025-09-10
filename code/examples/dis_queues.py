# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows a simple execution of a PCF command to display local queues matching a pattern
and then show their current depth.

The PCF parameters are built as a list of separate elements. Compare with the the dict-based approach
in the dis_channels example.

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

prefix = 'SYSTEM.*'
queue_type = mq.CMQC.MQQT_LOCAL

# The parameters needed for the INQUIRE Q command.
name_attrs = []
name_attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME,
                             String=prefix))
name_attrs.append(mq.CFIN(Parameter=mq.CMQC.MQIA_Q_TYPE,
                  Value=queue_type))

# The parameters needed for the INQUIRE Q STATUS command
status_attrs = []
status_attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME,
                               String=prefix))
status_attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_Q_STATUS_ATTRS,
                               Values=[mq.CMQCFC.MQIACF_ALL]))

qmgr = mq.connect(queue_manager, channel, conn_info, csp=csp)
pcf = mq.PCFExecute(qmgr, response_wait_interval=15000)

print()
print("Listing queues...")
try:
    response = pcf.MQCMD_INQUIRE_Q(name_attrs)
except mq.MQMIError as e:
    if e.comp == mq.CMQC.MQCC_FAILED and e.reason == mq.CMQC.MQRC_UNKNOWN_OBJECT_NAME:
        no_queues=True
        print('No queues matched given pattern.')
    else:
        raise
else:
    for queue_info in response:
        try:
            queue_name = queue_info[mq.CMQC.MQCA_Q_NAME]
            print(f'Found queue \"{mq.to_string(queue_name)}\"')
        except UnicodeError:
            print(f'Failure to decode msg: {queue_name}')
        except KeyError:
            print('Cannot find queue name in response: ', queue_info)

if not no_queues:
    print()
    print("Listing queue status...")
    try:
        response = pcf.MQCMD_INQUIRE_Q_STATUS(status_attrs)
    except mq.MQMIError as e:
        if e.comp == mq.CMQC.MQCC_FAILED and e.reason == mq.CMQC.MQRC_UNKNOWN_OBJECT_NAME:
            # Should not get here as we already know there are some queues matching the pattern
            print('No queues matched given pattern.')
        else:
            raise
    else:
        for queue_info in response:
            try:
                queue_name = queue_info[mq.CMQC.MQCA_Q_NAME]
                depth = queue_info[mq.CMQC.MQIA_CURRENT_Q_DEPTH]
                print(f'Found queue {queue_name} depth: {depth}')
            except KeyError as e:
                print('Failure to decode msg because ', e)

qmgr.disconnect()

print("Done.")
