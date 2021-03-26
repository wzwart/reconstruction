import importlib
import logging
import sys
import traceback

import h5py
import numpy as np
import copy

from PyQt5.QtGui import QPixmap

class Reconstruction:
    """
    Contains the 3D data for a feature
    """

    def __init__(self, parent=None, logger=None):
        """
        Initializes and empty feature object. For initialization with data, use @classmethod create_feature.
        :param parent: a pointer to the parent PatientData object, can be omitted
        :param logger: a pointer to the logger, can be omitted
        :param plotter: a pointer to the 3d plotter, can be omitted
        """
        self.parent = parent
        self.slices = []

        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger('Feature Logger')
            self.logger.setLevel(logging.ERROR)
            ch = logging.StreamHandler()
            self.logger.addHandler(ch)


    def set_macro_photo(self, path_macro_photo):
        self.macro_photo=QPixmap(path_macro_photo)


    @classmethod
    def load_from_tcl(cls, file_name, parent=None, logger=None):
        """
        Creates features from a hdf5 file
        :param file_name: name of the HDF5 file to read data from
        """

        obj = Reconstruction(parent=parent, logger=logger)

        return obj


    def update_data(self):
        return


    def add_slice_from_rect(self, rect):

        try:
            new_slice = Slice.create_from_photo(macro_photo=self.macro_photo, rect=rect, id=len(self.slices))
            self.slices.append(new_slice)
            self.logger.info(f"adding slice with rect {rect}")
            return new_slice
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            return None


    def delete_slice(self, id):
        self.logger.info(f"deleting id {id}")
        self.slices = [slice for slice in self.slices if not slice.id == id]

        if len(self.slices) > 0:
            new_active_slice=self.slices[0]
        else:
            new_active_slice = None
        return new_active_slice


    def remove_non_serializable_objects(self):
        del self.logger
        del self.parent
        for slice in self.slices:
            slice.remove_non_serializable_objects()

    def restore_non_serializable_objects(self, logger, plotter, parent):
        self.logger = logger
        self.plotter = plotter
        self.parent = parent
        for slice in self.slices:
            slice.restore_non_serializable_objects(logger=logger, plotter=plotter, parent=parent)




class Slice():
    def __init__(self, ):
        self.rect=[0,0,0,0]
        self.macro_photo=None
        self.id=0
        self.inner_points=[]
        self.outer_points=[]

    @classmethod
    def create_from_photo(cls, macro_photo, rect, id):
        obj = cls()
        obj.macro_photo=macro_photo
        obj.slice_photo=macro_photo.copy(rect)
        obj.rect=rect
        obj.id=id
        return obj


