# -*- coding: utf8 -*-
"""Test base API."""
from sys import version_info
import unittest

import ibmmq as mq

import utils
from test_setup import Tests

class TestGet(Tests):
    """Test Queue.get() method."""

    def setUp(self):
        """Initialize test environment."""
        super().setUp()

        self.create_queue(self.queue_name)

        self.message = b'12345'
        self.buffer_length = 3

        self.queue = mq.Queue(self.qmgr,
                                 self.queue_name,
                                 mq.CMQC.MQOO_INPUT_AS_Q_DEF | mq.CMQC.MQOO_OUTPUT)

    def tearDown(self):
        """Delete created objects."""
        if self.queue:
            self.queue.close()

        self.delete_queue(self.queue_name)

        super().tearDown()

    def _put_message(self):
        md = mq.MD()
        self.queue.put(self.message, md)

        return md

    ###########################################################################
    #
    # Real Tests start here
    #
    ###########################################################################

    def test_get_nontruncated(self):
        """Test nontruncated without buffer."""
        self._put_message()

        md_get = mq.MD()
        message = self.queue.get(None, md_get)

        self.assertEqual(self.message, message)

    def test_get_nontruncated_0(self):
        """Test nontruncated with zero buffer length."""
        self._put_message()

        md_get = mq.MD()
        try:
            self.queue.get(0, md_get)
        except mq.MQMIError as ex:
            self.assertEqual(ex.reason, mq.CMQC.MQRC_TRUNCATED_MSG_FAILED)
            self.assertEqual(ex.original_length,  # pylint: disable=no-member
                             len(self.message))

    def test_get_nontruncated_short(self):
        """Test nontruncated with short buffer."""
        self._put_message()

        md_get = mq.MD()
        try:
            self.queue.get(self.buffer_length, md_get)
        except mq.MQMIError as ex:
            self.assertEqual(ex.reason, mq.CMQC.MQRC_TRUNCATED_MSG_FAILED)
            self.assertEqual(ex.original_length,  # pylint: disable=no-member
                             len(self.message))

    def test_get_nontruncated_enough(self):
        """Test nontruncated with big enough buffer."""
        self._put_message()

        md_get = mq.MD()
        message = self.queue.get(len(self.message), md_get)

        self.assertEqual(self.message, message)

    def test_get_truncated(self):
        """Test truncated without buffer."""
        self._put_message()
        gmo = mq.GMO()
        gmo.Options = mq.CMQC.MQGMO_ACCEPT_TRUNCATED_MSG

        md_get = mq.MD()
        try:
            self.queue.get(0, md_get, gmo)
        except mq.MQMIError as ex:
            self.assertEqual(ex.reason, mq.CMQC.MQRC_TRUNCATED_MSG_ACCEPTED)
            self.assertEqual(ex.message, b'')  # pylint: disable=no-member
            self.assertEqual(ex.original_length,  # pylint: disable=no-member
                             len(self.message))

    def test_get_truncated_0(self):
        """Test truncated with zero buffer length."""
        self._put_message()
        gmo = mq.GMO()
        gmo.Options = mq.CMQC.MQGMO_ACCEPT_TRUNCATED_MSG

        md_get = mq.MD()
        try:
            self.queue.get(0, md_get, gmo)
        except mq.MQMIError as ex:
            self.assertEqual(ex.reason, mq.CMQC.MQRC_TRUNCATED_MSG_ACCEPTED)
            self.assertEqual(ex.message, b'')  # pylint: disable=no-member
            self.assertEqual(ex.original_length,  # pylint: disable=no-member
                             len(self.message))

    def test_get_truncated_short(self):
        """Test truncated with short buffer."""
        self._put_message()
        gmo = mq.GMO()
        gmo.Options = mq.CMQC.MQGMO_ACCEPT_TRUNCATED_MSG

        md_get = mq.MD()
        try:
            self.queue.get(self.buffer_length, md_get, gmo)
        except mq.MQMIError as ex:
            self.assertEqual(ex.reason, mq.CMQC.MQRC_TRUNCATED_MSG_ACCEPTED)
            self.assertEqual(ex.message,  # pylint: disable=no-member
                             self.message[:self.buffer_length])
            self.assertEqual(ex.original_length,  # pylint: disable=no-member
                             len(self.message))

    def test_get_truncated_enough(self):
        """Test truncated with big buffer."""
        self._put_message()
        gmo = mq.GMO()
        gmo.Options = mq.CMQC.MQGMO_ACCEPT_TRUNCATED_MSG

        md_get = mq.MD()
        message = self.queue.get(len(self.message), md_get, gmo)

        self.assertEqual(self.message, message)

    def test_get_nontruncated_big_msg(self):
        """Test get nontruncated big message"""
        md_put = mq.MD()
        if version_info.major >= 3:
            self.queue.put(bytes(4097), md_put)
        else:
            self.queue.put(bytes(b'\0'*4097), md_put)

        md_get = mq.MD()
        message = self.queue.get(None, md_get)

        self.assertEqual(len(message), 4097)
        self.assertEqual(md_put.PutDate, md_get.PutDate)

    def test_get_truncated_big_msg(self):
        """Test get nontruncated big message"""
        md_put = mq.MD()
        if version_info.major >= 3:
            self.queue.put(bytes(4097), md_put)
        else:
            self.queue.put(bytes(b'\0'*4097), md_put)
        gmo = mq.GMO()
        gmo.Options = mq.CMQC.MQGMO_ACCEPT_TRUNCATED_MSG

        md_get = mq.MD()
        try:
            _ = self.queue.get(None, md_get, gmo)
        except mq.MQMIError as ex:
            self.assertEqual(ex.reason, mq.CMQC.MQRC_TRUNCATED_MSG_ACCEPTED)
            self.assertEqual(ex.original_length,  # pylint: disable=no-member
                             4097)
            self.assertEqual(len(ex.message), 0)
            self.assertEqual(md_put.PutDate, md_get.PutDate)

    def test_put_string(self):
        """Test that putting a non-ASCII string is correctly converted during GET"""
        md = mq.MD()
        # file coding defined (utf-8)
        self.queue.put('тест', md)  # Cyrillic (non-ascii) characters

        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        # In Python3 can use unicode string
        self.assertEqual(md.Format, mq.CMQC.MQFMT_STRING)
        self.assertEqual(md.CodedCharSetId, 1208)

    def test_put_string_with_ccsid_and_format(self):
        """Test putting a string with explicit ccsid"""
        md = mq.MD(
            CodedCharSetId=1208,  # coding: utf8 is set
            Format=mq.CMQC.MQFMT_STRING)

        self.queue.put('тест', md)  # Cyrillic (non-ascii) characters

        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        # In Python3 can use unicode string
        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        self.assertEqual(md.Format, mq.CMQC.MQFMT_STRING)
        self.assertEqual(md.CodedCharSetId, 1208)

    def test_put_unicode(self):
        """Put a string that's already encoded to unicode bytes"""
        self.queue.put('\u0442\u0435\u0441\u0442')  # Unicode characters

        md = mq.MD()
        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        self.assertEqual(md.Format, mq.CMQC.MQFMT_STRING)
        self.assertEqual(md.CodedCharSetId, 1208)

    def test_put_unicode_with_ccsid_and_format(self):
        """Put a string that's already encoded, and be explicit about the CCSID"""
        md = mq.MD(
            CodedCharSetId=1208,
            Format=mq.CMQC.MQFMT_STRING)

        self.queue.put('\u0442\u0435\u0441\u0442', md)  # Unicode characters

        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        self.assertEqual(md.Format, mq.CMQC.MQFMT_STRING)
        self.assertEqual(md.CodedCharSetId, 1208)

    def test_put1_bytes(self):
        """Use PUT1 to test string handling with pre-converted unicode bytes"""
        md = mq.MD()
        self.qmgr.put1(self.queue_name, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82', md)  # Non-ascii characters

        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        self.assertEqual(md.Format, mq.CMQC.MQFMT_NONE)

    def test_put1_string(self):
        """Use PUT1 to test string handling with a unicode string"""
        md = mq.MD()
        # file coding defined (utf-8)
        self.qmgr.put1(self.queue_name, 'тест', md)  # Cyrillic (non-ascii) characters

        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        # In Python3 can use unicode string
        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        self.assertEqual(md.Format, mq.CMQC.MQFMT_STRING)
        self.assertEqual(md.CodedCharSetId, 1208)

    def test_put1_string_with_ccsid_and_format(self):
        """Use PUT1 to test string handling with a unicode string and explicit CCSID"""
        md = mq.MD(
            CodedCharSetId=1208,  # coding: utf8 is set
            Format=mq.CMQC.MQFMT_STRING)

        self.qmgr.put1(self.queue_name, 'тест', md)  # Cyrillic (non-ascii) characters

        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        # In Python3 can use unicode string
        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        self.assertEqual(md.Format, mq.CMQC.MQFMT_STRING)
        self.assertEqual(md.CodedCharSetId, 1208)

    def test_put1_unicode(self):
        """Use PUT1 to test string handling with a pre-converted unicode string"""
        self.qmgr.put1(self.queue_name, '\u0442\u0435\u0441\u0442')  # Unicode characters

        md = mq.MD()
        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        self.assertEqual(md.Format, mq.CMQC.MQFMT_STRING)
        self.assertEqual(md.CodedCharSetId, 1208)

    def test_put1_unicode_with_ccsid_and_format(self):
        """Use PUT1 to test string handling with a pre-converted unicode string and explicit CCSID"""
        md = mq.MD(
            CodedCharSetId=1208,
            Format=mq.CMQC.MQFMT_STRING)

        self.qmgr.put1(self.queue_name, '\u0442\u0435\u0441\u0442', md)  # Unicode characters

        gmo = mq.GMO()
        gmo.Options = gmo.Options & ~ mq.CMQC.MQGMO_CONVERT
        message = self.queue.get(None, md, gmo)

        self.assertEqual(message, b'\xd1\x82\xd0\xb5\xd1\x81\xd1\x82')
        self.assertEqual(md.Format, mq.CMQC.MQFMT_STRING)
        self.assertEqual(md.CodedCharSetId, 1208)

    def test_put1(self):
        """Simplest use of PUT1"""
        input_msg = b'Hello world!'
        self.qmgr.put1(self.queue_name, input_msg)
        # now get the message from the queue
        queue = mq.Queue(self.qmgr, self.queue_name)
        result_msg = queue.get()
        self.assertEqual(input_msg, result_msg)

    def test_inquire(self):
        """Test MQINQ on the qmgr"""
        attribute = mq.CMQC.MQCA_Q_MGR_NAME
        expected_value = self.queue_manager
        attribute_value = self.qmgr.inquire(attribute)
        self.assertEqual(len(attribute_value), mq.CMQC.MQ_Q_MGR_NAME_LENGTH)
        self.assertTrue(utils.strcmp(attribute_value.strip(), expected_value))


if __name__ == "__main__":
    unittest.main()
