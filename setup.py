
"""Setup script usable for setuptools"""
#
# Original Author: Maas-Maarten Zeeman
# Rewritten to remove deprecated distutils: Mark Taylor
#

import os
import platform

from setuptools import setup, Extension

from shutil import which
from struct import calcsize

# This is the only place where package version number is set!
# The version should correspond to PEP440 and gets normalised if
# not in the right format. VRM can be followed with a|b|rc with a further numeric
# to indicate alpha/beta/release candidate versions.
version = '2.0.0b1'

# If the MQ SDK is in a non-default location, set MQ_FILE_PATH environment variable.
# If that env var is not set, then use a default root of the current directory (which
# might not be necessary, but shouldn't do any harm.
custom_path = os.environ.get('MQ_FILE_PATH', None)

# Always build in 64-bit mode. And use libmqm regardless of whether the package
# will be used in client or local bindings mode. Since V7 the one library can handle
# both modes.
if calcsize('P') != 8:
    # Seems the closest exception (now an alias of EnvironmentError)
    raise OSError("Cannot build in 32-bit mode. Only 64-bit systems supported.")

def get_windows_settings():
    """ Windows settings.
    """

    library_dirs=[r'c:\Program Files\IBM\MQ\tools\Lib64']
    include_dirs=[r'c:\Program Files\IBM\MQ\tools\c\include']
    if custom_path:
        library_dirs.append(r'{}\tools\Lib64'.format(custom_path))
        include_dirs.append(r'{}\tools\c\include'.format(custom_path))

    libraries = ['mqm']

    return library_dirs, include_dirs, libraries

def get_aix_settings():
    """ AIX settings.
    """

    library_dirs=['/usr/mqm/lib64']
    include_dirs=['/usr/mqm/inc']

    if custom_path:
        library_dirs.append('{}/lib64'.format(custom_path))
        include_dirs.append('{}/inc'.format(custom_path))

    libraries = ['mqm_r']

    return library_dirs, include_dirs, libraries

def get_generic_unix_settings():
    """ Generic UNIX, including Linux, settings.
    """

    library_dirs=['/opt/mqm/lib64']
    include_dirs=['/opt/mqm/inc']

    if custom_path:
        library_dirs.append('{}/lib64'.format(custom_path))
        include_dirs.append('{}/inc'.format(custom_path))

    # Get an embedded rpath into the library which can reduce need for LD_LIBRARY_PATH
    for d in library_dirs:
        ld_flags.append("-Wl,-rpath," + d)
    libraries = ['mqm_r']

    return library_dirs, include_dirs, libraries

def get_locations_by_command_path(command_path):
    """ Extracts directory locations by the path to one of MQ commands, such as dspmqver.
    """
    command_dir = os.path.dirname(command_path)
    mq_installation_path = os.path.abspath(os.path.join(command_dir, '..'))

    library_dirs = ['{}/lib64'.format(mq_installation_path)]
    include_dirs = ['{}/inc'.format(mq_installation_path)]

    libraries = ['mqm_r']

    return library_dirs, include_dirs, libraries

# Define the C part(s) here. So we can potentially modify it
# for different platforms. For example: c_source.append('windows-specific.c')
c_source = ['code/ibmmq/ibmmqc.c']

ld_flags = []

# Get any platform-specific settings
plat=platform.system()
# Windows
if plat == "Windows":
    library_dirs, include_dirs, libraries = get_windows_settings()

# AIX
elif plat == "AIX":
    library_dirs, include_dirs, libraries = get_aix_settings()

# At this point, to preserve backward-compatibility we try out generic
# UNIX settings first, i.e. libraries and include files in well-known locations.
# Otherwise we look up dspmqver in $PATH.
else:
    has_generic_lib = os.path.exists('/opt/mqm/lib64')
    has_mq_file_path = os.environ.get('MQ_FILE_PATH', False)

    if has_generic_lib or has_mq_file_path:
        library_dirs, include_dirs, libraries = get_generic_unix_settings()

    else:
        # As one more efffort, we try to find
        # the path that dspmqver is installed to and find the rest
        # of the information needed in relation to that base directory.
        dspmqver_path = which('dspmqver')

        # We have found the command so we will be able to extract the relevant directories now
        if dspmqver_path:
            library_dirs, include_dirs, libraries = get_locations_by_command_path(dspmqver_path)
        # Otherwise, just pick the standard Unix directories and hope for the best.
        else:
            library_dirs, include_dirs, libraries = get_generic_unix_settings()

# print('Using library_dirs:`%s`, include:`%s`, libraries:`%s`' % (library_dirs, include_dirs, libraries))

# Can we find the MQ C header files? If not, there's no point in continuing, and we can
# give a reasonable error message immediately instead of trying to decode C compiler errors.
found_headers = False
for d in include_dirs:
    p = os.path.join(d,"cmqc.h")
    if os.path.isfile(p):
        found_headers = True
if not found_headers:
    raise FileNotFoundError("Cannot find MQ C header files. Ensure you have already installed the MQ Client and SDK")

long_description = """
Python library for IBM MQ
-------------------------

The "ibmmq" package is an open-source Python extension for IBM MQ.

It gives a full-featured implementation of the MQI programming interface, with additional
helper functions to assist with system monitoring and management.

Sample code
-----------

To put a message on a queue:

.. code-block:: python

    import ibmmq

    queue_manager = ibmmq.connect('QM1', 'DEV.APP.SVRCONN', '192.168.1.121(1414)')

    q = ibmmq.Queue(queue_manager, 'DEV.QUEUE.1')
    q.put('Hello from Python!')

To read the message back from the queue:

.. code-block:: python

    import ibmmq

    queue_manager = ibmmq.connect('QM1', 'DEV.APP.SVRCONN', '192.168.1.121(1414)')

    q = ibmmq.Queue(queue_manager, 'DEV.QUEUE.1')
    msg = q.get()
    print('Here is the message:', msg)
"""

# Define how the C module gets built
mqi_extension = Extension('ibmmq.ibmmqc',c_source, define_macros=[('PYVERSION','"' + version + '"')],
        library_dirs = library_dirs,
        include_dirs = include_dirs,
        extra_link_args = ld_flags,
        libraries = libraries)

_ = setup(name = 'ibmmq',
    version = version,
    description = 'Python Extension for IBM MQ (formerly WebSphere MQ and MQSeries).',
    long_description = long_description,
    long_description_content_type= 'text/x-rst',
    author='IBM MQ Development',
    url='https://ibm.com/software/products/en/ibm-mq',
    download_url='https://github.com/ibm-messaging/mq-mqi-python',
    platforms='OS Independent',
    package_dir = {'': 'code'},
    packages = ['ibmmq'],
    python_requires = ">=3.9",
    license_files = ['LICENSE*'],
    license='Python-2.0',
    keywords=('pymqi IBMMQ MQ WebSphere WMQ MQSeries IBM middleware messaging queueing asynchronous SOA EAI ESB integration'),
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: C',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    ext_modules = [mqi_extension]
    )
