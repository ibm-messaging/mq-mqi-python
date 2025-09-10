# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example shows the simplest connection mechanism to a queue manager. Only
the name is required. By default, this will try a local connection.

But setting MQSERVER and either running in an environment where only the MQ client components
are installed or setting MQ_CONNECT_TYPE=CLIENT will try to use a network connection.
"""

import ibmmq as mq

queue_manager = 'QM1'
qmgr = mq.connect(queue_manager)

print("Connection succeeded.")

qmgr.disconnect()
