## What is this?
Sledilka is a program that runs on boot, monitors the time of computer use, and turns it off according to the rules specified by the user.

Works on "M OS"!

This is not parental control, it's self-control time tracker. 

## Gallery
![Sledilka](/gallery/Interface.png)

## 1.2.6

### Changes
 - Added information in tray
 - Added color chaning feature
 - Fixed hibernation on linux
 - It can be hidden on boot (setting)
 - Fixed "Time limit" width
 - Backend of saving settings improved (now the same names for shutting down should work)

## How to use?
### Install python packages
For compilation (optional):
```
pip install nuitka zstandard ordered-set
```
For program:
```
pip install PyQt5 activewindow
```
For Windows also install these packages: ```pywin32 winshell```

You may compile it or use as python package (better):

### 1) Compilation
Run this command:
```
python -m nuitka --onefile --follow-imports --windows-icon-from-ico=icon.ico --plugin-enable=pyqt5 --disable-console Sledilka.py
```
### 2) Python installation
#### 2.1) System installation
 - Change third line to `sudo python3 setup.py build sdist install`
 - Run `setup.sh` file
 - Run `python3 -m Sledilka` in your directory for Sledilka
#### 2.2) User installation
 - Run `setup.sh` file
 - Run `python3 -m Sledilka` in your directory for Sledilka
### 3) Arch linux installation
 - Copy the PKGBUILD file and run `makepkg -sir`
