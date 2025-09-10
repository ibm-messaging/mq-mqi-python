"""MQSRO: Subscription Request Options"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class SRO(MQOpts):
    """ Construct an MQSRO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQSRO_STRUC_ID, '4s'],
                ['Version', CMQC.MQSRO_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQSRO_FAIL_IF_QUIESCING, MQLONG_TYPE],
                ['NumPubs', 0, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
