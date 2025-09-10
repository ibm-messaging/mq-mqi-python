"""MQRFH2 Structure: Name/Value pairs"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

import xml.etree.ElementTree as ET

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
                    ['NameValueCCSID', CMQC.MQCCSI_Q_MGR, MQLONG_TYPE]] # type: List[List[Union[str, int, bytes]]]

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

    def add_folder(self, folder_data):
        """ Adds a new XML folder to the RFH2 header.
        Checks if the XML is well formed and updates self.StrucLength.
        """

        ensure_not_unicode(folder_data)  # Python 3 bytes check

        # Check that the folder is valid xml and get the root tag name.
        try:
            folder_name = ET.fromstring(folder_data).tag
        except Exception as e:
            raise PYIFError('RFH2 - XML Folder not well formed. Exception: %s' % str(e)) from e

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

        ensure_not_unicode(buff) # Python 3 bytes check

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

            # Check that the folder is valid xml and get the root tag name.
            try:
                folder_name = ET.fromstring(folder_data).tag
            except Exception as e:
                raise PYIFError('RFH2 - XML Folder not well formed. Exception: %s' % str(e)) from e

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
