#!/bin/sh

# This script executes a GitHub Action to create binary wheels and
# downloads the generated artifacts ready to be published on PyPI

# It uses the "gh" command line. And that assumes you've already
# authenticated to the repo

curdir=`pwd`
dist=$curdir/../dist
mkdir -p $dist >/dev/null 2>&1
rc=0

# Bypass the workflow execution if we want to look at previous (failing?) runs
if [ -z "$NORUN" ]
then
  # Assumed that you've got the tokens for doing this
  gh workflow run release.yaml
  rc=$?
fi

if [ $rc -eq 0 ]
then
  sleep 5
  id=`gh run list --json databaseId --jq '.[].databaseId' | sort -n | tail -1`
  # If the ID is null, then we'll get an interactive list to choose from. So don't
  # treat it as an error
  gh run watch  --exit-status $id
  rc=$?
fi

# Download the artifacts to the same location as if we've done a local build
# The GitHub action creates them in subdirectories, but we will flatten that
if [ $rc -eq 0 ]
then
  cd $dist
  rm -rf art*
  gh run download -p "artifact*"
  mv artifact*/*.whl .
  mv artifact*/*tar.gz .
  find artifact* -type d | xargs rmdir
fi

exit $rc