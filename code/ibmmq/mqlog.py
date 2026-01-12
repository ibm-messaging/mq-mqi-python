"""
A common interface to logging functions that can be used by the ibmmq package.
All log messages are shown as coming from the same module - we don't have a per-file
logger.

It's expected that the strings passed here are already formatted
for simplicity (ie use f"xxx{var}" in the caller). Though you probably could use the %-style
with additional parameters to the functions as an alternative.
"""

# Copyright (c) 2025, 2026 IBM Corporation and other Contributors. All Rights Reserved.

import os
import logging
from ibmmq import ibmmqc

# We do NOT use basicConfig as that could affect any application logging; instead,
# set the configuration specific to this module's logger.
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

def critical(msg, *args):
    """Record a critical message. Not used in this package, but defined
    here for completeness.
    """
    if logger:
        logger.critical(msg, *args)

def error(msg, *args):
    """Record an error message"""
    if logger:
        logger.error(msg, *args)

def warning(msg, *args):
    """Record a warning message"""
    if logger:
        logger.warning(msg, *args)

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
    # There's no separate "TRACE" level in the Python logging API so we separate
    # it from DEBUG with a local flag.
    level = logging.DEBUG
    enable_native_logging = True
    trace_level = True
elif os.environ.get('MQIPY_DEBUG'):
    level = logging.DEBUG
    enable_native_logging = True
else:
    level = logging.WARN  # We only use WARN/ERROR in normal use, so no point in enabling INFO

logger.setLevel(level)

# If you've asked for a specfic filename, then override the default
# logging propagation and only allow that file to be used. If the
# file cannot be created/written, then there is an exception generated.
filename = os.environ.get('MQIPY_LOG_FILENAME')
if filename:
    for h in logger.handlers:
        logger.removeHandler(h)
    h = logging.FileHandler(filename)  # Default constructor has mode=append
    # consider adding: "%(threadName)s %(thread)d"
    h.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(name)-8s %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(h)
    logger.propagate = False
    if enable_native_logging:
        ibmmqc.MQLOGCF(level, filename)
else:
    if enable_native_logging:
        ibmmqc.MQLOGCF(level)
