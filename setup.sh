#!/bin/bash

if [ -z "$1" ]
  then
    prefix=$HOME/.local
else
    prefix=$1
fi
# pip uninstall Sledilka
python3 setup.py build sdist
python3 -m pip install dist/* --target=$prefix
