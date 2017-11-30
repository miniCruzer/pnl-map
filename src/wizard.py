"""
QWizard for running through a full export from QuickBooks formatted data into the Popeyes specified
spreadsheet.
"""
import os

import pythoncom
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QComboBox, QFileDialog, QFormLayout, QHBoxLayout,
                             QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
                             QProgressBar, QPushButton, QSpinBox, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWizard,
                             QWizardPage)

from .libexcel import (workbook_close, workbook_list_sheets, workbook_load,
                       worksheet_cell_set_raw, worksheet_iter, worksheet_load,
                       worksheet_set_number_format)
from .mapper import parse_map, search_map

__version__ = "0.0.2"
__author__ = "Samuel Hoffman"

# pylint: disable=C0103

EXCEL_FILE_FILTER = "Excel (*.xlsx *.xlsm)"

SOURCE_FIELD_NAME = "QuickBooks Workbook"
DESTINATION_FIELD_NAME = "Popeyes P&L Workbook"
MAP_FIELD_NAME = "Map File"

DST_COL = 1
SRC_COL = 0

SRC_COLUMNS = ('C', 'D', 'E', 'F', 'G', 'H')
SRC_STOP = {"C": None, "D": None, "E": None, "F": None, "G": None, "H": None}
DST_COLUMNS = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K')
DST_STOP = {'A': None, 'B': None, 'C': None, 'D': None, 'E': None,
            'F': None, 'G': None, 'H': None, 'I': None, 'J': None, 'K': None}


class SheetLoaderThread(QThread):
    """ load spreadsheets' sheet names in a separate thread """
    resultReady = pyqtSignal(list)

    def __init__(self, srcbkpath, dstbkpath, table, parent=None):
        super(SheetLoaderThread, self).__init__(parent)

        self.srcbkpath = srcbkpath
        self.dstbkpath = dstbkpath
        self.table = table

    def run(self):

        pythoncom.CoInitialize()  # pylint: disable=E1101

        srcbk = workbook_load(self.srcbkpath)
        dstbk = workbook_load(self.dstbkpath)

        src_sheets = list(workbook_list_sheets(srcbk))
        dst_sheets = list(workbook_list_sheets(dstbk))

        rows = [(name, list(dst_sheets)) for name in src_sheets]

        workbook_close(srcbk)
        workbook_close(dstbk)

        self.resultReady.emit(rows)


class ConverterThread(QThread):

    """ separate thread for working with Excel """

    resultReady = pyqtSignal()
    completedSheet = pyqtSignal(str)

    def __init__(self, srcbk, dstbk, mapfile, sheet_map_src2dst, parent=None):
        super(ConverterThread, self).__init__(parent)

        self.srcbkpath = srcbk
        self.dstbkpath = dstbk
        self.mapfile = mapfile
        self.sheet_map_src2dst = sheet_map_src2dst

    def run(self):

        map_dict = {}
        pythoncom.CoInitialize()  # pylint: disable=E1101
        srcbk = workbook_load(self.srcbkpath)
        dstbk = workbook_load(self.dstbkpath)

        with open(self.mapfile) as fhandle:
            map_dict = parse_map(fhandle.readlines())

        for srcshname, dstshname in self.sheet_map_src2dst.items():

            srcsh = worksheet_load(srcbk, srcshname)
            dstsh = worksheet_load(dstbk, dstshname)

            source_data = {}

            for row, data in worksheet_iter(srcsh, 1, SRC_COLUMNS, SRC_STOP):

                key = data["E"] or data["D"] or data["C"] or str(row)
                values = data["F"], data["G"], data["H"]

                if any(values):
                    source_data[key] = values

            for row, data in worksheet_iter(dstsh, 1, DST_COLUMNS, DST_STOP):
                keyword = data['A']

                if not keyword:
                    continue

                if keyword and keyword not in map_dict:
                    continue

                if row > 5:
                    worksheet_set_number_format(
                        dstsh, "B", row, "#,##0.00;-#,##0.00")
                    worksheet_set_number_format(
                        dstsh, "D", row, "#,##0.00;-#,##0.00")
                    worksheet_set_number_format(
                        dstsh, "F", row, "#,##0.00;-#,##0.00")

                method, term = map_dict[keyword]

                values = search_map(source_data, method, term)
                if not values:
                    worksheet_cell_set_raw(dstsh, "B", row, "0")
                    worksheet_cell_set_raw(dstsh, "D", row, "0")
                    worksheet_cell_set_raw(dstsh, "F", row, "0")
                    continue

                worksheet_cell_set_raw(dstsh, "B", row, values[0])
                worksheet_cell_set_raw(dstsh, "D", row, values[1])
                worksheet_cell_set_raw(dstsh, "F", row, values[2])

            self.completedSheet.emit(dstsh.Name)

        workbook_close(srcbk)
        self.resultReady.emit()


