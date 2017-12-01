""" main """

import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from src.mapper import MapEditor
from src.wizard import Wizard
from src.ui import Ui_MainWindow


class MainWindow(Ui_MainWindow, QMainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.wizardCmd.clicked.connect(self.launchWizard)
        self.mapEditCmd.clicked.connect(self.launchMapEditor)

    def launchWizard(self):
        """ launch the conversion wizard """
        wiz = Wizard(self)
        wiz.exec_()

    def launchMapEditor(self):
        """ launch the map editor """
        dialog = MapEditor(self)
        dialog.exec_()


def launch_gui():
    """ launch the GUI application and ignore all other command line arguments """

    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    launch_gui()
