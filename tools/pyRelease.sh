#!/bin/bash
# Upload a package/project to the PyPI environment. Options
# allow selection of the real production server, the test.pypi.org server,
# or a locally hosted server.

function cleanup {
  : # Nothing needed for now
}

function continueYN {
   prompt="$1"
    while true
    do
      read -p "$prompt? [Y/N] " yn
      case $yn in
      y*|Y*)
        echo 0
        return
        ;;
      n*|N*)
        echo 1
        return
        ;;
      *)
        ;;
      esac
    done
    return $rc
}


function printSyntax {
cat << EOF
Usage: pyRelease.sh [-k keyfile] [-p packageName] [-l Y|N] [-r] [ -e venvLocation] [-v]
Options:
    -k File containing API Key (default depends on repository)
    -l Use empty(Y)/untouched(N) local server at $localRepository
    -p package name (default $defaultPkg)
    -r Use PyPI repository (default $defaultRepository)

    -e Location of a Python virtual environment
    -v Verbose
EOF
exit 1
}

curdir=`pwd`
root=$curdir/..

testRepository="testpypi"
prodRepository="pypi"
localRepository="http://localhost:8080"
defaultRepository=$testRepository
repositoryFlag="--repository"

useTestServer=true
useLocalServer=false
verbose=false

keyFileProd="$HOME/.creds/pythonPyPi"
keyFileTest="$HOME/.creds/pythonTestPyPi"
keyFileOpt=""

defaultPkg="ibmmq"

repository=$defaultRepository
pkg=$defaultPkg

venv=$root/../venv_build

while getopts :e:k:l:p:rv o
do
  case $o in
  e)
    venv=$OPTARG
    ;;
  k)
    keyFileOpt=$OPTARG
    ;;
  p)
    pkg=$OPTARG
    ;;
  l)
    # Use "testInstServer.sh" to setup a local PyPI server
    repository=$localRepository
    repositoryFlag="--repository-url"
    useLocalServer=true
    # Option to delete any packages on the server so we can reuse
    # the version number
    case $OPTARG in
    y|Y)
      echo "Deleting packages from test server"
      rm -f $root/../venv_pypi/packages/*tar.gz
      ;;
    n|N)
      # Leave server untouched
      echo "Not deleting packages from test server"
      ;;
    *)
      printSyntax
      ;;
    esac
    ;;
  r)
    useTestServer=false
    repository=$prodRepository
    ;;
  v)
    verbose=true
    ;;
  *)
    printSyntax
    ;;
  esac
done

# Check for no further parameters
shift $((OPTIND-1))
if [ "$1" != "" ]
then
  printSyntax
fi

if [ ! -z "$keyFileOpt" ]
then
  keyFile=$keyFileOpt
else
  if $useTestServer
  then
    keyFile=$keyFileTest
  else
    keyFile=$keyFileProd
  fi
fi

. $venv/bin/activate
if [ $? -ne 0 ]
then
  echo "ERROR: Cannot activate virtual build env"
  exit 1
fi

trap cleanup EXIT

# Need these in our venv
(
pip install --upgrade pip
pip install --upgrade build
pip install --upgrade twine
) 2>&1 | grep -v "Requirement already satisfied"

# Create a unique version number based on the current epoch. As we can't overwrite versions even on the test pypi environment.
# Not currently used for the real project, where the version is "hardcoded" in setup.py
if $useTestServer
then
  bver=`date +"%s"`
  export PYVER="2.0.0a$bver"
fi

cd $root
if [ ! -r "$keyFile" ]
then
  echo "ERROR: File $keyFile does not exist"
  exit 1
fi

# First line of the file contains our Token
tok=`cat $keyFile | head -1`
if [ -z "$tok" ]
then
  echo "ERROR: Cannot read credentials from file: $keyFile"
  exit 1
fi

# First line of the keyFile should start with "pypi-..."
if ! [[ $tok =~ "pypi-" ]]
then
  echo "ERROR: Token has wrong format. Should begin \"pypi-\""
  exit 1
fi

cd $root

# Get rid of temporary directories that we don't want included
rm -rf dist
rm -rf code/$pkg.egg-info

# Even though we're not going to upload the binary wheel, we do
# want the build process to create it as a "final" check on the contents
python -m build | grep -Ev "^copying|^adding"
if [ $? -ne 0 ]
then
  echo "ERROR: Failed to build."
  exit 1
fi

# Does the tar file contain what we expect?
if $verbose
then
cd $root/dist
echo "----------------------------"
echo "     CONTENTS OF TAR        "
echo "----------------------------"
cat *tar* | tar -tvzf -
echo

# Don't care about the wheel's contents as it's not normally uploaded
# unzip -l *whl
fi

cd $root
python -m twine check --strict dist/*
if [ $? -ne 0 ]
then
  echo "ERROR: Cannot validate package"
  exit 1
fi

# This is one final chance to quit manually before we try to do the upload
yn=`continueYN "Continue with upload to $repository"`
if [ "$yn" -ne "0" ]
then
  echo "Exiting."
  exit 1
fi

# This sets the credentials for the upload
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="$tok"

# Only upload the source distribution, not the wheel which will fail.
# PyPI does not accept binary packages tagged with a simple "linux_x86_64" or similar.
# See  https://discuss.python.org/t/pypi-org-unsupported-platform-tag-openbsd-7-0-amd64/16302 for one discussion.
# And using the "manylinux" prebuilder environments is getting way too complicated.

# verboseUpload="--verbose"

# If using the local repository, then first make sure the pypi-server is running
# And uncomment the upload line if you want to try uploading binary wheels to the local server.
if $useLocalServer
then
  echo
  # python -m twine upload $repositoryFlag $repository $verboseUpload dist/$pkg*whl*
  if [ $? -ne 0 ]
  then
    echo "ERROR: Upload of binary wheel failed"
    exit 1
  fi
fi

python -m twine upload $repositoryFlag $repository $verboseUpload dist/$pkg*.tar.gz
if [ $? -ne 0 ]
then
  echo "ERROR: Upload failed"
  exit 1
fi

echo "Upload to repository $repository was successful"
exit 0
