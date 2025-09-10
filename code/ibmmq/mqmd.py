"""MQMD: Message Descriptor"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class MD(MQOpts):
    """ Construct an MQMD Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    This is initialised as a V2 structure as every in-support version of MQ supports
    that level.
    """
    def __init__(self, **kw):
        super().__init__(tuple([
            ['_StrucId', CMQC.MQMD_STRUC_ID, '4s'],
            ['Version', CMQC.MQMD_VERSION_2, MQLONG_TYPE],
            ['Report', CMQC.MQRO_NONE, MQLONG_TYPE],
            ['MsgType', CMQC.MQMT_DATAGRAM, MQLONG_TYPE],
            ['Expiry', CMQC.MQEI_UNLIMITED, MQLONG_TYPE],
            ['Feedback', CMQC.MQFB_NONE, MQLONG_TYPE],
            ['Encoding', CMQC.MQENC_NATIVE, MQLONG_TYPE],
            ['CodedCharSetId', CMQC.MQCCSI_Q_MGR, MQLONG_TYPE],
            ['Format', b'', '8s'],
            ['Priority', CMQC.MQPRI_PRIORITY_AS_Q_DEF, MQLONG_TYPE],
            ['Persistence', CMQC.MQPER_PERSISTENCE_AS_Q_DEF, MQLONG_TYPE],
            ['MsgId', b'', '24s'],
            ['CorrelId', b'', '24s'],
            ['BackoutCount', 0, MQLONG_TYPE],
            ['ReplyToQ', b'', '48s'],
            ['ReplyToQMgr', b'', '48s'],
            ['UserIdentifier', b'', '12s'],
            ['AccountingToken', b'', '32s'],
            ['ApplIdentityData', b'', '32s'],
            ['PutApplType', CMQC.MQAT_NO_CONTEXT, MQLONG_TYPE],
            ['PutApplName', b'', '28s'],
            ['PutDate', b'', '8s'],
            ['PutTime', b'', '8s'],
            ['ApplOriginData', b'', '4s'],
            ['GroupId', b'', '24s'],
            ['MsgSeqNumber', 1, MQLONG_TYPE],
            ['Offset', 0, MQLONG_TYPE],
            ['MsgFlags', CMQC.MQMF_NONE, MQLONG_TYPE],
            ['OriginalLength', CMQC.MQOL_UNDEFINED, MQLONG_TYPE]]), **kw)

# Backward compatibility
md = MD
