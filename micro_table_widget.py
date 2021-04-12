import sys, traceback

from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QStyle
from PyQt5.QtCore import Qt , QRect
from PyQt5.QtGui import QIcon , QPainter , QPixmap

import logging

name_col = {"col": 0, "header": "Image_ID"}
rect_col = {"col": 1, "header": "Rect"}
img_col = {"col": 2, "header": "Img"}


cols = [ name_col,rect_col,img_col]



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



class MicroTableWidget(QTableWidget):

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

        self.cellClicked.connect(self.cell_clicked)
        self.set_app(app)

    def set_app(self, app):
        self.app=app
        self.update_table_widget()


    def update_table_widget(self):
        try:
            if not self.app.reconstruction is None:
                micro_photos = self.app.reconstruction.micro_photos
            else:
                micro_photos =[]



            present_in_app = [False for i in range(len(micro_photos))]
            present_in_table_widget = [False for i in range(self.rowCount())]

            self.logger.info(f"We have {len(present_in_table_widget)} micro photos in the Micro Table Widget")
            self.logger.info(f"We have {len(present_in_app)} micro photos in the application")

            for i, micro_photo in enumerate(micro_photos):
                for j in range(self.rowCount()):
                    if self.item(j, name_col['col']).micro_photo == micro_photo:
                        present_in_app[i] = True
                        present_in_table_widget[j] = True

            for i, micro_photo_id in enumerate(micro_photos):
                micro_photo=micro_photos[micro_photo_id]
                if not present_in_app[i]:
                    self.logger.info(f"Adding micro photo {micro_photo} to Micro Table Widget")
                    row_to_add = self.rowCount()
                    self.setRowCount(row_to_add + 1)
                    self.setRowHeight(row_to_add, self.image_height)
                    item = QTableWidgetItem(f"{micro_photo.slide_score_image_id}")
                    item.micro_photo = micro_photo
                    self.setItem(row_to_add, name_col['col'], item)
                    if not hasattr(micro_photo, "size"):
                        self.logger.error("alert")
                    item = QTableWidgetItem(f"{micro_photo.size}")
                    item.micro_photo = micro_photo
                    self.setItem(row_to_add, rect_col['col'], item)

                    item = QTableWidgetItem(f"")
                    item.micro_photo = micro_photo
                    self.setItem(row_to_add, img_col['col'], item)
                    self.setCellWidget(row_to_add, img_col['col'], ImageWidget(image = micro_photo.pixmap, parent = self))

            for j in range(len(present_in_table_widget)-1,-1,-1):
                if not present_in_table_widget[j]:
                    self.logger.info(f"Remove micro photo {self.item(j, name_col['col'])} from Micro Table Widget")
                    self.removeRow(j)

            self.setHorizontalHeaderLabels(self.headers)
            header = self.horizontalHeader()
            for i in range(self.num_cols - 1):
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(self.num_cols - 1, QHeaderView.Stretch)




        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())



    def cell_clicked(self, row, col):
        try:

            item = self.item(row, col)
            self.app.reconstruction.active_micro_photo=item.micro_photo.slide_score_image_id
            self.logger.info(f"{self.app.reconstruction.active_micro_photo}")
            self.app.gui.tabs_left.setCurrentIndex(1)


        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

