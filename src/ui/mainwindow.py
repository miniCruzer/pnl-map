# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui\mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 606)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.wizardCmd = QtWidgets.QCommandLinkButton(self.centralwidget)
        self.wizardCmd.setObjectName("wizardCmd")
        self.verticalLayout.addWidget(self.wizardCmd)
        self.mapEditCmd = QtWidgets.QCommandLinkButton(self.centralwidget)
        self.mapEditCmd.setObjectName("mapEditCmd")
        self.verticalLayout.addWidget(self.mapEditCmd)
        self.quitCmd = QtWidgets.QCommandLinkButton(self.centralwidget)
        self.quitCmd.setObjectName("quitCmd")
        self.verticalLayout.addWidget(self.quitCmd)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 600, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.quitCmd.clicked.connect(MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Popeyes P&L Converter"))
        self.wizardCmd.setText(_translate("MainWindow", "Conversion wizard"))
        self.wizardCmd.setDescription(_translate("MainWindow", "Convert a QuickBooks export to the Popeyes format."))
        self.mapEditCmd.setText(_translate("MainWindow", "Map files"))
        self.mapEditCmd.setDescription(_translate("MainWindow", "Create and edit company map files."))
        self.quitCmd.setText(_translate("MainWindow", "Quit"))
        self.quitCmd.setDescription(_translate("MainWindow", "Exit program."))

