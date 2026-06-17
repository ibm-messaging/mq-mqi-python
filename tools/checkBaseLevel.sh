#!/bin/bash

# Take traces of the application so we can check the version of MQ client
# that we have run against.
function strtrc {
    export MQTRACEPATH=$mqTracePath
    if [ -d $mqTracePath ]
    then
      rm -f $MQTRACEPATH/*TRC $MQTRACEPATH/*FMT
    fi
    strmqtrc >/dev/null 2>&1
}

function endtrc {
   cd $mqTracePath
   (
     endmqtrc
     dspmqtrc *TRC
     rm -f *TRC
   ) >/dev/null 2>&1

   pythonTrc=`grep "Program Name" *FMT | grep python | cut -d: -f1`
   if [ ! -z "$pythonTrc" ]
   then
     mqLevel=`grep LVLS $pythonTrc | awk '{print $4}'`
   else
     mqLevel="N/A"
   fi
   echo "MQ version: $mqLevel"
}

# Make sure we can compile against the oldest "supported" level of MQ (9.1)
# Assumes the MQ installation is under /opt/mqm.91
# Also do a basic check with Python 3.9, the oldest version
# we claim to support. There's a venv assumed to have been created for that version.

curdir=`pwd`
mqTracePath=/tmp/mq.trace
mkdir -p $mqTracePath #  2>/dev/null 2>&1

# Use different virtual envs for different versions of Python
for i in 0 1 2
do
  case $i in
  0)
    # Newest python; oldest MQ
    export MQ_FILE_PATH=/opt/mqm.91
    venv=../../venv
    python=python
    ;;
  1)
    # Oldest python; oldest MQ
    export MQ_FILE_PATH=/opt/mqm.91
    venv=../../venv_39
    python=python3.9
    ;;
  2)
    # Oldest python; newest MQ
    export MQ_FILE_PATH=/opt/mqm
    venv=../../venv_39
    python=python3.9
    ;;
  esac

  cd $curdir
  . $venv/bin/activate
  if [ $? -ne 0 ]
  then
    echo "ERROR: Could not activate venv: $venv"
    exit 1
  fi

  # MQ 9.1.5 Redist Client package does not have setmqenv, so
  # we fake it and export the symbols that might be relevant
  if [ -x $MQ_FILE_PATH/bin/setmqenv ]
  then
    . $MQ_FILE_PATH/bin/setmqenv -k -s
  else
    tmpenv=/tmp/crtmqenv.$$
    $MQ_FILE_PATH/bin/crtmqenv -k -s > $tmpenv
    . $tmpenv
    rm -f $tmpenv
  fi

  export LD_LIBRARY_PATH
  export PATH
  export MQ_INSTALLATION_NAME
  export MQ_INSTALLATION_PATH

  echo
  mqVer=`$MQ_FILE_PATH/bin/dspmqver -f2 | awk '{print $2}'`
  printf "Running test in %s against MQ: %s\n" "$venv" "$mqVer"

  python -m pip install -q --upgrade pip
  pip uninstall -y ibmmq >/dev/null 2>&1
  cd ..

  # Do an install of the local tree to check it builds
  pip install -q -e .
  pip list 2>&1| grep -q ibmmq
  if [ $? -ne 0 ]
  then
    echo "ERROR: Could not install ibmmq in venv: $venv"
    exit 1
  fi

  echo "Python version: " `$python --version`

  # Now try to connect as a client to the qmgr. Since my machine
  # is using the redist client package, it can't rely on version-switching
  # to use local bindings. We collect trace info in order to extract the
  # actual runtime version of MQ client.
  strtrc
  $python $curdir/../code/examples/connect_client.py
  rc=$?
  endtrc

  if [ $rc -ne 0 ]
  then
    echo "ERROR: Failed running with MQ in $MQ_FILE_PATH in venv: $venv"
    exit 1
  fi

done
exit $rc

