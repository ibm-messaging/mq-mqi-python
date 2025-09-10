"""Classes for executing PCF commands
"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqerrors import *
from ibmmq import CMQC, CMQCFC, CMQSTRC, MD, PMO, GMO, OD
from mqqueue import Queue
from mqpcf import *

from mqqmgr import *

try:
    from typing import Any, Union, Dict
except ImportError:
    pass

class ByteString:
    """ A simple wrapper around string values, suitable for passing into
    calls wherever IBM's docs state a 'byte string' object should be passed in.
    """
    def __init__(self, value: bytes):
        self.value = value
        self._byte_string = True

    def __len__(self) -> int:
        return len(self.value)

class _Filter:
    """ The base class for PCF filters. The initializer expects the user to provide
    the selector, value and the operator to use. For instance, they can be respectively
    MQCA_Q_DESC, 'MY.QUEUE.*', MQCFOP_LIKE. Compare with the public Filter class.
    """
    _filter_type = None  # type: Union[str, None]

    def __init__(self, selector, value, operator):
        self.selector = selector  # this is int
        self.value = ensure_strings_are_bytes(value)
        self.operator = operator  # this is int

    def __repr__(self):
        msg = '<%s at %s %s:%s:%s>'
        return msg % (self.__class__.__name__, hex(id(self)), self.selector, self.value, self.operator)

# ################################################################################################################################

class StringFilter(_Filter):
    """ A subclass of _Filter suitable for passing string filters around.
    """
    _filter_type = 'string'

# ################################################################################################################################

class IntegerFilter(_Filter):
    """ A subclass of _Filter suitable for passing integer filters around.
    """
    _filter_type = 'integer'

# ################################################################################################################################

class ByteStringFilter(_Filter):
    """ A subclass of _Filter suitable for passing byte string filters around.
    """
    _filter_type = 'bytestring'

###############################################################################################################################

class FilterOperator:
    """ Creates low-level filters based on what's been provided in the high-level
    Filter object.
    """
    operator_mapping = {
        'less': CMQCFC.MQCFOP_LESS,
        'equal': CMQCFC.MQCFOP_EQUAL,
        'greater': CMQCFC.MQCFOP_GREATER,
        'not_less': CMQCFC.MQCFOP_NOT_LESS,
        'not_equal': CMQCFC.MQCFOP_NOT_EQUAL,
        'not_greater': CMQCFC.MQCFOP_NOT_GREATER,
        'like': CMQCFC.MQCFOP_LIKE,
        'not_like': CMQCFC.MQCFOP_NOT_LIKE,
        'contains': CMQCFC.MQCFOP_CONTAINS,
        'excludes': CMQCFC.MQCFOP_EXCLUDES,
        'contains_gen': CMQCFC.MQCFOP_CONTAINS_GEN,
        'excludes_gen': CMQCFC.MQCFOP_EXCLUDES_GEN,
        } # type: Dict[str, int]

    def __init__(self, selector:int, operator_name:str):
        self.filter_cls = _Filter # Start with the parent class as the first ref is how mypy sees it
        if CMQC.MQIA_FIRST <= selector <= CMQC.MQIA_LAST:
            self.filter_cls = IntegerFilter
        elif CMQC.MQCA_FIRST <= selector <= CMQC.MQCA_LAST:
            self.filter_cls = StringFilter
        elif CMQC.MQBA_FIRST <= selector <= CMQC.MQBA_LAST:
            self.filter_cls = ByteStringFilter
        else:
            msg = 'selector [%s] is of an unsupported type (not an integer ' + \
                'or string or bytestring attribute).'
            raise Error(msg % selector)
        self.selector = selector
        self.operator = self.operator_mapping.get(operator_name)
        # Do we support the operator?
        if not self.operator:
            msg = 'Operator [%s] is not supported.'
            raise Error(msg % operator_name)

    def __call__(self, value: Union[str, int]) -> _Filter: # Union[IntegerFilter, StringFilter, ByteStringFilter]:
        ensure_not_unicode(value)
        return (self.filter_cls)(self.selector, value, self.operator)

# ################################################################################################################################

class Filter:
    """ The user-facing filtering class which provides syntactic sugar
    on top of _Filter and its subclasses.
    """
    def __init__(self, selector:int):
        self.selector = selector

    def __getattribute__(self, name:str) -> FilterOperator:
        """ A generic method for either fetching the Filter object's
        attributes or calling magic methods like 'like', 'contains' etc.
        """
        if name=='selector':
            return object.__getattribute__(self, name)

        return FilterOperator(self.selector, name)

# ################################################################################################################################

#
# This piece of magic shamelessly plagiarised from xmlrpclib.py. It
# works a bit like a C++ STL functor.
#
class _Method:
    def __init__(self, pcf, name):
        # type: (PCFExecute, str) -> None
        self.__pcf = pcf
        self.__name = name

    def __getattr__(self, name):
        # type: (str) -> _Method
        return _Method(self.__pcf, '%s.%s' % (self.__name, name))

    def __call__(self, *args):
        # type: (Union[dict, list, _Filter]) -> list
        if self.__name[0:7] == 'CMQCFC.':
            self.__name = self.__name[7:]
        if self.__pcf.qm:
            bytes_encoding = self.__pcf.bytes_encoding
            _ = self.__pcf.qm.getHandle()
        else:
            bytes_encoding = 'utf8'
            _ = self.__pcf.getHandle()

        len_args = len(args)

        if len_args == 2:
            args_dict, filters = args

        elif len_args == 1:
            args_dict, filters = args[0], []

        else:
            args_dict, filters = {}, []

        # MQCFH_VERSION_3 means we have a minimum of MQ V6 as the
        # target qmgr.
        mqcfh = CFH(Version=CMQCFC.MQCFH_VERSION_3,
                    Command=CMQCFC.__dict__[self.__name],
                    Type=CMQCFC.MQCFT_COMMAND_XR,
                    ParameterCount=len(args_dict) + len(filters))
        message = mqcfh.pack()

        parameter = MQOpts([]) # Set an initial type, to satisfy mypy

        if args_dict:
            if isinstance(args_dict, dict):
                for key, value in args_dict.items():
                    if isinstance(value, (str, bytes)):
                        if is_unicode(value):
                            value = value.encode(bytes_encoding)

                        parameter = CFST(Parameter=key,
                                         String=value)
                    elif isinstance(value, ByteString):
                        parameter = CFBS(Parameter=key,
                                         String=value.value)
                    elif isinstance(value, int):
                        # Backward compatibility for older behaviour
                        # returning a single value instead of a list
                        is_list = False
                        for item in CMQCFC.__dict__:
                            if ((item[:7] == 'MQIACF_' or item[:7] == 'MQIACH_')
                                and item[-6:] == '_ATTRS'
                                and CMQCFC.__dict__[item] == key):

                                is_list = True
                                break

                        if not is_list:
                            parameter = CFIN(Parameter=key,
                                            Value=value)
                        else:
                            parameter = CFIL(Parameter=key,
                                            Values=[value])
                    elif isinstance(value, list):
                        if isinstance(value[0], int):
                            parameter = CFIL(Parameter=key, Values=value)
                        elif isinstance(value[0], (str, bytes)):
                            _value = []
                            for item in value:
                                if is_unicode(item):
                                    item = item.encode(bytes_encoding)
                                _value.append(item)
                            value = _value

                            parameter = CFSL(Parameter=key, Strings=value)

                    message = message + parameter.pack()
            elif isinstance(args_dict, list):
                for parameter in args_dict:
                    message = message + parameter.pack()

        if filters:
            for pcf_filter in filters:
                if isinstance(pcf_filter, _Filter):
                    if pcf_filter._filter_type == 'string':
                        pcf_filter = CFSF(Parameter=pcf_filter.selector,
                                          Operator=pcf_filter.operator,
                                          FilterValue=pcf_filter.value)
                    elif pcf_filter._filter_type == 'integer':
                        pcf_filter = CFIF(Parameter=pcf_filter.selector,
                                          Operator=pcf_filter.operator,
                                          FilterValue=pcf_filter.value)
                    elif pcf_filter._filter_type == 'bytestring':
                        pcf_filter = CFBF(Parameter=pcf_filter.selector,
                                          Operator=pcf_filter.operator,
                                          FilterValue=pcf_filter.value)

                message = message + pcf_filter.pack()

        # Either open the command queue, or use the pre-opened Queue object
        command_queue_opened = False
        if self.__pcf._command_queue is None:
            assert self.__pcf.qm is not None # Keep mypy happy
            command_queue = Queue(self.__pcf.qm,
                              self.__pcf.command_queue_name,
                              CMQC.MQOO_OUTPUT)
            self.__pcf._command_queue = command_queue
            command_queue_opened = True
        else:
            command_queue = self.__pcf._command_queue

        put_md = MD(Format=CMQC.MQFMT_ADMIN,
                    MsgType=CMQC.MQMT_REQUEST,
                    ReplyToQ=self.__pcf.reply_queue_name,
                    Feedback=CMQC.MQFB_NONE,
                    # Multiply the wait time to give a reasonable expiry time
                    # Convert to tenths and then x3 (for out, back and delay)
                    Expiry=(self.__pcf.response_wait_interval // 100) * 3,
                    Report=CMQC.MQRO_PASS_DISCARD_AND_EXPIRY | CMQC.MQRO_DISCARD_MSG)
        put_opts = PMO(Options=CMQC.MQPMO_NO_SYNCPOINT)

        command_queue.put(message, put_md, put_opts)

        # If it was opened for this run, then close it again immediately
        if command_queue_opened:
            command_queue.close()
            self.__pcf._command_queue = None

        gmo_options = CMQC.MQGMO_NO_SYNCPOINT + CMQC.MQGMO_FAIL_IF_QUIESCING + \
                      CMQC.MQGMO_WAIT

        if self.__pcf.convert:
            gmo_options = gmo_options + CMQC.MQGMO_CONVERT

        get_opts = GMO(
            Options=gmo_options,
            Version=CMQC.MQGMO_VERSION_2,
            MatchOptions=CMQC.MQMO_MATCH_CORREL_ID,
            WaitInterval=self.__pcf.response_wait_interval)
        get_md = MD(CorrelId=put_md.MsgId)

        # Initialise the list of responses
        ress = []

        got_all_replies = False
        in_cmdscope = False

        while True:
            try:
                message = self.__pcf.reply_queue.get(None, get_md, get_opts)
                res, mqcfh_response = self.__pcf.unpack(message)

                t = mqcfh_response.Type

                # The XR messages come back from a z/OS queue manager. For an individual qmgr operation
                # they are essentially meaningless. But for something with a CMDSCOPE flag, then they
                # show how we need to process and wait for all responses.
                # Note: The MQCACF_RESPONSE_Q_MGR_NAME element shows which qmgr replied when using CMDSCOPE
                flag = 0
                if t == CMQCFC.MQCFT_XR_MSG:
                    # Look for flag saying cmdscope ACCEPTED
                    try:
                        flag = res.get(CMQCFC.MQIACF_COMMAND_INFO)
                        if flag == CMQCFC.MQCMDI_CMDSCOPE_ACCEPTED:
                            in_cmdscope = True
                    except KeyError:
                        pass

                # Have all the replies been received? Different for CMDSCOPE(*) compared to regular
                if in_cmdscope:
                    if t == CMQCFC.MQCFT_XR_MSG:
                        try:
                            flag = res.get(CMQCFC.MQIACF_COMMAND_INFO)
                            if flag == CMQCFC.MQCMDI_CMDSCOPE_COMPLETED:
                                got_all_replies = True
                        except KeyError:
                            pass
                elif mqcfh_response.Control == CMQCFC.MQCFC_LAST:
                    got_all_replies = True

                # Don't add these to the responses
                if t in (CMQCFC.MQCFT_XR_MSG, CMQCFC.MQCFT_XR_SUMMARY):
                    res = None

                if res:
                    ress.append(res)

                # print(f"Flag: {flag} incmd: {in_cmdscope} gotall: {got_all_replies}")
                if got_all_replies:
                    break

            except MQMIError as e:
                # There might be something special we want to do with 2033s.
                # But for now, just report it in the same way as any other failure.
                if e.reason  == CMQC.MQRC_NO_MSG_AVAILABLE:
                    # print("Timed out...")
                    raise e
                    # return ress
                raise e

        return ress

# ################################################################################################################################

def _merge_dicts(*dict_args):
    result = {}
    for d in dict_args:
        result.update(d)
    return result

#
# Execute a PCF commmand. Inspired by Maas-Maarten Zeeman
#
class PCFExecute(QueueManager):

    """Send PCF commands or inquiries. PCFExecute must be connected to the Queue Manager
    (using one of the techniques inherited from QueueManager) before
    it's used. Commands are executed by calling a CMQC defined
    MQCMD_* method on the object.  """

    qm = None  # type: Union[QueueManager, None]

    iaStringDict = _merge_dicts(CMQSTRC.MQIA_DICT, CMQSTRC.MQIACF_DICT, CMQSTRC.MQIACH_DICT)
    caStringDict = _merge_dicts(CMQSTRC.MQCA_DICT, CMQSTRC.MQCACF_DICT, CMQSTRC.MQCACH_DICT)
    baStringDict = _merge_dicts(CMQSTRC.MQBACF_DICT)

    def __init__(self, name=None,
                 model_queue_name=b'SYSTEM.DEFAULT.MODEL.QUEUE',
                 reply_queue_name=None,
                 dynamic_queue_name=b'PYMQPCF.*',
                 command_queue_name=b'SYSTEM.ADMIN.COMMAND.QUEUE',
                 command_queue=None,
                 response_wait_interval=5000,  # 5 seconds
                 convert=True):
        # type: (Any, Union[str,bytes], Union[None,bytes,str], Union[str,bytes], Union[str,bytes], Union[None,Queue], int, bool) -> None
        """PCFExecute(name = '')

        Connect to the Queue Manager 'name' (default value '') ready
        for a PCF command. If name is a QueueManager instance, it is
        used for the connection, otherwise a new connection is made """

        # The default value gives backwards-compatible version where the
        # command queue is opened for each execution. But we can supply
        # a pre-opened queue handle
        self._command_queue = command_queue

        self.__command_queue_name = command_queue_name

        self.__convert = convert
        self.__response_wait_interval = response_wait_interval

        if model_queue_name and reply_queue_name:
            raise PYIFError('Do not specify both a model_queue_name and a reply_queue_name')

        # From here, we can treat the 2 qnames as equivalent. So assign to one and use it
        # There is an internal __reply_queue_name field, but that comes from the result of the
        # MQOPEN - gives the TDQ name if that's been created.
        if reply_queue_name:
            model_queue_name = reply_queue_name

        if isinstance(name, QueueManager):
            self.qm = name
            super().__init__(None)
        else:
            super().__init__(name)
            self.qm = self

        od = OD(ObjectName=model_queue_name,
                DynamicQName=dynamic_queue_name)

        self.__reply_queue = Queue(self.qm, od, CMQC.MQOO_INPUT_EXCLUSIVE)
        self.__reply_queue_name = od.ObjectName.strip()

    @property
    def command_queue_name(self):
        """Return the command queue name"""
        return self.__command_queue_name

    @property
    def convert(self):
        """Return whether data conversion is active"""
        return self.__convert

    @property
    def reply_queue(self):
        """Return the reply queue object"""
        return self.__reply_queue

    @property
    def reply_queue_name(self):
        """Return the reply queue name"""
        return self.__reply_queue_name

    @property
    def response_wait_interval(self):
        """Return the wait interval for this object"""
        return self.__response_wait_interval

    def __getattr__(self, name):
        """MQCMD_*(attrDict)

        Execute the PCF command or inquiry, passing an an optional
        dictionary of MQ attributes.  The command must begin with
        MQCMD_, and must be one of those defined in the CMQC
        module. If attrDict is passed, its keys must be an attribute
        as defined in the CMQC or CMQC modules (MQCA_*, MQIA_*,
        MQCACH_* or MQIACH_*). The key value must be an int or string,
        as appropriate.

        If an inquiry is executed, a list of dictionaries (one per
        matching query) is returned. Each dictionary encodes the
        attributes and values of the object queried. The keys are as
        defined in the CMQC module (MQIA_*, MQCA_*), The values are
        strings or ints, as appropriate.

        If a command was executed, or no inquiry results are
        available, an empty list is returned.  """

        return _Method(self, name)

    @staticmethod
    def stringify_keys(raw_dict):
        """stringifyKeys(raw_dict)

        Return raw_dict with its keys converted to string
        mnemonics, as defined in CMQC. """

        rv = {}
        for k in raw_dict.keys():
            if isinstance(raw_dict[k], bytes):
                d = PCFExecute.caStringDict
            elif isinstance(raw_dict[k], str):
                raise TypeError('In Python 3 use bytes, not str (found "{0}":"{1}")'.format(k, raw_dict[k]))
            else:
                d = PCFExecute.iaStringDict
            try:
                rv[d[k]] = raw_dict[k]
            except KeyError:
                rv[k] = raw_dict[k]
        return rv

    # Backward compatibility
    stringifyKeys = stringify_keys

    def disconnect(self):
        """ Disconnect from reply_queue
        """
        try:
            if self.__reply_queue and self.__reply_queue.get_handle():
                self.__reply_queue.close()
        except MQMIError:
            pass
        finally:
            self.__reply_queue = None
            self.__reply_queue_name = None

    @staticmethod
    def unpack(message: bytes) -> tuple[dict, CFH]:
        """Unpack PCF message to dictionary
        """

        mqcfh = CFH(Version=CMQCFC.MQCFH_VERSION_1)
        mqcfh.unpack(message[:CMQCFC.MQCFH_STRUC_LENGTH])

        if mqcfh.Version != CMQCFC.MQCFH_VERSION_1:
            mqcfh = CFH(Version=mqcfh.Version)
            mqcfh.unpack(message[:CMQCFC.MQCFH_STRUC_LENGTH])

        if mqcfh.CompCode != CMQC.MQCC_OK:
            raise MQMIError(mqcfh.CompCode, mqcfh.Reason)

        res = {}  # type: Dict[str, Union[int, str, bool, Dict]]
        index = mqcfh.ParameterCount
        cursor = CMQCFC.MQCFH_STRUC_LENGTH
        parameter = None  # type: Union[MQOpts, None]
        group = None  # type: Union[None, Dict[str, Union[str, int, bool]]]
        group_count = 0

        while index > 0:

            value = None # Will always be set by one of these clauses
            parameter_type = struct.unpack(MQLONG_TYPE, message[cursor:cursor + 4])[0]

            if group_count == 0:
                group = None
            if group is not None:
                group_count -= 1
            if parameter_type == CMQCFC.MQCFT_STRING:
                parameter = CFST()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFST_STRUC_LENGTH_FIXED])
                if parameter.StringLength > 1:
                    parameter = CFST(StringLength=parameter.StringLength)
                    parameter.unpack(message[cursor:cursor + parameter.StrucLength])
                value = parameter.String
            elif parameter_type == CMQCFC.MQCFT_STRING_LIST:
                parameter = CFSL()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFSL_STRUC_LENGTH_FIXED])
                if parameter.StringLength > 1:
                    parameter = CFSL(StringLength=parameter.StringLength,
                                     Count=parameter.Count,
                                     StrucLength=parameter.StrucLength)
                    parameter.unpack(message[cursor:cursor + parameter.StrucLength])
                value = parameter.Strings
            elif parameter_type == CMQCFC.MQCFT_INTEGER:
                parameter = CFIN()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFIN_STRUC_LENGTH])
                value = parameter.Value
            elif parameter_type == CMQCFC.MQCFT_INTEGER64:
                parameter = CFIN64()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFIN64_STRUC_LENGTH])
                value = parameter.Value
            elif parameter_type == CMQCFC.MQCFT_INTEGER_LIST:
                parameter = CFIL()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFIL_STRUC_LENGTH_FIXED])
                if parameter.Count > 0:
                    parameter = CFIL(Count=parameter.Count,
                                     StrucLength=parameter.StrucLength)
                    parameter.unpack(message[cursor:cursor + parameter.StrucLength])
                value = parameter.Values
            elif parameter_type == CMQCFC.MQCFT_INTEGER64_LIST:
                parameter = CFIL64()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFIL64_STRUC_LENGTH_FIXED])
                if parameter.Count > 0:
                    parameter = CFIL64(Count=parameter.Count,
                                       StrucLength=parameter.StrucLength)
                    parameter.unpack(message[cursor:cursor + parameter.StrucLength])
                value = parameter.Values
            elif parameter_type == CMQCFC.MQCFT_GROUP:
                parameter = CFGR()
                parameter.unpack(message[cursor:cursor + parameter.StrucLength])
                group_count = parameter.ParameterCount
                index += group_count
                group = {}
                res[parameter.Parameter] = res.get(parameter.Parameter, [])
                res[parameter.Parameter].append(group)
            elif parameter_type == CMQCFC.MQCFT_BYTE_STRING:
                parameter = CFBS()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFBS_STRUC_LENGTH_FIXED])
                if parameter.StringLength > 1:
                    parameter = CFBS(StringLength=parameter.StringLength)
                    parameter.unpack(message[cursor:cursor + parameter.StrucLength])
                value = parameter.String
            elif parameter_type == CMQCFC.MQCFT_STRING_FILTER:
                parameter = CFSF()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFSF_STRUC_LENGTH_FIXED])
                if parameter.FilterValueLength > 0:
                    parameter = CFSF(FilterValueLength=parameter.FilterValueLength)
                    parameter.unpack(message[cursor:cursor + parameter.StrucLength])
                value = (parameter.Operator, parameter.FilterValue)
            elif parameter_type == CMQCFC.MQCFT_BYTE_STRING_FILTER:
                parameter = CFBF()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFBF_STRUC_LENGTH_FIXED])
                if parameter.FilterValueLength > 0:
                    parameter = CFBF(FilterValueLength=parameter.FilterValueLength)
                    parameter.unpack(message[cursor:cursor + parameter.StrucLength])
                value = (parameter.Operator, parameter.FilterValue)
            elif parameter_type == CMQCFC.MQCFT_INTEGER_FILTER:
                parameter = CFIF()
                parameter.unpack(message[cursor:cursor + CMQCFC.MQCFIF_STRUC_LENGTH])
                value = (parameter.Operator, parameter.FilterValue)
            else:
                pcf_type = struct.unpack(MQLONG_TYPE, message[cursor:cursor + 4])
                raise NotImplementedError('Unpack for type ({}) not implemented'.format(pcf_type))
            index -= 1
            cursor += parameter.StrucLength
            if parameter.Type == CMQCFC.MQCFT_GROUP:
                continue
            if group is not None:
                group[parameter.Parameter] = value
            else:
                res[parameter.Parameter] = value

        return res, mqcfh