def sheet_mapper(rows, tbl) -> QTableWidget:
    """ create a sheet mapping QTableWidget. used for matching destination column names with source
    column names """

    tbl.setColumnCount(2)
    tbl.setRowCount(len(rows))

    for idx, (name, dst_sheets) in enumerate(rows):

        # create item, make it uneditable
        item = QTableWidgetItem(name)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        tbl.setItem(idx, SRC_COL, item)

        # create a combo box to match the source sheet name with any destination sheet tname
        box = QComboBox(tbl)
        box.addItems(dst_sheets)
        tbl.setCellWidget(idx, DST_COL, box)
        box.setCurrentIndex(idx)

    return tbl


class IntroPage(QWizardPage):

    """ Simple introduction page for the Wizard. """

    def __init__(self, parent=None):
        super(IntroPage, self).__init__(parent=parent)

        self.setTitle("P&L Wizard")
        self.setSubTitle("This wizard will help you export QuickBooks P&L data into the Popeyes"
                         f" provided P&L workbook.\n\nv{__version__}")


class WorkbookPage(QWizardPage):

    """ Page for selection of source and destination workbooks """

    def __init__(self, parent=None):
        super(WorkbookPage, self).__init__(parent=parent)

        self.setTitle("P&L Wizard - Select Workbooks")
        self.setSubTitle("Use the browse buttons below to select the QuickBooks spreadsheet"
                         " (source) and then the Popeyes spreadsheet. Then select a map file from"
                         " the drop down list for the corresponding QuickBooks spreadsheet. Each"
                         " company will have a separate map file. <b>Make sure neither workbook is"
                         " already open in Excel before clicking Next!</b>")

        self.mainLayout = QFormLayout(self)
        self.setLayout(self.mainLayout)
        self.setCommitPage(True)
        self.setButtonText(QWizard.CommitButton, "Load Spreadsheets")

        # source workbook
        self.sourceBookPath = QLineEdit()
        self.browseSourceBook = QPushButton("Browse ...")
        self.browseSourceBook.clicked.connect(self.openSrcBook)

        srcLayout = QHBoxLayout()
        srcLayout.addWidget(self.sourceBookPath)
        srcLayout.addWidget(self.browseSourceBook)

        self.mainLayout.addRow("Source Workbook", srcLayout)

        # destination workbook
        self.destBookPath = QLineEdit()
        self.browseDestBook = QPushButton("Browse ...", self)
        self.browseDestBook.clicked.connect(self.openDstBook)

        dstLayout = QHBoxLayout()
        dstLayout.addWidget(self.destBookPath)
        dstLayout.addWidget(self.browseDestBook)

        self.mainLayout.addRow("Destination Workbook", dstLayout)

        # map files
        self.mapFileComboBox = QComboBox()
        for entry in os.scandir("maps"):
            name = os.path.basename(os.path.splitext(entry.name)[0]).title()
            self.mapFileComboBox.addItem(name, entry.path)

        self.mainLayout.addRow("Map File", self.mapFileComboBox)

        self.registerField(SOURCE_FIELD_NAME + "*", self.sourceBookPath)
        self.registerField(DESTINATION_FIELD_NAME + "*", self.destBookPath)

        # validation failure reasons
        self.invalidSrc = QLabel(
            "<font color='red'>Unable to find source workbook.</font>")
        self.invalidDst = QLabel(
            "<font color='red'>Unable to find destination workbook.</font>")
        self.invalidMap = QLabel(
            "<font color='red'>Unable to find map file.</font>")

        self.invalidSrc.hide()
        self.invalidDst.hide()
        self.invalidMap.hide()

        self.mainLayout.addWidget(self.invalidSrc)
        self.mainLayout.addWidget(self.invalidDst)
        self.mainLayout.addWidget(self.invalidMap)

    def initializePage(self):
        """ reimplemented function """
        self.wizard().mapFileBx = self.mapFileComboBox

    def validatePage(self):
        """ used by Qt to validate the page completeness """
        srcpath = os.path.isfile(self.sourceBookPath.text())
        dstpath = os.path.isfile(self.destBookPath.text())
        mappath = os.path.isfile(self.mapFileComboBox.currentData())

        self.invalidSrc.setHidden(srcpath)
        self.invalidDst.setHidden(dstpath)
        self.invalidMap.setHidden(mappath)

        if self.sourceBookPath.text() == self.destBookPath.text():
            QMessageBox.critical(
                self, "Error", "Source workbook and destination workbook cannot be the same.")
            return False

        return srcpath and dstpath and mappath

    def openSrcBook(self):
        """ browse to the file path for the source book then update appropriate labels """
        path = QFileDialog.getOpenFileName(
            self, "Open Source Workbook", "", EXCEL_FILE_FILTER)
        if path:
            self.sourceBookPath.setText(os.path.normpath(path[0]))

    def openDstBook(self):
        """ browse to the file path for the destination book then update appropriate labels """
        path = QFileDialog.getOpenFileName(
            self, "Open Destination Workbook", "", EXCEL_FILE_FILTER)
        if path:
            self.destBookPath.setText(os.path.normpath(path[0]))


