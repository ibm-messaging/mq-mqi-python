"""Setup tests environment."""
import os.path
from unittest import TestCase
from unittest import main # pylint: disable=unused-import

import ibmmq as mq

import config  # noqa
import utils  # noqa

class Tests(TestCase):
    """Setup and tearsdown tests environment."""

    version = '0000000'

    queue_name = ''
    queue_manager = ''
    channel = ''
    host = ''
    port = ''
    user = ''
    password = ''

    prefix = ''

    qmgr = None  # type: mq.QueueManager
    pcf = None  # type: mq.PCFExecute

    CHCKLOCL = None

    @classmethod
    def setUpClass(cls):
        """Initialize test environment."""
        cls.prefix = os.environ.get('PY_IBMMQ_TEST_OBJECT_PREFIX', 'PYIBMMQ.')

        # max length of queue names is 48 characters
        cls.queue_name = '{prefix}MSG.QUEUE'.format(prefix=config.MQ.QUEUE.PREFIX)
        cls.queue_manager = config.MQ.QM.NAME
        cls.channel = config.MQ.QM.CHANNEL
        cls.app_channel = config.MQ.QM.APP_CHANNEL
        cls.host = config.MQ.QM.HOST
        cls.port = config.MQ.QM.PORT
        cls.user = config.MQ.QM.USER
        cls.password = config.MQ.QM.PASSWORD

        cls.app_user = config.MQ.QM.APP_USER
        cls.app_password = config.MQ.QM.APP_PASSWORD

        cls.conn_info = '{0}({1})'.format(cls.host, cls.port)

        if mq.__mqbuild__ == 'server':
            cls.qmgr = mq.QueueManager(cls.queue_manager)
        else:
            cls.qmgr = mq.QueueManager(None)
            cls.qmgr.connectTCPClient(cls.queue_manager, mq.CD(), cls.channel,
                                      cls.conn_info, cls.user, cls.password)

        cls.pcf = mq.PCFExecute(cls.qmgr, response_wait_interval=30000)

        cls.version = cls.inquire_qmgr_version().decode()

    @classmethod
    def tearDownClass(cls):
        """Clear test environment."""
        if cls.pcf.is_connected:
            cls.pcf.disconnect()
        if cls.qmgr.is_connected:
            cls.qmgr.disconnect()

    def setUp(self):
        """Set up tesing environment."""

    def tearDown(self):
        """Clear test environment."""

    @classmethod
    def inquire_qmgr_version(cls):
        """Inqure Queue Manager version."""
        return cls.qmgr.inquire(mq.CMQC.MQCA_VERSION)

    def create_queue(self, queue_name, max_depth=5000, attrs=None):
        """Create queue."""
        if not attrs:
            attrs = []
            attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME,
                                    String=utils.py3str2bytes(queue_name)))
            attrs.append(mq.CFIN(Parameter=mq.CMQC.MQIA_Q_TYPE,
                                    Value=mq.CMQC.MQQT_LOCAL))
            attrs.append(mq.CFIN(Parameter=mq.CMQC.MQIA_MAX_Q_DEPTH,
                                    Value=max_depth))
            attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_REPLACE,
                                    Value=mq.CMQCFC.MQRP_YES))

        self.pcf.MQCMD_CREATE_Q(attrs)

    def delete_queue(self, queue_name):
        """Delete queue."""
        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME,
                                String=utils.py3str2bytes(queue_name)))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_PURGE,
                                Value=mq.CMQCFC.MQPO_YES))
        self.pcf.MQCMD_DELETE_Q(attrs)

    def create_channel(self, channel_name, attrs=None):
        """Create channle."""
        if not attrs:
            attrs = []
            attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_CHANNEL_NAME,
                                    String=utils.py3str2bytes(channel_name)))
            attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACH_CHANNEL_TYPE,
                                    Value=mq.CMQXC.MQCHT_SVRCONN))
            attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_REPLACE,
                                    Value=mq.CMQCFC.MQRP_YES))
        self.pcf.MQCMD_CREATE_CHANNEL(attrs)

    def delete_channel(self, channel_name):
        """Delete channel."""
        attrs = []
        attrs.append(mq.CFST(Parameter=mq.CMQCFC.MQCACH_CHANNEL_NAME,
                                String=utils.py3str2bytes(channel_name)))
        self.pcf.MQCMD_DELETE_CHANNEL(attrs)

    def create_auth_rec(self, attrs):
        """Create authentication recoed."""
        self.pcf.MQCMD_SET_CHLAUTH_REC(attrs)

    def delete_auth_rec(self, attrs):
        """Delete authentication recoed."""
        self.pcf.MQCMD_SET_CHLAUTH_REC(attrs)

    @classmethod
    def edit_qmgr(cls, attrs):
        """Edit connected Queue Manager."""
        cls.pcf.MQCMD_CHANGE_Q_MGR(attrs)
