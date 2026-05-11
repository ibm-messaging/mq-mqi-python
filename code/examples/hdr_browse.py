# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example browses a queue, formatting any known MQ header structures that it finds. It is
an extension to the DLH example, in that it deals with a number of other headers
including the XQH found on messages on transmission queues. It also decodes PCF event messages.
"""

import sys

import ibmmq as mq
from ibmmq import CMQC

def lookup(k):
    '''Convert a PCF field to the corresponding string.
    '''

    s = mq.CMQSTRC.MQIA_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQIACF_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQIACH_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQIAMO_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQIAMO64_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQCA_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQCACF_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQCACH_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQCAMO_DICT.get(k)
    if s is None:
        s = mq.CMQSTRC.MQBACF_DICT.get(k)

    if s is None:
        s = f"<UNKNOWN> [{str(k)}]"
    return s


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


try:
    # If the qname is given as the only parm on command line, accept that
    od.ObjectName = sys.argv[1]
except IndexError:
    # This is an XMITQ associated with a STOPPED channel, because we want to look at XQH processing
    od.ObjectName = 'QM2.STOPPED'

print("Opening queue: ", od.ObjectName)

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
        encoding = md['Encoding']

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
                encoding = emd['Encoding']
                # print(f'G = {emd['GroupId']}')

                print()
                offset += CMQC.MQXQH_CURRENT_LENGTH

                print(emd.to_string())

            elif fmt == CMQC.MQFMT_MD_EXTENSION:
                # This will only be seen when looking at transmission queues with the XQH block
                mde = mq.MDE().unpack(msg[offset:offset + CMQC.MQMDE_CURRENT_LENGTH])
                fmt = mde['Format']
                ccsid = mde['CodedCharSetId']
                encoding = mde['Encoding']

                offset += CMQC.MQMDE_CURRENT_LENGTH

                print(mde.to_string())

            elif fmt == CMQC.MQFMT_RF_HEADER_2:
                rfh2 = mq.RFH2()
                rfh2.unpack(msg[offset:], encoding)
                fmt = rfh2['Format']
                offset += rfh2['StrucLength']

                print(rfh2.to_string())
                # Extract the separate folders ...
                folders = rfh2.get_folders()
                for folder in folders:
                    print(f'  Folder {folder} = ', rfh2[folder])

            elif fmt == CMQC.MQFMT_DEAD_LETTER_HEADER:
                dlh = mq.DLH()
                dlh.unpack(msg[offset:offset + CMQC.MQDLH_CURRENT_LENGTH])
                fmt = dlh['Format']
                ccsid = dlh['CodedCharSetId']
                encoding = dlh['Encoding']

                offset += CMQC.MQDLH_CURRENT_LENGTH

                print(dlh.to_string())

            elif fmt in [CMQC.MQFMT_ADMIN, CMQC.MQFMT_EVENT]:
                # This is not suitable for handling PCF commands and their responses. But it does work for reading other
                # PCF-formatted messages such as events. There are no message body contents or additional headers after
                # events, so set the offset to the end.

                # The unpack call returns everything already decoded. So we don't need to work out if the field is
                # an int or string. This method returns a tuple with the MQCFH as the second element
                evt = mq.PCFExecute.unpack(msg)

                parms = evt[0]
                cfh = evt[1]

                print(f"Command: {mq.CMQSTRC.MQCMD_DICT.get(cfh['Command'])}")

                # Print out the contents. There's no attempt to make this look pretty, unlike amqsevt. But it shows how
                # to walk through the elements.
                keys = parms.keys()
                for k in keys:
                    # An event message may contain groups. But there's no additional nesting.
                    # So we can walk through the group contents without needing to worry about recursion.
                    if mq.CMQC.MQGA_FIRST <= k <= mq.CMQC.MQGA_LAST:
                        group = parms[k]
                        for _, g in enumerate(group):
                            gkeys = g.keys()

                            print(f"  Group: {mq.CMQSTRC.MQGACF_DICT.get(k)}")
                            for gk in gkeys:
                                s = lookup(gk)
                                v = g[gk]
                                if s.startswith("MQCA"):
                                    v = mq.to_string(v)
                                print(f"    {s:<32s} : {v}")

                    else:
                        s = lookup(k)
                        v = parms[k]
                        if s.startswith("MQCA"):
                            v = mq.to_string(v)
                        print(f"  {s:<32s} : {v}")

                offset += len(msg)
                headers = False

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
