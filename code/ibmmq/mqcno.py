"""MQCNO: Connection Options"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, ibmmqc

class CNO(MQOpts):
    """ Construct an MQCNO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.

    It assumes a minimum of MQNO_VERSION_5 (available from MQ 8.0) in the
    available fields. The connect() method will then set the version >5 if the
    application has not set it
    """
    def __init__(self, **kw):

        cno_current_version = ibmmqc.__strucversions__.get("cno",1)
        opts = [['_StrucId', CMQC.MQCNO_STRUC_ID, '4s'],
                ['Version', CMQC.MQCNO_VERSION_5, MQLONG_TYPE],
                ['Options', CMQC.MQCNO_NONE,MQLONG_TYPE],
                ['_ClientConnOffset',0,MQLONG_TYPE],
                ['_ClientConnPtr',0,'P'],
                ['ConnTag',b'','128s'],
                ['_SSLConfigPtr',0,'P'],
                ['_SSLConfigOffset',0,MQLONG_TYPE],
                ['ConnectionId',b'','24s'],
                ['_SecurityParmsOffset',0,MQLONG_TYPE],
                ['_SecurityParmsPtr',0,'P']]

        if cno_current_version >= CMQC.MQCNO_VERSION_6:
            opts += [['CCDTUrl',0,'P'],
                ['_CCDTUrlOffset',0,MQLONG_TYPE],
                ['_CCDTUrlLength',0,MQLONG_TYPE],
                ['_Reserved',0,INTEGER64_TYPE]]

        if cno_current_version >= CMQC.MQCNO_VERSION_7:
            opts += [['ApplName',CMQC.MQAN_NONE, '28s'],
                     ['_Reserved2',0,MQLONG_TYPE]]

        if cno_current_version >= CMQC.MQCNO_VERSION_8:
            opts += [['_BalanceParmsPtr',0,'P'],
                    ['_BalanceParmsOffset',0,MQLONG_TYPE],
                    ['_Reserved3', 0, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
