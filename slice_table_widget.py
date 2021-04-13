import logging
import sys
import traceback

from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QHeaderView, QStyle

#  column definition
# 'col' sets the columns number, 'header' defines the header string

active_col = {"col": 0, "header": "Active"}
name_col = {"col": 1, "header": "Name"}
rect_col = {"col": 2, "header": "Rect"}
thumbnail_col = {"col": 3, "header": "Thumbnail"}
remove_col = {"col": 4, "header": "Del"}

# the list of columns
cols = [active_col, name_col, rect_col, thumbnail_col, remove_col]


class SliceTableWidget(QTableWidget):
    '''
    This is the widget on the right hand side, showing the individual Slices
    '''

    def __init__(self, app, logger=None):
        self.num_cols = len(cols)

        # setting the width and height of the thumbnails,
        # currently width and hieght are fixed values.
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

    def set_app(self, app):
        self.app = app
        self.update_table_widget()

    def update_table_widget(self):

        # full update on table widget
        # this method creates a list of all slices in the application that are present in the widget:
        # slices_in_app_present_in_widget
        # and a second list of all slices in the widget that are present in the app:
        # slices_in_widget_present_in_app
        # any slice in the app that is not present in the widget is added to the widget
        # any slice in the widget that is not present in the app is removed from the widget.


        try:
            if self.app.reconstruction is None:
                self.logger.info(f"Reconstruction is None")
                slices = []
            else:
                slices = self.app.reconstruction.slices
                macro_photo = self.app.reconstruction.macro_photo
                self.logger.debug(f"slices = {slices} ")

            slices_in_app_present_in_widget = [False for i in range(len(slices))]
            slices_in_widget_present_in_app = [False for i in range(self.rowCount())]

            self.logger.debug(f"We have {len(slices_in_widget_present_in_app)} slices in the Slice Table Widget")
            self.logger.debug(f"We have {len(slices_in_app_present_in_widget)} slices in the application")

            for i, slice in enumerate(slices):
                for j in range(self.rowCount()):
                    if self.item(j, name_col['col']).slice == slice:
                        self.logger.debug(f"Slice {slice.id} already present in  SLice Table Widget")
                        slices_in_app_present_in_widget[i] = True
                        slices_in_widget_present_in_app[j] = True

            for i, slice in enumerate(slices):
                if not slices_in_app_present_in_widget[i]:
                    self.logger.debug(f"Adding Slice {slice.id} to SLice Table Widget")
                    # this is where each row is formatted
                    row_to_add = self.rowCount()
                    self.setRowCount(row_to_add + 1)
                    self.setRowHeight(row_to_add, self.image_height)

                    # the column with the dimensions:

                    item = QTableWidgetItem(f"{slice.id}")
                    item.slice = slice
                    self.setItem(row_to_add, name_col['col'], item)

                    # the column with the dimensions:
                    item = QTableWidgetItem(f"{list(slice.rect.getCoords())}")
                    item.slice = slice
                    self.setItem(row_to_add, rect_col['col'], item)

                    # the column with the thumbnail:

                    item = QTableWidgetItem(f"")
                    item.slice = slice
                    self.setItem(row_to_add, thumbnail_col['col'], item)
                    self.setCellWidget(row_to_add, thumbnail_col['col'],
                                       SliceThumbnailWidget(image=macro_photo.copy(slice.rect), parent=self))
                    # the column with the trash-bin:
                    remove_item = QTableWidgetItem("")
                    # showing the trash bin icon
                    remove_item.setIcon(self.style().standardIcon(getattr(QStyle, "SP_TrashIcon")))
                    remove_item.slice = slice
                    self.setItem(row_to_add, remove_col['col'], remove_item)

            for j in range(len(slices_in_widget_present_in_app) - 1, -1, -1):
                if not slices_in_widget_present_in_app[j]:
                    self.logger.info(f"Remove Slice {self.item(j, name_col['col'])} from Slice Table Widget")
                    self.removeRow(j)

            # adding the headers
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
            self.logger.debug(f"clicked  {row},  {col}")
            item = self.item(row, col)
            if col in [name_col['col'], thumbnail_col['col']]:
                self.logger.info(f"{item.slice.rect}")
                self.app.set_active_slice_by_id(item.slice.id)
                # activate the correct on the left hand side (not the macro photo, but the slices)
                self.app.gui.tabs_left.setCurrentIndex(1)
            # if the trash bin is clicked in the remove column, the respective slice is removed from the widget.
            if col == remove_col['col']:
                id = item.slice.id
                self.removeRow(row)
                self.app.delete_slice(id=id)
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


class SliceThumbnailWidget(QWidget):
    '''
    A simple class for showing thumbnails of the slices as part of the Slice Table Widget
    '''

    def __init__(self, image, parent):
        super(SliceThumbnailWidget, self).__init__(parent)
        self.image = image
        self.parent = parent
        self.setFixedWidth(self.parent.image_width)

    def paintEvent(self, event):
        painter = QPainter(self)
        # ToDo: retain aspect ratio
        target = QRect(0, 0, self.width(), self.height())
        source = QRect(0, 0, self.image.width(), self.image.height())
        painter.drawPixmap(target, self.image, source)
