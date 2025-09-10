"""MQCMHO, MQDMHO, MQPD, MQIMPO, MQSMPO, MQDMPO: Structures for
controlling Message Handles and Properties
"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC

class CMHO(MQOpts):
    """ Construct an MQCMHO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQCMHO_STRUC_ID, '4s'],
                ['Version', CMQC.MQCMHO_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQCMHO_DEFAULT_VALIDATION, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class DMHO(MQOpts):
    """ Construct an MQDMHO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQDMHO_STRUC_ID, '4s'],
                ['Version', CMQC.MQDMHO_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQDMHO_NONE, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class PD(MQOpts):
    """ Construct an MQPD Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQPD_STRUC_ID, '4s'],
                ['Version', CMQC.MQPD_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQPD_NONE, MQLONG_TYPE],
                ['Support', CMQC.MQPD_SUPPORT_OPTIONAL, MQLONG_TYPE],
                ['Context', CMQC.MQPD_NO_CONTEXT, MQLONG_TYPE],
                ['CopyOptions', CMQC.MQCOPY_DEFAULT, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class SMPO(MQOpts):
    """ Construct an MQSMPO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQSMPO_STRUC_ID, '4s'],
                ['Version', CMQC.MQSMPO_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQSMPO_SET_FIRST, MQLONG_TYPE],
                ['ValueEncoding', CMQC.MQENC_NATIVE, MQLONG_TYPE],
                ['ValueCCSID', CMQC.MQCCSI_APPL, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class DMPO(MQOpts):
    """ Construct an MQDMPO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQDMPO_STRUC_ID, '4s'],
                ['Version', CMQC.MQDMPO_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQDMPO_DEL_FIRST, MQLONG_TYPE]]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class IMPO(MQOpts):
    """ Construct an MQIMPO Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw):
        opts = [['_StrucId', CMQC.MQIMPO_STRUC_ID, '4s'],
                ['Version', CMQC.MQIMPO_VERSION_1, MQLONG_TYPE],
                ['Options', CMQC.MQIMPO_INQ_FIRST, MQLONG_TYPE],
                ['RequestedEncoding', CMQC.MQENC_NATIVE, MQLONG_TYPE],
                ['RequestedCCSID', CMQC.MQCCSI_APPL, MQLONG_TYPE],
                ['ReturnedEncoding', CMQC.MQENC_NATIVE, MQLONG_TYPE],
                ['ReturnedCCSID', (0), MQLONG_TYPE],
                ['_Reserved1', (0), MQLONG_TYPE],

                # ReturnedName
                ['ReturnedNameVSPtr', 0, 'P'],
                ['ReturnedNameVSOffset', (0), MQLONG_TYPE],
                ['ReturnedNameVSBufSize', (0), MQLONG_TYPE],
                ['ReturnedNameVSLength', (0), MQLONG_TYPE],
                ['ReturnedNameVSCCSID', (0), MQLONG_TYPE],

                ['TypeString', b'', '8s']]

        super().__init__(tuple(opts), **kw)
