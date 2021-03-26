import logging 
import sys
import traceback
from pathlib import Path

from reconstruction import Reconstruction
from reconstruction import Slice


class Application():
    def __init__(self, gui ):

        self.gui = gui

        self.active_slice=None
        self.logger = logging.getLogger('session data main')
        self.logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
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

        self.reconstruction=Reconstruction(parent=self,logger=self.logger)
        self.reconstruction.set_macro_photo(path_macro_photo=r".\macro_photos\macro_1.jpg")


    def add_slice(self, rect):
        try:
            new_slice = self.reconstruction.add_slice_from_rect(rect=rect)
            self.set_active_slice(new_slice)
            self.logger.info(f"adding slice with rect {rect}")
            # note that set_active_slice already performs a gui update
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def delete_slice(self, id):
        new_active_slice= self.reconstruction.delete_slice(id)
        self.set_active_slice(new_active_slice)
        #note that set_active_slice already performs a gui update


    def set_active_slice(self,slice):
        self.active_slice=slice
        self.logger.info(f"setting slice to {self.active_slice.id}")
        self.gui.slice_photo_widget.set_slice(slice=self.active_slice)
        self.gui.tabs.setCurrentIndex(2)
        self.gui.update()

