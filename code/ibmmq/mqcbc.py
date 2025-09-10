"""MQCBC: Callback Context"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class CBC(MQOpts):
    """ Construct an MQCBC Structure with default values as per MQI. There
    are no real default values here, other than as needed to build the structure
    as the object is created and initialised by the qmgr rather than the application.
    """

    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQCBC_STRUC_ID, '4s'],
                ['Version', CMQC.MQCBC_VERSION_2, MQLONG_TYPE],
                ['CallType', 0, MQLONG_TYPE],
                ['Hobj', 0, MQLONG_TYPE],
                ['CallbackArea', 0, 'P'],
                ['ConnectionArea', 0, 'P'],
                ['CompCode', 0, MQLONG_TYPE],
                ['Reason', 0, MQLONG_TYPE],
                ['State', 0,  MQLONG_TYPE],
                ['DataLength', 0, MQLONG_TYPE],
                ['BufferLength', 0,  MQLONG_TYPE],
                ['Flags', 0, MQLONG_TYPE],
                ['ReconnectDelay', 0, MQLONG_TYPE]]

        # Some padding is needed to match the C structure, even though it's not
        # listed in cmqc.h
        opts += [['_Reserved1',0,MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
