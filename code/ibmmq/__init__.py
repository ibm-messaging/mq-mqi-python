# Python MQI Class Wrappers. High level classes for the MQI
# Extension. These present an object interface to the MQI.
#
# Author: L. Smithson (lsmithson@open-networks.co.uk)
# Author: Dariusz Suchojad (dsuch at zato.io)
# Author: Mark Taylor (ibmmqmet on GitHub)
#

# Copyright (c) 2025 IBM Corporation and other Contributors. All Rights Reserved.
# Copyright (c) 2009-2024 Dariusz Suchojad. All Rights Reserved.

"""
ibmmq - Python Classes for IBM MQ

These classes wrap the lower level C MQI calls. They present an OO
interface originally inspired by the MQI C++ classes.

Classes are also provided for easy use of the MQI structure parameters
(MQMD, MQGMO etc.) from Python. These allow Python scripts to set/get
structure members by attribute, dictionary etc.

External classes corresponding to MQI structures include:

    * MD              - Main MQI structures
    * CNO, CSP
    * BNO, SCO, CD
    * OD,  SD
    * GMO, PMO
    * SRO, STS

    * CBD, CTLO, CBC - Related to callbacks

    * CMHO, DMHO       - Message Properties
    * IMPO, SMPO, DMPO
    * PD

    * RFH2             - Application structures
    * DLH
    * TM, TMC2
    * IIH, CIH         - IMS, CICS headers

    * CFH              - PCF elements
    * CFGR
    * CFIL, CFIL64
    * CFIN, CFIN64
    * CFSF, CFBF, CFIF
    * CFSL, CFST
    * CFBS

Classes for MQ objects include
    * QueueManager
    * Queue
    * Topic
    * Subscription
    * MessageHandle

    * PCFExecute - Programmable Command Format operations

    * MQMIError - MQI specific error
    * PYIFError - Python library error

The following MQI operations are supported:

    * MQCONN, MQDISC (QueueManager.connect()/QueueManager.disconnect())
    * MQCONNX (QueueManager.connectWithOptions())
    * MQOPEN/MQCLOSE (Queue.open(), Queue.close(), Topic.open(), Topic.close())
    * MQPUT/MQPUT1/MQGET (Queue.put(), QueueManager.put1(), Queue.get(), Topic.pub())
    * MQSTAT (QueueManager.stat())
    * MQCMIT/MQBACK (QueueManager.commit()/QueueManager.backout())
    * MQBEGIN (QueueManager.begin())
    * MQINQ (QueueManager.inquire(), Queue.inquire())
    * MQSET (Queue.set())
    * MQSUB/MQSUBRQ (Subscription.sub(), Subscription.subrq())
    * MQCRTMH/MQDLTMH (MessageHandle(), MessageHandle.dlt())
    * MQSETMP/MQINQMP/MQDLTMP (MessageHandle.properties.set(), MessageHandle.properties.inq(), MessageHandle.properties.dlt())

To use this package, connect to the Queue Manager (using QueueManager.connect()), then open a queue (using
Queue.open()). You may then put or get messages on the queue (using Queue.put(), Queue.get()), as required.

Where possible, this package assumes the MQI defaults for all parameters. It can also defer a queue open until the put/get call.

The library maps all MQI warning & error status to the MQMIError exception. Errors detected by the package itself raise
the PYIFError exception. Both these exceptions are subclasses of the Error class.

MQI constants are defined in the CMQC and CMQXC modules; PCF constants are defined in CMQCFC.

PCF commands and inquiries are executed by calling a MQCMD_* method on an instance of a PCFExecute object.

The package is thread safe. Objects have the same thread scope as their MQI counterparts.

"""

# This file has relatively little content but is the primary module applications will access directly.
# It loads the various classes and methods from other files in this directory.

# Get information about the loaded package
from importlib.metadata import version

# Python 3.8+ DLL loading for Windows only.
try:
    from os import add_dll_directory  # type: ignore
    from os import environ
    from os.path import join
    from os.path import exists

    mq_home_path = environ.get('MQ_FILE_PATH')

    if mq_home_path:
        for d in ['bin', 'bin64']:
            mq_dll_directory = join(mq_home_path, d)
            if exists(mq_dll_directory):
                add_dll_directory(mq_dll_directory)
except ImportError:
    # If it fails, we'll try to continue anyway
    pass

# Load the C library
try:
    from . import ibmmqc # type: ignore
except ImportError:
    import ibmmqc # type: ignore # Backward compatibility

# Import the MQI definitions. They are not used directly in this
# file, but reexported for apps to reference.
from ibmmq import CMQCFC
from ibmmq import CMQXC, CMQSTRC

from ibmmq import CMQC

# Import the classes that implement each MQI structure. Order can be
# critical here to ensure we don't get loops in the definitions

# Using "import *" lets them get reexported as if they were part of this main module
from mqopts import *

from mqmd import *
from mqgmo import *
from mqpmo import *

from mqcbd import *

from mqcno import *
from mqbno import *
from mqcsp import *
from mqcd import *
from mqod import *
from mqsd import *

from mqsco import *
from mqsro import *
from mqsts import *

from mqctlo import *
from mqcbc import *

from mqtm import *
from mqxqh import *

from mqpcf import *
from mqrfh2 import *
from mqdlh import *
from mqiih import *
from mqcih import *

# The message property structures
from mqprops import *

# Exception classes
from mqerrors import *

# MQI Verbs associated with their relevant classes
from mqobject import *
from mqqargs import * # A shared part
from mqqmgr import *
from mqqueue import *
from mqsub import *
from mqtopic import *
from mqmsghdl import *

# And the PCF parse/execute module
from mqadmin import *

# The versions of this package (as found in the C and Python layers)
__c_version__ = ibmmqc.__version__
__py_version__ = version('ibmmq')
__version__ = __py_version__

# Ensure consistency. Messing with LD_LIBRARY_PATH for example might cause us to load the wrong
# extension version.
if __py_version__ != __c_version__:
    raise EnvironmentError(f'Mismatch between C \'{__c_version__}\' and Python \'{__py_version__}\' package versions')

# The CMDLEVEL the C code was compiled against
__cmdlevel__ = ibmmqc.__cmdlevel__

# Not really useful now, but left in for any compatibility
__mqbuild__ = ibmmqc.__mqbuild__

def get_versions():
    """Return an object containing versions for this library and the underlying MQ"""
    return {"module": __version__, "MQ": __cmdlevel__}

def to_string(v, encoding=default.bytes_encoding):
    """Use the specified encoding to convert MQCHAR[] to a Python3 string, stripping trailing NULs/spaces.
    If there's an error, return the input unchanged.
    """
    if isinstance(v,bytes):
        try:
            return v.decode(encoding).strip()
        except UnicodeError:
            pass
    return v
