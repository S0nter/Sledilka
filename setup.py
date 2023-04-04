from setuptools import setup

datafiles = [('',
              ['src/Segoe UI.ttf', 'src/icon.ico', 'src/Sledilka.py', 'src/limit_operations.py', 'src/base_functions.py', 'src/file_operations.py']),
             ('Translations',
              ['src/Translations/English.sltr', 'src/Translations/Русский.sltr'])]
setup(name="Sledilka",
      version='1.2.7',
      data_files=datafiles,
      install_requires=['setuptools',
                        'activewindow',
                        "importlib",
                        "datetime",
                        "PyQt5",
                        "winshell;platform_system=='Windows'",
                        "winshell;platform_system=='win-amd64'"],
      zip_safe=False)
