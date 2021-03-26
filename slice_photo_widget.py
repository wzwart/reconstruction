import sys
import traceback

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QLabel , QRubberBand ,QApplication
from PyQt5.QtGui import QPixmap, QColor , QPainter, QPolygon


class SlicePhotoWidget(QLabel):

    def __init__(self, parent=None, app=None):

        QLabel.__init__(self)
        self.app=app
        self.logger = app.logger
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)

        self.origin = QPoint()
        self.slice = None
        self.paint()




    def mousePressEvent(self, event):

        modifiers = QApplication.keyboardModifiers()
        control = bool(modifiers & Qt.ControlModifier)

        if event.button() == Qt.LeftButton:

            point = QPoint(event.pos())
            if control:
                self.slice.inner_points.append(point)
            else:
                self.slice.outer_points.append(point)
            self.paint()

    def set_slice(self,slice):
        self.slice=slice



    def paint(self):

        try:
            pixmap_bg = QPixmap(self.size())
            pixmap_bg.fill(QColor(50,50,250))

            painter = QPainter()
            painter.begin(pixmap_bg)


            if not self.slice is None:
                photo=self.slice.slice_photo
                size_draw=QSize(min(self.width(),photo.width()),min(self.height(),photo.height()))



                painter.drawPixmap(QRect(QPoint(0,0),size_draw), photo, QRect(QPoint(0,0),size_draw))

                painter.setPen(Qt.green)
                painter.drawPolygon(QPolygon(self.slice.inner_points))
                painter.setPen(Qt.blue)
                painter.drawPolygon(QPolygon(self.slice.outer_points))



            painter.end()
            self.setPixmap(pixmap_bg)

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass
