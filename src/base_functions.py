from pprint import pformat
from os import popen
from loguru import logger
from sys import stdout

try:
    from paths import log_path
except ImportError:
    from .paths import log_path

logger.remove(0)
logger.add(log_path, level='DEBUG', rotation='10 MB', format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <5}</level> | <cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>')  # format="{time} | {level} |  | {message}",  # noqa
logger.add(stdout, format='<level>{level: <5}</level> | <cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>')  # noqa


def log(*text, depth=1):
    logger.opt(depth=depth).info(normalise(text))


def debug(*text):
    logger.opt(depth=1).debug(normalise(text))


def error(*text):
    logger.opt(depth=1, exception=True).error(normalise(text))


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
    debug(popen(command).read())


def normalise(sth):
    ls = []
    for i in sth:
        if type(i) in [dict, list, tuple]:
            i = pformat(i, indent=4)
        ls.append(str(i))
    return " ".join(ls)


def is_between(time, time_range) -> bool:
    if time_range[1] < time_range[0]:
        return time >= time_range[0] or time <= time_range[1]
    return time_range[0] <= time <= time_range[1]
