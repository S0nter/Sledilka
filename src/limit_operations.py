from sys import platform
from base_functions import run
if platform == 'win32':
    from ctypes import windll


def lock_comp():
    if platform == 'win32':
        user = windll.LoadLibrary('user32.dll')
        user.LockWorkStation()
    elif platform == 'linux':
        run('loginctl lock-session')


def hiber():
    if platform == 'win32':
        run('shutdown -h')
    elif platform == 'linux':
        run('loginctl hibernate')


def shutdown(phrases):
    if platform == 'win32':
        run(f'shutdown -t 10 -s -c {phrases["needs rest from the monitor"]}')
    elif platform == 'linux':
        run('loginctl poweroff')


def reboot(phrases):
    if platform == 'win32':
        run(f'shutdown -t 10 -r -c {phrases["needs rest from the monitor"]}')
    elif platform == 'linux':
        run('loginctl reboot')
