#!/bin/bash

if [ -z "$1" ]
  then
    prefix=$HOME/.local
else
    prefix=$1
fi
pip uninstall Sledilka
python3 setup.py build sdist install --prefix=$prefix
#.local/lib/python3.10
