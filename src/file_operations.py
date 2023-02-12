import json
from sys import platform, argv
from os import getcwd, path, chdir, mkdir, listdir
# from paths import tran_path

if platform == 'win32':
    from win32com.client import Dispatch  # noqa


def add_to_startup(phrases: dict) -> None:
    try:
        if platform == 'win32':
            make_shortcut('Sledilka', path.abspath('Sledilka.exe'), 'startup')
        elif platform == 'linux':
            user = path.expanduser('~')
            run = 'python3 ' + argv[0]
            # run = 'python3 -m Sledilka'
            file = open(f'{user}/.config/autostart/Sledilka.desktop', 'w')
            file.write(f"""[Desktop Entry]
Type=Application
Exec=cd {getcwd()} && {run}
Path={getcwd()}
Icon={getcwd()}/icon.ico
StartupNotify=true
Terminal=false
TerminalOptions=
X-DBUS-ServiceName=Sledilka
X-DBUS-StartupType=Unique
X-GNOME-Autostart-enabled=true
X-KDE-SubstituteUID=false
X-KDE-Username=
Hidden=false
NoDisplay=false
Name[en_IN]=Sledilka
Name[ru_RU]=Следилка
Name={phrases["app name"]}
Comment[en_IN]=
Comment=
""")
            file.close()
            print('Home path (user):', path.expanduser('~'))
    except Exception as exc:
        print('Adding to sturtup failed because', exc)


def make_shortcut(name, target, path_to_save, w_dir='default', icon='default'):
    print('make_shortcut')
    if path_to_save == 'desktop':
        '''Saving on desktop'''
        # Соединяем пути, с учётом разных операционок.
        path_to_save = path.join(winshell.desktop(), f'{name}.lnk')
    elif path_to_save == 'startup':
        '''Adding to startup (windows)'''
        user = path.expanduser('~')
        path_to_save = path.join(fr"{user}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/",
                                 f'{name}.lnk')
    else:
        path_to_save = path.join(path_to_save, f'{name}.lnk')
    if path.exists(path_to_save):
        do = False
    else:
        do = True
    if do:
        if icon == 'default':
            icon = target
        if w_dir == 'default':
            w_dir = path.dirname(target)
        # С помощью метода Dispatch, обьявляем работу с Wscript
        # (работа с ярлыками, реестром и прочей системной информацией в windows)
        shell = Dispatch('WScript.Shell')
        # Создаём ярлык.
        shortcut = shell.CreateShortCut(path_to_save)
        # Путь к файлу, к которому делаем ярлык.
        shortcut.Targetpath = target
        # Путь к рабочей папке.
        shortcut.WorkingDirectory = w_dir
        # Тырим иконку.
        shortcut.IconLocation = icon
        # Обязательное действо, сохраняем ярлык.
        shortcut.save()


def transave(phrases, tran_name, tran_path) -> None:
    prev = getcwd()
    try:
        chdir(tran_path)
    except FileNotFoundError:
        mkdir(tran_path)
        chdir(tran_path)
    with open(f'{tran_name}.sltr', 'w') as file:
        json.dump(phrases, file, ensure_ascii=False)
        chdir(prev)


def tran_list(tran_path) -> list:
    prev = getcwd()
    chdir(tran_path)
    res = [t.replace('.sltr', '') for t in listdir(tran_path) if path.isfile(t)]
    chdir(prev)
    return res
