import importlib
import sys
import traceback
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QTabWidget, QTextEdit, QVBoxLayout

from application import Application
from macro_photo_widget import MacroPhotoWidget
from coupe_table_widget import CoupeTableWidget
from slice_photo_widget import SlicePhotoWidget
from slice_table_widget import SliceTableWidget



class ReconstructionGui(QWidget):
    '''
    The main widget for the reconstruction gui
    '''

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.app = Application(gui=self)
        self.logger = self.app.logger
        self.init_gui()
        self.app.start()
        self.update()

    def init_gui(self):

        self.tabs_left = QTabWidget()
        self.macro_photo_widget = MacroPhotoWidget(parent=self.parent, app=self.app)
        self.slice_photo_widget = SlicePhotoWidget(parent=self.parent, app=self.app)
        self.tabs_left.addTab(self.macro_photo_widget, "MacroPhoto")
        self.tabs_left.addTab(self.slice_photo_widget, "Slice")

        self.tabs_right = QTabWidget()
        self.slice_table_widget = SliceTableWidget(app=self.app, logger=self.app.logger)
        self.coupe_table_widget = CoupeTableWidget(app=self.app, logger=self.app.logger)
        self.tabs_right.addTab(self.slice_table_widget, "Macro")
        self.tabs_right.addTab(self.coupe_table_widget, "Micro")


        self.logger_box = QTextEdit()
        self.logger_box.setUndoRedoEnabled(False)
        self.logger_box.setReadOnly(True)
        h = GuiLogger()
        h.edit = self.logger_box
        # attaching the logger box to the logger
        logging.getLogger().addHandler(h)

        top_layout = QHBoxLayout()
        vlayout = QVBoxLayout()
        top_layout.addWidget(self.tabs_left)
        vlayout.addWidget(self.tabs_right)
        vlayout.addWidget(self.logger_box)
        top_layout.addLayout(vlayout)

        self.logger = self.app.logger
        self.setLayout(top_layout)
        self.setWindowTitle('PCaVision Reconstruction Tool')
        self.show()

    def update(self):
        '''
        generic update function
        When called the gui is updated to the state as defined in the application and the reconstruction
        :return:
        '''
        self.logger.debug("Updating GUI")
        self.slice_table_widget.update_table_widget()
        self.coupe_table_widget.update_table_widget()
        self.macro_photo_widget.paint()
        self.slice_photo_widget.paint()
        return

    def keyReleaseEvent(self, event: QKeyEvent) -> None:

        try:
            self.logger.debug("Key Release")
            if event.key() in [Qt.Key_Control]:
                self.slice_photo_widget.paint(clear_coupe=True)
        except():
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass


    def keyPressEvent(self, event: QKeyEvent) -> None:

        '''
        The Key Press Event supports the following keys:


        Ctrl+C: Perform the semi-automatic foreground-background segmentation on slices
        Ctrl+L: Load a Reconstruction object from the pickle file (as configured in app.pickle_file_path)
        Alt+L:  Load a Reconstruction object from the json file (as configured in app.json_file_path)
        Ctrl+S: Save the Reconstruction object to the  pickle file (as configured in app.pickle_file_path)
        Alt+L:  Load a Reconstruction object to the json file (as configured in app.json_file_path)
        Ctrl+Z: Removes the latest trace from the slice
        Ctrl+R: Reloads and updates the code for the Application and the Reconstruction
        Alt+R:  Reset the state of the Application

        :param event:
        :return:
        '''


        try:
            self.logger.debug("Key Press")

            modifiers = QApplication.keyboardModifiers()
            control = bool(modifiers & Qt.ControlModifier)
            alt = bool(modifiers & Qt.AltModifier)
            shift = bool(modifiers & Qt.ShiftModifier)

            if event.key() in [Qt.Key_C] and control:
                self.app.logger.info("Calculate")
                if self.tabs_left.currentWidget() == self.slice_photo_widget:
                    self.app.calc_foreground_background_mask()
            elif event.key() in [Qt.Key_L] and control:
                self.app.logger.info("Load Reconstruction from pickle")
                self.app.load_reconstruction_from_pickle()
            elif event.key() in [Qt.Key_L] and alt:
                self.app.logger.info("Load Reconstruction from JSON")
                self.app.load_reconstruction_from_json()


            elif event.key() in [Qt.Key_S] and control:
                self.app.logger.info("Save Reconstruction as pickle")
                self.app.save_reconstruction_to_pickle()
            elif event.key() in [Qt.Key_S] and alt:
                self.app.logger.info("Save Reconstruction as JSON")
                self.app.save_reconstruction_as_json()
            elif event.key() in [Qt.Key_Z] and control:
                self.app.logger.info("Undo")
                if self.tabs_left.currentWidget() == self.slice_photo_widget:
                    self.app.logger.debug("Undo slice")
                    self.app.remove_latest_trace_from_active_slice()
            elif event.key() in [Qt.Key_R] and control and not alt:
                self.app.logger.info("Reload")
                self.reload(reset=False)
            elif event.key() in [Qt.Key_R] and control and alt:
                self.app.logger.info("Reset")
                self.reload(reset=True)
        except():
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            pass

    def connect(self):
        '''
        This function connects buttons/ keys to specific functions in the application
        this needs to be in a separate function, such that the application can be reloaded and re-attached to the buttons & keys
        Currently this function is still empty as there are no buttons/keys in the application
        :return:
        '''

        return

    def disconnect(self):
        '''
        This function disconnects buttons/ keys to specific functions in the application
        this needs to be in a separate function, such that the application can be reloaded and re-attached to the buttons & keys
        Currently this function is still empty as there are no buttons/keys in the application
        :return:
        '''

        return

    def reload(self, reset=True):
        '''
        The reload function reloads the application and its reconstruction
        This allows for updating the code while the GUI is active
        This function does not reload the
        :return:
        '''
        try:
            self.disconnect()
            import application
            self.logger.warning("Reloading Application")
            importlib.reload(application)
            from application import Application
            if reset:
                # create a new empty application
                self.app = Application(gui=self, logger=self.logger)
            else:
                # or create a copy of the existing application, but with functionality that is reloaded
                self.app = Application.create_copy(application=self.app)
            # add the new application for all widgets that use it
            self.macro_photo_widget.set_app(self.app)
            self.slice_photo_widget.set_app(self.app)
            self.slice_table_widget.set_app(self.app)
            self.coupe_table_widget.set_app(self.app)
            # reconnect buttons:
            self.connect()
            # and update the gui
            self.update()

        except:
            print(sys.exc_info()[0])
            print(traceback.format_exc())
            pass



class GuiLogger(logging.Handler):
    '''
    A class based on logging.handler, used for capturing the logger output and send it to the logger box
    '''
    def emit(self, record):
        self.edit.append(self.format(record))


if __name__ == "__main__":
    parent = QApplication(sys.argv)
    ex = ReconstructionGui(parent)
    sys.exit(parent.exec_())
