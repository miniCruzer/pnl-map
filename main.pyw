""" main """

import sys

from PyQt5.QtWidgets import QApplication

from src.wizard import Wizard


def launch_gui():
    """ launch the GUI application and ignore all other command line arguments """

    app = QApplication(sys.argv)
    wizard = Wizard()
    wizard.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    launch_gui()
