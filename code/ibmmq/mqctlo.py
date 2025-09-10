"""MQCTLO: MQCTL Options"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class CTLO(MQOpts):
    """ Construct an MQCTLO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQCTLO_STRUC_ID, '4s'],
                ['Version', CMQC.MQCTLO_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQCTLO_NONE, MQLONG_TYPE],
                ['_Reserved', 0, MQLONG_TYPE],
                ['ConnectionArea', 0, 'P']]

        super().__init__(tuple(opts), **kw)
