#!/bin/sh

# Install a package from the test PyPI server
# Should do this before doing a real release

curdir=`pwd`
root=$curdir/..
pkg="ibmmq"
PYVER=`cat ../setup.py | grep "^version =" | awk '{print $3}' | sed "s/'//g"`
PYVER="0.0.0"
echo looking for version: $PYVER

v=$root/../venv_test
. $v/bin/activate
if [ $? -ne 0 ]
then
  echo "ERROR: Cannot activate virtual test env"
  exit 1
fi

pip uninstall -y  $pkg >/dev/null 2>&1
echo "Waiting ..."
for i in 1 # 2 3 4 5 6 7 8 9 10 11 12
do
  printf "."
  sleep 10
done
echo

# pip install --upgrade pip
# Need to include the 'extra-index-url' so that we can get dependencies (in particular 'setuptools') installed

verbose="--verbose"
pip install $verbose --index-url https://test.pypi.org/simple/ --no-cache-dir --extra-index-url https://pypi.org/simple/ $pkg=="$PYVER"
if [ $? -ne 0 ]
then
  echo "ERROR: Problem installing"
  exit 1
fi

# Try to run some code that uses the newly-installed package
python -i << EOF
import $pkg
print("MQRC_NOT_AUTHORIZED = ",$pkg.CMQC.MQRC_NOT_AUTHORIZED)
EOF
