"""MQMDE: Message Descriptor Extension"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class MDE(MQOpts):
    """ Construct an MQMDE Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    This will rarely be needed as the package primarily deals with MDv2 structures. But
    the MQXQH always contains only an MDv1 which in turn might be followed by an MDE that
    has to be parsed.
    """
    def __init__(self, **kw):
        super().__init__(tuple([
            ['_StrucId', CMQC.MQMDE_STRUC_ID, '4s'],
            ['Version', CMQC.MQMDE_VERSION_2, MQLONG_TYPE],
            ['StrucLength', CMQC.MQMDE_LENGTH_2, MQLONG_TYPE],
            ['Encoding', CMQC.MQENC_NATIVE, MQLONG_TYPE],
            ['CodedCharSetId', CMQC.MQCCSI_Q_MGR, MQLONG_TYPE],
            ['Format', b'', '8s'],
            ['Flags', CMQC.MQMDEF_NONE, MQLONG_TYPE],
            ['GroupId', b'', '24s'],
            ['MsgSeqNumber', 1, MQLONG_TYPE],
            ['Offset', 0, MQLONG_TYPE],
            ['MsgFlags', CMQC.MQMF_NONE, MQLONG_TYPE],
            ['OriginalLength', CMQC.MQOL_UNDEFINED, MQLONG_TYPE]]), **kw)
