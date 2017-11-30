# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\mapeditor.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MapEditor(object):
    def setupUi(self, MapEditor):
        MapEditor.setObjectName("MapEditor")
        MapEditor.resize(563, 575)
        self.verticalLayout = QtWidgets.QVBoxLayout(MapEditor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.mapTable = QtWidgets.QTableWidget(MapEditor)
        self.mapTable.setObjectName("mapTable")
        self.mapTable.setColumnCount(3)
        self.mapTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.mapTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.mapTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.mapTable.setHorizontalHeaderItem(2, item)
        self.mapTable.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout.addWidget(self.mapTable)
        self.splitter_2 = QtWidgets.QSplitter(MapEditor)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName("splitter_2")
        self.addRowButton = QtWidgets.QPushButton(self.splitter_2)
        self.addRowButton.setObjectName("addRowButton")
        self.delRowButton = QtWidgets.QPushButton(self.splitter_2)
        self.delRowButton.setObjectName("delRowButton")
        self.verticalLayout.addWidget(self.splitter_2)
        self.splitter = QtWidgets.QSplitter(MapEditor)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.saveMapButton = QtWidgets.QPushButton(self.splitter)
        self.saveMapButton.setObjectName("saveMapButton")
        self.saveAsButton = QtWidgets.QPushButton(self.splitter)
        self.saveAsButton.setObjectName("saveAsButton")
        self.openMapButton = QtWidgets.QPushButton(self.splitter)
        self.openMapButton.setObjectName("openMapButton")
        self.newMapButton = QtWidgets.QPushButton(self.splitter)
        self.newMapButton.setObjectName("newMapButton")
        self.verticalLayout.addWidget(self.splitter)

        self.retranslateUi(MapEditor)
        QtCore.QMetaObject.connectSlotsByName(MapEditor)

    def retranslateUi(self, MapEditor):
        _translate = QtCore.QCoreApplication.translate
        MapEditor.setWindowTitle(_translate("MapEditor", "Dialog"))
        item = self.mapTable.horizontalHeaderItem(0)
        item.setText(_translate("MapEditor", "Row Name"))
        item = self.mapTable.horizontalHeaderItem(1)
        item.setText(_translate("MapEditor", "Search Method"))
        item = self.mapTable.horizontalHeaderItem(2)
        item.setText(_translate("MapEditor", "Search Term"))
        self.addRowButton.setText(_translate("MapEditor", "Add"))
        self.delRowButton.setText(_translate("MapEditor", "Delete"))
        self.saveMapButton.setText(_translate("MapEditor", "Save"))
        self.saveAsButton.setText(_translate("MapEditor", "Save As ..."))
        self.openMapButton.setText(_translate("MapEditor", "Open"))
        self.newMapButton.setText(_translate("MapEditor", "New"))