class SheetMapPage(QWizardPage):

    """ worksheet mapping page """

    def __init__(self, parent=None):
        super(SheetMapPage, self).__init__(parent=parent)

        self.setTitle("P&L Wizard - Map Worksheets")
        self.setSubTitle("Use the following table to map worksheet names together in the QuickBooks"
                         " export (source) to the Popeyes spreadsheet (destination)")

        self.mainLayout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.mainLayout.addWidget(self.table)

        self.lastRowDst = QSpinBox()
        self.lastRowSrc = QSpinBox()
        self.setCommitPage(True)
        self.setButtonText(QWizard.CommitButton, "Convert")
        self.complete = False
        self.names = [""] * 2

    def initializePage(self):
        """ fire the sheet loader thread and wait for it to finish """

        srcpath = self.field(SOURCE_FIELD_NAME)
        dstpath = self.field(DESTINATION_FIELD_NAME)

        self.names[SRC_COL] = os.path.basename(srcpath)
        self.names[DST_COL] = os.path.basename(dstpath)

        thread = SheetLoaderThread(srcpath, dstpath, self.table, self)
        thread.resultReady.connect(self.sheetsLoaded)
        thread.start()

    def sheetsLoaded(self, rows):
        """ called when the sheet loader thread finished loading sheets from both workbooks """

        sheet_mapper(rows, self.table)
        self.table.setHorizontalHeaderLabels(self.names)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

        self.complete = True
        self.completeChanged.emit()
        self.wizard().table = self.table

    def isComplete(self):
        return self.complete


class ConvertPage(QWizardPage):

    def __init__(self, parent=None):
        super(ConvertPage, self).__init__(parent=parent)
        self.setTitle("P&L Wizard - Finished")
        self.setSubTitle(
            "Please wait while the spreadsheets are converted ...")

        self.mainLayout = QVBoxLayout(self)

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)

        self.pwindow = QPlainTextEdit(self)
        self.pwindow.setReadOnly(True)

        self.complete = False

        self.mainLayout.addWidget(self.pbar)
        self.mainLayout.addWidget(self.pwindow)

    def initializePage(self):
        sheet_map_src2dst = {}
        table = self.wizard().table

        srcpath = self.field(SOURCE_FIELD_NAME)
        dstpath = self.field(DESTINATION_FIELD_NAME)
        mapfile = self.wizard().mapFileBx.currentData()

        sheets = table.rowCount()

        for row in range(sheets):
            src = table.item(row, SRC_COL).text()
            dst = table.cellWidget(row, DST_COL).currentText()

            sheet_map_src2dst[src] = dst

        self.pbar.setMaximum(sheets)
        self.pbar.show()

        thread = ConverterThread(
            srcpath, dstpath, mapfile, sheet_map_src2dst, self)
        thread.completedSheet.connect(self.oneSheetDone)
        thread.resultReady.connect(self.conversionComplete)
        thread.start()

    def oneSheetDone(self, name):
        self.pwindow.setPlainText(
            self.pwindow.toPlainText() + f"Finished {name} ...\n")
        self.pbar.setValue(self.pbar.value() + 1)
        self.completeChanged.emit()

    def conversionComplete(self):
        self.complete = True
        self.completeChanged.emit()
        self.setSubTitle(
            "Conversion completed. The finished spreadsheet is open in Excel.")
        self.pwindow.setPlainText(
            self.pwindow.toPlainText() + f"Done.")

    def isComplete(self):
        return self.complete


class Wizard(QWizard):

    """ Base class for the Wizard """

    def __init__(self, parent=None):
        super(Wizard, self).__init__(parent=parent)

        self.table = None
        self.mapFileBx = None
        self.srcbk = None
        self.dstbk = None

        # prevents initializePage from running 2x
        self.setOption(QWizard.IndependentPages, True)
        self.setOption(QWizard.HaveHelpButton, False)

        # add pages
        self.addPage(IntroPage(self))
        self.addPage(WorkbookPage(self))
        self.addPage(SheetMapPage(self))
        self.addPage(ConvertPage(self))

        self.setWindowTitle("QuickBooks to Popeyes Exporter")
        self.resize(640, 700)
