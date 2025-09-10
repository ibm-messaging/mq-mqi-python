#!/bin/bash

# Assumption that qmgr has been started using the runContainer script.
# The container will have the DEV config, users=app/password and admin/password.
# Basic connectivity config is in ../../tox.ini with potential overrides in config.py

curdir=`pwd`

# Somewhere that's got a Python virtual environment prepared
venv="../../../venv_ibmmq"

. $venv/bin/activate
if [ $? -ne 0 ]
then
  echo "ERROR: Cannot activate virtual env in $venv"
  exit 1
fi

cd $curdir

# Make sure we've got the main test tool
which tox >/dev/null 2>&1
if [ $? -ne 0 ]
then
  pip install tox
fi

# And now run them
# Tests are run in the alphabetic order of test*.py
tox -e container  2>&1

