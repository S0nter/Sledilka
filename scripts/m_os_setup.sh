#!/usr/bin/env bash

# Creating directories
mkdir -p ~/.config/autostart
mkdir -p ~/.local/share/sledilka

# Cloning the repository
cd ~/.local/share/sledilka/
git clone --depth 1 https://github.com/S0nter/Sledilka .

# Cleanup
rm -r gallery docs scripts .git

# Setting up virtual environment with required packages
cd src
python -m venv venv
venv/bin/python -m pip install activewindow importlib datetime PyQt6 loguru

venv/bin/python Sledilka.py
