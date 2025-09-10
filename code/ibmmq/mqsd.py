"""MQSD: Subscription Descriptor"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class SD(MQOpts):
    """ Construct an MQSD Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQSD_STRUC_ID, '4s'],
                ['Version', CMQC.MQSD_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQSO_NON_DURABLE, MQLONG_TYPE],
                ['ObjectName', b'', '48s'],
                ['AlternateUserId', b'', '12s'],
                ['AlternateSecurityId', CMQC.MQSID_NONE, '40s'],
                ['SubExpiry', CMQC.MQEI_UNLIMITED, MQLONG_TYPE],

                # ObjectString
                ['ObjectStringVSPtr', 0, 'P'],
                ['ObjectStringVSOffset', (0), MQLONG_TYPE],
                ['ObjectStringVSBufSize', (0), MQLONG_TYPE],
                ['ObjectStringVSLength', (0), MQLONG_TYPE],
                ['ObjectStringVSCCSID', (0), MQLONG_TYPE],

                # Subname
                ['SubNameVSPtr', 0, 'P'],
                ['SubNameVSOffset', (0), MQLONG_TYPE],
                ['SubNameVSBufSize', (0), MQLONG_TYPE],
                ['SubNameVSLength', (0), MQLONG_TYPE],
                ['SubNameVSCCSID', (0), MQLONG_TYPE],

                # SubUserData
                ['SubUserDataVSPtr', 0, 'P'],
                ['SubUserDataVSOffset', (0), MQLONG_TYPE],
                ['SubUserDataVSBufSize', (0), MQLONG_TYPE],
                ['SubUserDataVSLength', (0), MQLONG_TYPE],
                ['SubUserDataVSCCSID', (0), MQLONG_TYPE],

                ['SubCorrelId', CMQC.MQCI_NONE, '24s'],
                ['PubPriority', CMQC.MQPRI_PRIORITY_AS_Q_DEF, MQLONG_TYPE],
                ['PubAccountingToken', CMQC.MQACT_NONE, '32s'],
                ['PubApplIdentityData', b'', '32s'],

                # SelectionString
                ['SelectionStringVSPtr', 0, 'P'],
                ['SelectionStringVSOffset', (0), MQLONG_TYPE],
                ['SelectionStringVSBufSize', (0), MQLONG_TYPE],
                ['SelectionStringVSLength', (0), MQLONG_TYPE],
                ['SelectionStringVSCCSID', (0), MQLONG_TYPE],

                ['SubLevel', 1, MQLONG_TYPE],

                # SelectionString
                ['ResObjectStringVSPtr', 0, 'P'],
                ['ResObjectStringVSOffset', (0), MQLONG_TYPE],
                ['ResObjectStringVSBufSize', (0), MQLONG_TYPE],
                ['ResObjectStringVSLength', (0), MQLONG_TYPE],
                ['ResObjectStringVSCCSID', (0), MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
