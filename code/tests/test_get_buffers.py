"""Test Get Buffers usage.

The setup of this test puts lots of messages of random sizes to a single queue.

The test then opens the same queue multiple times for input and picks one of the
handles at random to do an MQGET. That should test that reuse of the buffers, the
automatic buffer resizing, and the map clearance during MQCLOSE and MQDISC are OK.

The number of messages retrieved ought to be the same as the number put. Similarly, the
total bytes ought to be the same in and out.
"""
import random
import ibmmq as mq

from test_setup import Tests  # noqa
from test_setup import main   # pylint: disable=no-name-in-module

alpha = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

class TestGetBuffer(Tests):
    """Class for MQ Get Buffer testing."""

    max_puts = 200
    put_bytes = 0

    @classmethod
    def setUpClass(cls):
        """Initialize test environment."""
        super(TestGetBuffer, cls).setUpClass()

        # max length of queue names is 48 characters
        cls.queue_name = "{prefix}GB.QUEUE".format(prefix=cls.prefix)

    @classmethod
    def tearDownClass(cls):
        """Tear down test environment."""
        super(TestGetBuffer, cls).tearDownClass()

    def setUp(self):
        """Set up tesing environment."""
        super().setUp()

        self.create_queue(self.queue_name)
        self.get_queue = mq.Queue(self.qmgr, self.queue_name)

        self.clear_queue(self.get_queue)
        self.get_queue.close()

        # Put messages
        self.put_queue = mq.Queue(self.qmgr, self.queue_name)

        for _ in range(0, self.max_puts):
            # Build a message of random printable chars
            msg_len = random.randint(0, 32768)  # Message length
            buf = ""
            for _ in range(0, msg_len):
                c = alpha[random.randint(0, len(alpha) - 1)]
                buf += (c)
            self.put_queue.put(buf)
            self.put_bytes += msg_len
        self.put_queue.close()

    def tearDown(self):
        """Delete the created objects."""
        if self.queue_name:
            self.delete_queue(self.queue_name)

        super().tearDown()

    def clear_queue(self, queue):
        """Clear a queue via repeated gets"""
        try:
            while True:
                queue.get()
        except mq.MQMIError as e:
            if e.reason == mq.CMQC.MQRC_NO_MSG_AVAILABLE:
                return
            raise e

    def test_gets(self):
        """Get the messages from a random hObj """
        queues = []
        got_messages = 0
        got_bytes = 0

        # Open the same queue multiple times
        for _ in range(0, self.max_puts):
            od = mq.OD()
            od.ObjectName = self.queue_name
            q = mq.Queue(self.qmgr)
            q.open(od, mq.CMQC.MQOO_INPUT_SHARED)
            o = [q, False]
            queues.append(o)

        # Now we've got the hObj handles, get message from one of them
        for _ in range(0, len(queues)):
            r = random.randint(0, len(queues) - 1)
            o = queues[r]

            try:
                md = mq.MD()
                gmo = mq.GMO()
                gmo.Options = mq.CMQC.MQGMO_FAIL_IF_QUIESCING
                message = o[0].get(None, md, gmo)
                print(f"Msg: {message[0:20]} len: {len(message)}", flush=True)
                got_messages += 1
                got_bytes += len(message)
            except mq.MQMIError as e:
                print(e, flush=True)
            o[1] = True

        # Only close the queues that we've done an MQGET for
        for q in queues:
            # print(f"Looking at {q}", flush=True)
            if q[1]:
                try:
                    o = q[0]
                    o.close()
                except mq.MQMIError:
                    pass

        self.assertEqual(self.max_puts, got_messages)
        self.assertEqual(self.put_bytes, got_bytes)


if __name__ == '__main__':
    main(module='test_get_buffers')
