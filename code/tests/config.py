"""Use the environment to get configuration values for connection to qmgr"""
import os.path
import utils


class PATHS:
    """Location of testcases"""
    TESTS_DIR = os.path.normpath(os.path.dirname(__file__))


class MQ:
    """
    Configuration for the tests
    By default, inherited from tox.ini
    """
    class QM:
        """Queue manager connection setup"""
        NAME = os.environ.get('PY_IBMMQ_TEST_QM_NAME', 'QM1')
        HOST = os.environ.get('PY_IBMMQ_TEST_QM_HOST', 'localhost')
        PORT = os.environ.get('PY_IBMMQ_TEST_QM_PORT', '1413')
        TRANSPORT = os.environ.get('PY_IBMMQ_TEST_QM_TRANSPORT', 'TCP')

        CHANNEL = os.environ.get('PY_IBMMQ_TEST_QM_CHANNEL', 'DEV.ADMIN.SVRCONN')
        USER = os.environ.get('PY_IBMMQ_TEST_QM_USER', 'admin')
        PASSWORD = os.environ.get('PY_IBMMQ_TEST_QM_PASSWORD', 'password')

        APP_CHANNEL = os.environ.get('PY_IBMMQ_TEST_QM_APP_CHANNEL', 'DEV.APP.SVRCONN')
        APP_USER = os.environ.get('PY_IBMMQ_TEST_QM_APP_USER', 'app')
        APP_PASSWORD = os.environ.get('PY_IBMMQ_TEST_QM_APP_PASSWORD', 'password')

        MIN_COMMAND_LEVEL = os.environ.get(
            'PY_IBMMQ_TEST_QM_MIN_COMMAND_LEVEL', '800')

        class CONNAUTH:
            """Configuration of authentication credentials"""
            # user/password connection authentication is a MQ >= 8.0 feature
            SUPPORTED = os.environ.get('PY_IBMMQ_TEST_QM_CONNAUTH_SUPPORTED',
                                       '1')
            # Set to OPTIONAL or REQUIRED
            # OPTIONAL: If a user ID and password are provided by a client
            # application then they must be a valid pair. It is not mandatory
            # to provide user + password, though.
            # REQUIRED: A valid user ID and password are mandatory.
            USE_PW = os.environ.get(
                'PY_IBMMQ_TEST_QM_CONNAUTH_USE_PW', 'REQUIRED')

            # Delay time in seconds for API call returns in case of auth
            # failures (some DoS-countermeasure). For testing purposes we
            # usually want this as fast as possible. This value gets used in
            # create_mq_objects.py for the creation of the queue manager conn
            # auth.
            FAIL_DELAY = os.environ.get(
                'PY_IBMMQ_TEST_QM_CONNAUTH_FAIL_DELAY', '0')

    class QUEUE:
        """Queue naming setup"""
        PREFIX = os.environ.get('PY_IBMMQ_TEST_QUEUE_PREFIX', 'UNITTEST')
        QUEUE_NAMES = {
            'TestRFH2PutGet': PREFIX + 'TEST.PYIBMMQ.RFH2PUTGET',
            'TestQueueManager': PREFIX + 'TEST.PYIBMMQ.QUEUEMANAGER',
            }

    # convenience attribute derived from above settings, may be used for tests
    # that mandate the MQSERVER environment variable
    # E.g. MQSERVER="SVRCONN.1/TCP/mq.example.org(1777)"
    MQSERVER = '%(channel)s/%(transport)s/%(host)s(%(port)s)' % {
        'channel': QM.CHANNEL,
        'transport': QM.TRANSPORT,
        'host': QM.HOST,
        'port': QM.PORT,
        }

    APP_MQSERVER = '%(channel)s/%(transport)s/%(host)s(%(port)s)' % {
        'channel': QM.APP_CHANNEL,
        'transport': QM.TRANSPORT,
        'host': QM.HOST,
        'port': QM.PORT,
        }


if __name__ == '__main__':
    utils.print_config(PATHS, MQ)
