#!/bin/bash

dir=$(cd $(dirname $0); pwd)
env=$dir/venv

if [[ -e $env ]]
then
    rm -rf $env
fi

virtualenv -p python2.7 $env
. $env/bin/activate

easy_install -Z -H None $dir/vendor/python-ping-2011.10.17.376a019.tar.gz

# ugh
cp src/pingtool.py venv/bin/

ed venv/bin/pingtool.py <<EOF
1
c
#!$env/bin/python
.
wq
EOF