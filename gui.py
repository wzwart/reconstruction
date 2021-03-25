import sys


from PyQt5.QtWidgets import  QApplication, QHBoxLayout,QWidget , QTabWidget



from table_widget import RectTableWidget
from application import Application
from macro_photo_widget import MacroFotoWidget

class Gui(QWidget):

    def __init__(self, parent):
        super().__init__()
        self.parent=parent
        self.app=Application(gui=self)
        self.initGUI()

    def initGUI(self):

        self.tabs = QTabWidget()


        self.rect_table_widget=RectTableWidget(app=self.app, logger=self.app.logger)
        self.macro_foto_widget=MacroFotoWidget(parent=self.parent, app=self.app)

        self.tabs.addTab(self.macro_foto_widget, "Features")

        layout= QHBoxLayout()
        layout.addWidget(self.tabs)
        layout.addWidget(self.rect_table_widget)
        self.logger=self.app.logger
        self.setLayout(layout)
        self.setWindowTitle('Absolute')
        self.show()



if __name__ == "__main__":
    parent = QApplication(sys.argv)
    ex = Gui(parent)

    sys.exit(parent.exec_())