import logging 
import sys
import traceback
from pathlib import Path
from PyQt5.QtGui import QPixmap


class Application():
    def __init__(self, gui ):

        self.gui = gui
        self.slices=[]
        self.active_slice=None
        self.macro_photo=None

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

        self.macro_photo=QPixmap(r".\macro_photos\macro_1.jpg")


    def add_slice(self, rect):
        try:
            new_slice=Slice.create_from_photo(macro_photo=self.macro_photo, rect=rect, id=len(self.slices))
            self.slices.append(new_slice)
            self.logger.info(f"adding slice with rect {rect}")
            self.gui.rect_table_widget.update_table_widget()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def delete_slice(self, id):
        self.logger.info(f"deleting id {id}")
        self.slices = [slice for slice in self.slices if not slice.id==id]

        self.gui.rect_table_widget.update_table_widget()
        self.gui.macro_foto_widget.paint()


class Slice():
    def __init__(self, ):
        self.rect=[0,0,0,0]
        self.macro_photo=None
        self.id=0

    @classmethod
    def create_from_photo(cls, macro_photo, rect, id):
        obj = cls()
        obj.macro_photo=macro_photo
        obj.rect=rect
        obj.id=id
        return obj


