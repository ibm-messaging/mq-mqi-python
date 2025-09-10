"""MQDLH: Dead Letter Header"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class DLH(MQOpts):
    """ Construct an MQDLH Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQDLH_STRUC_ID, '4s'],
                ['Version', CMQC.MQDLH_VERSION_1, MQLONG_TYPE],
                ['Reason', CMQC.MQRC_NONE, MQLONG_TYPE],
                ['DestQName', b'', '48s'],
                ['DestQMgrName', b'', '48s'],
                ['Encoding', 0, MQLONG_TYPE],
                ['CodedCharSetId', CMQC.MQCCSI_UNDEFINED, MQLONG_TYPE],
                ['Format', CMQC.MQFMT_NONE,'8s'],
                ['PutApplType', 0, MQLONG_TYPE],
                ['PutApplName', b'', '28s'],
                ['PutDate', b'', '8s'],
                ['PutTime', b'', '8s']]

        super().__init__(tuple(opts), **kw)

    # Return the DLH as a formatted structure based on the message buffer. You
    # can then choose to also do a to_string() on the contents. This method
    # means you can pass the entire buffer, not just the DLH slice
    def get_header(self,buf):
        """Return the unpacked header from the full message buffer"""
        dlh = super().unpack(buf[:CMQC.MQDLH_LENGTH_1])
        return dlh
