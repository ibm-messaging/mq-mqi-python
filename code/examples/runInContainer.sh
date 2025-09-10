#!/bin/bash

# This is an example of building a container that contains the MQ client and a Python
# program that works with it.

# Basic name for the container. If we have a version tag from a git clone, use that
# in the container tag. Otherwise just use "latest"
TAG=mq-python-example-connect
VER=`git tag -l 2>/dev/null| sort | tail -1 `
if [ -z "$VER" ]
then
  VER="latest"
fi

echo Building container with tag $TAG:$VER

# Can set the RDURL environment variable to tell the downloads to come from somewhere else"
#  export RDURL="--build-arg RDURL_ARG=http://example.com:8000/redist"

# Build the container which includes copying the program and installing the underlying MQ packages
docker build -t $TAG:$VER $RDURL -f  Dockerfile .
rc=$?

if [ $rc -eq 0 ]
then
  # This line tries to grab a currently active IPv4 address for this machine. It's probably
  # not what you want to use for a real system but it's useful for testing. "localhost"
  # does not necessarily work inside the container so we need a real address. Can also
  # set an environment variable to explicitly configure it.
  addr=`ip -4 addr | grep -v altname | grep "state UP" -A2 | grep inet | tail -n1 | awk '{print $2}' | cut -f1 -d'/'`

  if [ ! -z "FORCE_ADDR" ]
  then
    addr=$FORCE_ADDR
  fi

  echo "Local address is $addr"
  port="1414"
  if [ ! -z "addr" ]
  then
    # Run the container.
    docker run --rm \
       -it \
       -e MQSERVER="SYSTEM.DEF.SVRCONN/TCP/$addr($port)" \
       $TAG:$VER
  else
    echo "Cannot find a working address for this system"
    exit 1
  fi
fi

exit $rc
