"""MQCIH: CICS Information Header"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class CIH(MQOpts):
    """ Construct an MQCIH Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    The initialisation assumes a CIH Version 2 which has been valid for many years.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQCIH_STRUC_ID, '4s'],
                ['Version', CMQC.MQCIH_VERSION_2, MQLONG_TYPE],
                ['StrucLength',CMQC.MQCIH_LENGTH_2,MQLONG_TYPE],
                ['Encoding',0,MQLONG_TYPE],
                ['CodedCharSetId',0,MQLONG_TYPE],
                ['Format',CMQC.MQFMT_NONE,'8s'],
                ['Flags',CMQC.MQCIH_NONE, MQLONG_TYPE],
                ['ReturnCode',CMQC.MQCRC_OK, MQLONG_TYPE],
                ['CompCode',CMQC.MQCC_OK, MQLONG_TYPE],
                ['Reason',CMQC.MQRC_NONE,MQLONG_TYPE],
                ['UOWControl',CMQC.MQCUOWC_ONLY,MQLONG_TYPE],
                ['GetWaitInterval',CMQC.MQCGWI_DEFAULT,MQLONG_TYPE],
                ['LinkType',CMQC.MQCLT_PROGRAM,MQLONG_TYPE],
                ['OutputDataLength',CMQC.MQCODL_AS_INPUT,MQLONG_TYPE],
                ['FacilityKeepTime',0,MQLONG_TYPE],
                ['ADSDescriptor',CMQC.MQCADSD_NONE,MQLONG_TYPE],
                ['ConversationalTask',CMQC.MQCCT_NO,MQLONG_TYPE],
                ['TaskEndStatus',CMQC.MQCTES_NOSYNC,MQLONG_TYPE],
                ['Facility',CMQC.MQCFAC_NONE,'8s'],
                ['Function',CMQC.MQCFUNC_NONE,'4s'],
                ['AbendCode',' ','4s'],
                ['Authenticator',' ','8s'],
                ['_Reserved1',' ','8s'],
                ['ReplyToFormat',CMQC.MQFMT_NONE,'8s'],
                ['RemoteSysId',' ','4s'],
                ['RemoteTransId',' ','4s'],
                ['TransactionId',' ','4s'],
                ['FacilityLike',' ','4s'],
                ['AttentionId',' ','4s'],
                ['StartCode',CMQC.MQCSC_NONE,'4s'],
                ['CancelCode',' ','4s'],
                ['NextTransactionId',' ','4s'],
                ['_Reserved2',' ','8s'],
                ['_Reserved3',' ','8s'],
                ['CursorPosition',0,MQLONG_TYPE],
                ['ErrorOffset',0,MQLONG_TYPE],
                ['InputItem',0,MQLONG_TYPE],
                ['_Reserved4',0,MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
