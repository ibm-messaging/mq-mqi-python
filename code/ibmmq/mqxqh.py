"""MQXQH: Transmission header"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class XQH(MQOpts):
    """ Construct an MQXQH Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    Note that this is different from the C MQI definition of the XQH, as that incorporates
    an embedded MQMDv1 structure.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQXQH_STRUC_ID, '4s'],
                ['Version', CMQC.MQXQH_VERSION_1, MQLONG_TYPE],
                ['RemoteQName', b'', '48s'],
                ['RemoteQMgrName', b'', '48s'], ]

        super().__init__(tuple(opts), **kw)
