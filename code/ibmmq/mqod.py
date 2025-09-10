"""MQOD: Object Descriptor"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, ibmmqc

# This would have to change for running on a z/OS system where
# the dynamic queue prefix is "CSQ.*"
_default_dq_prefix = b'AMQ.*'

class OD(MQOpts):
    """ Construct an MQOD Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQOD_STRUC_ID, '4s'],
                ['Version', CMQC.MQOD_VERSION_4, MQLONG_TYPE],
                ['ObjectType', CMQC.MQOT_Q, MQLONG_TYPE],
                ['ObjectName', b'', '48s'],
                ['ObjectQMgrName', b'', '48s'],
                ['DynamicQName', _default_dq_prefix, '48s'],
                ['AlternateUserId', b'', '12s'],
                ['RecsPresent', 0, MQLONG_TYPE],
                ['KnownDestCount', 0, MQLONG_TYPE],
                ['UnknownDestCount', 0, MQLONG_TYPE],
                ['InvalidDestCount', 0, MQLONG_TYPE],
                ['ObjectRecOffset', 0, MQLONG_TYPE],
                ['ResponseRecOffset', 0, MQLONG_TYPE],
                ['ObjectRecPtr', 0, 'P'],
                ['ResponseRecPtr', 0, 'P'],
                ['AlternateSecurityId', b'', '40s'],
                ['ResolvedQName', b'', '48s'],
                ['ResolvedQMgrName', b'', '48s'], ]

        od_current_version = ibmmqc.__strucversions__.get("od",1)
        if od_current_version >= CMQC.MQOD_VERSION_4:
            opts += [

                # ObjectString
                ['ObjectStringVSPtr', 0, 'P'],
                ['ObjectStringVSOffset', (0), MQLONG_TYPE],
                ['ObjectStringVSBufSize', (0), MQLONG_TYPE],
                ['ObjectStringVSLength', (0), MQLONG_TYPE],
                ['ObjectStringVSCCSID', (0), MQLONG_TYPE],

                # SelectionString
                ['SelectionStringVSPtr', 0, 'P'],
                ['SelectionStringVSOffset', (0), MQLONG_TYPE],
                ['SelectionStringVSBufSize', (0), MQLONG_TYPE],
                ['SelectionStringVSLength', (0), MQLONG_TYPE],
                ['SelectionStringVSCCSID', (0), MQLONG_TYPE],

                # ResObjectString
                ['ResObjectStringVSPtr', 0, 'P'],
                ['ResObjectStringVSOffset', (0), MQLONG_TYPE],
                ['ResObjectStringVSBufSize', (0), MQLONG_TYPE],
                ['ResObjectStringVSLength', (0), MQLONG_TYPE],
                ['ResObjectStringVSCCSID', (0), MQLONG_TYPE],

                ['ResolvedType', (-3), MQLONG_TYPE]]

            # For 64bit platforms MQLONG is an int and this pad
            # needs to be here for MQ 7.0
            if MQLONG_TYPE == 'i':
                opts += [['pad', b'', '4s']]

        super().__init__(tuple(opts), **kw)

# Backward compatibility
od = OD
