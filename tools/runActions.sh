#!/bin/sh

# This script executes a GitHub Action to create binary wheels and
# downloads the generated artifacts ready to be published on PyPI

# It uses the "gh" command line. And that assumes you've already
# authenticated to the repo

curdir=`pwd`
dist=$curdir/../dist
mkdir -p $dist >/dev/null 2>&1
rc=0

# Assumed that you've got the tokens for doing this
gh workflow run release.yaml
rc=$?
if [ $rc -eq 0 ]
then
  gh run watch  --exit-status
  rc=$?
fi

# Download the artifacts to the same location as if we've done a local build
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