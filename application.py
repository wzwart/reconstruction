import logging 
import sys
import traceback
import importlib
from pathlib import Path

from reconstruction import Reconstruction



class GuiLogger(logging.Handler):
    def emit(self, record):
        self.edit.append(self.format(record))  # implementation of append_line omitted


class Application():
    def __init__(self, gui,  config_file="config.ini",logger= None ):

        self.gui = gui
        self.config_file = config_file

        self.reconstruction = None
        self.active_slice = None

        if logger is None:
            self.logger = logging.getLogger('session data main')
            self.logger.setLevel(logging.DEBUG)
            h = GuiLogger()
            #todo consider whether gui.logger_box should be explicitly mentioned here
            h.edit = self.gui.logger_box
            logging.getLogger().addHandler(h)
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.log_file = Path("log/gui.log")
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            ch_file = logging.FileHandler(self.log_file, mode='w+')
            ch_file.setLevel(logging.DEBUG)
            formatter_file = logging.Formatter('%(levelname)s - %(message)s')
            ch_file.setFormatter(formatter_file)
            self.logger.addHandler(ch)
            self.logger.addHandler(ch_file)
        else:
            self.logger=logger

        self.path_macro_photo=r".\macro_photos\Patient 1 Macrofoto anoniem.jpg"

    def say_hello(self):
        self.logger.info("hello")

    @classmethod
    def create_copy(cls, application):
        try:
            obj = cls(gui=application.gui, config_file=application.config_file, logger=application.logger)
            import reconstruction
            obj.logger.info("Reloading Reconstruction")
            importlib.reload(reconstruction)
            from reconstruction import Reconstruction
            obj.reconstruction = Reconstruction.create_copy(reconstruction=application.reconstruction, parent=obj, logger=application.logger)
            obj.reconstruction.set_macro_photo(path_macro_photo=application.path_macro_photo)
            if application.active_slice is None:
                obj.set_active_slice_by_id(-1)
            else:
                obj.set_active_slice_by_id(application.active_slice.id)
            return obj
        except:
            application.logger.error(
                f'Unexpected error: {sys.exc_info()[0]} \n {traceback.format_exc()}')
            return None


    def start(self):
        self.logger.info("Starting Application..")

        init_from_pkl=False
        if init_from_pkl:
            self.load_reconstruction_from_pickle(file_name=r"reconstr.pkl")

        else:
            self.reconstruction = Reconstruction(parent=self, logger=self.logger)
            self.reconstruction.set_macro_photo(path_macro_photo=self.path_macro_photo)
            self.reconstruction.load_micro_photos()


    def add_slice(self, rect):
        try:
            new_slice = self.reconstruction.add_slice_from_rect(rect=rect)
            self.set_active_slice_by_id(new_slice.id)
            self.logger.info(f"adding slice with rect {rect}")
            # note that set_active_slice already performs a gui update
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def delete_slice(self, id):
        new_active_slice= self.reconstruction.delete_slice(id)
        if new_active_slice is None:
            self.set_active_slice_by_id(-1)
        else:
            self.set_active_slice_by_id(new_active_slice)
        #note that set_active_slice already performs a gui update


    def set_active_slice_by_id(self,id=-1):
        try:
            if id < 0:
                self.gui.slice_photo_widget.set_slice(slice=None)
                self.gui.update()
            else:
                for slice in self.reconstruction.slices:
                    if slice.id==id:
                        self.active_slice = slice
                        self.logger.info(f"setting slice to {self.active_slice.id}")
                        self.gui.slice_photo_widget.set_show_taces(True)
                        self.gui.slice_photo_widget.set_slice(slice=self.active_slice)
                        self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def remove_latest_trace_from_active_slice(self):
        try:
            self.active_slice.remove_latest_trace()
            self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def load_reconstruction_from_pickle(self,file_name):
        try:
            self.reconstruction = Reconstruction.load_from_pickle(file_name=file_name, parent=self, logger=self.logger, path_macro_photo=self.path_macro_photo)
            self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def calc_mask(self):
        try:
            self.logger.info("Calc Mask")
            self.active_slice.calc_mask()
            self.gui.slice_photo_widget.set_show_taces(False)
            self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def add_ruler_end(self, ruler_end_point):
        try:
            self.logger.info(f"{ruler_end_point}")
            self.reconstruction.add_ruler_point(ruler_end_point)
            self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
