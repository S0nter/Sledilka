from sys import platform
from os import popen
if platform == 'win32':
    from ctypes import windll


def lock_comp():
    if platform == 'win32':
        user = windll.LoadLibrary('user32.dll')
        user.LockWorkStation()
    elif platform == 'linux':
        popen('loginctl lock-session')


def hiber():
    if platform == 'win32':
        print(popen('shutdown -h').read())
    elif platform == 'linux':
        pass
