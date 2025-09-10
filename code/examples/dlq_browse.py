# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example browses a queue, formatting any Dead Letter Headers that it finds
"""

import ibmmq as mq
from ibmmq import CMQC

# Use a local connection instead of client
qmgr = mq.connect('QM1')

ok = True

od = mq.OD()
od.ObjectName = "SYSTEM.DEAD.LETTER.QUEUE"
q = mq.Queue(qmgr, od, CMQC.MQOO_BROWSE)

gmo = mq.GMO()
gmo.Options = CMQC.MQGMO_BROWSE_FIRST
while ok:
    try:
        md = mq.MD()
        msg = q.get(None, md, gmo)
        gmo.Options = CMQC.MQGMO_BROWSE_NEXT
        fmt = md['Format']

        print("----------------------")
        if fmt == CMQC.MQFMT_DEAD_LETTER_HEADER:
            offset = CMQC.MQDLH_LENGTH_1

            # Print a neatly formatted version of the DLH - strings are real strings
            dlh = mq.DLH().get_header(msg)

            # The to_string method changes the DLH contents, so we stash the
            # Format in its bytes version
            fmt = dlh['Format']
            print("DLH: ", dlh.to_string())

            # If there is an RFH2, then also decode and print that. The encoding
            # for the RFH2 (big/little-endian indicator) comes from the DLH.
            if fmt == CMQC.MQFMT_RF_HEADER_2:
                rfh2 = mq.RFH2()
                rfh2.unpack(msg[offset:], dlh['Encoding'])
                print()
                print("RFH: ", rfh2.to_string())
                offset += rfh2['StrucLength']

            # And now print the message body
            print()
            print("MSG: ", msg[offset:])
        else:
            print(msg)
        print()

    except mq.MQMIError as e:
        if e.reason == CMQC.MQRC_NO_MSG_AVAILABLE:
            print("No more messages.")
            ok = False
        else:
            raise
q.close()
qmgr.disconnect()
