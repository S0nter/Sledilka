## What is this?
Sledilka is a program that runs on boot, monitors the time of computer use, and turns it off according to the rules specified by the user.
~~Works on "M OS"!~~<br> I should find a way to compile without `libc`

## 1.2.4

### Changes
 - Translations
 - Bugfixes
 - Moved from PyQt6 to PySide6

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
Run this command:
```
python -m nuitka --onefile --follow-imports --windows-icon-from-ico=icon.ico --plugin-enable=pyside6 --disable-console Sledilka.py
```
