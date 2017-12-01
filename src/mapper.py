""" map file instruction parser """

import os
import re
from typing import (Any, Callable, Dict,  # pylint: disable=unused-import
                    Iterable, List, Tuple)

from PyQt5.QtWidgets import (QComboBox, QDialog, QFileDialog, QMessageBox,
                             QTableWidgetItem)

from .ui.mapeditor import Ui_MapEditor

SEARCH_DISPATCH_TABLE = {}  # type: Dict[str, Callable]

MapDict = Dict[str, Tuple[str, str]]  # pylint: disable=C0103


class MapError(Exception):
    """ base exception for map file parsing errors """
    pass


def parse_map(text: List[str]) -> MapDict:
    """ parse a map file """
    map_regex = re.compile(r"^(.*) = ([^ ]+): (.*)$")

    sheetmap = {}

    for num, line in enumerate(text):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        res = map_regex.search(line)

        if not res:
            raise MapError(f"could not match line {num + 1}: {line!r}")

        dst = res.group(1)
        method = res.group(2).strip()
        search = res.group(3).strip()

        sheetmap[dst] = method, search

    return sheetmap


def longest(iterable: Iterable[Tuple]) -> int:
    """ return the longest length item in the iterable

    >>> longest(["a", "aa", "aaa", "aaaa"])
    4
    """
    length = 0
    for item in iterable:
        if len(item) > length:
            length = len(item)
    return length


def search_map(data_dict: Dict[str, Tuple], method: str, term: str) -> Any:
    """ search mapped data 'data_dict' for a

    >>> crew = ('17,776.98', '7,010.61', '12,407.40')
    >>> managers = ('7,614.43', '11,680.64', '9,689.94')
    >>> data = {
    ...     "5108 · Wages - Crew": crew,
    ...     "5109 · Salaries Managers" : managers,
    ... }
    >>> search_map(data, "starts", "5108") == crew
    True
    >>> search_map(data, "ends", "Wages - Crew") == crew
    True
    >>> search_map(data, "contains", "Wages") == crew
    True
    >>> search_map(data, "exact", "5109 · Salaries Managers") == managers
    True
    >>> search_map(data, "set", "0")
    ('0', '0', '0')
    >>> search_map(data, "each", "1,2,3")
    ['1', '2', '3']
    >>> search_map(data, "re", "^5109") == managers
    True
    >>> search_map(data, "fail", "5109")
    Traceback (most recent call last):
    ...
    MapError: invalid search method 'fail'
    """
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
            raise MapError(f"invalid search method {method!r}")


def starts_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'starts' will return value if key starts with the search term

    >>> starts_method("Hello", "Hello World", "squaids")
    'squaids'
    >>> starts_method("Bello", "Hello World", "squaids")
    ''
    """
    return value if key.startswith(term) else ""


def ends_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'ends' will return value if key ends with the search term

    >>> ends_method("World", "Hello World", "squaids")
    'squaids'
    >>> ends_method("Werld", "Hello World", "squaids")
    ''
    """
    return value if key.endswith(term) else ""


def contains_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'contains' will return 'value' if 'key' contains 'term'

    >>> contains_method("lo Wo", "Hello World", "squaids")
    'squaids'
    >>> contains_method("xxx", "Hello World", "squaids")
    ''
    """
    return value if term in key else ""


def exact_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'exact' will return 'value' if 'key' == 'term'

    >>> exact_method("Hello World", "Hello World", "squaids")
    'squaids'
    >>> exact_method("xxx", "Hello World", "squaids")
    ''
    """
    return value if key == term else ""


def regex_method(term: str, key: str, value: Any) -> str:
    """ Map file search method 'regex' will return 'value' if regex pattern 'term' matches 'key'

    >>> regex_method(r"Hello (?:World|Werld|Squidward)", "Hello World", "squaids")
    'squaids'
    >>> regex_method("xxx", "Hello World", "squaids")
    ''
    """
    return value if re.search(term, key) else ""


def ignore(term):
    return term


SEARCH_DISPATCH_TABLE["starts"] = starts_method
SEARCH_DISPATCH_TABLE["ends"] = ends_method
SEARCH_DISPATCH_TABLE["contains"] = contains_method
SEARCH_DISPATCH_TABLE["exact"] = exact_method
SEARCH_DISPATCH_TABLE["re"] = regex_method
SEARCH_DISPATCH_TABLE["set"] = ignore
SEARCH_DISPATCH_TABLE["each"] = ignore
# pylint: disable=C0103


NAME_COL = 0
METH_COL = 1
TERM_COL = 2


