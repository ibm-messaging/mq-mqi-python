"""
A common interface to the logging functions.

It's expected that the strings passed here are already formatted
for simplicity (ie use f"xxx{var}" in the caller)
"""

# Copyright (c) 2025, 2026 IBM Corporation and other Contributors. All Rights Reserved.

import os
import logging
from ibmmq import ibmmqc

logger = logging.getLogger('ibmmq')
trace_level = False

def trace(msg, *args):
    """The Python logger doesn't have a separate trace level
    so we fake it. Trace is more detailed than debug.
    """
    if logger and trace_level:
        logger.debug(msg, *args)

def debug(msg, *args):
    """Add some indent to the message if we are also
    using the TRACE pseudo-loglevel
    """
    indent = ""
    if trace_level:
        indent = "  "
    if logger:
        logger.debug(indent + msg, *args)

def error(msg, *args):
    """Record an error message"""
    logger.error(msg, *args)

def trace_entry(s, *args):
    """Record entry to a function"""
    trace("> " + s, *args)

def trace_exit(s: str, **kwargs):
    """Record exit of a function. The "ep" attribute lets us
    annotate when there are multiple potential exits from a function (usually
    because of error handling).
    """
    ep = kwargs.get('ep')
    if ep:
        trace("<" + s + " EP:" + str(ep))
    else:
        trace("< " + s)


# Create a logger for Python. Also configure the C layer
# if we've asked for trace/debug output.
enable_native_logging = False

# TRACE takes precedence over DEBUG
if os.environ.get('MQIPY_TRACE'):
    level = logging.DEBUG  # There's no separate "trace" level in the Python logging API
    enable_native_logging = True
    trace_level = True
elif os.environ.get('MQIPY_DEBUG'):
    level = logging.DEBUG
    enable_native_logging = True
else:
    level = logging.WARN  # We only use WARN/ERROR in normal use, so no point in enabling INFO

logging.basicConfig(level=level)

# If you've asked for a specfic filename, then override the default
# logging propagation and only allow that file to be used. If the
# file cannot be created/written, then there is an exception generated.
filename = os.environ.get('MQIPY_LOG_FILENAME')
if filename:
    for h in logger.handlers:
        logger.removeHandler(h)
    h = logging.FileHandler(filename)
    # consider adding: "%(threadName)s %(thread)d"
    h.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(name)-8s %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(h)
    logger.propagate = False
    if enable_native_logging:
        ibmmqc.MQLOGCF(level, filename)
else:
    if enable_native_logging:
        ibmmqc.MQLOGCF(level)
