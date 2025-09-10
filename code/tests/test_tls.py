"""Test connection with TLS(SSL)."""

import os.path
import unittest

import ibmmq as mq

from test_setup import Tests
from test_setup import main
import utils

# pylint: disable=pointless-string-statement
"""
Preparation:
    Define env variable:
        PY_IBMMQ_TEST_TLS_SKIP = 0

Create keydb files:
    Default keydb localtion is:
        Server:
            Unix: /var/mqm/qmgrs/queue_manager_name/ssl
        Client:
            Unix: user HOME directory

Command for keydb creation (for Unix):

runmqakm -keydb -create -db /var/mqm/qmgrs/MQTEST/ssl/mqtest.kdb -pw Secret13 -stash
runmqakm -cert -create -db /var/mqm/qmgrs/MQTEST/ssl/mqtest.kdb -type kdb -pw Secret13 \
    -label mqtest -dn CN=mqtest -size 2048 -x509version 3 -expire 365 -fips -sig_alg SHA256WithRSA

runmqakm -keydb -create -db ~/client.kdb -pw Secret13 -stash
runmqakm -cert -create -db ~/client.kdb -type kdb -pw Secret13 \
    -label client -dn CN=client -size 2048 -x509version 3 -expire 365 -fips -sig_alg SHA256WithRSA

runmqakm -cert -extract -db /var/mqm/qmgrs/MQTEST/ssl/mqtest.kdb -pw Secret13 \
    -label mqtest -target ~/mqtest.pem
runmqakm -cert -add -db ~/client.kdb -pw Secret13 \
    -label mqtest -file ~/mqtest.pem

runmqakm -cert -extract -db ~/client.kdb -pw Secret13 \
    -label client -target ~/client.pem
runmqakm -cert -add -db /var/mqm/qmgrs/MQTEST/ssl/mqtest.kdb -pw Secret13 \
    -label client -file ~/client.pem
"""

