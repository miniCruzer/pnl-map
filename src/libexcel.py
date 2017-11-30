"""
pywin32 Excel wrappers that are less ugly and cumbersome
"""

#
# Copyright (c) 2017 Samuel Hoffman
#
# sheetcore.py: read and write from sheets
#

from typing import (Any, Dict, Generator,  # pylint: disable=unused-import
                    Iterable, Tuple)

import win32com.client as win32


def workbook_load(path: str, visible=True):
    """ load an excel workbook """
    excel = win32.dynamic.Dispatch("Excel.Application")
    excel.Visible = visible
    excel.DisplayAlerts = False
    return excel.Workbooks.Open(path)


def workbook_close(workb):
    """ close an excel workbook object """
    workb.Close()


def workbook_list_sheets(workbk):
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


def worksheet_iter(worksh, start_row: int, get_columns: tuple, until: dict,
                   consecutive=3) -> Generator[Tuple[int, Dict[str, Any]], None, None]:
    """ iterate rows of a worksheet, yielding values of cells from each row.
    worksh - worksheet object to iterate
    start_row - row number >=1 to begin iterating
    get_columns - tuple of columns to retrieve values of
    until - dictionary columns to values - when all columns match these values, iteration will stop
    consecutive - number of consecutive rows that must match 'until' to stop iteration
    """

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
