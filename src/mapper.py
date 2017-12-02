""" map file instruction parser """

import json
import logging
import os
import re
import shutil
from typing import (Any, Callable, Dict,  # pylint: disable=unused-import
                    Generator, Iterable, List, Tuple)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QComboBox, QDialog, QFileDialog, QListWidgetItem,
                             QMessageBox, QTableWidgetItem)

from .libexcel import ExcelThread
from .ui import Ui_MapConfig, Ui_MapEditor, Ui_PreloadRows

SEARCH_DISPATCH_TABLE = {}  # type: Dict[str, Callable]

MapDict = Dict[str, Tuple[str, str]]  # pylint: disable=C0103


class MapError(Exception):
    """ base exception for map file parsing errors """
    pass


class DuplicateThread(Exception):
    """ raised when an attempt has been made to launch 2 ExcelThread objects at once """
    pass


class MapData:
    """ representation of a Map File with header data """

    def __init__(self, config: dict, data: MapDict) -> None:
        self.config = config
        self.data = data


MAP_REGEX = re.compile(r"^(?P<rowtitle>.*) = (?P<method>[^ ]+): (?P<term>.*)$")


def parse_map(text: str) -> MapData:
    """ parse a map file """

    try:
        config, data = text.split("__DATA__", 1)
    except ValueError:
        logging.exception(f"parsing map data failed: {text!r}")
        raise MapEditor("unable to split map file by header separator")

    sheetmap = {}

    for num, line in enumerate(data.split("\n")):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        res = MAP_REGEX.search(line)

        if not res:
            raise MapError(f"could not match line {num + 1}: {line!r}")

        dst = res.group("rowtitle")
        method = res.group("method").strip()
        search = res.group("term").strip()

        sheetmap[dst] = (method, search)

    return MapData(json.loads(config), sheetmap)


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
    """ placeholder for a search method """
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


class MapConfig(Ui_MapConfig, QDialog):
    """ configure map file header configuration """

    def __init__(self, config=None, parent=None) -> None:
        super().__init__(parent)
        self.setupUi(self)

        self.addSrcKeyButton.clicked.connect(self.addSrcKey)
        self.delSrcKeyButton.clicked.connect(self.delSrcKey)
        self.addSrcDataButton.clicked.connect(self.addSrcVal)
        self.delSrcDataButton.clicked.connect(self.delSrcVal)
        self.addDstKeyButton.clicked.connect(self.addDstKey)
        self.delDstKeyButton.clicked.connect(self.delDstKey)
        self.addDstDataButton.clicked.connect(self.addDstVal)
        self.delDstDataButton.clicked.connect(self.delDstVal)
        self.browseTemplateFile.clicked.connect(self.selectTemplateFile)

        if config and isinstance(config, dict):
            self._load_config(config)

    def _default_item(self) -> QListWidgetItem:
        item = QListWidgetItem()
        item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled)
        return item

    def _load_config(self, config: dict):

        try:

            self.srcKeyList.addItems(config['source_key_columns'].split(","))
            self.srcDataList.addItems(config['source_val_columns'].split(","))
            self.dstKeyList.addItems(
                config["destination_key_columns"].split(","))
            self.dstDataList.addItems(
                config["destination_val_columns"].split(","))

            self.templateLineEdit.setText(os.path.normpath(config["template"]))
            self.cellFormatLineEdit.setText(config["number_format"])
            self.fallbackValueLineEdit.setText(config["fallback_value"])

        except KeyError:
            logging.exception(
                f"failed to load config due to a missing directive. {config!r}")

    def addSrcKey(self):
        """ add a blank item to the source accounts box """
        item = self._default_item()
        self.srcKeyList.addItem(item)
        self.srcKeyList.editItem(item)
        logging.debug(f"added new blank source key. widget is now at row "
                      f"{self.srcKeyList.currentRow()}")

    def delSrcKey(self):
        """ delete selected item from source accounts box """
        item = self.srcKeyList.takeItem(self.srcKeyList.currentRow())
        logging.debug(f"deleted source key item {item.text()!r}, widget is now at row "
                      f"{self.srcKeyList.currentRow()}")

    def addSrcVal(self):
        """ add a blank item to the restaurant data box """
        item = self._default_item()
        self.srcDataList.addItem(item)
        self.srcDataList.editItem(item)
        logging.debug(f"added new blank source value. widget is now at row "
                      f"{self.srcDataList.currentRow()}")

    def delSrcVal(self):
        """ delete selected item from the restaurant data box """
        item = self.srcDataList.takeItem(self.srcDataList.currentRow())
        logging.debug(f"deleted source value item {item.text()!r}. widget is now at row "
                      f"{self.srcDataList.currentRow()}")

    def addDstKey(self):
        """ add a blank item to the template account box """
        item = self._default_item()
        self.dstKeyList.addItem(item)
        self.dstKeyList.editItem(item)
        logging.debug(f"added destination key item. widget is now at row "
                      f" {self.dstKeyList.currentRow()}")

    def delDstKey(self):
        """ delete selected item from the template account box """
        row = self.dstKeyList.currentRow()
        item = self.dstKeyList.takeItem(row)
        logging.debug(f"deleted destination key item {item.text()!r}. widget is now at row "
                      f"{self.dstKeyList.currentRow()}")

    def addDstVal(self):
        """ add item to the template restaurant data box """
        item = self._default_item()
        self.dstDataList.addItem(item)
        self.dstDataList.editItem(item)
        logging.debug(f"added destination value. widget is now at row "
                      f"{self.dstDataList.currentRow()}")

    def delDstVal(self):
        """ delete item form the template restaurant data box """
        item = self.dstDataList.takeItem(self.dstDataList.currentRow())
        logging.debug(f"deleted destination value {item.text()!r}. widget is now at row "
                      f"{self.dstDataList.currentRow()}")

    def selectTemplateFile(self):
        """ used to allow the user to browse to the template excel spreadsheet """
        path = QFileDialog.getOpenFileName(
            self, "Open", "templates", "Excel (*.xlsx)")
        if path[0]:
            logging.debug(f"set template file to {path[0]!r}")
            self.templateLineEdit.setText(os.path.normpath(path[0]))

    def _get_items(self, attr) -> Generator[str, None, None]:
        logging.debug(f"getting all items in {attr!r}")
        for row in range(attr.count()):
            yield attr.item(row).text()

    def getSrcKeys(self) -> List[str]:
        """ return all column letters in source accounts box """
        return list(self._get_items(self.srcKeyList))

    def getSrcVal(self) -> List[str]:
        """ return all column letters in source data box """
        return list(self._get_items(self.srcDataList))

    def getDstKeys(self) -> List[str]:
        """ return all column letters in template accounts box """
        return list(self._get_items(self.dstKeyList))

    def getDstVals(self) -> List[str]:
        """ return all column letters in tempalte data box """
        return list(self._get_items(self.dstDataList))


