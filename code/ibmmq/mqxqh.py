"""MQXQH: Transmission header"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, MD

class XQH(MQOpts):
    """ Construct an MQXQH Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    Note that this is different from the C MQI definition of the XQH, as that incorporates
    an embedded MQMDv1 structure. Instead, we have the get_embedded_md() method to extract
    that separately. This is primarily used to parse an already-available XQH, not to build a new
    message from scratch.

    Note that if an app really wants to construct an XQH to PUT a message directly to an XMITQ,
    then you'd have to do quite a bit more work which we don't really assist with in this class.
    But normally, the XQH will come automatically when you write to a remote queue.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQXQH_STRUC_ID, '4s'],
                ['Version', CMQC.MQXQH_VERSION_1, MQLONG_TYPE],
                ['RemoteQName', b'', '48s'],
                ['RemoteQMgrName', b'', '48s'], ]

        super().__init__(tuple(opts), **kw)

    # Return the XQH as a formatted structure based on the message buffer.
    def get_header(self, buf):
        """Return the unpacked header from the full message buffer"""
        xqh = super().unpack(buf[:CMQC.MQXQH_CURRENT_LENGTH - CMQC.MQMD_LENGTH_1])
        return xqh

    # Return the MQMD that is part of the real (full) MQXQH structure. It is always
    # an MQMDv1, but this package usually deals with MQMDv2. So we extract the block and add
    # a zero-filled pad array to ensure it's the right length. Which means that the MDv2 fields
    # (eg GroupId) may not be accurate if the original message was using those MDv2 fields.
    # If the Format in this MD indicates there is a subsequent MQMDE, which corresponds to
    # the MDv2 fields, then you can extract that and unpack it directly before then
    # continuing on to the rest of the message body.
    def get_embedded_md(self, buf):
        """Return the unpacked MQMDv1 header from the full message buffer"""
        offset = CMQC.MQXQH_CURRENT_LENGTH - CMQC.MQMD_LENGTH_1         # Where does it start in the buffer
        pad = CMQC.MQMD_LENGTH_2 - CMQC.MQMD_LENGTH_1                   # How long is the padding
        md_buf = buf[offset:CMQC.MQXQH_CURRENT_LENGTH] + bytearray(pad)
        md = MD().unpack(md_buf)
        return md
