"""MQSTS: Status returned  by MQSTAT"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, ibmmqc

class STS(MQOpts):
    """ Construct an MQSTS Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQSTS_STRUC_ID, '4s'],
                ['Version', CMQC.MQSTS_VERSION_2, MQLONG_TYPE],
                ['CompCode',CMQC.MQCC_OK, MQLONG_TYPE],
                ['Reason',CMQC.MQRC_NONE, MQLONG_TYPE],
                ['PutSuccessCount',0,MQLONG_TYPE],
                ['PutWarningCount',0,MQLONG_TYPE],
                ['PutFailureCount',0,MQLONG_TYPE],
                ['ObjectType',CMQC.MQOT_Q,MQLONG_TYPE],
                ['ObjectName',b'', '48s'],
                ['ObjectQMgrName',b'','48s'],
                ['ResolvedObjectName',b'','48s'],
                ['ResolvedQMgrName', b'', '48s']]

        sts_current_version = ibmmqc.__strucversions__.get("sts",1)
        if sts_current_version >= 2:
            opts += [
                # ObjectString
                ['ObjectStringVSPtr', 0, 'P'],
                ['ObjectStringVSOffset', (0), MQLONG_TYPE],
                ['ObjectStringVSBufSize', (0), MQLONG_TYPE],
                ['ObjectStringVSLength', (0), MQLONG_TYPE],
                ['ObjectStringVSCCSID', (0), MQLONG_TYPE],

                 # SubName
                ['SubNameVSPtr', 0, 'P'],
                ['SubNameVSOffset', (0), MQLONG_TYPE],
                ['SubNameVSBufSize', (0), MQLONG_TYPE],
                ['SubNameVSLength', (0), MQLONG_TYPE],
                ['SubNameVSCCSID', (0), MQLONG_TYPE],

                ['OpenOptions', 0, MQLONG_TYPE],
                ['SubOptions',0, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
