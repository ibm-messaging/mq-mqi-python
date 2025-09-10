To migrate from PyMQI V1 to the IBMMQ V2 package:

* Make sure your versions of MQ and Python meet the prereq levels given in the [README](README.md)
* Use pip install with the new package name: `pip install ibmmq`
* Change applications to import the new name. You can use `import ibmmq as pymqi"`to avoid changing the rest of the
  application code.
* Check application code for use of previously-deprecated definitions. Most likely misuse is of the MQCHT_ variables,
  which are in CMQXC, not CMQC.

See the [CHANGELOG](CHANGELOG.md) for more details on what has been removed and added.

PyMQI V1 had its own backwards-compatibility option for some of its original classes and method names. Those original
names did not conform to the now-preferred `snake_case` style. For example, there's `md = MD` and
`connectWithOptions=connect_with_options`. Those trivial aliases have been kept for the V2 library, but should not be
used for future development.
