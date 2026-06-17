#!/bin/bash

# Start a local PyPI server instance to help test the packaging process
#
# Controls:
#  $1=STOP to kill the server and not restart it
#  set env var ALLIF to true to have the server listen on all network interfaces

curdir=`pwd`

root=$curdir/..
venv=$root/../venv_pypi

. $venv/bin/activate
if [ $? -ne 0 ]
then
  echo "ERROR: Could not activate virtual server env at $venv"
  exit 1
else
  # Install the server package if it's not already there
  pip install -q --upgrade pip pypiserver
fi

pid=`ps -ef|grep pypi-server|grep -v grep | awk '{print $2}'`
if [ ! -z "$pid" ]
then
  kill $pid
fi

if [ "$1" != "STOP" ]
then
  cd $venv
  # Clean out any existing packages
  rm -rf ./packages/*
  echo "Running a local pypi server with a clean packages directory."

  # This server is unprotected - no TLS, no authentication, no authorisation controls
  # But it's normally only listening on localhost, so should not be remotely accessible
  interface=127.0.0.1
  if [ ! -z "$ALLIF" ]
  then
    # Enable any network interface.
    interface=0.0.0.0
  fi
  pypi-server run --verbose  -i $interface -p 8080  -a . -P . $* ./packages >pypi-server.log 2>&1 &
else
  echo "Any running pypi server was stopped."
fi
