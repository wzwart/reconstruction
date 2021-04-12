import sys, traceback

from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QStyle
from PyQt5.QtCore import Qt , QRect
from PyQt5.QtGui import QIcon , QPainter , QPixmap

import logging

active_col = {"col": 0, "header": "Active"}
name_col = {"col": 1, "header": "Name"}
rect_col = {"col": 2, "header": "Rect"}
img_col = {"col": 3, "header": "Img"}
remove_col = {"col": 4, "header": "Del"}

cols = [active_col, name_col,rect_col,img_col,remove_col]



class ImageWidget(QWidget):

    def __init__(self, image, parent):
        super(ImageWidget, self).__init__(parent)
        self.image = image
        self.parent=parent
        self.setFixedWidth(self.parent.image_width)


    def paintEvent(self, event):
        painter = QPainter(self)
        target=  QRect(0,0,self.width(), self.height())
        source=  QRect(0,0,self.image.width(), self.image.height())
        painter.drawPixmap(target, self.image, source)



class SliceTableWidget(QTableWidget):

    def __init__(self, app, logger=None):
        self.num_cols = len(cols)

        self.image_width = 300
        self.image_height = 300


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
        self.set_app(app)

        self.cellClicked.connect(self.cell_clicked)
        self.cellPressed.connect(self.cell_pressed)


    def set_app(self, app):
        self.app=app
        self.update_table_widget()

    def update_table_widget(self):
        try:
            if self.app.reconstruction is None:
                self.logger.info(f"Reconstruction is None")
                slices = []
            else:
                slices = self.app.reconstruction.slices
                macro_photo=self.app.reconstruction.macro_photo
                self.logger.info(f"slices = {slices} ")

            present_in_app = [False for i in range(len(slices))]
            present_in_table_widget = [False for i in range(self.rowCount())]


            self.logger.info(f"We have {len(present_in_table_widget)} slices in the Slice Table Widget")
            self.logger.info(f"We have {len(present_in_app)} slices in the application")

            for i, slice in enumerate(slices):
                for j in range(self.rowCount()):
                    if self.item(j, name_col['col']).slice == slice:
                        self.logger.info(f"Slice {slice.id} already present in  SLice Table Widget")
                        present_in_app[i] = True
                        present_in_table_widget[j] = True

            for i, slice in enumerate(slices):
                if not present_in_app[i]:
                    self.logger.info(f"Adding Slice {slice.id} to SLice Table Widget")
                    row_to_add = self.rowCount()
                    self.setRowCount(row_to_add + 1)
                    self.setRowHeight(row_to_add, self.image_height)
                    item = QTableWidgetItem(f"{slice.id}")
                    item.slice = slice
                    self.setItem(row_to_add, name_col['col'], item)

                    item = QTableWidgetItem(f"{list(slice.rect.getCoords())}")
                    item.slice = slice
                    self.setItem(row_to_add, rect_col['col'], item)

                    item = QTableWidgetItem(f"")
                    item.slice = slice
                    self.setItem(row_to_add, img_col['col'], item)
                    self.setCellWidget(row_to_add, img_col['col'], ImageWidget(image = macro_photo.copy(slice.rect), parent = self))

                    remove_item = QTableWidgetItem("")
                    remove_item.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TrashIcon")))
                    remove_item.slice = slice
                    self.setItem(row_to_add, remove_col['col'], remove_item)




            for j in range(len(present_in_table_widget)-1,-1,-1):
                if not present_in_table_widget[j]:
                    self.logger.info(f"Remove Slice {self.item(j, name_col['col'])} from Slice Table Widget")
                    self.removeRow(j)

            self.setHorizontalHeaderLabels(self.headers)
            header = self.horizontalHeader()
            for i in range(self.num_cols - 1):
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(self.num_cols - 1, QHeaderView.Stretch)


        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def cell_pressed(self, row, col):
        if col == active_col['col']:
            self.logger.info(f"activate  {row}")
            self.app.set_active_contour(self.item(row, name_col['col']).slice)

    def cell_clicked(self, row, col):
        try:
            self.logger.debug(f"clicked  {row},  {col}")
            item = self.item(row, col)
            if col in  [name_col['col'], img_col['col']] :
                self.logger.info(f"{item.slice.rect}")
                self.app.set_active_slice_by_id(item.slice.id)
                self.app.gui.tabs_left.setCurrentIndex(1)


            if col == remove_col['col']:
                id = item.slice.id
                self.removeRow(row)
                self.app.delete_slice(id=id)

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