class TestTLS(Tests):
    """Test Queue.get() method."""

    tls_channel_name = 'SSL.SVRCONN'
    cypher_spec = 'TLS_RSA_WITH_AES_256_CBC_SHA256'
    client_dn = 'CN=client'
    certificate_label_qmgr = 'mqtest'
    certificate_label_client = 'client'
    key_repo_location_client = os.path.expanduser('~')
    key_repo_location_qmgr = '/var/mqm/qmgrs/{}/ssl'

    @classmethod
    def setUpClass(cls):
        """Initialize test environment."""
        cls.skip = int(os.environ.get(
            'PY_IBMMQ_TEST_TLS_SKIP', 1))

        if cls.skip:
            raise unittest.SkipTest('PY_IBMMQ_TEST_TLS_SKIP initialized')

        super(TestTLS, cls).setUpClass()
        cls.tls_channel_name = os.environ.get(
            'PY_IBMMQ_TEST_TLS_CHL_NAME',
            cls.prefix + cls.tls_channel_name).encode()
        cls.cypher_spec = os.environ.get(
            'PY_IBMMQ_TEST_TLS_CYPHER_SPEC',
            cls.cypher_spec).encode()
        cls.client_dn = os.environ.get(
            'PY_IBMMQ_TEST_TLS_CLIENT_DN',
            cls.client_dn).encode()
        cls.certificate_label_qmgr = os.environ.get(
            'PY_IBMMQ_TEST_TLS_CERT_LABEL_QMGR',
            cls.certificate_label_qmgr).encode()
        cls.certificate_label_client = os.environ.get(
            'PY_IBMMQ_TEST_TLS_CERT_LABEL_CLIENT',
            cls.certificate_label_client).encode()
        cls.key_repo_location_qmgr = os.environ.get(
            'PY_IBMMQ_TEST_TLS_KEY_REPO_LOCATION_QMGR',
            cls.key_repo_location_qmgr.format(cls.queue_manager)).encode()
        cls.key_repo_location_client = os.environ.get(
            'PY_IBMMQ_TEST_TLS_KEY_REPO_LOCATION_CLIENT',
            cls.key_repo_location_client).encode()

        cls.key_repo_location_client_path = os.path.join(
            cls.key_repo_location_client,
            cls.certificate_label_client)

        cls.key_repo_location_qmgr_path = os.path.join(
            cls.key_repo_location_qmgr,
            cls.certificate_label_qmgr)

        cls._key_repo_location_qmgr = cls.qmgr.inquire(mq.CMQC.MQCA_SSL_KEY_REPOSITORY)
        cls._certificate_label_qmgr = cls.qmgr.inquire(mq.CMQC.MQCA_CERT_LABEL)

        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_SSL_KEY_REPOSITORY,
                                String=cls.key_repo_location_qmgr_path))
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_CERT_LABEL,
                                String=cls.certificate_label_qmgr))

        cls.edit_qmgr(attrs)

    @classmethod
    def tearDownClass(cls):
        """Clear test environment."""
        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_SSL_KEY_REPOSITORY,
                                String=cls._key_repo_location_qmgr))
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_CERT_LABEL,
                                String=cls._certificate_label_qmgr))

        cls.edit_qmgr(attrs)
        super(TestTLS, cls).tearDownClass()

    def setUp(self):
        """Initialize test environment."""
        super().setUp()

        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_CHANNEL_NAME,
                                String=utils.py3str2bytes(self.tls_channel_name)))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACH_CHANNEL_TYPE,
                                Value=mq.CMQXC.MQCHT_SVRCONN))
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_SSL_CIPHER_SPEC,
                                String=self.cypher_spec))
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_SSL_PEER_NAME,
                                String=self.client_dn))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACH_SSL_CLIENT_AUTH,
                                Value=mq.CMQXC.MQSCA_OPTIONAL))
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_CERT_LABEL,
                                String=self.certificate_label_qmgr))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_REPLACE,
                                Value=mq.CMQCFC.MQRP_YES))
        self.create_channel(self.tls_channel_name, attrs)

        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_CHANNEL_NAME,
                                String=utils.py3str2bytes(self.tls_channel_name)))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_CHLAUTH_TYPE,
                                Value=mq.CMQCFC.MQCAUT_USERMAP))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_ACTION,
                                Value=mq.CMQCFC.MQACT_REPLACE))
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_CLIENT_USER_ID,
                                String=utils.py3str2bytes(self.user)))
        attrs.append(mq.CFIN(Parameter=mq.CMQC.MQIA_CHECK_CLIENT_BINDING,
                                Value=mq.CMQCFC.MQCHK_REQUIRED_ADMIN))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACH_USER_SOURCE,
                                Value=mq.CMQC.MQUSRC_MAP))
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_MCA_USER_ID,
                                String=b'mqm'))

        self.create_auth_rec(attrs)

        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_CHANNEL_NAME,
                                String=utils.py3str2bytes(self.tls_channel_name)))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_CHLAUTH_TYPE,
                                Value=mq.CMQCFC.MQCAUT_BLOCKUSER))
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_MCA_USER_ID_LIST,
                                String=b'nobody'))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACH_WARNING,
                                Value=mq.CMQC.MQWARN_NO))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_ACTION,
                                Value=mq.CMQCFC.MQACT_REPLACE))
        self.create_auth_rec(attrs)

    def tearDown(self):
        """Delete created objects."""
        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_CHANNEL_NAME,
                                String=utils.py3str2bytes(self.tls_channel_name)))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_CHLAUTH_TYPE,
                                Value=mq.CMQCFC.MQCAUT_USERMAP))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_ACTION,
                                Value=mq.CMQCFC.MQACT_REMOVEALL))
        self.delete_auth_rec(attrs)

        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_CHANNEL_NAME,
                                String=utils.py3str2bytes(self.tls_channel_name)))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_CHLAUTH_TYPE,
                                Value=mq.CMQCFC.MQCAUT_BLOCKUSER))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_ACTION,
                                Value=mq.CMQCFC.MQACT_REMOVEALL))
        self.delete_auth_rec(attrs)

        self.delete_channel(self.tls_channel_name)

        super().tearDown()

    ###########################################################################
    #
    # Real Tests start here
    #
    ###########################################################################

    def test_connection_with_tls(self):
        """Test connection to QueueManager with TLS."""
        qmgr = mq.QueueManager(None)
        conn_info = mq.ensure_bytes('{0}({1})'.format(self.host, self.port))

        cd = mq.CD(Version=mq.CMQXC.MQCD_VERSION_7, # pylint: disable=C0103
                      ChannelName=self.tls_channel_name,
                      ConnectionName=conn_info,
                      SSLCipherSpec=self.cypher_spec)

        sco = mq.SCO(Version=mq.CMQC.MQSCO_VERSION_5,
                        KeyRepository=os.path.join(self.key_repo_location_client,
                                                   self.certificate_label_client),
                        CertificateLabel=self.certificate_label_client)

        opts = mq.CMQC.MQCNO_HANDLE_SHARE_NO_BLOCK

        qmgr.connectWithOptions(self.queue_manager, cd, sco, opts=opts,
                                user=self.user, password=self.password)
        is_connected = qmgr.is_connected
        if is_connected:
            qmgr.disconnect()

        self.assertTrue(is_connected)

if __name__ == '__main__':
    main(module='test_tls')