class PreloadRowsDialog(Ui_PreloadRows, QDialog):
    """ prompt user to input sheet name from which to load row titles """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

    def setSheets(self, sheets):
        """ set the sheet selection combo box """
        self.sheetNamesComboBox.addItems(sheets)


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
        self.preloadRowsButton.clicked.connect(self.preloadRowNames)
        self.configButton.clicked.connect(self.openMapConfig)

        self._dirty = False
        self.current = None
        self.config = {}
        self.defaultTitle = self.windowTitle()
        self.preloadThread = None
        self.preloadedRows = []
        self.preloadDialog = None
        self.cfgDialog = None
    # signals

    def openMap(self):
        """ open map file """
        if not self.dirtyCheck():
            return

        path = QFileDialog.getOpenFileName(
            self, "Open Map File", "maps", "Text Documents (*.txt)")

        if path[0]:
            path = path[0]

            logging.debug(f"attempting to open map file at {path}")

            mapfh = open(path, 'r')
            data = mapfh.read()
            mapfh.close()

            try:
                self.loadMap(parse_map(data))
            except MapError:
                logging.exception(f"map file {path!r} is corrupted")
                QMessageBox.critical(self, "Load error",
                                     "Unable to corrupted map file.")
                return

            self.setWindowTitle(
                f"{self.defaultTitle} - {os.path.basename(path)}")

            self.current = path
            self.dirty = False

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
        if not self.dirtyCheck():
            return
        self.mapTable.clearContents()
        self.mapTable.setRowCount(0)
        self.current = None
        self.config = None
        self.cfgDialog = None
        self.setWindowTitle(self.defaultTitle)

    @property
    def dirty(self):
        """property for marking map file changes as 'dirty' if changes have been made but not saved
        to the disk"""
        return self._dirty

    @dirty.setter
    def dirty(self, value):

        if value != self._dirty:
            self._dirty = value
            if value:
                logging.debug("mapfile has been marked dirty", stack_info=True)
                self.setWindowTitle(self.windowTitle() + "*")
            else:
                logging.info("mapfile has been marked clean")
                self.setWindowTitle(self.windowTitle().replace("*", ""))

    def newRow(self):
        """ add a row to the map table """
        self.dirty = True

        rows = self.mapTable.rowCount() + 1

        logging.debug(f"new row count for map table: {rows}")

        self.mapTable.setRowCount(rows)

        meths = QComboBox()
        meths.addItems(SEARCH_DISPATCH_TABLE.keys())
        meths.currentIndexChanged.connect(self.makeDirty)

        self.mapTable.setCellWidget(rows - 1, NAME_COL, self.makePreloadBox())
        self.mapTable.setCellWidget(rows - 1, METH_COL, meths)
        self.mapTable.setItem(rows - 1, TERM_COL, QTableWidgetItem())

        self.mapTable.scrollToBottom()

    def delRow(self):
        """ delete the current selected row from the map table """
        self.dirty = True

        remove = set()

        for item in self.mapTable.selectedItems():
            remove.add(item.row())

        logging.debug(f"removing row(s) {remove!r}")

        for row in remove:
            self.mapTable.removeRow(row)

    def filterChanged(self, state):  # pylint: disable=unused-argument
        """regex filter was toggled, re-run filter"""
        self.filterRows(self.rowFilterLineEdit.text())

    def filterRows(self, text):
        """loop through all rows, and see if "text" matches the row name by regex or contains"""

        for row in range(self.mapTable.rowCount()):

            hide = False

            cellText = self.mapTable.cellWidget(
                row, NAME_COL).currentText()

            if self.filterRegex.isChecked():

                try:
                    res = re.search(text, cellText)
                except:
                    return

                if res:
                    hide = False
                else:
                    hide = True

            else:
                if text.casefold() in cellText.casefold():
                    hide = False
                else:
                    hide = True

            self.mapTable.setRowHidden(row, hide)

    def preloadRowNames(self):
        """ used to prime the preloader thread and initialize the PreloadRowsDialog for loading
        possible row names into the map table's Row Name colum """
        name = QFileDialog.getOpenFileName(
            self, "Open Excel Spreadsheet", "templates", "Excel (*.xlsx)")

        if name[0]:

            self.preloadDialog = PreloadRowsDialog(self)
            self.preloadDialog.accepted.connect(self.preloadStart)
            self.preloadDialog.rejected.connect(self.preloadCancel)

            self.launchExcelThread(name[0])
            self.preloadThread.sheetNamesReady.connect(
                self.preloadDialog.setSheets)
            self.preloadThread.start()

            self.preloadDialog.exec_()

    def preloadStart(self):
        """ recieved requested sheet name and column from the user, request values from preloader
        thread """
        sheet = self.preloadDialog.sheetNamesComboBox.currentText()
        column = (self.preloadDialog.columnLineEdit.text(),)

        self.preloadThread.get(sheet, column)
        self.preloadThread(
            f"requesting column {column!r} from sheet {sheet!r}")

    def preloadCancel(self):
        """ cancel preload thread """
        logging.debug("requesting preloader thread to shutdown")
        self.preloadThread.shutdown = True

    def preloadRowsDone(self, sheet, rows, error):  # pylint: disable=unused-argument
        """ called from the preloader thread when all the cells requested were retrieved """
        self.preloadThread.shutdown = True
        self.preloadedRows.clear()

        if error:
            logging.debug(
                f"Excel Thread responded with: {error!r}", stack_info=True)
            QMessageBox.warning(self, "Row preloading error", "An error occurred while trying to"
                                f" preload cells: {error}")
            return

        for num in rows.values():
            for column in num.values():
                if column:
                    self.preloadedRows.append(column)

        for row in range(self.mapTable.rowCount()):

            box = self.mapTable.cellWidget(row, NAME_COL)
            box.currentIndexChanged.disconnect(self.makeDirty)

            txt = box.currentText()
            box.addItems(self.preloadedRows)
            box.setCurrentText(txt)
            box.currentIndexChanged.connect(self.makeDirty)

    def resetThread(self):
        """ called when the preloader thread exits for cleanup """
        self.preloadThread = None

    def makeDirty(self):
        """ make the table dirty """
        self.dirty = True

    def openMapConfig(self):
        """ open the config editor for the open map """

        self.cfgDialog = MapConfig(self.config, self)
        self.cfgDialog.accepted.connect(self.getConfigHeader)
        self.cfgDialog.exec_()

    def getConfigHeader(self):
        """ slot for when the config dialog is accepted; collect all header data """
        self.config['source_key_columns'] = ",".join(
            self.cfgDialog.getSrcKeys())
        self.config['source_val_columns'] = ",".join(
            self.cfgDialog.getSrcVal())
        self.config['destination_key_columns'] = ",".join(
            self.cfgDialog.getDstKeys())
        self.config['destination_val_columns'] = ",".join(
            self.cfgDialog.getDstVals())
        self.config['template'] = self.cfgDialog.templateLineEdit.text()
        self.config['fallback_value'] = self.cfgDialog.fallbackValueLineEdit.text()
        self.config['number_format'] = self.cfgDialog.cellFormatLineEdit.text()

    # methods

    def loadMap(self, map_dict: MapData):
        """ populate the map table with a parsed map dictionary """

        self.mapTable.setRowCount(len(map_dict.data))
        self.config = map_dict.config

        # if the appropriate configuration settings exist in the loaded map header, MapEditor should
        # attempt to preload cells from the template worksheet. if not, silently continue.
        # TODO: introduce the appropriate locks to make sure bad things don't happen whlie loading
        try:
            self.launchExcelThread(self.config["template"], self.config["default_sheet"],
                                   self.config["destination_key_columns"].split(","))
            self.preloadThread.start()
        except KeyError:
            logging.exception("unable to preload rows from template sheet due to incomplete config",
                              stack_info=True)

        for row, (key, (method, search_term)) in enumerate(map_dict.data.items()):

            methbox = QComboBox()
            methbox.addItems(SEARCH_DISPATCH_TABLE.keys())

            if method in SEARCH_DISPATCH_TABLE:
                methbox.setCurrentText(method)

            methbox.currentIndexChanged.connect(self.makeDirty)

            box = self.makePreloadBox()
            box.setCurrentText(key)

            self.mapTable.setCellWidget(row, NAME_COL, box)
            self.mapTable.setCellWidget(row, METH_COL, methbox)
            self.mapTable.setItem(row, TERM_COL, QTableWidgetItem(search_term))

    def dumpMap(self, path):
        """ dump current map data to file at 'path' - this performs an atomic save in case there's
        an Exception during the write process to prevent corrupting the previous version of the map
        file already on the disk """

        tmp = f"{path}.tmp"
        mapfh = open(tmp, 'w')

        json.dump(self.config, mapfh, indent=2)
        mapfh.write("\n__DATA__\n")

        for row in range(self.mapTable.rowCount()):
            name = self.mapTable.cellWidget(row, NAME_COL).currentText()
            meth = self.mapTable.cellWidget(row, METH_COL).currentText()
            term = self.mapTable.item(row, TERM_COL).text()

            mapfh.write(f"{name} = {meth}: {term}\r\n")

        mapfh.close()
        shutil.move(tmp, path)

    def dirtyCheck(self) -> bool:
        """Check if changes have been made to the current open table, and prompt user to save
        changes before proceeding with the next action.

        returns True to proceed and returns False to not proceed
        """

        logging.debug("entered dirty check", stack_info=True)

        if self.dirty:
            ans = QMessageBox.question(self,
                                       "Save changes?",
                                       "Would you like to save changes the current map file?",
                                       QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ans == QMessageBox.Save:
                logging.info("saving changes to map file")
                self.saveMap()
                self.dirty = False
                return True
            elif ans == QMessageBox.Cancel:
                logging.info("action canceled at save menu")
                return False
            logging.info("changes discarded")
        return True

    def makePreloadBox(self, txt=""):
        """ return a QComboBox of preloaded rows, if any """

        box = QComboBox()
        box.setEditable(True)
        box.addItems(self.preloadedRows)
        if txt:
            box.setCurrentText(txt)
        box.currentIndexChanged.connect(self.makeDirty)

        return box

    def launchExcelThread(self, path, sheet="", columns=None):
        """ bootstrap an Excel thread with the appropriate signals/slots. if 'sheet' and 'columns'
        parameters are passed, they will be sent to the ExcelThread before starting it """
        if self.preloadThread is not None:
            raise DuplicateThread("an ExcelThread is already running")

        self.preloadThread = ExcelThread(os.path.normpath(path), self)
        self.preloadThread.finished.connect(self.resetThread)

        self.preloadThread.rowsReady.connect(self.preloadRowsDone)

        if sheet and columns:
            self.preloadThread.get(sheet, columns)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
