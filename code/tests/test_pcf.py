"""Test PCF usage."""
import os
from sys import version_info as sys_version_info

from unittest import skip
from unittest import skipIf
from ddt import data  # type: ignore
from ddt import ddt

try:
    from typing import List
except ImportError:
    pass

import ibmmq as mq

from test_setup import Tests  # noqa
from test_setup import main   # pylint: disable=no-name-in-module

@ddt
class TestPCF(Tests):
    """Class for MQ PCF testing."""

    messages_dir = os.path.join(os.path.dirname(__file__), "messages")

    @classmethod
    def setUpClass(cls):
        """Initialize test environment."""
        super(TestPCF, cls).setUpClass()

        # max length of queue names is 48 characters
        cls.queue_name = "{prefix}PCF.QUEUE".format(prefix=cls.prefix)

    @classmethod
    def tearDownClass(cls):
        """Tear down test environment."""
        super(TestPCF, cls).tearDownClass()

    def setUp(self):
        """Set up tesing environment."""
        super().setUp()

        self.create_queue(self.queue_name)

    def tearDown(self):
        """Delete the created objects."""
        if self.queue_name:
            self.delete_queue(self.queue_name)

        super().tearDown()

    @skip('Test not implemented')
    def test_mqcfbf(self):
        """Test MQCFBF PCF byte string filter parameter."""

    def test_mqcfbs(self):
        """Test MQCFBS PCF byte string parameter.

        Also uses MQCFIN and MQCFIL as parameters
        """
        attrs = []  # type: List[mq.MQOpts]
        attrs.append(mq.CFBS(Parameter=mq.CMQCFC.MQBACF_GENERIC_CONNECTION_ID,
                                String=b''))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_CONN_INFO_TYPE,
                                Value=mq.CMQCFC.MQIACF_CONN_INFO_CONN))
        attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_CONNECTION_ATTRS,
                                Values=[mq.CMQCFC.MQIACF_ALL]))

        object_filters = []
        object_filters.append(
            mq.CFIF(Parameter=mq.CMQC.MQIA_APPL_TYPE,
                       Operator=mq.CMQCFC.MQCFOP_EQUAL,
                       FilterValue=mq.CMQC.MQAT_USER))

        results = self.pcf.MQCMD_INQUIRE_CONNECTION(attrs, object_filters)

        self.assertGreater(len(results), 0)

    def test_mqcfif(self):
        """Test string filter MQCFIF.

        Also uses MQCFST, MQCFIN and MQCFIL as parameters
        """
        attrs = []  # type: List[mq.MQOpts]
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME,
                                String=b'*'))
        attrs.append(mq.CFIN(Parameter=mq.CMQC.MQIA_Q_TYPE,
                                Value=mq.CMQC.MQQT_LOCAL))
        attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_Q_ATTRS,
                                Values=[mq.CMQC.MQIA_CURRENT_Q_DEPTH, mq.CMQC.MQCA_Q_DESC]))

        object_filters = []
        object_filters.append(
            mq.CFIF(Parameter=mq.CMQC.MQIA_CURRENT_Q_DEPTH,
                       Operator=mq.CMQCFC.MQCFOP_GREATER,
                       FilterValue=0))

        results = self.pcf.MQCMD_INQUIRE_Q(attrs, object_filters)

        self.assertTrue(results, 'Queue not found')
        for result in results:
            self.assertTrue(result[mq.CMQC.MQIA_CURRENT_Q_DEPTH] > 0,
                            'Found Queue with depth {}'.format(result[mq.CMQC.MQIA_CURRENT_Q_DEPTH]))

    def test_mqcfsf(self):
        """Test string filter MQCFSF.

        Also uses MQCFST, MQCFIN and MQCFIL as parameters
        """
        attrs = []  # type: List[mq.MQOpts]
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME,
                                String=b'*'))
        attrs.append(mq.CFIN(Parameter=mq.CMQC.MQIA_Q_TYPE,
                                Value=mq.CMQC.MQQT_LOCAL))
        attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_Q_ATTRS,
                                Values=[mq.CMQC.MQIA_CURRENT_Q_DEPTH, mq.CMQC.MQCA_Q_DESC]))

        object_filters = []
        object_filters.append(
            mq.CFSF(Parameter=mq.CMQC.MQCA_Q_DESC,
                       Operator=mq.CMQCFC.MQCFOP_LIKE,
                       FilterValue=b'IBM MQ*'))

        results = self.pcf.MQCMD_INQUIRE_Q(attrs, object_filters)

        self.assertTrue(results, 'Queue not found')
        for result in results:
            self.assertTrue(not result[mq.CMQC.MQCA_Q_DESC].startswith(b'MQ'),
                            'Found Queue with description {}'.format(result[mq.CMQC.MQCA_Q_DESC]))
            self.assertTrue(mq.CMQC.MQCA_Q_DESC in result,
                            'Attribute {} is not returned'.format(result[mq.CMQC.MQCA_Q_DESC]))

    @data([], [b'One'], [b'One', b'Two', b'Three'])
    def test_mqcfsl(self, value):
        """Test MQCFSL PCF string list parameter.

        Also uses MQCFST and MQCFIN as parameters
        """
        attrs = []  # type: List[mq.MQOpts]
        attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_NAMELIST_NAME,
                                String='{}NAMELIST'.format(self.prefix).encode()))
        attrs.append(mq.CFSL(Parameter=mq.CMQC.MQCA_NAMES,
                                Strings=value))
        attrs.append(mq.CFIN(Parameter=mq.CMQCFC.MQIACF_REPLACE,
                                Value=mq.CMQCFC.MQRP_YES))

        try:
            self.pcf.MQCMD_CREATE_NAMELIST(attrs)
        except Exception:  # pylint: disable=broad-except
            self.fail('Exception occurs!')
        else:
            attrs = []
            attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_NAMELIST_NAME,
                                    String='{}NAMELIST'.format(self.prefix).encode()))
            attrs.append(mq.CFIL(Parameter=mq.CMQCFC.MQIACF_NAMELIST_ATTRS,
                                    Values=[mq.CMQC.MQCA_NAMES, mq.CMQC.MQIA_NAME_COUNT]))

            results = self.pcf.MQCMD_INQUIRE_NAMELIST(attrs)

            self.assertEqual(results[0][mq.CMQC.MQIA_NAME_COUNT], len(value))

            if results[0][mq.CMQC.MQIA_NAME_COUNT] > 0:
                for item in results[0][mq.CMQC.MQCA_NAMES]:
                    item = item.strip()
                    self.assertTrue(item in value, '{} value not in values list'.format(item))
                    value.remove(item)

            attrs = []
            attrs.append(mq.CFST(Parameter=mq.CMQC.MQCA_NAMELIST_NAME,
                                    String='{}NAMELIST'.format(self.prefix).encode()))
            self.pcf.MQCMD_DELETE_NAMELIST(attrs)

    @data([], [1], [1, 2, 3, 4, 5])
    def test_arbitrary_message_with_mqcfil(self, value):
        """Test arbitrary message with MQCFIL."""
        message = mq.CFH(Version=mq.CMQCFC.MQCFH_VERSION_1,
                            Type=mq.CMQCFC.MQCFT_USER,
                            ParameterCount=1).pack()
        message = message + mq.CFIL(Parameter=1,
                                       Values=value).pack()

        queue = mq.Queue(self.qmgr, self.queue_name,
                            mq.CMQC.MQOO_INPUT_AS_Q_DEF + mq.CMQC.MQOO_OUTPUT)

        put_md = mq.MD(Format=mq.CMQC.MQFMT_PCF)
        queue.put(message, put_md)

        get_opts = mq.GMO(
            Options=mq.CMQC.MQGMO_NO_SYNCPOINT + mq.CMQC.MQGMO_FAIL_IF_QUIESCING,
            Version=mq.CMQC.MQGMO_VERSION_2,
            MatchOptions=mq.CMQC.MQMO_MATCH_CORREL_ID)
        get_md = mq.MD(MsgId=put_md.MsgId)  # pylint: disable=no-member
        message = queue.get(None, get_md, get_opts)
        queue.close()
        unpacked_message = mq.PCFExecute.unpack(message)

        self.assertTrue(isinstance(unpacked_message[0][1], list),
                        'Returned value is not list: {}'.format(type(unpacked_message[0][1])))

        self.assertTrue(len(unpacked_message[0][1]) == len(value), 'List length is different!')

        for item in unpacked_message[0][1]:
            self.assertTrue(item in value, '{} value not in values list'.format(item))
            value.remove(item)

    def test_mqcfgr_mqcfin64_mqcfil64(self):
        """Test arbitrary message with MQCFIL."""

        # Groups require CFH_VERSION_3
        cfh = mq.CFH(Version=mq.CMQCFC.MQCFH_VERSION_3,
                            Type=mq.CMQCFC.MQCFT_USER,
                            ParameterCount=4)
        message = cfh.pack()
        message += mq.CFST(Parameter=mq.CMQC.MQCA_Q_MGR_NAME,
                              String=b'QM1').pack()
        # group1
        message += mq.CFGR(Parameter=mq.CMQCFC.MQGACF_Q_STATISTICS_DATA,
                              ParameterCount=3).pack()
        message += mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME,
                              String=b'SYSTEM.ADMIN.COMMAND.QUEUE').pack()
        message += mq.CFIN64(Parameter=mq.CMQCFC.MQIAMO_Q_MIN_DEPTH,
                                Value=10).pack()
        message += mq.CFIL64(Parameter=mq.CMQCFC.MQIAMO64_AVG_Q_TIME,
                                Values=[1, 2, 3]).pack()
        # group2
        message += mq.CFGR(Parameter=mq.CMQCFC.MQGACF_Q_STATISTICS_DATA,
                              ParameterCount=3).pack()
        message += mq.CFST(Parameter=mq.CMQC.MQCA_Q_NAME,
                              String=b'SYSTEM.ADMIN.COMMAND.QUEUE2').pack()
        message += mq.CFIN64(Parameter=mq.CMQCFC.MQIAMO_Q_MIN_DEPTH,
                                Value=20).pack()
        message += mq.CFIL64(Parameter=mq.CMQCFC.MQIAMO64_AVG_Q_TIME,
                                Values=[111, 222]).pack()

        message += mq.CFST(Parameter=mq.CMQCFC.MQCAMO_START_TIME,
                              String=b'10.41.58').pack()

        queue = mq.Queue(self.qmgr, self.queue_name,
                            mq.CMQC.MQOO_INPUT_AS_Q_DEF + mq.CMQC.MQOO_OUTPUT)

        put_md = mq.MD(Format=mq.CMQC.MQFMT_PCF)
        queue.put(message, put_md)

        get_opts = mq.GMO(
            Options=mq.CMQC.MQGMO_NO_SYNCPOINT + mq.CMQC.MQGMO_FAIL_IF_QUIESCING,
            Version=mq.CMQC.MQGMO_VERSION_2,
            MatchOptions=mq.CMQC.MQMO_MATCH_CORREL_ID)
        get_md = mq.MD(MsgId=put_md.MsgId)  # pylint: disable=no-member
        message = queue.get(None, get_md, get_opts)
        queue.close()
        message, _ = mq.PCFExecute.unpack(message)

        self.assertEqual({
            mq.CMQC.MQCA_Q_MGR_NAME: b'QM1\x00',
            mq.CMQCFC.MQCAMO_START_TIME: b'10.41.58',
            mq.CMQCFC.MQGACF_Q_STATISTICS_DATA: [
                {
                    mq.CMQC.MQCA_Q_NAME: b'SYSTEM.ADMIN.COMMAND.QUEUE\x00\x00',
                    mq.CMQCFC.MQIAMO_Q_MIN_DEPTH: 10,
                    mq.CMQCFC.MQIAMO64_AVG_Q_TIME: [1, 2, 3],
                },
                {
                    mq.CMQC.MQCA_Q_NAME: b'SYSTEM.ADMIN.COMMAND.QUEUE2\x00',
                    mq.CMQCFC.MQIAMO_Q_MIN_DEPTH: 20,
                    mq.CMQCFC.MQIAMO64_AVG_Q_TIME: [111, 222],
                },
            ]
        }, message)

    def test_unpack_header(self):
        """Test unpack header."""
        message = mq.CFH(Version=mq.CMQCFC.MQCFH_VERSION_1,
                            Type=mq.CMQCFC.MQCFT_STATISTICS,
                            Command=mq.CMQCFC.MQCMD_STATISTICS_Q,
                            ParameterCount=1).pack()
        message += mq.CFST(Parameter=mq.CMQC.MQCA_Q_MGR_NAME,
                              String=b'QM1').pack()

        queue = mq.Queue(self.qmgr, self.queue_name,
                            mq.CMQC.MQOO_INPUT_AS_Q_DEF + mq.CMQC.MQOO_OUTPUT)

        put_md = mq.MD(Format=mq.CMQC.MQFMT_PCF)
        queue.put(message, put_md)

        get_opts = mq.GMO(
            Options=mq.CMQC.MQGMO_NO_SYNCPOINT + mq.CMQC.MQGMO_FAIL_IF_QUIESCING,
            Version=mq.CMQC.MQGMO_VERSION_2,
            MatchOptions=mq.CMQC.MQMO_MATCH_CORREL_ID)
        get_md = mq.MD(MsgId=put_md.MsgId)  # pylint: disable=no-member
        message = queue.get(None, get_md, get_opts)
        queue.close()
        message, header = mq.PCFExecute.unpack(message)

        self.assertEqual(header.Command, mq.CMQCFC.MQCMD_STATISTICS_Q)  # pylint: disable=no-member
        self.assertEqual(header.Type, mq.CMQCFC.MQCFT_STATISTICS)  # pylint: disable=no-member

        self.assertEqual({
            mq.CMQC.MQCA_Q_MGR_NAME: b'QM1\x00',
        }, message)

    def test_unpack_group(self):
        """Test parameters group unpack."""
        with open(os.path.join(self.messages_dir, "statistics_q.dat"), "rb") as file:
            binary_message = file.read()
            message, header = mq.PCFExecute.unpack(binary_message)

            self.assertEqual(header.Command, mq.CMQCFC.MQCMD_STATISTICS_Q)  # pylint: disable=no-member
            self.assertEqual(header.Type, mq.CMQCFC.MQCFT_STATISTICS)  # pylint: disable=no-member

            self.assertEqual(message[mq.CMQC.MQCA_Q_MGR_NAME].strip(), b'mq_mgr1')
            self.assertEqual(message[mq.CMQCFC.MQCAMO_START_DATE], b'2020-06-15\x00\x00')
            self.assertEqual(len(message[mq.CMQCFC.MQGACF_Q_STATISTICS_DATA]), 16)

            item = message[mq.CMQCFC.MQGACF_Q_STATISTICS_DATA][0]
            self.assertEqual(item[mq.CMQC.MQCA_Q_NAME].strip(), b'SYSTEM.ADMIN.COMMAND.QUEUE')
            self.assertEqual(item[mq.CMQCFC.MQIAMO_PUTS], [14, 0])

    def test_unpack_cfsf(self):
        """Test unpack of PCF message with MQCFSF structure."""
        with open(os.path.join(self.messages_dir, "pcf_with_cfsf.dat"), "rb") as file:
            binary_message = file.read()

            message, _ = mq.PCFExecute.unpack(binary_message)

        self.assertEqual(message.get(mq.CMQCFC.MQGACF_COMMAND_DATA, [{}])[0].get(mq.CMQC.MQCA_Q_DESC)[0],
                         mq.CMQCFC.MQCFOP_LIKE)

        self.assertEqual(message.get(mq.CMQCFC.MQGACF_COMMAND_DATA,
                                     [{}])[0].get(mq.CMQC.MQCA_Q_DESC)[1].rstrip(b'\x00'),
                         b'test*')

    @skip('Test not implemented')
    def test_unpack_cfbf(self):
        """Test unpack of PCF message with MQCFBF structure."""

    def test_unpack_cfif(self):
        """Test unpack of PCF message with MQCFIF structure."""
        with open(os.path.join(self.messages_dir, "pcf_with_cfif.dat"), "rb") as file:
            binary_message = file.read()

            message, _ = mq.PCFExecute.unpack(binary_message)

        self.assertEqual(message.get(mq.CMQCFC.MQGACF_COMMAND_DATA, [{}])[0].get(mq.CMQC.MQIA_CURRENT_Q_DEPTH),
                         (mq.CMQCFC.MQCFOP_GREATER, 0))

    @skipIf(sys_version_info < (3, 7), 'Python pre 3.7 issues')
    def test_mqcfbs_old(self):
        """Test byte string MQCFBS and MQCFIL with old style."""
        attrs = {
            mq.CMQCFC.MQBACF_GENERIC_CONNECTION_ID: mq.ByteString(b''),
            mq.CMQCFC.MQIACF_CONN_INFO_TYPE: mq.CMQCFC.MQIACF_CONN_INFO_CONN,
            mq.CMQCFC.MQIACF_CONNECTION_ATTRS: [mq.CMQCFC.MQCACH_CONNECTION_NAME,
                                                   mq.CMQCFC.MQCACH_CHANNEL_NAME]
        }
        fltr = mq.Filter(mq.CMQC.MQIA_APPL_TYPE).equal(mq.CMQC.MQAT_USER)

        results = self.pcf.MQCMD_INQUIRE_CONNECTION(attrs, [fltr])

        self.assertGreater(len(results), 0)
        self.assertTrue(mq.CMQCFC.MQCACH_CONNECTION_NAME in results[0].keys())
        self.assertTrue(mq.CMQCFC.MQCACH_CHANNEL_NAME in results[0].keys())

    @skipIf(sys_version_info < (3, 7), 'Python pre 3.7 issues')
    @data(['test1'],
          ['test1', b'test2'],
          [b'test1', 'test2'])
    def test_mqcfsl_old(self, names):
        """Test list MQCFSL with old style."""

        args = {
            mq.CMQC.MQCA_NAMELIST_NAME: "{prefix}PCF.NAMELIST".format(prefix=self.prefix),
            mq.CMQC.MQCA_NAMES: names,
            mq.CMQCFC.MQIACF_REPLACE: mq.CMQCFC.MQRP_YES
        }

        self.pcf.MQCMD_CREATE_NAMELIST(args)

        args = {
            mq.CMQC.MQCA_NAMELIST_NAME: "{prefix}PCF.NAMELIST".format(prefix=self.prefix),
            mq.CMQCFC.MQIACF_NAMELIST_ATTRS: [mq.CMQC.MQCA_NAMES]
        }
        results = None
        try:
            results = self.pcf.MQCMD_INQUIRE_NAMELIST(args)
        finally:
            args = {
                mq.CMQC.MQCA_NAMELIST_NAME: "{prefix}PCF.NAMELIST".format(prefix=self.prefix),
            }

            self.pcf.MQCMD_DELETE_NAMELIST(args)
        for name in names:
            self.assertTrue(mq.ensure_bytes(name) in [x.strip() for x in results[0][mq.CMQC.MQCA_NAMES]])

    @data(mq.CMQCFC.MQIACF_ALL, [mq.CMQCFC.MQIACF_ALL],
          mq.CMQC.MQCA_Q_DESC, [mq.CMQC.MQCA_Q_DESC],
          [mq.CMQC.MQIA_CURRENT_Q_DEPTH, mq.CMQC.MQCA_Q_DESC])
    def test_object_filter_int_old_queue(self, value):
        """Test object filter with integer attribute. Old style."""
        attrs = {
            mq.CMQC.MQCA_Q_NAME: b'*',
            mq.CMQCFC.MQIACF_Q_ATTRS: value
            }

        filter_depth = mq.Filter(mq.CMQC.MQIA_CURRENT_Q_DEPTH).greater(0)

        results = self.pcf.MQCMD_INQUIRE_Q(attrs, [filter_depth])

        self.assertTrue(results, 'Queue not found')
        for result in results:
            self.assertTrue(result[mq.CMQC.MQIA_CURRENT_Q_DEPTH] > 0,
                            'Found Queue with depth {}'.format(result[mq.CMQC.MQIA_CURRENT_Q_DEPTH]))

    @skip('https://stackoverflow.com/questions/62250844/ibm-mq-pcf-parameters-order')
    @data(mq.CMQCFC.MQIACF_ALL, [mq.CMQCFC.MQIACF_ALL],
          mq.CMQCFC.MQCACH_DESC, [mq.CMQCFC.MQCACH_DESC],
          [mq.CMQCFC.MQCACH_DESC, mq.CMQCFC.MQIACH_CHANNEL_TYPE])
    def test_object_filter_int_old_channel(self, value):
        """Test object filter with integer attribute. Old style."""
        attrs = {
            mq.CMQCFC.MQCACH_CHANNEL_NAME: b'*',
            mq.CMQCFC.MQIACF_CHANNEL_ATTRS: value}

        filter_type = mq.Filter(mq.CMQCFC.MQIACH_CHANNEL_TYPE).equal(mq.CMQXC.MQCHT_SVRCONN)

        results = self.pcf.MQCMD_INQUIRE_CHANNEL(attrs, [filter_type])

        self.assertTrue(results, 'Channel not found')
        for result in results:
            self.assertTrue(result[mq.CMQCFC.MQIACH_CHANNEL_TYPE] == mq.CMQXC.MQCHT_SVRCONN,
                            'Found Channel with type {}'.format(result[mq.CMQCFC.MQIACH_CHANNEL_TYPE]))

    def test_object_filter_str_old(self):
        """Test object filter with string attribute. Old style."""
        attrs = {
            mq.CMQC.MQCA_Q_NAME: b'*',
            mq.CMQCFC.MQIACF_Q_ATTRS: [mq.CMQC.MQIA_CURRENT_Q_DEPTH, mq.CMQC.MQCA_Q_DESC]
            }

        filter_depth = mq.Filter(mq.CMQC.MQCA_Q_DESC).like(b'IBM MQ *')

        results = self.pcf.MQCMD_INQUIRE_Q(attrs, [filter_depth])

        self.assertTrue(results, 'Queue not found')
        for result in results:
            self.assertTrue(not result[mq.CMQC.MQCA_Q_DESC].startswith(b'MQ'),
                            'Found Queue with description {}'.format(result[mq.CMQC.MQCA_Q_DESC]))

    def test_disconnect(self):
        """Test disconnect for PCF object."""
        # pylint: disable=protected-access

        pcf = mq.PCFExecute(self.qmgr)

        self.assertTrue(pcf.reply_queue)
        self.assertTrue(pcf.reply_queue_name)

        pcf.disconnect()

        self.assertTrue(self.qmgr)
        self.assertFalse(pcf.reply_queue)
        self.assertFalse(pcf.reply_queue_name)

if __name__ == "__main__":
    main(module="test_pcf")
