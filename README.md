## What is this?
Sledilka is a program that runs on boot, monitors the time of computer use, and turns it off according to the rules specified by the user.

## 1.2.3

### Changes
 - Better multiprocessing, stability

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
For Windows also install these pacmkages: ```pywin32 winshell```
### Compilation
Run this command:
```
python -m nuitka --onefile --follow-imports --windows-icon-from-ico=icon.ico --plugin-enable=pyqt6 --disable-console Sledilka.py
```
