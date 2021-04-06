import sys
import traceback
import importlib

from PyQt5.QtWidgets import  QApplication, QHBoxLayout,QWidget , QTabWidget , QTextEdit, QVBoxLayout
from PyQt5.QtGui import QKeyEvent , QCloseEvent , QTextCursor
from PyQt5.QtCore import Qt, QObject, pyqtSignal



from table_widget import RectTableWidget
from application import Application
from reconstruction import Reconstruction
from macro_photo_widget import MacroPhotoWidget
from slice_photo_widget import SlicePhotoWidget
from micro_table_widget import MicroTableWidget


class Gui(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent=parent
        self.logger_box = QTextEdit()
        self.logger_box.setUndoRedoEnabled(False)
        self.logger_box.setReadOnly(True)
        self.app=Application(gui=self)
        self.logger=self.app.logger
        self.initGUI()
        self.app.start()

    def initGUI(self):

        self.tabs_left = QTabWidget()
        self.macro_photo_widget = MacroPhotoWidget(parent=self.parent, app=self.app)
        self.slice_photo_widget = SlicePhotoWidget(parent=self.parent, app=self.app)
        self.tabs_left.addTab(self.macro_photo_widget, "MacroPhoto")
        self.tabs_left.addTab(self.slice_photo_widget, "Slice")

        self.tabs_right = QTabWidget()
        self.rect_table_widget = RectTableWidget(app=self.app, logger=self.app.logger)
        self.micro_table_widget = MicroTableWidget(app=self.app, logger=self.app.logger)
        self.tabs_right.addTab(self.rect_table_widget, "Macro")
        self.tabs_right.addTab(self.micro_table_widget, "Micro")

        top_layout = QHBoxLayout()
        vlayout = QVBoxLayout()
        top_layout.addWidget(self.tabs_left)
        vlayout.addWidget(self.tabs_right)
        vlayout.addWidget(self.logger_box)
        top_layout.addLayout(vlayout)

        self.logger=self.app.logger
        self.setLayout(top_layout)
        self.setWindowTitle('PCaVision Reconstruction Tool')
        self.show()


    def update(self):
        self.logger.debug("updating GUI")
        self.rect_table_widget.update_table_widget()
        self.macro_photo_widget.paint()
        self.slice_photo_widget.paint()
        self.micro_table_widget.update_table_widget()


    def keyPressEvent(self, event: QKeyEvent) -> None:
        try:
            self.logger.debug("Key Press")

            modifiers = QApplication.keyboardModifiers()
            control = bool(modifiers & Qt.ControlModifier)
            alt = bool(modifiers & Qt.AltModifier)
            shift = bool(modifiers & Qt.ShiftModifier)

            if event.key() in [Qt.Key_C] and control:
                self.app.logger.info("Calculate")
                if self.tabs_left.currentWidget()==self.slice_photo_widget:
                    self.app.calc_mask()
            elif event.key() in [Qt.Key_L] and control:
                self.app.logger.info("Load reconstructrion")
                self.app.load_reconstruction_from_pickle(file_name= r"reconstr.pkl")
            elif event.key() in [Qt.Key_S] and control:
                self.app.logger.info("Save reconstructrion")
                self.app.reconstruction.save_to_pickle(file_name= r"reconstr.pkl")
            elif event.key() in [Qt.Key_Z] and control:
                self.app.logger.info("Undo")
                if self.tabs_left.currentWidget() == self.slice_photo_widget:
                    self.app.logger.debug("Undo slice")
                    self.app.remove_latest_trace_from_active_slice()
            elif event.key() in [Qt.Key_R] and control and not alt:
                self.app.logger.info("Reload")
                self.reload()
            elif event.key() in [Qt.Key_R] and control and alt:
                self.app.logger.info("Reset")
                self.app=Application(self)
                self.update()
        except():
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass


    def connect(self):
        return

    def disconnect(self):
        return

    def reload(self):
        try:
            self.disconnect()
            import application
            self.logger.warning("reloading application")
            importlib.reload(application)
            from application import Application
            self.app = Application.create_copy(application=self.app)
            self.macro_photo_widget.set_app(self.app)
            self.slice_photo_widget.set_app(self.app)
            self.rect_table_widget.set_app(self.app)
            self.micro_table_widget.set_app(self.app)
            self.connect()
            self.update()

        except:
            print(sys.exc_info()[0])
            print(traceback.format_exc())
            pass



if __name__ == "__main__":
    parent = QApplication(sys.argv)
    ex = Gui(parent)

    sys.exit(parent.exec_())