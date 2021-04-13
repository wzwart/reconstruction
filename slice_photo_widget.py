import sys
import traceback

from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QPixmap, QColor, QPainter
from PyQt5.QtWidgets import QLabel, QRubberBand, QApplication


class SlicePhotoWidget(QLabel):
    '''
    The Slice Photo Widget is for showing a slice
    It
    '''

    def __init__(self, parent=None, app=None):

        QLabel.__init__(self)
        self.set_app(app)
        self.logger = app.logger
        self.setMouseTracking(True) # only when set to true we can capture mouse events within this widget.
        self.slice = None # a pointer to the slice we are rendering
        self.show_traces = True # a boolean flag, to indicate which rendering mode we are in: showing the traces,
        # or showing slice together with the mask.
        self.paint() #
        self.coupe_pos = QPoint(0, 0) # the position at which we render the coupe
        self.tracing=False # a boolean flag, indicating whether the user is drawing traces,
        # because the left-mouse button is pressed, or not

    def set_app(self, app):
        '''
        setting the app
        mainly used when reloadig the application, or when initializing the widget
        '''
        self.app = app
        self.set_slice(app.active_slice)

    def mouseMoveEvent(self, event):
        '''
        This widget catches it's own mouse events
        :param event: automatically provide input
        :return:
        '''
        try:
            modifiers = QApplication.keyboardModifiers()
            control = bool(modifiers & Qt.ControlModifier)
            if control:
                self.coupe_pos = event.pos()
                self.paint()
            if event.buttons() & Qt.LeftButton:
                if not self.tracing:
                    self.slice.start_trace()
                    self.tracing=True
                self.slice.add_to_trace(event.pos())
                self.paint()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass

    def mouseReleaseEvent(self, event):
        '''
        We catch the mouse release event as well as it marks the ent of tracing
        :param event:
        :return:
        '''
        if event.button() == Qt.LeftButton:
            self.tracing=False

    def set_slice(self, slice):
        self.slice = slice

    def set_show_traces(self, show_traces):
        self.show_traces = show_traces

    def paint(self, clear_coupe=False):
        '''

        :param clear_coupe: This is used to override the ctrl button
        In this way we can also call paint from the main gui when Ctrl button is released
        :return:
        '''
        try:

            pixmap_bg = QPixmap(self.size())
            pixmap_bg.fill(QColor(255, 255, 255))
            painter = QPainter()
            painter.begin(pixmap_bg)
            if not self.slice is None:
                self.slice.paint(painter=painter, size=self.size(), show_traces=self.show_traces)

            # was the ctrl button pressed?
            modifiers = QApplication.keyboardModifiers()
            ctrl = bool(modifiers & Qt.ControlModifier)

            # if so, do we need to show a transparent coupe?
            if ctrl and not clear_coupe:
                if not self.app.reconstruction is None:
                    if not self.app.reconstruction.active_coupe is None:
                        coupe = self.app.reconstruction.coupes[
                            self.app.reconstruction.active_coupe]
                        pixmap = coupe.pixmap_trans
                        source = QRect(0, 0, pixmap.width(), pixmap.height())
                        # an arbitrary zoom factor of 2 for now
                        target = QRect(self.coupe_pos.x(), self.coupe_pos.y(), pixmap.width() * 2, pixmap.height() * 2)
                        painter.drawPixmap(target, pixmap, source)
            painter.end()
            self.setPixmap(pixmap_bg)
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass
