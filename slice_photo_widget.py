import sys
import traceback

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QLabel , QRubberBand ,QApplication
from PyQt5.QtGui import QPixmap, QColor , QPainter, QPolygon, QBrush


class SlicePhotoWidget(QLabel):

    def __init__(self, parent=None, app=None):

        QLabel.__init__(self)
        self.app=app
        self.logger = app.logger
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.setMouseTracking(True)
        self.origin = QPoint()
        self.slice = None
        self.paint()



    def mouseMoveEvent(self, event) :
        try:

            modifiers = QApplication.keyboardModifiers()
            control = bool(modifiers & Qt.ControlModifier)


            if event.buttons() & Qt.LeftButton:
                self.slice.add_to_trace(event.pos())
                self.logger.info(f"{event.pos()}")
                self.paint()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass







    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.slice.end_trace()

    def mousePressEvent(self, event):

        modifiers = QApplication.keyboardModifiers()
        control = bool(modifiers & Qt.ControlModifier)

        # if event.button() == Qt.LeftButton:
        #
        #
        #     point = QPoint(event.pos())
        #     if control:
        #         self.slice.inner_points.append(point)
        #     else:
        #         self.slice.outer_points.append(point)
        #     self.paint()

    def set_slice(self,slice):
        self.slice=slice




    def paint(self):

        try:
            pixmap_bg = QPixmap(self.size())
            pixmap_bg.fill(QColor(50,50,250))

            painter = QPainter()
            painter.begin(pixmap_bg)


            if not self.slice is None:
                self.slice.paint(painter=painter, size=self.size())

            painter.end()
            self.setPixmap(pixmap_bg)

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass
