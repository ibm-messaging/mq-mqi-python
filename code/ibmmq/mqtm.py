"""MQTM, MQTMC2: Trigger Monitor structures"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

# ################################################################################################################################

class TM(MQOpts):
    """ Construct an MQTM Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        super().__init__(tuple([
            ['_StrucId', CMQC.MQTM_STRUC_ID, '4s'],
            ['Version', CMQC.MQTM_VERSION_1, MQLONG_TYPE],
            ['QName', b'', '48s'],
            ['ProcessName', b'', '48s'],
            ['TriggerData', b'', '64s'],
            ['ApplType', 0, MQLONG_TYPE],
            ['ApplId', b'', '256s'],
            ['EnvData', b'', '128s'],
            ['UserData', b'', '128s']]), **kw)

# ################################################################################################################################

class TMC2(MQOpts):
    """ Construct an MQTMC2 Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        super().__init__(tuple([
            ['_StrucId', CMQC.MQTMC_STRUC_ID, '4s'],
            ['Version', CMQC.MQTMC_VERSION_2, '4s'],
            ['QName', b'', '48s'],
            ['ProcessName', b'', '48s'],
            ['TriggerData', b'', '64s'],
            ['ApplType', b'', '4s'],
            ['ApplId', b'', '256s'],
            ['EnvData', b'', '128s'],
            ['UserData', b'', '128s'],
            ['QMgrName', b'', '48s']]), **kw)
