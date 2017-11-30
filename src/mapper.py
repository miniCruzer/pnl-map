""" map file instruction parser """

import re
from typing import (Any, Callable, Dict,  # pylint: disable=unused-import
                    Iterable, List, Tuple)

SEARCH_DISPATCH_TABLE = {} # type: Dict[str, Callable]


class MapError(Exception):
    """ base exception for map file parsing errors """
    pass


def parse_map(text: List[str]) -> Dict[str, Tuple[str, str]]:
    """ parse a map file """
    map_regex = re.compile(r"^(.*) = ([^ ]+): (.*)$")

    sheetmap = {}

    for num, line in enumerate(text):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        res = map_regex.search(line)

        if not res:
            raise MapError(f"could not match line {num + 1}: {line}")

        dst = res.group(1)
        method = res.group(2).strip()
        search = res.group(3).strip()

        sheetmap[dst] = method, search

    return sheetmap


def longest(iterable: Iterable[Tuple]) -> int:
    """ return the longest length item in the iterable """
    length = 0
    for item in iterable:
        if len(item) > length:
            length = len(item)
    return length


def search_map(data_dict: Dict[str, Tuple], method: str, term: str) -> Any:
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

        if method in SEARCH_DISPATCH_TABLE:
            retval = SEARCH_DISPATCH_TABLE[method](term, key, value)
            if retval:
                return retval
        else:
            raise ValueError(f"invalid search method {method!r}")


def starts_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'starts' will return value if key starts with the search term """
    return value if key.startswith(term) else ""

def ends_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'ends' will return value if key ends with the search term """
    return value if key.endswith(term) else ""

def contains_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'contains' will return 'value' if 'key' contains 'term' """
    return value if key in term else ""

def exact_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'exact' will return 'value' if 'key' == 'term' """
    return value if key == term else ""

def regex_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'regex' will return 'value' if regex pattern 'term' matches 'key' """
    return value if re.search(term, key) else ""

SEARCH_DISPATCH_TABLE["starts"] = starts_method
SEARCH_DISPATCH_TABLE["ends"] = ends_method
SEARCH_DISPATCH_TABLE["contains"] = contains_method
SEARCH_DISPATCH_TABLE["exact"] = exact_method
