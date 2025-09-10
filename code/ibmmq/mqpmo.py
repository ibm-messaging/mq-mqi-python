"""MQPMO: Put Message Options"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, ibmmqc

class PMO(MQOpts):
    """ Construct an MQPMO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [
            ['_StrucId', CMQC.MQPMO_STRUC_ID, '4s'],
            ['Version', CMQC.MQPMO_VERSION_3, MQLONG_TYPE],
            ['Options', CMQC.MQPMO_NONE, MQLONG_TYPE],
            ['Timeout', -1, MQLONG_TYPE],
            ['Context', 0, MQLONG_TYPE],
            ['KnownDestCount', 0, MQLONG_TYPE],
            ['UnknownDestCount', 0, MQLONG_TYPE],
            ['InvalidDestCount', 0, MQLONG_TYPE],
            ['ResolvedQName', b'', '48s'],
            ['ResolvedQMgrName', b'', '48s'],
            ['RecsPresent', 0, MQLONG_TYPE],
            ['PutMsgRecFields',  0, MQLONG_TYPE],
            ['PutMsgRecOffset', 0, MQLONG_TYPE],
            ['ResponseRecOffset', 0, MQLONG_TYPE],
            ['PutMsgRecPtr', 0, 'P'],
            ['ResponseRecPtr', 0, 'P']]

        pmo_current_version = ibmmqc.__strucversions__.get("pmo",1)
        if pmo_current_version >= CMQC.MQPMO_VERSION_3:
            opts += [
                ['OriginalMsgHandle', 0, 'q'],
                ['NewMsgHandle', 0, 'q'],
                ['Action', 0, MQLONG_TYPE],
                ['PubLevel', 9, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)

# Backward compatibility
pmo = PMO
