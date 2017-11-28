""" main """
#
# Copyright (c) 2017 Samuel Hoffman
#
# main.py: main entry point
#

import argparse
import os

from src.libexcel import (workbook_load,
                          worksheet_cell_set_raw, worksheet_iter,
                          worksheet_load, worksheet_set_number_format)
from src.mapper import parse_map, search_map


SHEET_MAP_NAME = {
    "Jan 17": "January",
    "Feb 17": "February",
    "Mar 17": "March",
    "Apr 17": "April",
    "May 17": "May",
    "Jun 17": "June",
    "Jul 17": "July",
    "Aug 17": "August",
    "Sep 17": "September",
    "Oct 17": "October"
}

def launch_gui():
    """ launch the GUI application and ignore all other command line arguments """
    from PyQt5.QtWidgets import QApplication
    import sys

    from src.wizard import Wizard

    app = QApplication(sys.argv)
    wizard = Wizard()
    wizard.show()

    sys.exit(app.exec_())

def main():
    """main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--sourcebook", help="Path to source Workbook")
    parser.add_argument("--destbook", help="Path to destination Workbook")
    parser.add_argument("--mapfile", help="Path to map file")
    parser.add_argument("--nogui", action='store_true', help="Do not launch GUI helper")

    args = parser.parse_args()

    if not args.nogui:
        launch_gui()

    map_dict = {}
    with open(args.mapfile) as mapfh:
        map_dict = parse_map(mapfh.readlines())

    srcbk = workbook_load(os.path.abspath(args.sourcebook))
    dstbk = workbook_load(os.path.abspath(args.destbook))

    src_columns = ("C", "D", "E", "F", "G", "H")
    source_stop = {"C": "", "D": "", "E": "", "F": "", "G": "", "H": ""}
    dest_columns = ("A",)

    for srcshname, dstshname in SHEET_MAP_NAME.items():

        srcsh = worksheet_load(srcbk, srcshname)
        dstsh = worksheet_load(dstbk, dstshname)

        source_data = {}

        for row, data in worksheet_iter(srcsh, 1, src_columns, source_stop, 40):

            key = data["E"] or data["D"] or data["C"] or str(row)
            values = data["F"], data["G"], data["H"]

            if any(values):
                source_data[key] = values

        # workbook_close(srcbk)

        for row, data in worksheet_iter(dstsh, 5, dest_columns, {}, 72):
            keyword = data['A']

            if not keyword:
                continue

            if keyword and keyword not in map_dict:
                continue

            if row != 5:
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


if __name__ == "__main__":
    main()
