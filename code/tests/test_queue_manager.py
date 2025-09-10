""" Tests for mq.QueueManager class.
"""

# pylint: disable=missing-function-docstring,no-name-in-module

import unittest

import ibmmq as mq

import config
import utils

try:
    from typing import List
except ImportError:
    pass

from test_setup import Tests
from test_setup import main

class TestQueueManager(Tests):
    """Testing the queue manager"""
    CHCKCLNT = None  # type: int

    @classmethod
    def setUpClass(cls):
        """Initialize test environment."""
        super(TestQueueManager, cls).setUpClass()

        # Get CHCKCLNT value
        attrs = []  # type: List[mq.MQOpts]
        attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_Q_MGR_ATTRS,
                                Values=[mq.CMQC.MQCA_CONN_AUTH]))
        results = cls.pcf.MQCMD_INQUIRE_Q_MGR(attrs)
        conn_auth_name = results[0][mq.CMQC.MQCA_CONN_AUTH]

        attrs = []  # type: List[mq.MQOpts]

        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_AUTH_INFO_NAME,
                                String=conn_auth_name))
        attrs.append(mq.CFIN(Parameter=mq.CMQC.MQIA_AUTH_INFO_TYPE,
                                Value=mq.CMQC.MQAIT_IDPW_OS))
        attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_AUTH_INFO_ATTRS,
                                Values=[mq.CMQC.MQIA_CHECK_CLIENT_BINDING]))

        results = cls.pcf.MQCMD_INQUIRE_AUTH_INFO(attrs)
        cls.CHCKCLNT = results[0][mq.CMQC.MQIA_CHECK_CLIENT_BINDING]

        # Add required rights for pinging QMGR
        attrs = []  # type: List[mq.MQOpts]
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACF_AUTH_PROFILE_NAME,
                                String=b'SYSTEM.DEFAULT.MODEL.QUEUE'))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_OBJECT_TYPE,
                                Value=mq.CMQC.MQOT_Q))
        attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_AUTH_ADD_AUTHS,
                                Values=[mq.CMQCFC.MQAUTH_DISPLAY,
                                        mq.CMQCFC.MQAUTH_INPUT]))
        attrs.append(mq.CFSL(Parameter=mq.CMQCFC.MQCACF_PRINCIPAL_ENTITY_NAMES,
                                Strings=[utils.py3str2bytes(cls.app_user)]))
        cls.pcf.MQCMD_SET_AUTH_REC(attrs)

        attrs = []  # type: List[mq.MQOpts]
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACF_AUTH_PROFILE_NAME,
                                String=b'SYSTEM.ADMIN.COMMAND.QUEUE'))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_OBJECT_TYPE,
                                Value=mq.CMQC.MQOT_Q))
        attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_AUTH_ADD_AUTHS,
                                Values=[mq.CMQCFC.MQAUTH_OUTPUT]))
        attrs.append(mq.CFSL(Parameter=mq.CMQCFC.MQCACF_PRINCIPAL_ENTITY_NAMES,
                                Strings=[utils.py3str2bytes(cls.app_user)]))
        cls.pcf.MQCMD_SET_AUTH_REC(attrs)

        attrs = []  # type: List[mq.MQOpts]
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACF_AUTH_PROFILE_NAME,
                                String=utils.py3str2bytes(cls.queue_manager)))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_OBJECT_TYPE,
                                Value=mq.CMQC.MQOT_Q_MGR))
        attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_AUTH_ADD_AUTHS,
                                Values=[mq.CMQCFC.MQAUTH_DISPLAY]))
        attrs.append(mq.CFSL(Parameter=mq.CMQCFC.MQCACF_PRINCIPAL_ENTITY_NAMES,
                                Strings=[utils.py3str2bytes(cls.app_user)]))
        results = cls.pcf.MQCMD_SET_AUTH_REC(attrs)

        if cls.pcf.is_connected:
            cls.pcf.disconnect()
        if cls.qmgr.is_connected:
            cls.qmgr.disconnect()

    def test_init_none(self):
        qmgr = mq.QueueManager(None)
        self.assertFalse(qmgr.is_connected)

    @utils.with_env_complement('MQSERVER', config.MQ.APP_MQSERVER)
    def test_init_name(self):
        # As the connect method provides no way to supply user & password, this
        # cannot work if the queue manager requires it
        if (config.MQ.QM.CONNAUTH.USE_PW == 'REQUIRED') or (self.CHCKCLNT == mq.CMQCFC.MQCHK_REQUIRED):
            self.skipTest('Test not viable for user/password-requiring queue manager')
            return

        # connecting with queue manager name needs MQSERVER set properly
        qmgr = mq.QueueManager(self.queue_manager)
        self.assertTrue(qmgr.is_connected)

        if qmgr.is_connected:
            qmgr.disconnect()

    @utils.with_env_complement('MQSERVER', config.MQ.APP_MQSERVER)
    def test_connect(self):
        # As the connect method provides no way to supply user & password, this
        # cannot work if the queue manager requires it
        if (config.MQ.QM.CONNAUTH.USE_PW == 'REQUIRED') or (self.CHCKCLNT == mq.CMQCFC.MQCHK_REQUIRED):
            self.skipTest('Test not viable for user/password-requiring queue manager')
            return

        qmgr = mq.QueueManager(None)
        self.assertFalse(qmgr.is_connected)
        qmgr.connect(self.queue_manager)
        self.assertTrue(qmgr.is_connected)
        if qmgr.is_connected:
            qmgr.disconnect()

    def test_connect_tcp_client(self):
        qmgr = mq.QueueManager(None)
        qmgr.connect_tcp_client(
            self.queue_manager, mq.cd(), self.channel, self.conn_info, user=self.user,
            password=self.password)
        self.assertTrue(qmgr.is_connected)
        if qmgr.is_connected:
            qmgr.disconnect()

    def test_connect_tcp_client_without_cred(self):
        if (config.MQ.QM.CONNAUTH.USE_PW == 'REQUIRED') or (self.CHCKCLNT == mq.CMQCFC.MQCHK_REQUIRED):
            self.skipTest('Test not viable for user/password-requiring queue manager')
            return

        qmgr = mq.QueueManager(None)
        with self.assertRaises(mq.MQMIError) as ex_ctx:
            qmgr.connect_tcp_client(
                self.queue_manager, mq.cd(), self.channel, self.conn_info)
            self.assertEqual(ex_ctx.exception.reason, mq.CMQC.MQRC_NOT_AUTHORIZED)
        if qmgr.is_connected:
            qmgr.disconnect()

    # This test should be run last
    # ConnectionName list with unaccessible QM affects on channel name of the next test if MQSERVER used
    # changing the order of ConnectionName entries does not affect to issue occurrence
    def test_zzz_connect_tcp_client_conection_list(self):
        qmgr = mq.QueueManager(None)
        conn_info = '127.0.0.1(22),{0}'.format(self.conn_info)
        qmgr.connect_tcp_client(
            self.queue_manager, mq.cd(), self.channel, conn_info, user=self.user,
            password=self.password)
        self.assertTrue(qmgr.is_connected)
        if qmgr.is_connected:
            qmgr.disconnect()

    # This test overlaps with test_mq80.test_successful_connect_without_optional_credentials,
    # but hey, why not
    def test_connect_tcp_client_with_none_credentials(self):
        if config.MQ.QM.CONNAUTH.USE_PW == 'REQUIRED' or self.CHCKCLNT == mq.CMQCFC.MQCHK_REQUIRED:
            self.skipTest('Test not viable for user/password-requiring queue manager')
            return

        qmgr = mq.QueueManager(None)
        qmgr.connect_tcp_client(
            self.queue_manager, mq.cd(), self.app_channel, self.conn_info, user=None,
            password=None)
        self.assertTrue(qmgr.is_connected)
        if qmgr.is_connected:
            qmgr.disconnect()

    def test_disconnect(self):
        qmgr = mq.QueueManager(None)
        qmgr.connect_tcp_client(
            self.queue_manager, mq.cd(), self.channel, self.conn_info, user=self.user,
            password=self.password)
        self.assertTrue(qmgr.is_connected)
        if qmgr.is_connected:
            qmgr.disconnect()
            self.assertFalse(qmgr.is_connected)

    def test_get_handle_unconnected(self):
        qmgr = mq.QueueManager(None)
        self.assertRaises(mq.PYIFError, qmgr.get_handle)

    def test_get_handle_connected(self):
        qmgr = mq.QueueManager(None)
        qmgr.connect_tcp_client(
            self.queue_manager, mq.cd(), self.channel, self.conn_info, user=self.user,
            password=self.password)
        handle = qmgr.get_handle()
        self.assertTrue(isinstance(handle, int))

        if qmgr.is_connected:
            qmgr.disconnect()

    @unittest.skip('Not implemented yet')
    def test_begin(self):
        pass

    @unittest.skip('Not implemented yet')
    def test_commit(self):
        pass

    @unittest.skip('Not implemented yet')
    def test_backout(self):
        pass

    def test_inquire(self):
        qmgr = mq.QueueManager(None)
        qmgr.connect_tcp_client(
            self.queue_manager, mq.cd(), self.channel, self.conn_info, user=self.user,
            password=self.password)
        attribute = mq.CMQC.MQCA_Q_MGR_NAME
        expected_value = utils.py3str2bytes(self.queue_manager)
        attribute_value = qmgr.inquire(attribute)
        self.assertEqual(len(attribute_value), mq.CMQC.MQ_Q_MGR_NAME_LENGTH)
        self.assertTrue(utils.strcmp(attribute_value.strip(), expected_value))

        if qmgr.is_connected:
            qmgr.disconnect()
            self.assertFalse(qmgr.is_connected)


if __name__ == '__main__':
    main(module="test_queue_manager")
