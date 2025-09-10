"""MQIIH: IMS Information Header"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class IIH(MQOpts):
    """ Construct an MQIIH Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.

    A message using this structure is expected to then follow it with the IMS transaction
    data: LLZZ<trancode><data>[LLZZ<data>][LLZZ<data>]. This class does not give any
    assistance in building the data elements.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQIIH_STRUC_ID, '4s'],
                ['Version', CMQC.MQIIH_VERSION_1, MQLONG_TYPE],
                ['StrucLength', CMQC.MQIIH_LENGTH_1, MQLONG_TYPE],
                ['Encoding', 0, MQLONG_TYPE],
                ['CodedCharSetId', 0, MQLONG_TYPE],
                ['Format', CMQC.MQFMT_NONE,'8s'],
                ['Flags', CMQC.MQIIH_NONE,MQLONG_TYPE],
                ['LTermOverride',' ','8s'],
                ['MFSMapName',' ','8s'],
                ['ReplyToFormat',CMQC.MQFMT_NONE,'8s'],
                ['Authenticator',CMQC.MQIAUT_NONE,'8s'],
                ['TranInstanceId',CMQC.MQITII_NONE,'16s'],
                ['TranState',CMQC.MQITS_NOT_IN_CONVERSATION,'b'],
                ['CommitMode',CMQC.MQICM_COMMIT_THEN_SEND,'b'],
                ['SecurityScope',CMQC.MQISS_CHECK,'b'],
                ['_Reserved',0,'b']]

        super().__init__(tuple(opts), **kw)
