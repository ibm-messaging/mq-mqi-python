#!/bin/bash

# Run a github action, monitor it, and then download the generated artifacts into
# a local "dist" directory.

curdir=`pwd`
dist=$curdir/../dist
mkdir -p $dist >/dev/null 2>&1
rc=0

# It's assumed that you've got the tokens for doing this. Could perhaps
# add a "gh auth" call if we wanted to pick up specific authorisations.

# Bypass the workflow execution if we want to look at previous (failing?) runs
if [ -z "$NORUN" ]
then
  # This runs against the default (main) branch. Add '--ref my-branch' if needed
  gh workflow run release.yaml
  rc=$?
  if [ $rc -eq 0  ]
  then
    sleep 5
  fi
fi

# Find the most recent run and extract its ID. Can then sit and watch it
# go through the various steps
if [ $rc -eq 0 ]
then
  id=`gh run list --json databaseId --jq '.[].databaseId' | sort -n | tail -1`
  if [ ! -z "$id" ]
  then
    gh run watch  --exit-status $id
    rc=$?
  else
    rc=1
  fi
fi

# Once complete
if [ $rc -eq 0 ]
then
  echo "About to download built artifacts"
  cd $dist
  rm -rf art* ibmmq*
  gh run download -p "artifact*"
  find . -type f | while read f
  do
    mv $f .
  done

  find artifact* -type d | xargs rmdir
  ls -lrt $dist
fi


