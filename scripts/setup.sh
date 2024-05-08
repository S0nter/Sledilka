#!/bin/bash


if [ -z "$1" ]
  then
    prefix=$HOME/.local
else
    prefix=$1
fi

python3 setup.py build sdist install --prefix=$prefix
