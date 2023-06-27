## What is this?
Sledilka is a program that runs on boot, monitors the time of computer use, and turns it off according to the rules specified by the user.

Works on "M OS"!

This is not parental control, it's self-control time tracker. 

## Gallery
![Sledilka](/gallery/Interface.png)

## 1.3

### Changes
 - Fixed loguru function path
 - Added new option to control screen time: Blocked hours
 - Wayland time tracking fix (requires dbus and kde/gnome/mint...)
 - Wayland icon fix
 - Removed whitespaces from various places in translations
 - Fixed crash when caused by limits enabling
 - Fixed color dialog (there is current color now)

## How to use?
### Install python packages
For compilation (optional):
```
pip install nuitka zstandard ordered-set
```
For program:
```
pip install PyQt5 activewindow importlib datetime loguru
```
For Windows also install these packages: ```pywin32 winshell```

You may compile it or use as python package (better)

### 1) Compilation
#### 1.1) Windows
 - Click green `Code` button, then `Download ZIP`
 - Unpack files to a dirirectory and it will be used by Sledilka
 - Copy path to folder with Sledilka's files
 - Press `Win + R` and enter `cmd`, press enter
 - type `cd /D <path you've copied earlier>`
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
