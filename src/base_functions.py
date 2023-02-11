from paths import log_path


def log(*text):
    s = ''
    for row in text:
        s += str(row) + ' '
    with open(log_path, 'a') as file:
        print(s)
        print(s, file=file)


def to_bool(_str):
    if _str == 'True':
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
