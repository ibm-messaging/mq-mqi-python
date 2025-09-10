# More examples are at https://github.com/ibm-messaging/mq-dev-patterns
# and in code/examples in the source distribution.

"""
This example sets up a TLS connection to the queue manager. It requires that
a suitable channel has been defined, and that certificates are in the appropriate
keystores, locally and on the qmgr.
"""
import logging

import ibmmq as mq

logging.basicConfig(level=logging.INFO)

queue_manager = 'QM1'
channel = 'SYSTEM.SSL.SVRCONN.1'
host = '127.0.0.1'
port = '1414'

conn_info = '%s(%s)' % (host, port)
ssl_cipher_spec = 'ANY_TLS12_OR_HIGHER'
key_repo_location = '/var/mqm/ssl/key'
message = 'Hello from Python!'

queue_name = 'DEV.QUEUE.1'

cd = mq.CD()
cd.ChannelName = channel
cd.ConnectionName = conn_info
cd.ChannelType = mq.CMQXC.MQCHT_CLNTCONN
cd.TransportType = mq.CMQXC.MQXPT_TCP
cd.SSLCipherSpec = ssl_cipher_spec

sco = mq.SCO()
sco.KeyRepository = key_repo_location

# Force a client connection
cno = mq.CNO()
cno.Options = mq.CMQC.MQCNO_CLIENT_BINDING

qmgr = mq.QueueManager(None)
qmgr.connect_with_options(queue_manager, cd, sco, cno=cno)
print("Connection successful.")

put_queue = mq.Queue(qmgr, queue_name)
put_queue.put(message)

get_queue = mq.Queue(qmgr, queue_name)
logging.info('Here is the message again: [%s]', get_queue.get())

put_queue.close()
get_queue.close()
qmgr.disconnect()

print("Done.")
