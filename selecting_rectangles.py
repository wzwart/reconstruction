import random, sys, traceback
import logging
from pathlib import Path

from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QLabel , QRubberBand, QApplication, QHBoxLayout,QWidget
from PyQt5.QtGui import *


from table_widget import RectTableWidget

class Example(QWidget):

    def __init__(self, app):
        super().__init__()
        self.app=app



        self.initUI()

    def initUI(self):

        lbl1 = QLabel('ZetCode', self)
        rect_table_widget=RectTableWidget(app=self.app,logger=app.logger )
        window=Window(self.app)
        layout= QHBoxLayout()
        layout.addWidget(window)
        layout.addWidget(rect_table_widget)
        self.logger=self.app.logger
        self.setLayout(layout)
        self.setWindowTitle('Absolute')
        self.show()




class Window(QLabel):

    def __init__(self, parent=None):

        QLabel.__init__(self)

        self.macro_photo = QPixmap(r".\..\macro_photos\macro_1.jpg")

        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        screen = parent.primaryScreen()
        screen_size = screen.size()

        self.origin = QPoint()
        self.logger=parent.logger

        self.setFixedWidth(int(screen_size.width()*.8))
        self.setFixedHeight(int(screen_size.height()*.8))
        self.create_pixmap(size=self.size())


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
            self.create_pixmap(size=self.size(), rect=rect)


    def create_pixmap(self, size, rect=None):

        try:


            pixmap_bg = QPixmap(size)
            pixmap_bg.fill(QColor(50,50,250))

            painter = QPainter()
            painter.begin(pixmap_bg)
            size_draw=QSize(min(size.width(),self.macro_photo.size().width()),min(size.height(),self.macro_photo.size().height()) )
            self.logger.info(f"Hi {size_draw}")
            painter.drawPixmap(QRect(QPoint(0,0),size_draw), self.macro_photo, QRect(QPoint(0,0),size_draw))

            if rect is  None:
                target=  QRect(0,0,100, 100)
                source = QRect(0,0,100, 100)
            else:
                target = rect
                source = rect
            painter.end()
            self.setPixmap(pixmap_bg)

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass





if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.logger = logging.getLogger('session data main')
    app.logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    app.log_file = Path("log/gui.log")
    app.log_file.parent.mkdir(parents=True, exist_ok=True)

    ch_file = logging.FileHandler(app.log_file, mode='w+')
    ch_file.setLevel(logging.DEBUG)
    formatter_file = logging.Formatter('%(levelname)s - %(message)s')
    ch_file.setFormatter(formatter_file)

    app.logger.addHandler(ch)
    app.logger.addHandler(ch_file)

    ex = Example(app)

    sys.exit(app.exec_())