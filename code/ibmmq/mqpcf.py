"""MQPCF structures: CFH, CFIN, CFIN64 etc"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from mqcommon import *
from mqopts import MQOpts
from ibmmq import CMQC, CMQCFC

try:
    from typing import Any, Dict, Union
except ImportError:
    pass

class CFH(MQOpts):
    """ Construct an MQCFH Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw: Dict[str,Any]):
        opts = [['Type', CMQCFC.MQCFT_COMMAND, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFH_STRUC_LENGTH, MQLONG_TYPE],
                ['Version', CMQCFC.MQCFH_VERSION_3, MQLONG_TYPE],
                ['Command', CMQCFC.MQCMD_NONE, MQLONG_TYPE],
                ['MsgSeqNumber', 1, MQLONG_TYPE],
                ['Control', CMQCFC.MQCFC_LAST, MQLONG_TYPE],
                ['CompCode', CMQC.MQCC_OK, MQLONG_TYPE],
                ['Reason', CMQC.MQRC_NONE, MQLONG_TYPE],
                ['ParameterCount', 0, MQLONG_TYPE]
               ]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFBF(MQOpts):
    """ Construct an MQCFBF (PCF Byte String Filter) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """

    def __init__(self, **kw: Dict[str, Any]):
        filter_value = kw.pop('FilterValue', '')
        filter_value_length = kw.pop('FilterValueLength', len(filter_value)) # type: int
        padded_filter_value_length = padded_count(filter_value_length)

        opts = [['Type', CMQCFC.MQCFT_BYTE_STRING_FILTER, MQLONG_TYPE],
                ['StrucLength',
                 CMQCFC.MQCFBF_STRUC_LENGTH_FIXED + padded_filter_value_length, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['Operator', 0, MQLONG_TYPE],
                ['FilterValueLength', filter_value_length, MQLONG_TYPE],
                ['FilterValue', filter_value, '{}s'.format(padded_filter_value_length)]
               ]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFBS(MQOpts):
    """ Construct an MQCFBS (PCF Byte String) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """

    def __init__(self, **kw: Dict[str,Any]):
        string = kw.pop('String', '')
        string_length = kw.pop('StringLength', len(string)) # type: int
        padded_string_length = padded_count(string_length)

        opts = [['Type', CMQCFC.MQCFT_BYTE_STRING, MQLONG_TYPE],
                ['StrucLength',
                 CMQCFC.MQCFBS_STRUC_LENGTH_FIXED + padded_string_length, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['StringLength', string_length, MQLONG_TYPE],
                ['String', string, '{}s'.format(padded_string_length)]
               ]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFGR(MQOpts):
    """ Construct an MQCFGR (PCF Group) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """

    def __init__(self, **kw: Dict[str, Any]):
        count = kw.pop('ParameterCount', 0)

        opts = [['Type', CMQCFC.MQCFT_GROUP, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFGR_STRUC_LENGTH, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['ParameterCount', count, MQLONG_TYPE],
               ]
        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFIF(MQOpts):
    """ Construct an MQCFIF (PCF Integer Filter) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """

    def __init__(self, **kw: Dict[str, Any]):
        opts = [['Type', CMQCFC.MQCFT_INTEGER_FILTER, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFIF_STRUC_LENGTH, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['Operator', 0, MQLONG_TYPE],
                ['FilterValue', 0, MQLONG_TYPE]
               ]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFIL(MQOpts):
    """ Construct an MQCFIL (PCF 32-bit integer List) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw: Dict[str, Any]):
        values = kw.pop('Values', []) # type: list[int]
        count = kw.pop('Count', len(values)) # type: int

        opts = [['Type', CMQCFC.MQCFT_INTEGER_LIST, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFIL_STRUC_LENGTH_FIXED + 4 * count, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['Count', count, MQLONG_TYPE],
                ['Values', values, MQLONG_TYPE, count],
               ]
        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFIL64(MQOpts):
    """ Construct an MQCFIL64 (PCF 64-bit integer List) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw: Dict[str, Any]):
        values = kw.pop('Values', []) # type: list[int]
        count = kw.pop('Count', len(values)) # type: int

        opts = [['Type', CMQCFC.MQCFT_INTEGER64_LIST, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFIL64_STRUC_LENGTH_FIXED + 8 * count, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['Count', count, MQLONG_TYPE],
                ['Values', values, INTEGER64_TYPE, count],
               ]
        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFIN(MQOpts):
    """ Construct an MQCFIN (PCF 32-bit integer) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw: Dict[str, Any]):
        opts = [['Type', CMQCFC.MQCFT_INTEGER, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFIN_STRUC_LENGTH, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['Value', 0, MQLONG_TYPE],
               ]
        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFIN64(MQOpts):
    """ Construct an MQCFIN64 (PCF 64-bit integer) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    def __init__(self, **kw: Dict[str, Any]):
        opts = [['Type', CMQCFC.MQCFT_INTEGER64, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFIN64_STRUC_LENGTH, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['Value', 0, INTEGER64_TYPE],
               ]
        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFSF(MQOpts):
    """ Construct an MQCFSF (PCF String Filter) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """

    def __init__(self, **kw: Dict[str, Any]):
        filter_value = kw.pop('FilterValue', '')
        filter_value_length = kw.pop('FilterValueLength', len(filter_value)) # type: int
        padded_filter_value_length = padded_count(filter_value_length)

        opts = [['Type', CMQCFC.MQCFT_STRING_FILTER, MQLONG_TYPE],
                ['StrucLength',
                 CMQCFC.MQCFSF_STRUC_LENGTH_FIXED + padded_filter_value_length, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['Operator', 0, MQLONG_TYPE],
                ['CodedCharSetId', CMQC.MQCCSI_DEFAULT, MQLONG_TYPE],
                ['FilterValueLength', filter_value_length, MQLONG_TYPE],
                ['FilterValue', filter_value, '{}s'.format(padded_filter_value_length)]
               ]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFSL(MQOpts):
    """ Construct an MQCFSL (PCF String List) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """

    def __init__(self, **kw: Dict[str,Any]):
        strings = kw.pop('Strings', []) # type: list[Union[str,bytes]]
        string_length = kw.pop('StringLength', len(max(strings, key=len)) if strings else 0) # type: int

        strings_count = len(strings)
        count = kw.pop('Count', strings_count) # type: int

        max_string_length = padded_count(string_length) if count else 0
        padded_strings_length = (max_string_length) * strings_count

        opts = [['Type', CMQCFC.MQCFT_STRING_LIST, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFSL_STRUC_LENGTH_FIXED + padded_strings_length, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['CodedCharSetId', CMQC.MQCCSI_DEFAULT, MQLONG_TYPE],
                ['Count', count, MQLONG_TYPE],
                ['StringLength', max_string_length, MQLONG_TYPE],
                ['Strings', strings if strings else [b''], '{}s'.format(max_string_length), (count if count else 1)]
               ]

        super().__init__(tuple(opts), **kw)

# ################################################################################################################################

class CFST(MQOpts):
    """ Construct an MQCFST (PCF String) structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """

    def __init__(self, **kw: Dict[str, Any]):
        string = kw.pop('String', '')
        string_length = kw.pop('StringLength', len(string)) # type: int
        padded_string_length = padded_count(string_length)

        opts = [['Type', CMQCFC.MQCFT_STRING, MQLONG_TYPE],
                ['StrucLength', CMQCFC.MQCFST_STRUC_LENGTH_FIXED + padded_string_length, MQLONG_TYPE],
                ['Parameter', 0, MQLONG_TYPE],
                ['CodedCharSetId', CMQC.MQCCSI_DEFAULT, MQLONG_TYPE],
                ['StringLength', string_length, MQLONG_TYPE],
                ['String', string, '{}s'.format(padded_string_length)]
               ]

        super().__init__(tuple(opts), **kw)