class MapEditor(Ui_MapEditor, QDialog):
    """ QDialog for map file editing """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.openMapButton.clicked.connect(self.openMap)
        self.saveMapButton.clicked.connect(self.saveMap)
        self.saveAsButton.clicked.connect(self.saveMapAs)
        self.newMapButton.clicked.connect(self.newMap)
        self.addRowButton.clicked.connect(self.newRow)
        self.delRowButton.clicked.connect(self.delRow)
        self.rowFilterLineEdit.textEdited.connect(self.filterRows)
        self.filterRegex.stateChanged.connect(self.filterChanged)

        self.dirty = False
        self.current = None
        self.defaultTitle = self.windowTitle()

    # signals

    def openMap(self):
        """ open map file """
        self.dirtyCheck()

        path = QFileDialog.getOpenFileName(
            self, "Open Map File", "", "Text Documents (*.txt)")

        if path[0]:

            mapfh = open(path[0], 'r')
            data = mapfh.readlines()
            mapfh.close()

            self.loadMap(parse_map(data))

            self.setWindowTitle(
                f"{self.defaultTitle} - {os.path.basename(path[0])}")

    def saveMapAs(self):
        """ save map to a specific file """
        path = QFileDialog.getSaveFileName(
            self, "Save Map File", "maps", "Text Documents (*.txt)")

        if not path[0]:
            return

        self.dumpMap(path[0])
        self.current = path[0]
        self.setWindowTitle(
            f"{self.defaultTitle} - {os.path.basename(self.current)}")
        self.dirty = False

    def saveMap(self):
        """ dump map table to the disk """
        if not self.current:
            self.saveMapAs()
        else:
            self.dumpMap(self.current)
            self.dirty = False

    def newMap(self):
        """ create a new map file """
        self.dirtyCheck()
        self.mapTable.clearContents()
        self.mapTable.setRowCount(0)
        self.dirty = False
        self.current = None
        self.setWindowTitle(self.defaultTitle)

    def newRow(self):
        """ add a row to the map table """
        self.dirty = True

        rows = self.mapTable.rowCount() + 1

        self.mapTable.setRowCount(rows)

        name = QTableWidgetItem()
        meths = QComboBox()
        meths.addItems(SEARCH_DISPATCH_TABLE.keys())
        term = QTableWidgetItem()

        self.mapTable.setItem(rows - 1, NAME_COL, name)
        self.mapTable.setCellWidget(rows - 1, METH_COL, meths)
        self.mapTable.setItem(rows - 1, TERM_COL, term)

    def delRow(self):
        """ delete the current selected row from the map table """
        self.dirty = True

        remove = set()

        for item in self.mapTable.selectedItems():
            remove.add(item.row())

        for row in remove:
            self.mapTable.removeRow(row)

    def filterChanged(self, state):
        """regex filter was toggled, re-run filter"""
        self.filterRows(self.rowFilterLineEdit.text())

    def filterRows(self, text):
        """loop through all rows, and see if "text" matches the row name by regex or contains"""

        for row in range(self.mapTable.rowCount()):

            hide = False

            if self.filterRegex.isChecked():
                if re.search(text, self.mapTable.item(row, NAME_COL).text()):
                    hide = False
                else:
                    hide = True

            else:
                if text.casefold() in self.mapTable.item(row, NAME_COL).text().casefold():
                    hide = False
                else:
                    hide = True

            self.mapTable.setRowHidden(row, hide)

    def makeDirty(self):
        """ make the table dirty """
        self.dirty = True

    # methods

    def loadMap(self, map_dict: MapDict):
        """ populate the map table with a parsed map dictionary """

        self.mapTable.setRowCount(len(map_dict))

        for row, (key, (method, search_term)) in enumerate(map_dict.items()):

            name = QTableWidgetItem(key)
            term = QTableWidgetItem(search_term)

            methbox = QComboBox()
            methbox.addItems(SEARCH_DISPATCH_TABLE.keys())

            if method in SEARCH_DISPATCH_TABLE:
                methbox.setCurrentText(method)

            methbox.currentIndexChanged.connect(self.makeDirty)

            self.mapTable.setItem(row, NAME_COL, name)
            self.mapTable.setCellWidget(row, METH_COL, methbox)
            self.mapTable.setItem(row, TERM_COL, term)

    def dumpMap(self, path):
        """ dump current map data to file at 'path' """

        mapfh = open(path, 'w')

        for row in range(self.mapTable.rowCount()):
            name = self.mapTable.item(row, NAME_COL).text()
            meth = self.mapTable.cellWidget(row, METH_COL).currentText()
            term = self.mapTable.item(row, TERM_COL).text()

            mapfh.write(f"{name} = {meth}: {term}\r\n")

        mapfh.close()

    def dirtyCheck(self):
        """Check if changes have been made to the current open table, and prompt user to save
        changes before proceeding with the next action."""

        if self.dirty:
            ans = QMessageBox.question(self,
                                       "Save changes?",
                                       "Would you like to save changes the current map file?")
            if ans == QMessageBox.Yes:
                self.saveMap()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
