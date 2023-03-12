from paths import log_path
from os import popen


def log(*text, sep=' ', end='\n'):
    print(*text, sep=sep, end=end)
    with open(log_path, 'a') as file:
        print(*text, sep=sep, end=end, file=file)


def to_bool(string: str) -> bool:
    if string == 'True':
        return True
    else:
        return False


def sort(dict_):
    sorted_dict = {}
    # sorted_keys = list(sorted(dict, key=dict.get))[::-1]
    sorted_keys = list(reversed(sorted(dict_, key=dict_.get)))

    for w in sorted_keys:
        sorted_dict[w] = dict_[w]
    return sorted_dict


def run(command):
    print(popen(command).read())

# def copytree(src, dst, symlinks=False, ignore=None):
#     import os, shutil
#     for item in os.listdir(src):
#         s = os.path.join(src, item)
#         d = os.path.join(dst, item)
#         print(s, d)
#         try:
#             if os.path.isdir(s):
#                 os.mkdir()
#                 shutil.copytree(s, d, symlinks, ignore)
#             else:
#                 shutil.copy2(s, d)
#         except shutil.SameFileError:
#             pass
