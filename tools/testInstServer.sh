#!/bin/bash

# Start a local PyPI server instance to help test the packaging process
curdir=`pwd`

root=$curdir/..
venv=$root/../venv_pypi

. $venv/bin/activate
if [ $? -ne 0 ]
then
  echo "ERROR: Could not activate virtual server env at $venv"
  exit 1
fi

pid=`ps -ef|grep pypi-server|grep -v grep | awk '{print $2}'`
if [ ! -z "$pid" ]
then
  kill $pid
fi

if [ "$1" != "STOP" ]
then
  cd $venv
  rm -rf ./packages/*
  echo "Running a local pypi server"
  pypi-server run --verbose  -p 8080  -a . -P . $* ./packages >pypi-server.log 2>&1 &
else
  echo "Any running pypi server was stopped"
fi
