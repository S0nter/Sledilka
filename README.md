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

## How to compile?
### Install python packages
For compilation:
```
pip install nuitka zstandard ordered-set
```
For program:
```
pip install PyQt6 activewindow darkdetect
```
For Windows also install these packages: ```pywin32 winshell```
### Compilation
Run this command to compile manually:
```
python -m nuitka --onefile --follow-imports --windows-icon-from-ico=icon.ico --plugin-enable=pyside6 --disable-console Sledilka.py
```
