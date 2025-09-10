# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example demonstrates setting and viewing message properties. It assumes
the queue is empty before starting. The value and class associated with the property
are logged.
"""

import logging

import ibmmq as mq

def read_props_wildcard():
    """A function to iterate through the properties, as it's used twice in this example"""
    props_to_read = True
    opts = mq.CMQC.MQIMPO_INQ_FIRST
    while props_to_read:
        try:
            property_value, prop_name  = get_msg_h.properties.get('usr.%',impo_options=opts)
            logging.info('  Property name: `%s`, property value: `%s` type %s', prop_name, property_value, type(property_value))
            opts = mq.CMQC.MQIMPO_INQ_NEXT

        except mq.MQMIError as e:
            if e.reason == mq.CMQC.MQRC_PROPERTY_NOT_AVAILABLE:
                logging.info('No more properties')
                props_to_read = False
            else:
                raise e

logging.basicConfig(level=logging.INFO)

queue_manager = 'QM1'
channel = 'DEV.APP.SVRCONN'
host = '127.0.0.1'
port = '1414'
queue_name = 'DEV.QUEUE.1'

conn_info = '%s(%s)' % (host, port)
user = 'app'
password = 'password'
logging.info('Starting message property example.')

# Connect to the qmgr
qmgr = mq.connect(queue_manager, channel, conn_info, user, password)

# Create a message handle to manipulate properties
put_msg_h = mq.MessageHandle(qmgr)

# Define the property names we are going to use
property_base_name = 'Property_'

p = []
p += [property_base_name + '0']
p += [property_base_name + '1']
p += [property_base_name + '2']

# Set values of different types
put_msg_h.properties.set(p[0], 'MyStringPropVal') # Default type is CMQC.MQTYPE_STRING
put_msg_h.properties.set(p[1], 42, property_type=mq.CMQC.MQTYPE_INT32)
put_msg_h.properties.set(p[2], 3.13, property_type=mq.CMQC.MQTYPE_FLOAT64)


pmo = mq.PMO(Version=mq.CMQC.MQPMO_VERSION_3) # PMO v3 is required if you want to use message handles
pmo.OriginalMsgHandle = put_msg_h.msg_handle
opts = mq.CMQC.MQOO_OUTPUT
put_md = mq.MD(Version=mq.CMQC.MQMD_CURRENT_VERSION)

put_queue = mq.Queue(qmgr, queue_name, opts)
put_queue.put(b'Property testing', put_md, pmo)

# Now retrieve the message and inspect its properties
get_msg_h = mq.MessageHandle(qmgr)

gmo = mq.GMO(Version=mq.CMQC.MQGMO_CURRENT_VERSION)
gmo.Options = mq.CMQC.MQGMO_PROPERTIES_IN_HANDLE + mq.CMQC.MQGMO_SYNCPOINT
gmo.MsgHandle = get_msg_h.msg_handle

get_md = mq.MD()
get_queue = mq.Queue(qmgr, queue_name)
message_body = get_queue.get(None, get_md, gmo)

# Two different ways to iterate through the query
# In the first, we don't know the property name so use a wildcard
logging.info('')
logging.info('Message received')
logging.info('Using wildcards to retrieve properties:')
read_props_wildcard()

# In the second, we ask for an explicit property
logging.info('')
logging.info('Using explicit names to retrieve properties:')

for prop in p:
    property_value  = get_msg_h.properties.get(prop)
    logging.info('  Property name: `%s`, property value: `%s` type %s', prop, property_value, type(property_value))

# Delete one of the properties
logging.info('')
logging.info("Deleting property: '%s'", p[1])
get_msg_h.properties.dlt(p[1])

# And see if the delete was successful
logging.info('')
logging.info('Using wildcards to retrieve properties again:')
read_props_wildcard()

# Cleanup and exit
put_msg_h.dlt()
get_msg_h.dlt()

put_queue.close()
get_queue.close()

# The message was read in syncpoint, so we need to commit the removal
qmgr.commit()
qmgr.disconnect()
