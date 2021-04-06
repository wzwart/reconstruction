import sys
import traceback
import numpy as np

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QLabel , QRubberBand , QApplication
from PyQt5.QtGui import QPixmap, QColor , QPainter , QKeyEvent

class MacroPhotoWidget(QLabel):

    def __init__(self, parent=None, app=None):

        QLabel.__init__(self)
        self.set_app(app)
        self.logger = app.logger
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)

        screen = parent.primaryScreen()
        screen_size = screen.size()
        self.origin_rubber_band = QPoint()

        self.setFixedWidth(int(screen_size.width()*.8))
        self.setFixedHeight(int(screen_size.height()*.95))
        self.position=QPoint(0, 0)
        self.paint()


    def set_app(self, app):
        self.app=app

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        alt = bool(modifiers & Qt.AltModifier)

        if event.button() == Qt.LeftButton and not alt:
            self.origin_rubber_band = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin_rubber_band, QSize()))
            self.rubberBand.show()

        if event.button() == Qt.RightButton:
            self.origin_position = QPoint(event.pos())

        if event.button() == Qt.LeftButton and alt:
            self.app.add_ruler_end(event.pos()+self.position)




    def mouseMoveEvent(self, event):

        if not self.origin_rubber_band.isNull():
            self.rubberBand.setGeometry(QRect(self.origin_rubber_band, event.pos()).normalized())

        if event.buttons() & Qt.RightButton:
            self.position = self.position + self.origin_position - QPoint(event.pos())
            self.origin_position = event.pos()
            self.paint()


    def mouseReleaseEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        alt = bool(modifiers & Qt.AltModifier)

        if event.button() == Qt.LeftButton and not alt:
            self.rubberBand.hide()

            rect=QRect(min(self.origin_rubber_band.x(), event.x())+self.position.x(), min(self.origin_rubber_band.y(), event.y())+self.position.y(), abs(event.x() - self.origin_rubber_band.x()), abs(event.y() - self.origin_rubber_band.y()))

            self.logger.info(f"{self.size()}, {rect}")
            self.app.add_slice(rect)
            self.paint()
        if event.button() == Qt.RightButton:
            self.paint()


    def paint(self):

        try:
            pixmap_bg = QPixmap(self.size())
            pixmap_bg.fill(QColor(50,50,250))

            painter = QPainter()
            painter.begin(pixmap_bg)
            self.app.say_hello()
            if not self.app.reconstruction is None:
                photo=self.app.reconstruction.macro_photo
                size_draw=QSize(min(self.width(),photo.size().width()),min(self.height(),photo.size().height()) )

                painter.setPen(Qt.red)
                font = painter.font()
                font.setPixelSize(48)
                painter.setFont(font)
                target=QRect(QPoint(0,0),size_draw)
                source=QRect(self.position, QPoint(size_draw.width(), size_draw.height()) + self.position)
                painter.drawPixmap(target, photo, source)

                for slice in self.app.reconstruction.slices:
                    painter.drawRect(slice.rect.x()-self.position.x(), slice.rect.y()-self.position.y(), slice.rect.width(), slice.rect.height())
                    coords=slice.rect.getCoords()
                    painter.drawText(QPoint(coords[0],coords[3]) - self.position, str(slice.id))

                if len(self.app.reconstruction.ruler_points) > 0:
                    painter.drawEllipse(self.app.reconstruction.ruler_points[0]-self.position, 10,10)
                if len(self.app.reconstruction.ruler_points) > 1:
                    p0=self.app.reconstruction.ruler_points[0]
                    p1=self.app.reconstruction.ruler_points[1]
                    painter.drawEllipse(p1-self.position, 10,10)
                    painter.drawLine(p0 - self.position, p1 - self.position,)
                    painter.drawLine(p0 - self.position,
                                     p1 - self.position)
                    p0_np = np.array(p0)
                    p1_np = np.array(p1)

                    # for i in range(13):

            painter.end()
            self.setPixmap(pixmap_bg)




        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass
