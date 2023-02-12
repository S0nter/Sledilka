## What is this?
Sledilka is a program that runs on boot, monitors the time of computer use, and turns it off according to the rules specified by the user.

~~Works on "M OS"!~~<br> I should find a way to compile without `glibc`

This is not parental control, it's self-control time tracker. 

## Gallery
![Sledilka](/gallery/Interface.png)

## 1.2.5

### Changes
 - Added "translation chooser" to the first program start
 - Moved from PySide6 to PyQt5 for better themes on linux
 - Multiple files
 - Added "About Qt" button
 - Added theme changer for timer and interface
 - Added official English translation
 - Compilation is not required

## How to use?
### Install python packages
For compilation (optional):
```
pip install nuitka zstandard ordered-set
```
For program:
```
pip install PyQt5 activewindow darkdetect
```
For Windows also install these packages: ```pywin32 winshell```

You may compile it or use as python package (better):

### 1) Compilation
Run this comma:
```
python -m nuitka --onefile --follow-imports --windows-icon-from-ico=icon.ico --plugin-enable=pyqt5 --disable-console Sledilka.py
```
### 2) Python installation
 - Run `setup.sh` file
 - Run `python3 -m Sledilka` in your directory for Sledilka
