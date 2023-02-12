from setuptools import setup

datafiles = [('',
              ['src/paths.py', 'src/Sledilka.py', 'src/base_functions.py', 'src/limit_operations.py', 'src/Segoe UI.ttf', 'src/icon.ico', 'src/file_operations.py']),
             ('Translations',
              ['src/Translations/English.sltr', 'src/Translations/Русский.sltr'])]
print(datafiles)
setup(name="Sledilka",
      version='1.2.5',
      # packages=['breeze_theme'],
      # py_modules=['sys',
      #             "csv",
      #             "json",
      #             "multiprocessing",
      #             "os",
      #             "threading",
      #             "time"],
      data_files=datafiles,
      # include_package_data=True,
      # packages=['src'],
      # package_data={
          # 'icon.ico': ['src/icon.ico'],
          # 'Segoe UI.ttf': ['src/Segoe UI.ttf']},
      install_requires=['setuptools',
                        'activewindow',
                        "importlib",
                        "datetime",
                        "PyQt5",
                        "darkdetect"],
      zip_safe=False)
