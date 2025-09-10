# Design Notes

A collection of thoughts on extending or modifying the Python code. This document describes the rationale behind some of
the decisions made for the re-implementation. These sections are not in any particular order; just how things came to
me. This is not intended to be a complete design, but a description of specific issues/solutions that I worked through.

## MQI Structure Contents
We want to be able to compile and run against older (to some level) versions of the MQI. Fields are added to a structure
based on the supported level of that structure. Control of that was originally done based on the MQCMDL_LEVEL_xxx
values, but I've moved to a style that does not require knowledge of which MQ version added a feature.

Instead, a map gets built at C compile time that - for each relevant structure - holds the "current" level of that
structure. So we can then extract the version and use it:

```
 csp_current_version = ibmmqc.__strucversions__.get("csp",1)
 if csp_current_version >= CMQC.MQCSP_VERSION_2:
            opts += [['_Reserved3', 0,INTEGER64_TYPE],
               ['InitialKey',0,'P'],
```

The version check can use a symbolic MQCSP_VERSION_2 because, regardless of the underlying C libraries, these are known
in the CMQC.py files we ship (always at the latest level). If new structures are defined in the MQI with corresponding
classes in Python (right now the MQBNO is the most recent), it's possible that the map will not contain the
CURRENT_VERSION value when built against older C libraries. So we force a version 1 as the returned value. The class may
not be USABLE, but at least the code will compile and you'll get some kind of MQ-level error.

If an application tries to set an attribute that is not known, it will probably get an AttributeError exception rather
than having it flow through to MQ and getting an MQI error. The error checking may depend on which style the application
is using for setting that attribute: `XYZ.abc=1`, `XYZ['abc']=1`, `XYZ.set(abc=1)` can behave differently, even though
the underlying effect is identical. There's apparently no good way for Python to "freeze" a class so that no new elements
can be added.

## Structure Versions
The MQI C policy is that (almost) all structures are initialised with VERSION_1, with the use of later versions being
controlled by the application. If an application uses a field from VERSION_3, that will not be recognised unless the app
also updates the Version value.

This permits applications to work with queue managers all the way back to V2 - if the newer field is not needed, then it
is ignored. This is not the same issue as building an application using older levels of MQ client: you would typically
get a compile error if you tried to use unavailable fields.

This is not, however, very usable as it is too easy for forget to bump the version when using new features. So there
might be some improvements that can be made in these wrappers because:
* Some structures are not sent to the remote machine.
* Really old queue managers need not be supported.

So we have a slightly different policy.

* Make the base content (initialised) content of structures what they were in MQ 9.1 (or when introduced)
* Set the VERSION in those initalised structures to the V8 level
* If we can easily recognise use of later fields - typically that's going to be a pointer-based value as we have to
  manipulate that anyway - then automatically increase the version
* Allow the user to downgrade the version if they need to work with old qmgrs
  * They may also need to upgrade the version, just like C programs
* Do NOT do "advanced" comparisons of every field in the structure to see if it's modified from default and hence could
  get auto-upgrade

## Class organisation
All of the MQI structures have corresponding Python classes that inherit from the `MQOpts` class. Among other things,
this manages how fields are packed/unpacked when converting to/from the C equivalent layouts.

The "MQ Object" classes - corresponding to things like queues or topics - originally had no superclass. This leads to
duplication and slightly different implementations. For this version of the package, I've created an`MQObject` class,
making the real MQ objects inherit from it.

For now, there is very limited function in that superclass. But over time I'd expect to migrate the Queue's `__q_handle`
and the Topics' `__topic_handle` to be a common `_object_handle`. And some of the other common operations (like MQCLOSE)
and object access utilities will also go into that. For example, functions to return the object's name or underlying
HOBJ value.

The other MQ objects that are not currently accessible but which could be MQOPEN'ed (for MQINQ) - Namelists and Process
definitions - could also get individual classes.

## String/Pointer fields
There are a number of fields in the MQI that are passed with a pointer. This is apart from the MQCHARV fields that
already had a public mechanism - for those, the application uses `set_vs` directly.

For example, in the MQCNO we have
```
PMQCHAR    CCDTUrlPtr;
MQLONG     CCDTUrlOffset;
MQLONG     CCDTUrlLength;
```

For the Python equivalent, these become a single public string (renamed) attribute with private attributes for the
length and offset. The "_" prefix is a hint that applications should not use these fields directly.
```
  ['CCDTUrl', 0, 'P'],
  ['_CCDTUrlOffset', 0, MQLONG_TYPE],  # At least one attribute (SSLPeerNamePtr) does not have a corresponding offset
  ['_CCDTUrlLength',0, MQLONG_TYPE],
```

