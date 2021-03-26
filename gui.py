import sys


from PyQt5.QtWidgets import  QApplication, QHBoxLayout,QWidget , QTabWidget



from table_widget import RectTableWidget
from application import Application
from macro_photo_widget import MacroPhotoWidget
from slice_photo_widget import SlicePhotoWidget

class Gui(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent=parent
        self.app=Application(gui=self)
        self.initGUI()

    def initGUI(self):

        self.tabs = QTabWidget()


        self.rect_table_widget=RectTableWidget(app=self.app, logger=self.app.logger)
        self.macro_photo_widget=MacroPhotoWidget(parent=self.parent, app=self.app)

        self.slice_photo_widget=SlicePhotoWidget(parent=self.parent, app=self.app)

        self.tabs.addTab(self.macro_photo_widget, "MacroPhoto")
        self.tabs.addTab(self.slice_photo_widget, "Slice")


        layout= QHBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(self.rect_table_widget)
        self.logger=self.app.logger
        self.setLayout(layout)
        self.setWindowTitle('PCaVision Reconstruction Tool')
        self.show()


    def update(self):
        self.logger.info("updating GUI")
        self.rect_table_widget.update_table_widget()
        self.macro_photo_widget.paint()
        self.slice_photo_widget.paint()


if __name__ == "__main__":
    parent = QApplication(sys.argv)
    ex = Gui(parent)

    sys.exit(parent.exec_())