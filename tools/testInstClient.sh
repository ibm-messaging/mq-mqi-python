#!/bin/bash

# Build the package ready for release. Then upload it to the local PyPI server.
# Then switch to a test environment where we reinstall it and do a basic check.
# This will validate that it's reasonable to ship the package to the public.

curdir=`pwd`

# Prepare for release, and push to the local server
echo Y  | ./pyRelease.sh -l Y -v
if [ $? -ne 0 ]
then
  echo "Release process failed"
  # exit 1
fi

pkg="ibmmq"
venv="venv_test"

# Now do a real installation from that server. Not an editable install that
# we do during development
root=$curdir/..
venv=$root/../$venv

. $venv/bin/activate
if [ $? -ne 0 ]
then
  echo "ERROR: Could not activate virtual server env at $venv"
  exit 1
fi

cd $venv

pip uninstall -y $pkg
# List available versions including pre-release
echo
pip index --index http://localhost:8080 --pre versions $pkg
echo
allowPreRelease="--pre"
pip install --index-url http://localhost:8080  $allowPreRelease $pkg #>="2.0.0"

# find . | grep $pkg | grep -v _pycache

# Run a very basic test to connect to a local qmgr
python -i << EOF
import $pkg

try:
    print('Version: ', $pkg.get_versions())
    qm=$pkg.connect('QM1', 'DEV.APP.SVRCONN','localhost')
    print("Connection succeeded")
except:
    print("Connection failed")

EOF

# And try running a bigger program direct from the source tree
# python $curdir/../code/examples/message_properties.py
