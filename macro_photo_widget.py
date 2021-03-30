import sys
import traceback

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QLabel , QRubberBand
from PyQt5.QtGui import QPixmap, QColor , QPainter , QKeyEvent


class MacroPhotoWidget(QLabel):

    def __init__(self, parent=None, app=None):

        QLabel.__init__(self)
        self.app=app
        self.logger = app.logger
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)

        screen = parent.primaryScreen()
        screen_size = screen.size()
        self.origin = QPoint()

        self.setFixedWidth(int(screen_size.width()*.8))
        self.setFixedHeight(int(screen_size.height()*.95))
        self.paint()


    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):

        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()

            rect=QRect(min(self.origin.x(), event.x()),min(self.origin.y(), event.y()), abs(event.x()-self.origin.x()) ,abs(event.y()-self.origin.y()) )

            self.logger.info(f"{self.size()}, {rect}")
            self.app.add_slice(rect)
            self.paint()

    def paint(self):

        try:
            pixmap_bg = QPixmap(self.size())
            pixmap_bg.fill(QColor(50,50,250))

            painter = QPainter()
            painter.begin(pixmap_bg)
            photo=self.app.reconstruction.macro_photo
            size_draw=QSize(min(self.width(),photo.size().width()),min(self.height(),photo.size().height()) )

            painter.setPen(Qt.red)
            font = painter.font()
            font.setPixelSize(48)
            painter.setFont(font)

            painter.drawPixmap(QRect(QPoint(0,0),size_draw), photo, QRect(QPoint(0,0),size_draw))

            for slice in self.app.reconstruction.slices:
                painter.drawRect(slice.rect)
                coords=slice.rect.getCoords()
                painter.drawText(QPoint(coords[0],coords[3]), str(slice.id))

            painter.end()
            self.setPixmap(pixmap_bg)

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass
