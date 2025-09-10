"""MQOpts: Base class for all MQI structures"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

import ctypes
import struct

from mqcommon import *
from mqerrors import *
from ibmmq import CMQC

try:
    from typing import Any, Optional, Union, Dict
except ImportError:
    pass


# These are fields from the MQI structures that are known to always be binary
# and which should not be converted back to strings. There are not many, so it's
# reasonable to list them here. But any new MQI fields will all need to be thought
# about to see if they need to be added to the list.
_binary_fields = ["AccountingToken",
                  "AlternateSecurityId",
                  "ConnectionId",
                  "ConnTag",
                  "CorrelId",
                  "Facility", # CIH
                  "GroupId",
                  "MCASecurityId",
                  "MsgId",
                  "MsgToken",
                  "PubAccountingToken",
                  "RemoteSecurityId",
                  "SubCorrelId",
                  "TranInstanceId" # IIH
                ]

# ################################################################################################################################
# MQI Python<->C Structure mapping. MQI uses lots of parameter passing
# structures in its API. These classes are used to set/get the
# parameters in the style of Python dictionaries & keywords. Pack &
# unpack calls are used to convert between python class attributes and
# 'C' structures, suitable for passing in/out of C functions.
#
# The MQOpts class defines common operations for structure definition,
# default values setting, member set/get and translation to & from 'C'
# structures. Specializations construct MQOpts with a list specifying
# structure member names, their default values, and pack/unpack
# formats. MQOpts uses this list to setup class attributes
# corresponding to the structure names, set up attribute defaults, and
# builds a format string usable by the struct package to translate to
# 'C' structures.

class MQOpts:
    """ Base class for packing/unpacking MQI Option structures. It is
    constructed with a list defining the member/attribute name,
    default value (from the CMQC module) and the member pack format
    (see the struct module for the formats). The list format is:

      [['Member0', CMQC.DEFAULT_VAL0, 'fmt1']
       ['Member1', CMQC.DEFAULT_VAL1, 'fmt2']
         ...
      ]

    MQOpts defines common methods to allow structure members to be
    set/get as attributes (foo.Member0 = 42), set/get as dictionary
    items (foo['Member0'] = 42) or set as keywords (foo.set(Member0 =
    42, Member1 = 'flipperhat'). The ctor can be passed an optional
    keyword list to initialize the structure members to non-default
    values. The get method returns all attributes as a dictionary.

    The pack() method packs all members into a 'C' structure according
    to the format specifiers passed to the ctor. The packing order is
    as specified in the list passed to the ctor. Pack returns a string
    buffer, which can be passed directly to the MQI 'C' calls.

    For packing, strings are truncated or padded with null bytes as appropriate to
    make them fit the given field length. There is no warning of overlong strings
    such as trying to use a 64-char queue name. For unpacking, the resulting bytes object
    always has exactly the specified number of bytes.

    The unpack() method does the opposite of pack. It unpacks a
    buffer into an MQOpts instance.

    Applications are not expected to use MQOpts directly. Instead,
    MQOpts is sub-classed as particular MQI structures.
    """

    def __init__(self, memlist, **kw):
        # type: (Union[list,tuple], Any) -> None
        """ Initialise the option structure. 'list' is a list of structure
        member names, default values and pack/unpack formats. 'kw' is an
        optional keyword dictionary that may be used to override default
        values set by MQOpts sub-classes.
        """

        self.__list = memlist[:]
        self.__format = ''

        # Dict to store c_char arrays to prevent memory addresses
        # from getting overwritten
        self.__vs_ctype_store = {} # type: Dict[str, Any]

        # Create the structure members as instance attributes and build
        # the struct.pack/unpack format string. The attribute name is
        # identical to the 'C' structure member name, except for some *Ptr fields.
        for i in memlist:
            setattr(self, i[0], i[1])
            try:
                i[3]
            except LookupError:
                i.append(1)
            self.__format = self.__format + i[2] * i[3]
        self.set(**kw)

    def pack(self) -> bytes:
        """ Pack the attributes into a 'C' structure to be passed to MQI
        calls. The pack order is as defined to the MQOpts
        ctor. Returns the structure as a bytes buffer.
        """

        # Build tuple for struct.pack() argument. Start with format string.
        args = [self.__format] # type: list[Any]

        # Now add the current attribute values to the tuple
        # In most cases, strings can be automatically converted from Unicode to the byte
        # array needed in an MQCHAR buffer. There are a few fields, however, where we really
        # do want to enforce that it's bytes for the MQBYTE[] buffers. None of these fields
        # are in the list elements.
        for i in self.__list:
            v = getattr(self, i[0])
            # Flatten attribs that are arrays
            if isinstance(v, list):
                for x in v:
                    args.append(ensure_strings_are_bytes(x))
            else:
                # print(f"{i[0]} is of value {v}: type {type(v)}")
                if i[0] in _binary_fields:
                    if not isinstance(v,bytes):
                        err = f'{i[0]} must be a byte array'
                        raise TypeError(err)
                args.append(ensure_strings_are_bytes(v))

        # print(f"Args to be packed are {args}")
        return struct.pack(*args)

    def unpack(self, buff: bytes):
        """ Unpack a 'C' structure 'buff' into self. Also returns self.
        """
        ensure_not_unicode(buff)

        # Increase buff length to the current MQOpts structure size
        diff_length = self.get_length() - len(buff)
        if diff_length > 0:
            buff += b'\x00' * diff_length

        # Unpack returns a tuple of the unpacked data, in the same
        # order (I hope!) as in the constructor's list arg.
        r = struct.unpack(self.__format, buff)
        x = 0
        for i in self.__list:

            if isinstance(i[1], list):
                ll = []
                for _j in range(i[3]):
                    ensure_not_unicode(r[x])
                    ll.append(r[x])
                    x = x + 1
                setattr(self, i[0], ll)
            else:
                ensure_not_unicode(r[x])  # Python 3 bytes check
                setattr(self, i[0], r[x])
                x = x + 1
        return self

    def to_string(self, encoding=default.bytes_encoding):
        """Given an MQI class (eg MQDLH), try to convert any string-like byte arrays into Python 3 strings.
        Fields that are known to be truly binary (like MsgId) are excluded from the conversion, but there
        may still be times that the output is not what you expected. This does modify the input structure
        so you might want to use a copy if you expect to continue to want to work with the original binary elements.
        """
        for i in self.__list:
            k=i[0]         # The attribute name
            v = self[i[0]] # The attribute value
            # There are no regular MQI structure fields that contain lists of strings/byte arrays:
            # the PCF MQCFSL is handled separately.
            if isinstance(v, bytes):
                if not k in _binary_fields:
                    try:
                        setattr(self,k, v.decode(encoding).strip())
                    except UnicodeError:
                        pass
                else:
                    pass
                    # print("Not decoding bytes for:",k)
            else:
                pass
                # print("Not decoding ", k)
        return self

    def set(self, **kw: Dict[str, Any]):
        """ Set a structure member using the keyword dictionary 'kw'.
        An AttributeError exception is raised for invalid member names.
        """

        for k,v in kw.items():
            # Only set if the attribute already exists. getattr raises
            # an exception if it doesn't.
            getattr(self, str(k))
            setattr(self, str(k), ensure_strings_are_bytes(v))

    def __setitem__(self, key:str, value: Any) -> None:
        """ Set the structure member attribute 'key' to 'value', as in obj['Attr'] = 42.
        """
        # Only set if the attribute already exists. getattr raises an
        # exception if it doesn't.
        getattr(self, key)
        setattr(self, key, ensure_strings_are_bytes(value))

    def get(self):
        # type: () -> dict
        """ Return a dictionary of the current structure member values. The dictionary is keyed by a 'C' member name.
        """
        d = {}
        for i in self.__list:
            d[i[0]] = getattr(self, i[0])
        return d

    def __getitem__(self, key: str) -> Any:
        """Return the member value associated with key, as in print obj['Attr'].
        """
        return getattr(self, key)

    def __str__(self) -> str:
        rv = ''
        for i in self.__list:
            rv = rv + str(i[0]) + ': ' + str(getattr(self, i[0])) + '\n'
        # Chop the trailing newline
        return rv[:-1]

    def __repr__(self) -> str:
        """ Return the packed buffer as a printable string.
        """
        return str(self.pack())

    def get_length(self) -> int:
        """ Returns the length of the (would be) packed buffer.
        """
        return struct.calcsize(self.__format)

    def set_vs(self, vs_name: str, vs_value: Union[bytes, str, None] = None, vs_offset: int = 0, vs_buffer_size: int = 0, vs_ccsid: int = 0) -> None:
        """ This method aids in the setting of the MQCHARV (variable length
        string) types in MQ structures. The type contains a pointer to a
        variable length string. A common example of a MQCHARV type
        is the ObjectString in the MQOD structure.
        In this module the ObjectString is defined as 5 separate
        elements (as per MQCHARV):
        ObjectStringVSPtr - Pointer
        ObjectStringVSOffset - Long
        ObjectStringVSBufSize - Long
        ObjectStringVSLength - Long
        ObjectStringVSCCSID - Long
        """

        vs_value = ensure_strings_are_bytes(vs_value) # allow known args be a string in Py3

        # if the VSPtr name is passed - remove VSPtr to be left with name.
        if vs_name.endswith('VSPtr'):
            vs_name_vsptr = vs_name
        else:
            vs_name_vsptr = vs_name + 'VSPtr'

        vs_name_vsoffset = vs_name + 'VSOffset'
        vs_name_vsbuffsize = vs_name + 'VSBufSize'
        vs_name_vslength = vs_name + 'VSLength'
        vs_name_vsccsid = vs_name + 'VSCCSID'

        c_vs_value = None
        c_vs_value_p = 0 # type: Optional[int]

        if vs_value is not None:
            c_vs_value = ctypes.create_string_buffer(vs_value)
            c_vs_value_p = ctypes.cast(c_vs_value, ctypes.c_void_p).value

        self[vs_name_vsptr] = c_vs_value_p
        self[vs_name_vsoffset] = vs_offset
        self[vs_name_vsbuffsize] = vs_buffer_size
        self[vs_name_vslength] = len(vs_value)
        self[vs_name_vsccsid] = vs_ccsid

        # Store c_char array object so memory location does not get overwritten
        self.__vs_ctype_store[vs_name] = c_vs_value

    def get_vs(self, vs_name):
        # type: (str) -> Union[bytes, str, None]
        """ This method returns the string to which the VSPtr pointer points to.
        """
        # if the VSPtr name is passed - remove VSPtr to be left with name.
        if vs_name.endswith('VSPtr'):
            vs_name_vsptr = vs_name
        else:
            vs_name_vsptr = vs_name + 'VSPtr'

        c_vs_value = None
        c_vs_value_p = self[vs_name_vsptr]
        if c_vs_value_p != 0:
            c_vs_value = ctypes.cast(c_vs_value_p, ctypes.c_char_p).value

        return c_vs_value

    # The C MQI will often define 3 fields to refer to a string:
    #   xxPtr, xxLength, xxOffset
    # To make it easier to use these in other languages, we expose these
    # via a single "xx" field and then fill in the other 2 pieces automatically.
    # The class has "xx", "_xxLength" and "_xxOffset" fields to guide which fields
    # are for internal use. But they are needed to maintain the same structure layout.
    # Offset is always 0. Length is set to the length of the string/byte array excluding
    # trailing NUL.

    def _set_ptr_field(self,field: str,value: Any):
        field_name_ptr = field

        # SSLPeerNamePtr has only ptr/len and we shouldn't change the name to match the
        # style of later similar attributes for compatibility reasons
        if field.endswith('Ptr'):
            field_base = field.replace('Ptr','')
        else:
            field_base = field

        field_name_offset = '_' + field_base + 'Offset'
        field_name_length = '_' + field_base + 'Length'

        # This error could happen if the package has been built against
        # a lower level of MQ than the field requires. Look for the hidden
        # attribute ("_xxLength") first. There may be backward compatibility
        # requirements on allowing the unhidden ("xxLength") version. If neither
        # are available, then raise the error.
        if not hasattr(self,field_name_length):
            field_name_length = field_base + 'Length'
            if not hasattr(self,field_name_length):
                raise MQMIError(CMQC.MQCC_FAILED,CMQC.MQRC_WRONG_VERSION)

        if hasattr(self,field_name_offset):
            self[field_name_offset] = 0

        self[field_name_length] = 0

        value = ensure_strings_are_bytes(value)
        c_value = None
        c_value_p = 0 # type: Optional[int]
        if value is not None and value != 0:
            c_value = ctypes.create_string_buffer(value)
            c_value_p = ctypes.cast(c_value, ctypes.c_void_p).value
            self[field_name_length] = len(c_value) - 1 # Ignore the trailing NUL that Python adds

        self[field_name_ptr] = c_value_p

        # Store c_char array object so memory location does not get overwritten
        self.__vs_ctype_store[field] = c_value
