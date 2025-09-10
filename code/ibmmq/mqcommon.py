"""Some basic functions mostly needed for data conversions"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

import struct

class default:
    """Global encoding options"""
    ccsid          = 1208
    bytes_encoding = 'utf8'

    # How are unicode strings converted to bytes for MQI fields? By default we pick an ASCII encoding, as
    # that is good for the majority of codepages where an MQ app is running.
    # A z/OS system might need to override this to ebcdic: "cp500" perhaps.
    mqi_encoding='ascii'

def padded_count(count: int, boundary: int = 4) ->int:
    """Calculate padded bytes count
    """
    return count + ((boundary - count & (boundary - 1)) & (boundary - 1))

def is_unicode(s) -> bool:
    """ Returns True if input arg is a Python 3 string (aka Python 2 unicode). False otherwise.
    """
    if isinstance(s, str) and not isinstance(s, bytes):
        return True
    return False

def ensure_not_unicode(value) -> None:
    """While we will mostly convert Unicode strings to bytes for MQI fields, there are a few remaining
    places where we don't want to do that - primarily in message body contents. Make sure the message
    data is what the application expects, by forcing them to use bytes.
    """
    if is_unicode(value):
        msg = 'Python 3 style string (unicode) found but not allowed here: `{0}`. Convert to bytes.'
        raise TypeError(msg.format(value))

def ensure_strings_are_bytes(s, encoding=default.mqi_encoding) -> bytes:
    """MQI CHAR fields need to be handled as byte arrays, even if provided
    via Python 3 unicode strings
    """
    if is_unicode(s):
        return s.encode(encoding)
    return s

# For compatibility
ensure_bytes = ensure_strings_are_bytes

#
# 64bit suppport courtesy of Brent S. Elmer, Ph.D. (mailto:webe3vt@aim.com)
#
# On 64 bit machines when MQ is compiled 64bit, MQLONG is an int defined
# in /opt/mqm/inc/cmqc.h or wherever your MQ installs to.
#
# On 32 bit machines, MQLONG is a long and many other MQ data types are set to MQLONG
#
# So, set MQLONG_TYPE to 'i' for 64bit MQ and 'l' for 32bit MQ so that the
# conversion from the Python data types to C data types in the MQ structures
# will work correctly.
#
# However, note that V2 of this package no longer supports running on 32-bit systems anyway
# so we're going to throw an error.

# Are we running 64 bit?
if struct.calcsize('P') == 8:
    MQLONG_TYPE = 'i'  # 64 bit
else:
    MQLONG_TYPE = 'l'  # 32 bit
    raise SystemError("32-bit systems are no longer supported in this package")

INTEGER64_TYPE = 'q'

# A debug tool
def _dump(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))
