# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example browses a queue, formatting any known MQ header structures that it finds. It is
an extension to the DLH example, in that it deals with a number of other headers
including the XQH found on messages on transmission queues.
"""

import ibmmq as mq
from ibmmq import CMQC

queue_manager = 'QM1'
channel = 'DEV.ADMIN.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'admin'
password = 'password'

qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

ok = True

od = mq.OD()
# This is an XMITQ associated with a STOPPED channel, because we want to look at XQH processing
od.ObjectName = 'QM2.STOPPED'

q = mq.Queue(qmgr, od, CMQC.MQOO_BROWSE)

gmo = mq.GMO()
gmo.Options = CMQC.MQGMO_BROWSE_FIRST
cnt = 1

while ok:
    try:
        md = mq.MD()
        msg = q.get(None, md, gmo)

        print('------------------------------------')
        print(f"Message: {cnt}")
        cnt += 1

        gmo.Options = CMQC.MQGMO_BROWSE_NEXT
        fmt = md['Format']

        headers = True
        offset = 0
        ccsid = md['CodedCharSetId']

        # Iterate through headers that we might expect to see until there are no more.
        while headers:
            print()
            print('------------')
            print(f'Header: {bytes.decode(fmt, "utf8")}')
            print('------------')

            if fmt == CMQC.MQFMT_XMIT_Q_HEADER:
                # The XQH definition in Python has only the first part of the XQH in C, with the
                # embedded MQMD excluded. But We can extract both parts explicitly with XQH methods.
                xqh = mq.XQH().get_header(msg)
                print(xqh.to_string())

                # The to_string method changes structure contents, so we first stash the
                # Format in its bytes version. That matches the CMQC definition as a bytes-string.
                emd = mq.XQH().get_embedded_md(msg)
                fmt = emd['Format']
                ccsid = emd['CodedCharSetId']
                # print(f'G = {emd['GroupId']}')

                print()
                offset += CMQC.MQXQH_CURRENT_LENGTH

                print(emd.to_string())

            elif fmt == CMQC.MQFMT_MD_EXTENSION:
                # This will only be seen when looking at transmission queues with the XQH block
                mde = mq.MDE().unpack(msg[offset:offset + CMQC.MQMDE_CURRENT_LENGTH])
                fmt = mde['Format']
                ccsid = mde['CodedCharSetId']
                offset += CMQC.MQMDE_CURRENT_LENGTH

                print(mde.to_string())

            elif fmt == CMQC.MQFMT_RF_HEADER_2:
                rfh2 = mq.RFH2()
                rfh2.unpack(msg[offset:], 'utf8')
                fmt = rfh2['Format']
                offset += rfh2['StrucLength']

                print(rfh2.to_string())

            elif fmt == CMQC.MQFMT_DEAD_LETTER_HEADER:
                dlh = mq.DLH()
                dlh.unpack(msg[offset:offset + CMQC.MQDLH_CURRENT_LENGTH])
                fmt = dlh['Format']
                ccsid = dlh['CodedCharSetId']
                offset += CMQC.MQDLH_CURRENT_LENGTH

                print(dlh.to_string())

            else:
                headers = False

        # And now print the message body. Strings get converted, otherwise just print bytes
        print()
        print('Message Body:')

        if fmt == CMQC.MQFMT_STRING:
            cp = 'utf8'  # Assume a codepage, though we might want to use the ccsid to be more discriminating
            print(bytes.decode(msg[offset:], cp))
        else:
            print(msg[offset:])

        print()

    except mq.MQMIError as e:
        if e.reason == CMQC.MQRC_NO_MSG_AVAILABLE:
            print('No more messages.')
            ok = False
        else:
            raise
q.close()
qmgr.disconnect()