The `_set_ptr_field` method does the necessary conversion before the structure is packed ready for its call to C:
```
  ccdt_url = cno.CCDTUrl
  cno._set_ptr_field('CCDTUrl',ccdt_url)
```
We use and stash an intermediate copy of the value so it can be restored after the MQI call. If the field comes from a
later version of the structure than is known, we will throw an MQI error with MQRC_WRONG_VERSION.

## Strings and Unicode and Bytes
Python3 strings are always unicode, while MQI char fields are essentially byte arrays. The original PyMQI enforced the
setting of (almost all) MQI fields to be done with bytes, and threw an exception if a Unicode string was passed in. So
you had do to something like `qName=b"SYSTEM.DEFAULT.MODEL.QUEUE"` to force the byte-ness.

Since we no longer support Python2 this becomes irritating. All input strings can now be given in either byte or unicode
format, with the conversion done automatically. Output strings, however will continue to be returned as bytes as we
don't know how the application is going to process them. Encoding from unicode to bytes will be done based on the
default `ascii` codepage, but that will be a global definition which could change in an EBCDIC environment.

A future version of the library might conceivably also have a global setting that hooks into the `unpack` method, and
does automatic conversion to Python3 unicode strings. It's likely too complex to have some fields being done one way,
and some the other. And we can't base it on the type of the input to that field, as it might not have been set. But any
global setting could be dynamically changed in between MQI verbs.

Note that we DO check some specific fields like MsgId to ensure that you have passed in a byte array. As these
correspond to MQBYTE[] buffers in the MQI. Setting them to a string will cause a TypeError.

A `to_string` method is available for unpacked structures which changes all string fields to the unicode string, and
trims trailing NUL/spaces. The MQBYTE fields are not modified from their byte format.

## Linked structures
This primarily (only?) affects the design of the MQCONNX API today. In C, there is a single parameter that contains
pointers to other structures. For example, the MQCNO has a field pointing at the MQCSP. For Python, the exposed API will
not explicitly have the link. The application passes separate MQCSP and MQCNO structures; they are also passed that way
to the C layer. The linkage is then fixed up in the C code.

```python
  connect_with_options(...csp=csp, cno=cno)
```
ends up with
```C
  cno.SecurityParmsPtr = csp;
```

The MQI does have linked pointers for the DistributionList support in MQOD and MQPMO structures. But we're not going to
support that feature.

## Preferred values
There are some methods in the original Python API where individual fields are passed. For example, the `CNO.Options`
flag is an explicit single parameter to the _connect_ operations. If both the `Options` value and a CNO object are
passed, we will take the `Options` value from the object in preference. New code should not continue the approach of
explicit field parameters - always use the full class.

## Support for new MQI versions and definitions
This can only be done by people in the MQ development team with access to the build servers.

The new MQI definitions have to be copied from the build systems. Use the `copyDefs` script with parameters
pointing to the relevant level. For example
```bash
copyDefs -f gold -l p943-L250525
```

This will also give a warning about any updated versions of structures. New fields in existing structures/classes or new
structures may need code in the Python and/or the C layer to match the enhancements, to ensure they are passed to the
underlying C MQI functions. You can probably follow existing patterns to work out how to do that. For example, look at
the CSP class and how it is used in the `connect` method and the `ibmmqc.CONNX` function.

Any new MQBYTE fields should also be added to the `_binary_fields` list in `mqopts.py`

## MQCB callback processing
Callbacks are a multi-step design: the application specifies its callback function, while there's a "hardcoded"
pair of callbacks in the Python and C layers that handle the mappings so that eventually the right user-defined
function gets called with the parameters appropriately reformatted into Python classes.

One thing to watch for in future is that the C function needs to grab/release the GIL around calls back to the
Python layer. The GIL itself is probably released while the Python functions are executed (that's transparent)
but it is necessary while the C function is executed as it's on a thread that the Python interpreter doesn't
know about otherwise. As some of the requirements for the GIL are relaxed going forward, there might be changes
needed here - initial reading suggests everything will continue to work unchanged but we can't be certain.

## Python/C split
In general, logic goes into the Python layer rather than C. For example, setting MQCNO_HANDLE_SHARE flags could be done
in the _connect()_ method or the MQCONNX C wrapper. I've chosen to do it in Python, to keep the C code as
straightforward as possible.

But the two layers are considered inseparable; you should not have the Python module using the C extension from a
different version of the the package. There is a runtime check to ensure consistency.

## Python multi-file split
The original package had all of the Python code in the `__init__.py` file. I've split it to essentially one file for each
structure/class and one file for each object type (qmgr, queue, topic etc). With a few "common" parts. The public APIs
are still accessible by just importing the main module.

The split had to be sensitive to import ordering; otherwise you can get errors about looped/nested imports. There's
probably a more elegant split of code across the multiple files, perhaps moving some of the common code to different
places (maybe into the new `MQObject` class), but this arrangement works for now. The split was important for
maintainability, being able to more easily find what was where.
