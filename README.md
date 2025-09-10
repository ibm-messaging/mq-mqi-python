# Python library for IBM MQ

The `ibmmq` package is an open-source Python extension for IBM MQ.

For many years, the PyMQI library has been used by companies around the world with their queue managers running on
Linux, Windows, UNIX and z/OS. It gives a full-featured implementation of the MQI programming interface, with additional
functions to assist with system monitoring and management.

This package has been substantially rewritten from its predecessor version, in an effort to modernise the implementation
and make it more maintainable. Various obsolete features have been removed, while adding capabilities both from the
latest levels of IBM MQ and to fill out missing options. There is a [design document](docs/DesignNotes.md) that gives
rationales for many of the changes.

In particular, support for Python 2 and 32-bit environments have been removed.

The package has been renamed to 'ibmmq' but otherwise maintains compatibility with APIs in the earlier 'pymqi'.

For simple migrations to the new version, see [here](docs/MIGRATION_V2.md). For more detailed information on
enhancements and removed features, see the [CHANGELOG](CHANGELOG.md) file.

## Supported versions

* Minimum local MQ version of 9.1 (the C client runtime and SDK components are required)
  * Will work as a client to versions back to at least 8.0 (and possibly earlier)
  * Does not require a local queue manager
* Python 3.9+

## Installation
The package is available from PyPI for easy installation.

### Prerequisites

* You first need to install an IBM MQ C client including the SDK component on the system where this package is about to
  be installed
* A C compiler
  * For Windows, you need a suitable C++ compiler. You need to install the compiler version that corresponds to your
    Python version. See [here](https://wiki.python.org/moin/WindowsCompilers) for more information.

### Using `pip`
* If you have not installed the MQ client in the default directory (`/opt/mqm` on Linux and MacOS), then set the
  `MQ_FILE_PATH` environment variable to reference that directory.
* Now you can use pip to install the Python package itself. To install globally, for all users on a machine, you will
  probably need to use `sudo`. More commonly, you can install in a local virtual environment:

```bash
    $ pip install ibmmq
```

### Installing directly from the GitHub repository
If you want to work with the library directly, perhaps to try modifications, then you can install an "editable" version
from the filesystem.

* Clone this repository
```
    $ git clone git@github.com:ibm-messaging/mq-mqi-python
```
* Create a python virtual environment
```
    $ python -m venv <directory>
```
* Activate the environment
```
    $ cd <venv directory>
    $ . ./bin/activate
```
* Install the library as a developer from the clone
```
    $ cd <repository clone>
    $ pip uninstall -y ibmmq # If it's already installed
    $ pip install -e .
```

*Note*: On MacOS I had problems using the system-supplied Python. There were messages such as not being able to find the
`pip` module. Instead I used a version installed from `homebrew`. You may also have to use `python3` as the command.

## MQI Capabilities
Almost all of the procedural MQI that is appropriate for applications is available with the V2 package. Missing and
partially-implemented functions have been filled out. For example, async consume (MQCB/MQCTL) and full message property
handling were added. New classes implement missing structures such as MQCNO and MQBNO. A fuller list is in the
[CHANGELOG](CHANGELOG.md).

### Not implemented
There are some features of the C MQI that are rarely, if-ever, used by applications and which have not been implemented:
* Distribution Lists (MQDH). Use publish/subscribe instead.
* Reference Messages (MQRMH)
* Authinfo strucures for client CRL checking (MQAIR). Using a CCDT can be an alternative.

Anything to do with exits, including data conversion exits, is also excluded. These need to be written in C.

## Demonstration code

As a simple demonstration of the power of the Python library, here are a couple of short programs.

To put a message on a queue:

```python
import ibmmq

queue_manager = ibmmq.connect('QM1', 'DEV.APP.SVRCONN', '192.168.1.121(1414)')

q = ibmmq.Queue(queue_manager, 'DEV.QUEUE.1')
q.put('Hello from Python!')
```

To read the message back from the queue:

```python
import ibmmq

queue_manager = ibmmq.connect('QM1', 'DEV.APP.SVRCONN', '192.168.1.121(1414)')

q = ibmmq.Queue(queue_manager, 'DEV.QUEUE.1')
msg = q.get()
print('Here is the message:', msg)
```

### Problems
You may also need to run the `setmqenv` command to ensure the MQ environment is correctly recognised before installing
and/or running applications. In particular, if you get an error about not being able to load the `ibmmqc` module, that
is very likely due to an incorrect LIBPATH/LD_LIBRARY_PATH setting.

## Provided Examples and Tests
Download the source distribution directly from PyPI or running `git clone` for the examples and unittest programs. These
are not included with the simple `pip install` process as that is fundamentally for runtime-only execution.

To use `pip` to download just the source distribution, you can use

```bash
pip download --no-binary=:all: ibmmq
```

There are many example programs in the `code/examples` directory. These show use of many of the package's methods. See
the [README](code/examples/README.md) file for a fuller list.

And unittest components are in the `code/tests` directory. With a `runAllTests.sh` script to exercise them. That script
is very likely to need changing for your environment (including how it starts a queue manager) but they may still
be helpful to see use of the functions.

## Contributions and Pull requests

Contributions to this package can be accepted under the terms of the Developer's Certificate of Origin, found in the
[DCO file](DCO1.1.txt) of this repository. When submitting a pull request, you must include a statement stating you
accept the terms in the DCO.

## Health Warning

This package is provided as-is with no guarantees of support or updates. You cannot use IBM formal support channels
(Cases/PMRs) for assistance with material in this repository. There are also no guarantees of compatibility with any
future versions of the package; the API is subject to change based on any feedback. Versioned releases are made to
assist with using stable APIs.

## Issues

Before opening a new issue please consider the following:

-   Please try to reproduce the issue using the latest version.
-   Please check the [existing issues](https://github.com/ibm-messaging/mq-mqi-python/issues)
    to see if the problem has already been reported. Note that the default search
    includes only open issues, but it may already have been closed.
-   When opening a new issue [here in github](https://github.com/ibm-messaging/mq-mqi-python/issues) please complete the template fully.

There might be references to historic issues/pull requests in the source code (and in the `git log`). Issues from the
original repository were not available to be migrated across to the new location.

## Acknowledgments
This package builds on the work done in PyMQI V1. Contributors to that include:
* Dariusz Suchojad (primary contributor/maintainer) 
* Vyacheslav Savchenko
* L. Smithson 
* hjoukl

