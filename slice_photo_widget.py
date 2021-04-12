import sys
import traceback

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QLabel , QRubberBand ,QApplication
from PyQt5.QtGui import QPixmap, QColor , QPainter, QPolygon, QBrush


class SlicePhotoWidget(QLabel):

    def __init__(self, parent=None, app=None):

        QLabel.__init__(self)
        self.set_app(app)
        self.logger = app.logger
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.setMouseTracking(True)
        self.origin = QPoint()
        self.slice = None
        self.show_traces=True
        self.paint()
        self.pos=QPoint(0,0)


    def set_app(self, app):
        self.app=app
        self.set_slice(app.active_slice)



    def mouseMoveEvent(self, event) :
        try:

            modifiers = QApplication.keyboardModifiers()
            control = bool(modifiers & Qt.ControlModifier)

            if control:
                self.pos = event.pos()
                self.paint()

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


    def set_show_taces(self, show_traces):
        self.show_traces=show_traces


    def paint(self):

        try:
            pixmap_bg = QPixmap(self.size())
            pixmap_bg.fill(QColor(255,255,255))

            painter = QPainter()

            painter.begin(pixmap_bg)

            modifiers = QApplication.keyboardModifiers()
            ctrl = bool(modifiers & Qt.ControlModifier)


            if not self.slice is None:
                self.logger.info(f"self.show_traces = {self.show_traces}")
                self.slice.paint(painter=painter, size=self.size(), show_traces=self.show_traces)

            if ctrl:
                if not self.app.reconstruction.active_micro_photo is None:
                    micro_photo = self.app.reconstruction.micro_photos[str(self.app.reconstruction.active_micro_photo)]
                    pixmap=micro_photo.pixmap_trans
                    source=QRect(0,0,pixmap.width(), pixmap.height())
                    target=QRect(self.pos.x(),self.pos.y(),pixmap.width()*2,pixmap.height()*2)
                    painter.drawPixmap(target, pixmap, source)

            painter.end()
            self.setPixmap(pixmap_bg)

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass
