"""Test the PubSub verbs"""

import sys
import unicodedata
import unittest
import ibmmq as mq
import utils
import config

if sys.version_info[0] >= 3:
    def unicode(x, encoding):
        """Turn Python3 strings into bytes"""
        if isinstance(x, bytes):
            return x.decode(encoding)
        return str(x)  # In py 3 every string is unicode.

# pylint: disable=missing-function-docstring

class TestPubSub(unittest.TestCase):  # pylint: disable=too-many-instance-attributes

    """Test Pub/Sub with the following six test cases:
    |-------+---------+-------------+----------+-------------|
    |       | Managed | Managed     | Provided | Provided    |
    |       | Durable | Non-Durable | Durable  | Non-Durable |
    |-------+---------+-------------+----------+-------------|
    | Admin | x       |             | x        |             |
    | API   | x       | x           | x        | x           |
    |-------+---------+-------------+----------+-------------|
    The combination Admin/Non-Durable is not possible.
    All tests follow the same procedure:
    1. Create or register the subscription
    2. Publish a message
    3. get() the message
    4. compare result with message
    5. tearDown(): delete objects
    """
    def setUp(self):
        self.topic_string_template = "/UNITTEST/{prefix}/PUBSUB/{{type}}/{{destination}}/{{durable}}".format(
            prefix=config.MQ.QUEUE.PREFIX)
        self.subname_template = "{prefix}'s {{type}} {{destination}} {{durable}} Subscription".format(
            prefix=config.MQ.QUEUE.PREFIX)
        self.msg_template = "Hello World in the topic string \"{{topic_string}}\""
        # max length of queue names is 48 characters
        self.queue_name_template = "{prefix}_Q_TEST_PUBSUB_{{type}}_PROVIDED_{{durable}}".format(prefix=config.MQ.QUEUE.PREFIX)
        self.queue_manager = config.MQ.QM.NAME
        self.channel = config.MQ.QM.CHANNEL
        self.host = config.MQ.QM.HOST
        self.port = config.MQ.QM.PORT
        self.user = config.MQ.QM.USER
        self.password = config.MQ.QM.PASSWORD

        self.conn_info = "{0}({1})".format(self.host, self.port)

        self.qmgr = mq.QueueManager(None)
        self.qmgr.connectTCPClient(self.queue_manager, mq.CD(), self.channel, self.conn_info, self.user, self.password)

        # list of tuples (subscription, subscription descriptions) for tearDown() to delete after the test
        self.sub_desc_list = []

    def msg_format(self, **kwargs):
        res = self.msg_template.format(**kwargs)
        return utils.py3str2bytes(res)

    def delete_sub(self, sub_desc):
        # can only delete a durable subscription
        if sub_desc["Options"] & mq.CMQC.MQSO_DURABLE:
            subname = sub_desc.get_vs("SubName")
            pcf = mq.PCFExecute(self.qmgr)
            args = {mq.CMQCFC.MQCACF_SUB_NAME: subname
                    }
            pcf.MQCMD_DELETE_SUBSCRIPTION(args)

    def delete_queue(self, sub_desc, queue_name):
        # must be unmanaged
        if not sub_desc["Options"] & mq.CMQC.MQSO_MANAGED:
            pcf = mq.PCFExecute(self.qmgr)
            args = {mq.CMQC.MQCA_Q_NAME: utils.py3str2bytes(queue_name),
                    mq.CMQCFC.MQIACF_PURGE: mq.CMQCFC.MQPO_YES}
            pcf.MQCMD_DELETE_Q(args)

    def tearDown(self):
        """Delete the created objects.
        """
        for (sub, sub_desc, queue_name) in self.sub_desc_list:
            self.delete_sub(sub_desc)
            if queue_name is None:
                sub_queue = sub.get_sub_queue()
                self.delete_queue(sub_desc, sub_queue)
            else:
                self.delete_queue(sub_desc, queue_name)
        self.qmgr.disconnect()

    @staticmethod
    def get_subscription_descriptor(subname, topic_string, options=0):
        sub_desc = mq.SD()
        sub_desc["Options"] = options
        sub_desc.set_vs("SubName", subname)
        sub_desc.set_vs("ObjectString", topic_string)
        return sub_desc

    def pub(self, msg, topic_string, *opts):
        topic = mq.Topic(self.qmgr, topic_string=topic_string)
        topic.open(open_opts=mq.CMQC.MQOO_OUTPUT)
        if not isinstance(msg, (str,bytes)):
            raise AttributeError('msg must be bytes or str to publish to topic.')  # py3
        topic.pub(msg, *opts)
        topic.close()

    def pub_rfh2(self, msg, topic_string, *opts):
        topic = mq.Topic(self.qmgr, topic_string=topic_string)
        topic.open(open_opts=mq.CMQC.MQOO_OUTPUT)
        if not isinstance(msg, (str,bytes)):
            raise AttributeError('msg must be bytes or str to publish to topic.')  # py3
        topic.pub_rfh2(msg, *opts)
        topic.close()

    def create_api_subscription(self):
        return mq.Subscription(self.qmgr)

    def create_admin_subscription(self, destination_class, subname, queue_name, topic_string):
        pcf = mq.PCFExecute(self.qmgr)
        args = {mq.CMQCFC.MQCACF_SUB_NAME: utils.py3str2bytes(subname),
                mq.CMQC.MQCA_TOPIC_STRING: utils.py3str2bytes(topic_string),
                mq.CMQCFC.MQIACF_DESTINATION_CLASS: destination_class,
                mq.CMQCFC.MQIACF_REPLACE: mq.CMQCFC.MQRP_YES}
        if destination_class is mq.CMQC.MQDC_PROVIDED:
            args[mq.CMQCFC.MQCACF_DESTINATION] = utils.py3str2bytes(queue_name)
        pcf.MQCMD_CREATE_SUBSCRIPTION(args)

    @staticmethod
    def create_get_opts():
        get_opts = mq.GMO(
            Options=mq.CMQC.MQGMO_NO_SYNCPOINT + mq.CMQC.MQGMO_FAIL_IF_QUIESCING + mq.CMQC.MQGMO_WAIT)
        get_opts["WaitInterval"] = 15000
        return get_opts

    def create_queue(self, queue_name):
        queue_type = mq.CMQC.MQQT_LOCAL
        max_depth = 123456

        args = {mq.CMQC.MQCA_Q_NAME: utils.py3str2bytes(queue_name),
                mq.CMQC.MQIA_Q_TYPE: queue_type,
                mq.CMQC.MQIA_MAX_Q_DEPTH: max_depth}
        pcf = mq.PCFExecute(self.qmgr)
        pcf.MQCMD_CREATE_Q(args)

############################################################################
#
# Real Tests start here
#
############################################################################

    def test_pubsub_api_managed_durable(self):
        topic_string = self.topic_string_template.format(type="API", destination="MANAGED", durable="DURABLE")
        subname = self.subname_template.format(type="Api", destination="Managed", durable="Durable")
        msg = self.msg_format(topic_string=topic_string)
        # register Subscription
        sub = self.create_api_subscription()

        # define a list self.sub_desc_list of subscription definitions so tearDown() can find it
        sub_desc = self.get_subscription_descriptor(subname, topic_string,
                                                    mq.CMQC.MQSO_CREATE + mq.CMQC.MQSO_DURABLE +
                                                    mq.CMQC.MQSO_MANAGED)
        self.sub_desc_list = [(sub, sub_desc, None)]

        sub.sub(sub_desc=sub_desc)
        # publish (put)
        self.pub(msg, topic_string)
        get_opts = self.create_get_opts()
        data = sub.get(None, mq.md(), get_opts)
        sub.close(sub_close_options=0, close_sub_queue=True)
        self.assertTrue(utils.strcmp(data, msg))

    def test_pubsub_api_managed_durable_1_to_n(self):
        """Test multiple subscriptions."""
        # number of subscriptions
        nsub = 5
        topic_string = self.topic_string_template.format(type="API", destination="MANAGED", durable="DURABLE")
        msg = self.msg_format(topic_string=topic_string)
        self.sub_desc_list = []
        subscriptions = []
        for n in range(nsub):
            sub_desc = self.get_subscription_descriptor(
                self.subname_template.format(type="Api", destination="Managed", durable="Durable{0}".format(n)),
                self.topic_string_template.format(type="API", destination="MANAGED", durable="DURABLE"),
                mq.CMQC.MQSO_CREATE + mq.CMQC.MQSO_DURABLE + mq.CMQC.MQSO_MANAGED)
            # register Subscription
            sub = self.create_api_subscription()
            self.sub_desc_list.append((sub, sub_desc, None))
            sub.sub(sub_desc=sub_desc)
            subscriptions.append(sub)

        # publish (put)
        self.pub(msg, topic_string)

        get_opts = self.create_get_opts()
        for n in range(nsub):
            data = subscriptions[n].get(None, mq.md(), get_opts)
            subscriptions[n].close(sub_close_options=0, close_sub_queue=True)
            self.assertTrue(utils.strcmp(data, msg))

    def test_pubsub_api_managed_non_durable(self):
        topic_string = self.topic_string_template.format(type="API", destination="MANAGED", durable="NON DURABLE")
        subname = self.subname_template.format(type="Api", destination="Managed", durable="Non Durable")
        msg = self.msg_format(topic_string=topic_string)
        sub_desc = self.get_subscription_descriptor(subname, topic_string,
                                                    mq.CMQC.MQSO_CREATE + mq.CMQC.MQSO_MANAGED)
        # register Subscription
        sub = self.create_api_subscription()
        self.sub_desc_list = [(sub, sub_desc, None)]
        sub.sub(sub_desc=sub_desc)
        # publish (put)
        self.pub(msg, topic_string)
        get_opts = self.create_get_opts()
        data = sub.get(None, mq.md(), get_opts)
        sub.close(sub_close_options=0, close_sub_queue=True)
        self.assertTrue(utils.strcmp(data, msg))

    def test_pubsub_api_managed_non_durable_rfh2(self):
        topic_string = self.topic_string_template.format(type="API_RFH2", destination="MANAGED", durable="NON DURABLE")
        subname = self.subname_template.format(type="Api_rfh2", destination="Managed", durable="Non Durable")
        msg = self.msg_format(topic_string=topic_string)
        sub_desc = self.get_subscription_descriptor(subname, topic_string,
                                                    mq.CMQC.MQSO_CREATE + mq.CMQC.MQSO_MANAGED)
        # register Subscription
        sub = self.create_api_subscription()
        self.sub_desc_list = [(sub, sub_desc, None)]
        sub.sub(sub_desc=sub_desc)

        # publish (put)
        put_mqmd = mq.md(
                            Format=mq.CMQC.MQFMT_RF_HEADER_2,
                            Encoding=273,
                            CodedCharSetId=1208)

        put_opts = mq.pmo()

        put_rfh2 = mq.RFH2(_StrucId=mq.CMQC.MQRFH_STRUC_ID,
                              Version=mq.CMQC.MQRFH_VERSION_2,
                              StrucLength=188,
                              Encoding=273,
                              CodedCharSetId=1208,
                              Format=mq.CMQC.MQFMT_STRING,
                              Flags=0,
                              NameValueCCSID=1208)
        # pylint: disable=line-too-long
        put_rfh2.add_folder(b"<psc><Command>RegSub</Command><Topic>$topictree/topiccat/topic</Topic><QMgrName>DebugQM</QMgrName><QName>PUBOUT</QName><RegOpt>PersAsPub</RegOpt></psc>")
        put_rfh2.add_folder(b"<testFolder><testVar>testValue</testVar></testFolder>")
        put_rfh2.add_folder(b"<mcd><Msd>xmlnsc</Msd></mcd>")

        self.pub_rfh2(msg, topic_string, put_mqmd, put_opts, [put_rfh2])
        get_opts = mq.GMO(Version=mq.CMQC.MQGMO_VERSION_4,
                             WaitInterval=15000,
                             Options=mq.CMQC.MQGMO_NO_SYNCPOINT + \
                                    mq.CMQC.MQGMO_FAIL_IF_QUIESCING + \
                                    mq.CMQC.MQGMO_WAIT)
        get_rfh2_list = []
        data = sub.get_rfh2(None, mq.md(Version=mq.CMQC.MQMD_VERSION_2), get_opts, get_rfh2_list)
        sub.close(sub_close_options=0, close_sub_queue=True)
        self.assertTrue(utils.strcmp(data, msg))

    def test_pubsub_admin_managed(self):
        topic_string = self.topic_string_template.format(type="ADMIN", destination="MANAGED", durable="DURABLE")
        subname = self.subname_template.format(type="Admin", destination="Managed", durable="Durable")
        msg = self.msg_format(topic_string=topic_string)
        queue_name = self.queue_name_template.format(type="ADMIN", durable="DURABLE")
        sub_desc = self.get_subscription_descriptor(subname, topic_string, mq.CMQC.MQSO_RESUME)

        # register Subscription
        self.create_admin_subscription(mq.CMQC.MQDC_MANAGED, subname, queue_name, topic_string)
        sub = mq.Subscription(self.qmgr)
        self.sub_desc_list = [(sub, sub_desc, None)]
        sub.sub(sub_desc=sub_desc)
        # publish (put)
        self.pub(msg, topic_string)

        get_opts = self.create_get_opts()
        data = sub.get(None, mq.md(), get_opts)

        sub.close(sub_close_options=0, close_sub_queue=True)
        self.assertTrue(utils.strcmp(data, msg))

    def test_pubsub_api_provided_durable(self):
        topic_string = self.topic_string_template.format(type="API", destination="PROVIDED", durable="DURABLE")
        subname = self.subname_template.format(type="Api", destination="Provided", durable="Durable")
        msg = self.msg_format(topic_string=topic_string)
        sub_desc = self.get_subscription_descriptor(subname, topic_string,
                                                    mq.CMQC.MQSO_CREATE + mq.CMQC.MQSO_DURABLE)
        queue_name = self.queue_name_template.format(type="API", durable="DURABLE")
        self.create_queue(queue_name)

        # create queue
        open_opts = mq.CMQC.MQOO_INPUT_AS_Q_DEF
        sub_queue = mq.Queue(self.qmgr, queue_name, open_opts)
        # register Subscription
        sub = self.create_api_subscription()
        self.sub_desc_list = [(sub, sub_desc, queue_name)]
        sub.sub(sub_desc=sub_desc, sub_queue=sub_queue)
        # publish (put)
        self.pub(msg, topic_string)

        get_opts = self.create_get_opts()
        data = sub.get(None, mq.md(), get_opts)

        sub.close(sub_close_options=0, close_sub_queue=True)
        self.assertTrue(utils.strcmp(data, msg))

    def test_pubsub_api_provided_non_durable(self):
        topic_string = self.topic_string_template.format(type="API", destination="PROVIDED", durable="NON DURABLE")
        subname = self.subname_template.format(type="Api", destination="Provided", durable="None Durable")
        msg = self.msg_format(topic_string=topic_string)
        sub_desc = self.get_subscription_descriptor(subname, topic_string,
                                                    mq.CMQC.MQSO_CREATE)
        queue_name = self.queue_name_template.format(type="API", durable="NON_DURABLE")
        # create queue
        self.create_queue(queue_name)
        open_opts = mq.CMQC.MQOO_INPUT_AS_Q_DEF
        sub_queue = mq.Queue(self.qmgr, queue_name, open_opts)
        # register Subscription
        sub = self.create_api_subscription()
        sub.sub(sub_desc=sub_desc, sub_queue=sub_queue)
        self.sub_desc_list = [(sub, sub_desc, queue_name)]
        # publish (put)
        self.pub(msg, topic_string)
        get_opts = self.create_get_opts()
        data = sub.get(None, mq.md(), get_opts)
        sub.close(sub_close_options=0, close_sub_queue=True)
        self.assertTrue(utils.strcmp(data, msg))

    def test_pubsub_admin_provided(self):
        topic_string = self.topic_string_template.format(type="ADMIN", destination="PROVIDED", durable="DURABLE")
        subname = self.subname_template.format(type="Admin", destination="Provided", durable="Durable")
        msg = self.msg_format(topic_string=topic_string)
        queue_name = self.queue_name_template.format(type="ADMIN", durable="DURABLE")
        sub_desc = self.get_subscription_descriptor(subname, topic_string, mq.CMQC.MQSO_RESUME)
        # create queue
        self.create_queue(queue_name)
        open_opts = mq.CMQC.MQOO_INPUT_AS_Q_DEF
        sub_queue = mq.Queue(self.qmgr, queue_name, open_opts)

        # register Subscription
        self.create_admin_subscription(mq.CMQC.MQDC_PROVIDED, subname, queue_name, topic_string)
        sub = mq.Subscription(self.qmgr)

        sub.sub(sub_desc=sub_desc, sub_queue=sub_queue)
        self.sub_desc_list = [(sub, sub_desc, queue_name)]
        # publish (put)
        self.pub(msg, topic_string)

        get_opts = self.create_get_opts()
        data = sub.get(None, mq.md(), get_opts)

        sub.close(sub_close_options=0, close_sub_queue=True)
        self.assertTrue(utils.strcmp(data, msg))

    def test_pubsub_already_exists(self):
        """Trying to register an already existing subscription should raise an exception.
        """
        topic_string = self.topic_string_template.format(type="API", destination="MANAGED", durable="DURABLE")
        subname = self.subname_template.format(type="Api", destination="Managed", durable="Durable")
        # define a list self.sub_desc_list of subscription definitions so tearDown() can find it
        sub_desc = self.get_subscription_descriptor(subname, topic_string,
                                                    mq.CMQC.MQSO_CREATE + mq.CMQC.MQSO_DURABLE + mq.CMQC.MQSO_MANAGED)
        # register Subscription
        sub = self.create_api_subscription()
        # this modifies the subscription descriptor
        sub.sub(sub_desc=sub_desc)
        sub = self.create_api_subscription()
        self.sub_desc_list = [(sub, sub_desc, None)]
        with self.assertRaises(mq.MQMIError) as cm:
            # create a new subscription descriptor
            # but do not add it to the list self.sub_desc_list
            # because tearDown() would try to delete the subscription
            # and fail because this registration will not succeed
            sub_desc = self.get_subscription_descriptor(subname, topic_string,
                                                        mq.CMQC.MQSO_CREATE + mq.CMQC.MQSO_DURABLE +
                                                        mq.CMQC.MQSO_MANAGED)
            sub.sub(sub_desc=sub_desc)
        # Exception should be
        # FAILED: MQRC_SUB_ALREADY_EXISTS
        self.assertEqual(cm.exception.reason, mq.CMQC.MQRC_SUB_ALREADY_EXISTS)

    def test_pubsub_encoding(self):
        """Test Encoding in managed and non durable subscription.
        """
        topic_string = self.topic_string_template.format(type="API", destination="MANAGED", durable="NON DURABLE")
        subname = self.subname_template.format(type="Api", destination="Managed", durable="Non Durable")
        messages = ["ascii", unicode("Euro sign: �", "iso-8859-15"), unicode("Uml�ut", "iso-8859-15"), unicodedata.lookup("INFINITY")]

        md = mq.md()
        # setting this means the message is entirely character data
        # md.Format = mq.CMQC.MQFMT_STRING
        # default
        # md.CodedCharSetId = mq.CMQC.MQCCSI_Q_MGR
        # UTF-8
        md.CodedCharSetId = 1208
        # UCS-2
        # md.CodedCharSetId = 1200
        # ISO-8859-1
        # md.CodedCharSetId = 819
        # ASCII
        # md.CodedCharSetId = 437

        # do not add the subscription to the list,
        # because tearDown() does not have to delete the subscription (in this non durable case)
        sub_desc = self.get_subscription_descriptor(subname, topic_string,
                                                    mq.CMQC.MQSO_CREATE + mq.CMQC.MQSO_MANAGED)
        # register Subscription
        sub = self.create_api_subscription()
        sub.sub(sub_desc=sub_desc)
        # publish (put)
        for msg in messages:
            self.pub(msg.encode("utf-8"), topic_string, md)

        get_opts = self.create_get_opts()
        get_opts["Options"] += mq.CMQC.MQGMO_CONVERT
        # md.CodedCharSetId = 819
        # md.CodedCharSetId = 437
        for msg in messages:
            # clear md for re-use
            md.MsgId = mq.CMQC.MQMI_NONE
            md.CorrelId = mq.CMQC.MQCI_NONE
            md.GroupId = mq.CMQC.MQGI_NONE
            # md.CodedCharSetId = 819
            data = sub.get(None, md, get_opts)
            self.assertEqual(unicode(data, "utf-8"), msg)
        sub.close(sub_close_options=0, close_sub_queue=True)


if __name__ == "__main__":
    unittest.main()
