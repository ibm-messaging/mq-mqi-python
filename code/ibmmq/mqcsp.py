"""MQCSP: Security Parameters"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, ibmmqc

class CSP(MQOpts):
    """ Construct an MQCSP Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):

        csp_current_version = ibmmqc.__strucversions__.get("csp",1)

        opts = [['_StrucId', CMQC.MQCSP_STRUC_ID, '4s'],
                ['Version', CMQC.MQCSP_VERSION_1, MQLONG_TYPE],
                ['AuthenticationType', CMQC.MQCSP_AUTH_NONE, MQLONG_TYPE],
                ['_Reserved1', 0, MQLONG_TYPE],
                ['CSPUserId', 0, 'P'],
                ['_CSPUserIdOffset', 0, MQLONG_TYPE],
                ['_CSPUserIdLength',0, MQLONG_TYPE],
                ['_Reserved2', 0, INTEGER64_TYPE],
                ['CSPPassword',0,'P'],
                ['_CSPPasswordOffset',0,MQLONG_TYPE],
                ['_CSPPasswordLength',0,MQLONG_TYPE]]

        if csp_current_version >= CMQC.MQCSP_VERSION_2:
            opts += [['_Reserved3', 0,INTEGER64_TYPE],
               ['InitialKey',0,'P'],
               ['_InitialKeyOffset',0,MQLONG_TYPE],
               ['_InitialKeyLength',0,MQLONG_TYPE]]

        if csp_current_version >= CMQC.MQCSP_VERSION_3:
            opts += [['_Reserved4', 0, INTEGER64_TYPE],
               ['Token',0,'P'],
               ['_TokenOffset',0,MQLONG_TYPE],
               ['_TokenLength',0,MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
