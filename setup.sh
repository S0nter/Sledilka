#!/bin/bash

python3 setup.py build sdist

if [ -z "$1" ];  then
    python3 -m pip install dist/*
else
    python3 -m pip install dist/* --prefix="$1"
fi 
