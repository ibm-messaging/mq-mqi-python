#!/bin/bash

# Make sure we can compile against the oldest "supported" level of MQ (9.1)
# Assumes the MQ installation is under /opt/mqm.91
# Also do a basic check with Python 3.9, the oldest version
# we claim to support. There's a venv assumed to have been created for that version.

curdir=`pwd`

# Location of old header files
export MQ_FILE_PATH=/opt/mqm.91

# Start with the default installed Python version
python=python

# Use different virtual envs for different versions of Python
for venv in ../../venv ../../venv_39
do

  cd $curdir
  . $venv/bin/activate
  pip uninstall -y ibmmq
  cd ..

  # Do an install of the local tree to check it builds
  pip install --verbose -e .
  pip list 2>&1| grep -q ibmmq
  if [ $? -ne 0 ]
  then
    echo "ERROR: Could not install ibmmq in venv: $venv"
    exit 1
  fi

  # MQ 9.1.5 Redist Client package does not have setmqenv, so
  # we fake it and export the symbols that might be relevant
  tmpenv=/tmp/crtmqenv.$$
  $MQ_FILE_PATH/bin/crtmqenv -k -s > $tmpenv
  . $tmpenv
  export LD_LIBRARY_PATH
  export PATH
  export MQ_INSTALLATION_NAME
  export MQ_INSTALLATION_PATH
  rm -f $tmpenv

  # Now try to connect as a client to the qmgr. Since my machine
  # is using the redist client package, it can't rely on version-switching
  # to use local bindings.
  $python $curdir/../code/examples/connect_client.py
  rc=$?
  if [ $rc -ne 0 ]
  then
    echo "ERROR: Failed running with MQ in $MQ_FILE_PATH in venv: $venv"
    exit 1
  fi

  # Reset the version of python for the 2nd loop
  python=python3.9

done
exit $rc

