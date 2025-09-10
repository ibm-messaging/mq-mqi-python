
# How to run the test suite

The tests can either run against a local queue manager or use a container image It is assumed that you are using a queue
manager with the "Developer" configuration: for example, queues like DEV.QUEUE.1 and appropriate authentication for the
'app' and 'admin' users.

## Virtual environment
You need a virtual environment. The scripts here assume it is in `../../../venv_ibmmq` To create one, use
`python -m venv <directory>`.

## Setting up the container
Use the `runContainer.sh` script to start a queue manager. The script will reuse an existing volume by default, but
running the script with a CLEAN parameter will create a new qmgr from scratch on each execution. You can use either
`docker` or `podman` as the container manager. See the script's usage information for available parameters.

## Connectivity
The `tox.ini` file in the root of the repo contains configuration information for the queue manager. The `config.py`
program in this directory also has configuration items. You might edit one or the other depending on your test
environment.

## Running the tests
The `runAllTests.sh` script then executes the tests using `tox`. The `-e container` flag uses that section of tox.ini; to
run against a local queue manager, you can edit the script to use `-e local`.

## Notes
* Tests are executed from test_* in alphabetic order.
* Python 3 strings are randomly converted to byte arrays when setting MQI fields
  * As V2 of the library can accept either style
  * Output strings will be checked in both styles for equality

## Missing
There is a lot of new function in V2 that does not currently have unittest cases written. But most of that is, in any
case, being executed by the example programs. So most things are covered one way or the other.
