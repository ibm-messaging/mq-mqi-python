"""MQBNO: Balancing Options"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class BNO(MQOpts):
    """ Construct an MQBNO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):

        opts = [['_StrucId', CMQC.MQBNO_STRUC_ID, '4s'],
                ['Version', CMQC.MQBNO_VERSION_1, MQLONG_TYPE],
                ['ApplType',CMQC.MQBNO_BALTYPE_SIMPLE, MQLONG_TYPE],
                ['Timeout', CMQC.MQBNO_TIMEOUT_AS_DEFAULT, MQLONG_TYPE],
                ['Options',CMQC.MQBNO_OPTIONS_NONE,MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
