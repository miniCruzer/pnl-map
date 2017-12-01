# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\preload.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PreloadRows(object):
    def setupUi(self, PreloadRows):
        PreloadRows.setObjectName("PreloadRows")
        PreloadRows.resize(302, 101)
        self.verticalLayout = QtWidgets.QVBoxLayout(PreloadRows)
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.sheetNameLabel = QtWidgets.QLabel(PreloadRows)
        self.sheetNameLabel.setObjectName("sheetNameLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.sheetNameLabel)
        self.sheetNamesComboBox = QtWidgets.QComboBox(PreloadRows)
        self.sheetNamesComboBox.setObjectName("sheetNamesComboBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.sheetNamesComboBox)
        self.columnLabel = QtWidgets.QLabel(PreloadRows)
        self.columnLabel.setObjectName("columnLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.columnLabel)
        self.columnLineEdit = QtWidgets.QLineEdit(PreloadRows)
        self.columnLineEdit.setObjectName("columnLineEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.columnLineEdit)
        self.verticalLayout.addLayout(self.formLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(PreloadRows)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(PreloadRows)
        self.buttonBox.accepted.connect(PreloadRows.accept)
        self.buttonBox.rejected.connect(PreloadRows.reject)
        QtCore.QMetaObject.connectSlotsByName(PreloadRows)

    def retranslateUi(self, PreloadRows):
        _translate = QtCore.QCoreApplication.translate
        PreloadRows.setWindowTitle(_translate("PreloadRows", "Dialog"))
        self.sheetNameLabel.setText(_translate("PreloadRows", "Sheet Name"))
        self.columnLabel.setText(_translate("PreloadRows", "Column"))
        self.columnLineEdit.setInputMask(_translate("PreloadRows", ">A"))
        self.columnLineEdit.setText(_translate("PreloadRows", "A"))

