"""MQGMO: Get Message Options"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, ibmmqc

class GMO(MQOpts):
    """ Construct an MQGMO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQGMO_STRUC_ID, '4s'],
                ['Version', CMQC.MQGMO_VERSION_4, MQLONG_TYPE],
                ['Options', CMQC.MQGMO_NO_WAIT, MQLONG_TYPE],
                ['WaitInterval', 0, MQLONG_TYPE],
                ['Signal1', 0, MQLONG_TYPE],
                ['Signal2', 0, MQLONG_TYPE],
                ['ResolvedQName', b'', '48s'],
                ['MatchOptions', CMQC.MQMO_MATCH_MSG_ID+CMQC.MQMO_MATCH_CORREL_ID, MQLONG_TYPE],
                ['GroupStatus', CMQC.MQGS_NOT_IN_GROUP, 'b'],
                ['SegmentStatus', CMQC.MQSS_NOT_A_SEGMENT, 'b'],
                ['Segmentation', CMQC.MQSEG_INHIBITED, 'b'],
                ['_Reserved1', b' ', 'c'],
                ['MsgToken', b'', '16s'],
                ['ReturnedLength', CMQC.MQRL_UNDEFINED, MQLONG_TYPE], ]

        gmo_current_version = ibmmqc.__strucversions__.get("gmo",1)
        if gmo_current_version >= 4:
            opts += [
                ['_Reserved2', (0), MQLONG_TYPE],
                ['MsgHandle', (0), 'q']]

        super().__init__(tuple(opts), **kw)

# Backward compatibility
gmo = GMO
