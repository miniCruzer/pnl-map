"""
pywin32 Excel wrappers that are less ugly and cumbersome

>>> import os
>>>
>>> wb = workbook_load(os.path.abspath("testdata/Test.xlsx"))
>>>
>>> list(workbook_list_sheets(wb))
['Jan 17', 'Feb 17', 'Mar 17', 'Apr 17', 'May 17', 'Jun 17', 'Jul 17', 'Aug 17', 'Sep 17', 'Oct 17']
>>>
>>> sheet = worksheet_load(wb, "Jan 17")
>>> worksheet_cell_get(sheet, "B", 2)
'Ordinary Income/Expense'
>>> worksheet_cell_set(sheet, "Z", 1, "ok")
>>> worksheet_cell_get(sheet, "Z", 1)
'ok'
>>>
>>> workbook_close(wb)

"""

from typing import (Any, Dict, Generator,  # pylint: disable=unused-import
                    Iterable, Tuple)

import win32com.client as win32
from PyQt5.QtCore import QThread, pyqtSignal


def workbook_load(path: str, visible=True):
    """ load an excel workbook"""
    excel = win32.dynamic.Dispatch("Excel.Application")
    excel.Visible = visible
    excel.DisplayAlerts = False
    return excel.Workbooks.Open(path)


def workbook_close(workb):
    """ close an excel workbook object """
    workb.Close()


def workbook_list_sheets(workbk) -> Generator[str, None, None]:
    """ yield a list of all worksheet names in a workbook object """
    for sheet in workbk.Sheets:
        yield sheet.Name


def worksheet_load(workbk, name: str):
    """ load a worksheet object from a workbook object """
    return workbk.Worksheets(name)


def worksheet_cell_get(worksh, column: str, row: int) -> Any:
    """ get a value from a cell range """
    cell = column + str(row)
    return worksh.Range(cell).Value


def worksheet_cell_set(worksh, column: str, row: int, value: Any) -> None:
    """ set a cell in a wokrsheet object """
    cell = column + str(row)
    worksh.Range(cell).Value = value


def worksheet_set_number_format(worksh, column: str, row: int, fmt: str) -> None:
    """ set a cell's number format """
    cell = column + str(row)
    worksh.Range(cell).NumberFormat = fmt


def worksheet_cell_set_raw(worksh, column: str, row: int, value: Any) -> None:
    """ set a cell in a workhseet object using Value2 (no # detection) """
    cell = column + str(row)
    worksh.Range(cell).Value2 = value


def worksheet_iter(worksh, start_row: int, get_columns: tuple, until=None,
                   consecutive=4) -> Generator[Tuple[int, Dict[str, Any]], None, None]:
    """ iterate rows of a worksheet, yielding values of cells from each row.
    worksh - worksheet object to iterate
    start_row - row number >=1 to begin iterating
    get_columns - tuple of columns to retrieve values of
    until - dictionary columns to values - when all columns match these values, iteration will stop
    if empty, defaults to all None for get_columns
    consecutive - number of consecutive rows that must match 'until' to stop iteration
    """

    if not until:
        until = {column: None for column in get_columns}

    if start_row < 1:
        raise ValueError("must start at row >=1")

    row = start_row
    matches = 0

    while True:

        values = {}  # type: Dict[str, Any]

        for column in get_columns:
            value = worksheet_cell_get(worksh, column, row)
            values[column] = value

        if values == until:
            matches += 1
            if matches == consecutive:
                break
        else:
            matches = 0

        yield (row, values)

        row += 1


class ExcelThread(QThread):
    """ handle an excel spreadsheet in a thread """

    sheetOpened = pyqtSignal(str)
    rowsReady = pyqtSignal(str, dict, str)
    sheetNamesReady = pyqtSignal(list)

    def __init__(self, path, parent=None):
        super().__init__(parent)

        self.shutdown = False
        self.path = path
        self.pending_sheets = []
        self.pending_get = {}
        self.loaded_sheets = {}

        self.workbook = None

    def run(self):
        """ infinite loop in a thread that waits for insructions fro the main thread """
        self.workbook = workbook_load(self.path)
        self.sheetNamesReady.emit(list(workbook_list_sheets(self.workbook)))

        while True:

            if self.shutdown:
                break

            if self.pending_sheets:
                self._load_pending_sheets()

            if self.pending_get:
                self._process_pending_get()

            self.sleep(1)

        workbook_close(self.workbook)

    def _load_pending_sheets(self):
        for sheet in self.pending_sheets:
            if sheet in workbook_list_sheets(self.workbook):
                self.loaded_sheets[sheet] = worksheet_load(
                    self.workbook, sheet)
            else:
                self.rowsReady.emit(
                    sheet, {}, f"no such sheet {sheet} in workbook")
                continue

        self.pending_sheets = []

    def _process_pending_get(self):

        for sheet, columns in self.pending_get.items():

            if sheet not in self.loaded_sheets:
                if sheet in workbook_list_sheets(self.workbook):
                    self.loaded_sheets[sheet] = worksheet_load(
                        self.workbook, sheet)
                else:
                    self.rowsReady.emit(
                        sheet, {}, f"no such sheet {sheet} in workbook")
                    continue

            cells = {row: data for row, data in worksheet_iter(
                self.loaded_sheets[sheet], 1, columns, {column: None for column in columns})}

            self.rowsReady.emit(sheet, cells, "")

        self.pending_get = {}

    def get(self, sheet, columns):
        """ request values of 'columns' from 'sheet' using worksheet_iter. if 'sheet' has not yet
        been loaded, an attempt will be made to load the sheet. If the sheet name does not exist in
        the loaded workbook, resultReady will be instantly emitted with an empty dictionary. """
        self.pending_get[sheet] = columns


if __name__ == '__main__':
    import doctest
    doctest.testmod()
