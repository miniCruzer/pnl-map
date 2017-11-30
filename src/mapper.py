""" map file instruction parser """

import re
from typing import Any, Dict, Iterable, Tuple


class MapError(Exception):
    """ base exception for map file parsing errors """
    pass


def parse_map(text: str) -> Dict[str, Tuple[str, str]]:
    """ parse a map file """
    map_regex = re.compile("^(.*) = ([^ ]+): (.*)$")

    sheetmap = {}

    for num, line in enumerate(text):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        res = map_regex.search(line)

        if not res:
            raise MapError("could not match line %s: %s" % ((num + 1), line))

        dst = res.group(1)
        method = res.group(2).strip()
        search = res.group(3).strip()

        sheetmap[dst] = method, search

    return sheetmap


def longest(iterable: Iterable[str]) -> int:
    """ return the longest length item in the iterable """
    length = 0
    for item in iterable:
        if len(item) > length:
            length = len(item)
    return length


def search_map(data_dict: dict, method: str, term: str) -> Any:
    """ search mapped data 'data_dict' for a  """
    if method == "set":
        longest_value = longest(data_dict.values())
        return (term,) * longest_value
    elif method == "each":
        longest_value = longest(data_dict.values())
        values = term.split(",")

        if longest_value != len(values):
            raise MapError(
                f"improper number of arguments for each - got {len(values)}, expected"
                f" {longest_value}: {term}")

        return values

    for key, value in data_dict.items():

        if method == "starts":
            if key.startswith(term):
                return value
        elif method == "ends":
            if key.endswith(term):
                return value
        elif method == "contains":
            if key in term:
                return value
        elif method == "exact":
            if key == term:
                return value
        elif method == "re":
            if re.search(term, key):
                return value
        else:
            raise ValueError("invalid search method %r" % method)
