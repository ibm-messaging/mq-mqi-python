"""Utility functions for handling different ways of opening queues"""

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

from typing import Union
from ibmmq import ensure_strings_are_bytes, MD, OD, PMO, GMO

def common_q_args(*opts):
    """ Process args common to put/get/put1. Module Private.
    """
    ln = len(opts)
    if ln > 2:
        raise TypeError('Too many args')
    m_desc = None
    pg_opts = None
    if ln > 0:
        m_desc = opts[0]
    if ln == 2:
        pg_opts = opts[1]
    if m_desc is None:
        m_desc = MD()
    if not isinstance(m_desc,MD):
        raise TypeError("Message Descriptor must be an instance of MD")
    if pg_opts:
        if not isinstance(pg_opts, (PMO,GMO)):
            raise TypeError("Options must be an instance of PMO or GMO")

    return m_desc, pg_opts

# Backward compatibility
commonQArgs = common_q_args

# Some support functions for Queue ops.
def _make_q_desc(qdesc_or_string: Union[str, bytes, OD]) -> OD:
    """Maybe make MQOD from string."""
    if isinstance(qdesc_or_string, (str, bytes)):
        return OD(ObjectName=ensure_strings_are_bytes(qdesc_or_string))
    return ensure_strings_are_bytes(qdesc_or_string)
