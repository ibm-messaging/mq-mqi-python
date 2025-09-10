"""MQCBD: Callback Descriptor"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class CBD(MQOpts):
    """ Construct an MQCBD Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQCBD_STRUC_ID, '4s'],
                ['Version', CMQC.MQCBD_VERSION_1, MQLONG_TYPE],
                ['CallbackType', CMQC.MQCBT_MESSAGE_CONSUMER, MQLONG_TYPE],
                ['Options', CMQC.MQCBDO_NONE, MQLONG_TYPE],
                ['CallbackArea',0,'P'],
                ['CallbackFunction',0,'P'],
                ['CallbackName',b'', '128s'],
                ['MaxMsgLength', CMQC.MQCBD_FULL_MSG_LENGTH, MQLONG_TYPE]]

        # Some padding is needed to match the C structure, even though it's not
        # listed in cmqc.h
        opts += [['_Reserved1',0,MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)
