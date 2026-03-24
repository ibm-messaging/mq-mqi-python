"""MQRFH2 Structure: Name/Value pairs"""

# Copyright (c) 2025, 2026 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

import xml.etree.ElementTree as ET
# from xml.dom.minidom import parseString
import re

from mqcommon import *
from mqopts import MQOpts
from mqerrors import *

from ibmmq import CMQC

try:
    from typing import Union, List
except ImportError:
    pass

# RFH2 Header parsing/creation Support - Hannes Wagener - 2010.
class RFH2(MQOpts):
    """ Construct a RFH2 Structure with default values as per MQI.
    The default values may be overridden by the optional keyword arguments 'kw'.
    """
    initial_opts = [['_StrucId', CMQC.MQRFH_STRUC_ID, '4s'],
                    ['Version', CMQC.MQRFH_VERSION_2, MQLONG_TYPE],
                    ['StrucLength', 0, MQLONG_TYPE],
                    ['Encoding', CMQC.MQENC_NATIVE, MQLONG_TYPE],
                    ['CodedCharSetId', CMQC.MQCCSI_Q_MGR, MQLONG_TYPE],
                    ['Format', CMQC.MQFMT_NONE, '8s'],
                    ['Flags', 0, MQLONG_TYPE],
                    ['NameValueCCSID', CMQC.MQCCSI_Q_MGR, MQLONG_TYPE]]  # type: List[List[Union[str, int, bytes]]]

    big_endian_encodings = [CMQC.MQENC_INTEGER_NORMAL,
                            CMQC.MQENC_DECIMAL_NORMAL,
                            CMQC.MQENC_FLOAT_IEEE_NORMAL,
                            CMQC.MQENC_FLOAT_S390,

                            # 17
                            CMQC.MQENC_INTEGER_NORMAL +
                            CMQC.MQENC_DECIMAL_NORMAL,

                            # 257
                            CMQC.MQENC_INTEGER_NORMAL +
                            CMQC.MQENC_FLOAT_IEEE_NORMAL,

                            # 272
                            CMQC.MQENC_DECIMAL_NORMAL +
                            CMQC.MQENC_FLOAT_IEEE_NORMAL,

                            # 273
                            CMQC.MQENC_INTEGER_NORMAL +
                            CMQC.MQENC_DECIMAL_NORMAL +
                            CMQC.MQENC_FLOAT_IEEE_NORMAL]

    def __init__(self, **kw):
        # Take a copy of private initial_opts
        self.opts = [list(x) for x in self.initial_opts]
        super().__init__(tuple(self.opts), **kw)

    @staticmethod
    def _folder_to_string(v, encoding=EncodingDefault.bytes_encoding):
        """This is another copy of the "to_string" method, but not overriding the superclass which applies it to
        structures. (Should look to merge them using types as discriminator.)
        And we can't use the version defined in __init__.py because of looped imports etc.

        Use the specified encoding to convert MQCHAR[] to a Python3 string, stripping trailing NULs/spaces.
        If there's an error, return the input unchanged.
        """
        if isinstance(v, bytes):
            try:
                null_index = v.find(0)
                if null_index != -1:
                    v = v[:null_index]
                return v.decode(encoding).strip()
            except UnicodeError:
                pass
        return v

    @staticmethod
    def get_folder_name(folder_data):
        """Try to get the folder name by parsing the folder_data string.
        But if it fails - which is quite likely if the XML is not "complete" - then
        drop through to using a regexp and direct string manipulation. The exception
        also happened with the previous implementation's minidom-based approach. See
        the unittests which now includes folders as created by Java programs to expand
        the range of what an RFH2 might include.
        """
        try:
            folder_name = ET.fromstring(folder_data).tag

        except ET.ParseError as e:
            # Look for the largest blob of data up to some whitespace. Assuming that matches, then
            # we may have something longer than the actual field, so we then split it at the first ">"
            matched = re.match(b"^<(\\S+)", folder_data)
            if matched:
                folder_name = RFH2._folder_to_string(matched[1])
                folder_name = folder_name.split(">")[0]
            else:
                raise PYIFError(f'RFH2 - XML Folder not well formed. Data {folder_data} Exception: {str(e)}') from e

        return folder_name

    def add_folder(self, folder_data):
        """ Adds a new XML folder to the RFH2 header.
        Checks if the XML is well formed and updates self.StrucLength.
        """

        ensure_not_unicode(folder_data)  # Python 3 bytes check

        # Check that the folder is valid xml and get the root tag name.
        folder_name = RFH2.get_folder_name(folder_data)

        # Make sure folder length divides by 4 - else add spaces
        folder_length = len(folder_data)
        remainder = folder_length % 4
        if remainder != 0:
            num_spaces = 4 - remainder
            folder_data = folder_data + b' ' * num_spaces
            folder_length = len(folder_data)

        self.opts.append([folder_name + 'Length', (folder_length), MQLONG_TYPE])
        self.opts.append([folder_name, folder_data, '%is' % folder_length])

        # Save the current values
        saved_values = self.get()

        # Reinit MQOpts with new fields added
        super().__init__(tuple(self.opts))

        # Reset the values to the saved values
        self.set(**saved_values)

        # Calculate the correct StrucLength
        self['StrucLength'] = self.get_length()

    def pack(self, encoding=None):
        """ Override pack in order to set correct numeric encoding in the format.
        """
        if encoding is not None:
            if encoding in self.big_endian_encodings:
                self.opts[0][2] = '>' + self.initial_opts[0][2]
                saved_values = self.get()

                # Apply the new opts
                super().__init__(tuple(self.opts))

                # Set from saved values
                self.set(**saved_values)

        return super().pack()

    def unpack(self, buff, encoding=None):
        """ Override unpack in order to extract and parse RFH2 folders.
        Encoding meant to come from the MQMD.
        """

        ensure_not_unicode(buff)  # Python 3 bytes check

        if buff[0:4] != CMQC.MQRFH_STRUC_ID:
            raise PYIFError('RFH2 - _StrucId not MQRFH_STRUC_ID. Value: %s' % buff[0:4])

        if len(buff) < 36:
            raise PYIFError('RFH2 - Buffer too short. Should be 36+ bytes instead of %s' % len(buff))
        # Take a copy of initial_opts and the lists inside
        self.opts = [list(x) for x in self.initial_opts]

        big_endian = False
        if encoding is not None:
            if encoding in self.big_endian_encodings:
                big_endian = True
        else:
            # If small endian first byte of version should be > 'x\00'
            if buff[4:5] == b'\x00':
                big_endian = True

        # Indicate bigendian in format
        if big_endian:
            self.opts[0][2] = '>' + self.opts[0][2]

        # Apply and parse the default header
        super().__init__(tuple(self.opts))
        super().unpack(buff[0:36])

        if self['StrucLength'] < 0:
            raise PYIFError('RFH2 - "StrucLength" is negative. Check numeric encoding.')

        if len(buff) > 36:
            if self['StrucLength'] > len(buff):
                raise PYIFError('RFH2 - Buffer too short. Expected: %s Buffer Length: %s'
                                % (self['StrucLength'], len(buff)))

        # Extract only the string containing the xml folders and loop
        s = buff[36:self['StrucLength']]

        while s:
            # First 4 bytes is the folder length. supposed to divide by 4.
            len_bytes = s[0:4]
            if big_endian:
                folder_length = struct.unpack('>l', len_bytes)[0]
            else:
                folder_length = struct.unpack('<l', len_bytes)[0]

            # Move on past four byte length
            s = s[4:]

            # Extract the folder string
            folder_data = s[:folder_length]
            null_index = folder_data.find(0)
            if null_index != -1:
                folder_data = folder_data[:null_index]

            # Check that the folder is valid xml and get the root tag name.
            folder_name = RFH2.get_folder_name(folder_data)

            # Append folder length and folder string to self.opts types
            self.opts.append([folder_name + 'Length', (folder_length), MQLONG_TYPE])
            self.opts.append([folder_name, folder_data, '%is' % folder_length])
            # Move on past the folder
            s = s[folder_length:]

        # Save the current values
        saved_values = self.get()

        # Apply the new opts
        super().__init__(tuple(self.opts))

        # Set from saved values
        self.set(**saved_values)

    def get_folders(self):
        """Return the list of folders in this RFH2"""
        folders = []
        d = self.get()
        for f in d:
            # All the folders have a pair of attributes: xxx and xxxLength
            if f.endswith("Length") and f != "StrucLength":
                f = f[0:len(f) - 6]
                folders.append(f)
        return folders
