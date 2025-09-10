""" All sorts of tests related to making the API PEP-8 compliant.
"""
import unittest

import ibmmq as mq

class TestApiTransitionPEP8(unittest.TestCase):
    """All sorts of tests related to making the API PEP-8 compliant."""

    def test_backward_compatibility(self):
        """Test backward-compatible.

        Makes sure all the relevant classes and methods have
        backward-compatible replacements.
        """
        self.assertEqual(mq.gmo, mq.GMO)
        self.assertEqual(mq.pmo, mq.PMO)
        self.assertEqual(mq.od, mq.OD)
        self.assertEqual(mq.md, mq.MD)
        self.assertEqual(mq.cd, mq.CD)
        self.assertEqual(mq.sco, mq.SCO)
        self.assertEqual(mq.QueueManager.connectWithOptions, mq.QueueManager.connect_with_options)
        self.assertEqual(mq.QueueManager.connectTCPClient, mq.QueueManager.connect_tcp_client)
        self.assertEqual(mq.QueueManager.getHandle, mq.QueueManager.get_handle)
        self.assertEqual(mq.PCFExecute.stringifyKeys, mq.PCFExecute.stringify_keys)
