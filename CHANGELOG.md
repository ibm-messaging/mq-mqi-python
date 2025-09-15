
# Changelog
Newest updates are at the top of this file.

## 2025 Sep 10 - V2
Initial release of the reworked PyMQI library for IBM MQ as `ibmmq`.

Apart from the change in package name, the main changes from the PyMQI V1 library implemented in this V2 release
include:

### Basic requirements
* Python 3.9 or later
* Running on MQ 9.1 or later
* Connecting to MQ 6 or later

Depending on what you are doing, older MQ versions may also work. But these are
the oldest levels designed for.

### Removals
* Removed 32-bit compile options
* Removed support for Python 2
* Removed use of the client-only library (libmqic) when building
  * The libmqm library is available everywhere and can do both client and local bindings.
  * Use MQ_CONNECT_MODE=CLIENT or CNO options to force the mode, if it's not automatic
* Removed deprecated definitions that were duplicated across packages
  * eg MQCHT_CLNTCONN is only in CMQXC, not CMQC
* Removed unused code eg MQAI

### Additions
* Constant definitions (CMQ*.py) updated to current MQ level
  * And made platform-aware
  * Corrected some initial values in structures
* Added CNO, CSP, BNO classes
* Added asynchronous consume via MQCB/MQCTL operations
  * Added CTLO, CBC, CBD classes for async consume
  * Python methods: QueueManager.ctl(), QueueManager.cb(), Queue.cb()
* Added MQDLTMH, MQDLTMP verbs
  * Python methods: QueueManager.dltmh(), QueueManager.dltmp()
  * Various bug fixes in existing property handling
  * Wildcard property processing in MQINQMP
* Added CMQSTRC dicts for easy conversion of ints to MQI constant names
* Added MQSUBRQ, MQSTAT verbs with corresponding classes mapping to their MQI structures
  * Python methods: Subscription.subrq() and QueueManager.stat()
* Added DLH class + get_header() method
* Added IIH, CIH classes
* Added to_string() method for MQI structures/classes to convert byte arrays into real strings
* Added get_name() method for queues and qmgrs
* MQINQ takes lists of selectors in a single operation, and returns a selector-indexed dict of attribute values
  * Previous single-selector variant still available
  * Python methods: QueueManager.inquire(), Queue.inquire()
  * Added `inq` as alias to `inquire` method on queue and qmgr classes to more closely match MQI verb name
* MQSET takes a dict of {selector:value}
  * Python method: Queue.set()
  * Previous single-selector variant still available
* Connections permit handles to be shared across threads as default
* Added put() as alias of pub() on topics, to better match use of MQPUT

* PCFExecute enhancements:
  * Constructor takes a reply_queue_name as an alternative to the model_queue_name. As you might want to use a fixed
    objectname.
  * It now does GET-CONVERT by default (when would you ever not want this?)
  * Can pass in a pre-opened command queue to constructor so it doesn't re-open on each command
  * Works against a z/OS queue manager without special application coding
    * Including CMDSCOPE(*) responses from QSGs

* All structure MQCHAR[] input parameters can be provided either by a Unicode (Python 3) string or (for backwards
  compatibility) as a byte array
  * For example, both `QName="ABC"` or `QName=b"ABC"` are valid.
  * OUTPUT fields are still - compatibly - given as the byte array. Conversion to strings is necessary if you want to
    process them that way. The new to_string() method on classes will do that for you. There is also a to_string()
    function to do the same work for specific strings.

* Most existing type annotations converted from comments to inline

### Tests and Examples
* The `examples` contents have been cleaned up
  * They now use a consistent set of objects (mostly the DEV.* definitions from the developer config)
    * With `app` and `admin` users both defined with password="password"
  * Some essentially duplicated examples removed
  * Comments added to describe the purpose of each program
  * Some examples use variant approaches to connection and authentication
* Examples added to demonstrate newer features
  * Async consume callbacks
  * Dead-letter header decoding
  * MQINQ/SET operations
  * Publish/Subscribe
* The `tests` contents have been cleaned up
  * But not significantly enhanced for newer versions of MQ
  * Assume use of Python 3
  * Added script to start a container with the appropriate Developer configuration - `docker` and `podman` options

### Other comments
* There has been substantial internal restructuring to split the original large \_\_init\__.py into separate files. It is
  now essentially one file per MQI structure (class) and per object type.
* Many imports of the package including tests and examples now use "... as mq" to shorten the typing
* Various other internal changes to make modules more maintainable in future
  * Added MQObject as superclass of queues, topics etc for potential future simplifications
* The C module is considered an internal interface and has changed to match new requirements from the Python layer above
  it.
* Text strings from error classes (MQMIError, PYIFError) slightly modified
