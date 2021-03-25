import sys, traceback

from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QStyle
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

import logging

active_col = {"col": 0, "header": "Active"}
name_col = {"col": 1, "header": "Name"}
rect_col = {"col": 2, "header": "Rect"}
remove_col = {"col": 3, "header": "Del"}

cols = [active_col, name_col,rect_col,remove_col]


class RectTableWidget(QTableWidget):

    def __init__(self, app, logger=None):
        self.num_cols = len(cols)
        self.headers = [""] * self.num_cols
        for col in cols:
            self.headers[col["col"]] = col["header"]
        super(QTableWidget, self).__init__(0, self.num_cols)

        if not logger is None:
            self.logger = logger
        else:
            self.logger = logging.getLogger('QTable Logger')
            self.logger.setLevel(logging.ERROR)
            ch = logging.StreamHandler()
            self.logger.addHandler(ch)
        self.app = app

        self.cellClicked.connect(self.cell_clicked)
        self.cellPressed.connect(self.cell_pressed)

    def update_table_widget(self):
        try:

            if not len(self.app.rects) == self.rowCount():

                self.logger.debug(f"{len(self.app.rects)} != {self.rowCount()}")

                present_in_tablewidget = [False for i in range(len(self.app.rects))]
                present_in_active_rect = [False for i in range(self.rowCount())]
                for i, rect in enumerate(self.app.rects):
                    for j in range(self.rowCount()):
                        self.logger.debug(
                            f"{i} {j} {self.item(j, name_col['col']).text()}  {self.item(j, 0).rect == rect} ")
                        if self.item(j, name_col['col']).rect == rect:
                            present_in_tablewidget[i] = True
                            present_in_active_rect[j] = True

                for i, rect in enumerate(self.app.rects):
                    if not present_in_tablewidget[i]:
                        row_to_add = self.rowCount()
                        self.setRowCount(row_to_add + 1)
                        item = QTableWidgetItem(f"{rect.meta['name']}")
                        item.rect = rect
                        self.setItem(row_to_add, name_col['col'], item)

                        # checkBoxItem = QTableWidgetItem()
                        # checkBoxItem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                        # checkBoxItem.rect = rect
                        # self.setItem(row_to_add, visible_2d_col['col'], checkBoxItem)
                        #
                        # checkBoxItem = QTableWidgetItem()
                        # checkBoxItem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                        # checkBoxItem.rect = rect
                        # self.setItem(row_to_add, visible_3d_col['col'], checkBoxItem)
                        #
                        # activeItem = QTableWidgetItem()
                        # activeItem.rect = rect
                        # self.setItem(row_to_add, active_col['col'], activeItem)


                        remove_item = QTableWidgetItem("")
                        remove_item.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TrashIcon")))
                        remove_item.rect = rect
                        self.setItem(row_to_add, remove_col['col'], remove_item)

                self.setHorizontalHeaderLabels(self.headers)
                header = self.horizontalHeader()
                for i in range(self.num_cols - 1):
                    header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
                header.setSectionResizeMode(self.num_cols - 1, QHeaderView.Stretch)

                for j in range(len(present_in_active_rect)):
                    if not present_in_active_rect[j]:
                        self.removeRow(j)

            for j in range(self.rowCount()):
                if not self.item(j, name_col['col']) is None:
                    rect = self.item(j, name_col['col']).rect

                    # if hasattr(rect, "iou"):
                    #     self.item(j, iou_col['col']).setText(f"{rect.iou:.3}")
                    # self.item(j, volume_col['col']).setText(f"{rect.get_volume() / 1e3:.2f}")
                    #
                    # self.logger.debug(f"{j} {rect.meta['name']} {rect.visible_2d}")
                    # if self.item(j, name_col['col']).rect.visible_2d:
                    #     self.item(j, visible_2d_col['col']).setCheckState(Qt.Checked)
                    # else:
                    #     self.item(j, visible_2d_col['col']).setCheckState(Qt.Unchecked)
                    #
                    # if self.item(j, name_col['col']).rect.visible_3d:
                    #     self.item(j, visible_3d_col['col']).setCheckState(Qt.Checked)
                    # else:
                    #     self.item(j, visible_3d_col['col']).setCheckState(Qt.Unchecked)

                    if self.item(j, name_col['col']).rect == self.app.active_rect:
                        self.item(j, active_col['col']).setIcon(
                            self.style().standardIcon(getattr(QStyle, "SP_DialogApplyButton")))
                    else:
                        self.item(j, active_col['col']).setIcon(QIcon())
                else:
                    self.logger.warning(f" Weird: self.item({j},{name_col['col']}) is None")

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def cell_pressed(self, row, col):
        if col == active_col['col']:
            self.logger.info(f"activate  {row}")
            self.app.set_active_contour(self.item(row, name_col['col']).rect)

    def cell_clicked(self, row, col):
        try:
            self.logger.debug(f"clicked  {row},  {col}")
            item = self.item(row, col)
            if col == name_col['col']:
                self.logger.info(f"{item.rect.meta}")


            if col == remove_col['col']:
                confirmed = True
                if not confirmed:
                    confirmed = self.app.gui.Yes_Cancel(
                        f"Are you sure you want to delete {item.rect.meta['name']} ?") == "Yes"
                if confirmed:
                    self.app.active_rect.rects.remove_rect(rect=item.rect)
                    self.removeRow(row)
                    self.app.gui.update_tabs_contents()

                else:
                    self.logger.info("Cancelling removal")
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

