from pprint import pformat
from paths import log_path
from os import popen
from loguru import logger

logger.add(log_path, level='DEBUG', rotation='10 MB')  # format="{time} | {level} |  | {message}",


def log(*text):
    # print(*text, sep=sep, end=end)
    # with open(log_path, 'a') as file:
    #     print(*text, sep=sep, end=end, file=file)
    logger.info(normalise(text))


def debug(*text):
    # logger.debug(" ".join(map(str, json.dumps(text, ensure_ascii=False, indent=4))))
    logger.debug(normalise(text))


def error(*text):
    logger.error(normalise(text))


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


# def is_iterable():
#     try:

