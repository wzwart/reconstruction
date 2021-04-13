import logging
import sys
import traceback

from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHeaderView

#  column definition
# 'col' sets the columns number, 'header' defines the header string

name_col = {"col": 0, "header": "Image_ID"}
rect_col = {"col": 1, "header": "Rect"}
img_col = {"col": 2, "header": "Img"}

# the list of columns
cols = [name_col, rect_col, img_col]

class CoupeTableWidget(QTableWidget):

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
        self.app = app
        self.update_table_widget()

    def update_table_widget(self):
        '''

        Full update on table widget
        this method creates a list of all coupes in the application that are present in the widget: 
        coupes_in_app_present_in_widget
        and a second list of all coupes in the widget that are present in the app:
        coupes_in_widget_present_in_app
        any coupe in the app that is not present in the widget is added to the widget
        any coupe in the widget that is not present in the app is removed from the widget.
        :return:
        '''

        try:
            if not self.app.reconstruction is None:
                coupes = self.app.reconstruction.coupes
            else:
                coupes = []

            coupes_in_app_present_in_widget = [False for i in range(len(coupes))]
            coupes_in_widget_present_in_app = [False for i in range(self.rowCount())]

            self.logger.info(f"We have {len(coupes_in_widget_present_in_app)} coupes in the Coupe Table Widget")
            self.logger.info(f"We have {len(coupes_in_app_present_in_widget)} coupes in the application")

            for i, coupe in enumerate(coupes):
                for j in range(self.rowCount()):
                    if self.item(j, name_col['col']).coupe == coupe:
                        coupes_in_app_present_in_widget[i] = True
                        coupes_in_widget_present_in_app[j] = True

            for i, coupe_id in enumerate(coupes):
                coupe = coupes[coupe_id]
                if not coupes_in_app_present_in_widget[i]:
                    self.logger.info(f"Adding coupe {coupe} to Coupe Table Widget")
                    row_to_add = self.rowCount()
                    self.setRowCount(row_to_add + 1)
                    self.setRowHeight(row_to_add, self.image_height)
                    item = QTableWidgetItem(f"{coupe.slide_score_image_id}")
                    item.coupe = coupe
                    self.setItem(row_to_add, name_col['col'], item)
                    if not hasattr(coupe, "size"):
                        self.logger.error("alert")
                    item = QTableWidgetItem(f"{coupe.size}")
                    item.coupe = coupe
                    self.setItem(row_to_add, rect_col['col'], item)
                    item = QTableWidgetItem(f"")
                    item.coupe = coupe
                    self.setItem(row_to_add, img_col['col'], item)
                    self.setCellWidget(row_to_add, img_col['col'], ImageWidget(image=coupe.pixmap, parent=self))

            for j in range(len(coupes_in_widget_present_in_app) - 1, -1, -1):
                if not coupes_in_widget_present_in_app[j]:
                    self.logger.info(f"Remove coupe {self.item(j, name_col['col'])} from Coupe Table Widget")
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
            self.app.reconstruction.active_coupe = item.coupe.slide_score_image_id
            self.logger.info(f"{self.app.reconstruction.active_coupe}")
            self.app.gui.tabs_left.setCurrentIndex(1)


        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


class ImageWidget(QWidget):
    '''
    A simple class for rendering images of the coupes as part of the CoupeTableWidget
    '''

    def __init__(self, image, parent):
        super(ImageWidget, self).__init__(parent)
        self.image = image
        self.parent = parent
        self.setFixedWidth(self.parent.image_width)

    def paintEvent(self, event):
        painter = QPainter(self)
        # todo: retain aspect ratio
        target = QRect(0, 0, self.width(), self.height())
        source = QRect(0, 0, self.image.width(), self.image.height())
        painter.drawPixmap(target, self.image, source)

