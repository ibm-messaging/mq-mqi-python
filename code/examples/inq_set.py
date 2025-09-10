# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows how to use the MQINQ and MQSET operations
"""

from datetime import datetime
import random
import ibmmq as mq
from ibmmq import CMQC, CMQSTRC

def dump_attrs(attributes):
    """ Dump the map of attributes and their values."""
    print("Object attributes are: ")
    for k in attributes:
        try:
            k_desc = attr_dicts[k]
        except KeyError:
            k_desc = "Unknown"

        print(f"  {k} [{k_desc}] = {attributes[k]}")

# Merge all the attribute strings into a single dict
attr_dicts={}
for d in CMQSTRC.MQIA_DICT, CMQSTRC.MQIACF_DICT, CMQSTRC.MQIACH_DICT, \
         CMQSTRC.MQCA_DICT, CMQSTRC.MQCACF_DICT, CMQSTRC.MQCACH_DICT:
    attr_dicts.update(d)

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'

csp = mq.CSP()
csp.CSPUserId = user
csp.CSPPassword = password

queue_name = "DEV.QUEUE.1"

# Connect to qmgr
qmgr = mq.connect(queue_manager, channel, conn_info, csp=csp)

# This shows the original single-attribute version of MQINQ
# Note that we haven't explicitly opened the qmgr for INQUIRE
print("INQ (1) on QMgr")
print("QMgr version: ", qmgr.inquire(CMQC.MQCA_VERSION))

# And using the multi-selector model
print()
print("INQ (2) on QMgr")

selectors = [CMQC.MQCA_VERSION,
             CMQC.MQIA_COMMAND_LEVEL]
attrs = qmgr.inquire(selectors)
dump_attrs(attrs)

# Get access to the queue for INQ and SET
od = mq.OD()
od.ObjectName = queue_name
q = mq.Queue(qmgr, od, CMQC.MQOO_SET | CMQC.MQOO_INQUIRE)

# Doing an MQSET for the queue, to change two attributes in a single operation.
# Use a random number for trigger depth so we can see it change with repeated executions.
print()
print("SET on Queue")
now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
selectors={CMQC.MQCA_TRIGGER_DATA:now,
           CMQC.MQIA_TRIGGER_DEPTH:random.randint(1,99)
          }
# print("Set selectors: ", selectors)
dump_attrs(selectors)
q.set(selectors)

# Doing an MQINQ for a queue, using the multi-selector approach. This should show
# values including those we just did an MQSET for.
selectors=[CMQC.MQCA_Q_DESC,
           CMQC.MQIA_TRIGGER_DEPTH,
           CMQC.MQCA_BACKOUT_REQ_Q_NAME,
           CMQC.MQCA_TRIGGER_DATA,
           CMQC.MQIA_CURRENT_Q_DEPTH]
attrs = q.inquire(selectors)

print()
print("INQ on Queue")
dump_attrs(attrs)

q.close()
qmgr.disconnect()

print()
print("Done.")
