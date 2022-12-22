## What is this?
Sledilka is a program that runs on boot, monitors the time of computer use, and turns it off according to the rules specified by the user.

## 1.2.3

### Changes
 - Better multiprocessing, stability

## How to compile?
Run this command:
```
<Python binary> -m nuitka --onefile --follow-imports --windows-icon-from-ico=icon.ico --plugin-enable=pyqt6 --disable-console Sledilka.py
```
