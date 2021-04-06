import importlib
import logging
import pickle
import sys
import traceback

from PyQt5.QtGui import QPixmap

from micro_photo import MicroPhoto
from slice import Slice
from slide_score_api.slidescore import APIClient


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
        self.micro_photos={}
        self.macro_photo=None
        self.active_micro_photo=None
        self.ruler_points=[]

        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger('Feature Logger')
            self.logger.setLevel(logging.ERROR)
            ch = logging.StreamHandler()
            self.logger.addHandler(ch)


    @classmethod
    def create_copy(cls, reconstruction, parent=None, logger=None):
        if reconstruction is None:
            return None
        obj = cls(parent=parent, logger=logger)
        import micro_photo
        obj.logger.warning("reloading microphotos")
        importlib.reload(micro_photo)
        from micro_photo import MicroPhoto
        for miro_photo_id in reconstruction.micro_photos:
            obj.micro_photos[miro_photo_id] = MicroPhoto.create_copy(
                micro_photo=reconstruction.micro_photos[miro_photo_id],
                parent=parent,
                logger=logger)
        obj.active_micro_photo=reconstruction.active_micro_photo
        import slice
        obj.logger.warning("reloading Slices")
        importlib.reload(slice)
        from slice import Slice
        for slice in reconstruction.slices:
            obj.slices.append(Slice.create_copy(slice=slice,logger=logger))

        obj.ruler_points=reconstruction.ruler_points
        return obj



    def load_micro_photos(self):
        self.init_slides_score_api()
        self.get_micro_photo_ids()
        self.get_micro_photos(max_cnt=3)



    def init_slides_score_api(self):

        self.slide_score_api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJOYW1lIjoiV2ltIEFQSSBhY2Nlc3MiLCJJRCI6IjQwIiwiVmVyc2lvbiI6IjEuMCIsIkNhbkNyZWF0ZVVwbG9hZEZvbGRlcnMiOiJGYWxzZSIsIkNhblVwbG9hZCI6IkZhbHNlIiwiQ2FuRG93bmxvYWRTbGlkZXMiOiJUcnVlIiwiQ2FuRGVsZXRlU2xpZGVzIjoiRmFsc2UiLCJDYW5VcGxvYWRPbmx5SW5Gb2xkZXJzIjoiIiwiQ2FuUmVhZE9ubHlTdHVkaWVzIjoiIiwiQ2FuTW9kaWZ5T25seVN0dWRpZXMiOiIiLCJDYW5HZXRDb25maWciOiJUcnVlIiwiQ2FuR2V0UGl4ZWxzIjoiVHJ1ZSIsIkNhblVwbG9hZFNjb3JlcyI6IkZhbHNlIiwiQ2FuQ3JlYXRlU3R1ZGllcyI6IkZhbHNlIiwiQ2FuUmVpbXBvcnRTdHVkaWVzIjoiRmFsc2UiLCJDYW5EZWxldGVPd25lZFN0dWRpZXMiOiJGYWxzZSIsIkNhbkdldFNjb3JlcyI6IlRydWUiLCJDYW5HZXRBbnlTY29yZXMiOiJUcnVlIiwibmJmIjoxNjE2NDkxNTE1LCJleHAiOjE2NDc5OTAwMDAsImlhdCI6MTYxNjQ5MTUxNX0.duMtd4ZHkyfDSEP2E5MHvnamggZutoCFuYuARn_M_xo"
        self.slide_score_server='https://slidescore.angiogenesis-analytics.nl'
        self.slice_score_user = "wim.zwart@angiogenesis-analytics.nl"
        self.slide_score_study_id = 2
        self.slide_score_case_id = 13
        self.slide_score_api = APIClient(self.slide_score_server, self.slide_score_api_token)



    def get_micro_photo_ids(self):

        response = self.slide_score_api.perform_request("Scores",
                                                        {"studyid": self.slide_score_study_id, "question": None, "email": self.slice_score_user, "imageid": None,
                                        "caseid": self.slide_score_case_id})
        rjson = response.json()

        self.slide_score_image_ids = set()
        self.slide_score_case_name = ""
        for r in rjson:
            if not len(self.slide_score_case_name) > 0:
                self.slide_score_case_name = r['caseName']
            elif self.slide_score_case_name != r['caseName']:
                self.logger.error(f"inconsistent casename {r['caseName']}")

            self.slide_score_image_ids.add(r['imageID'])

        self.logger.info(f"Case Name {self.slide_score_case_name} : {self.slide_score_image_ids}")

    def get_micro_photos(self, max_cnt=-1):
        cnt=0
        try:
            for slide_score_image_id in self.slide_score_image_ids:
                if cnt < max_cnt or max_cnt==-1:
                    self.micro_photos[slide_score_image_id] = MicroPhoto(
                        slide_score_image_id=slide_score_image_id,
                        slide_score_case_id=self.slide_score_case_id,
                        slide_score_study_id=self.slide_score_study_id,
                        slide_score_api=self.slide_score_api,
                        logger=self.logger,
                        parent=self.parent)
                    self.micro_photos[slide_score_image_id].get_metadata()
                    self.micro_photos[slide_score_image_id].process_meta_data()
                    self.micro_photos[slide_score_image_id].get_image()

                    cnt +=1
                    self.active_micro_photo=slide_score_image_id


        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            return None


    def set_macro_photo(self, path_macro_photo):
        self.macro_photo=QPixmap(path_macro_photo)


    @classmethod
    def load_from_pickle(cls, file_name, parent, logger, path_macro_photo):
        try:
            logger.info(f"Reloading Reconstruction from {file_name}")
            obj = pickle.load(open(file_name, "rb"))
            logger.info(f"obj obtained")
            obj.init_slides_score_api()
            obj.restore_non_serializable_objects(parent=parent, logger=logger, macro_photo=QPixmap(path_macro_photo),slide_score_api=obj.slide_score_api)
            logger.info(f"obj restored_non_serializable_objects")
            return obj
        except:
            logger.error(sys.exc_info()[0])
            logger.error(traceback.format_exc())
            return None


    def save_to_pickle(self, file_name):

        try:
            slide_score_api=self.slide_score_api
            logger = self.logger
            parent= self.parent
            macro_photo=self.macro_photo
            self.logger.info("Saving")
            self.remove_non_serializable_objects()
            pickle.dump(self, open(file_name, "wb"))
            logger.info("Saved")
            self.restore_non_serializable_objects(logger=logger, parent=parent, macro_photo=macro_photo,slide_score_api=slide_score_api)
            logger.info("Restored")
        except:
            logger.error(sys.exc_info()[0])
            logger.error(traceback.format_exc())
            return None


    def update_data(self):
        return


    def add_slice_from_rect(self, rect):

        try:
            new_slice = Slice.create_from_photo(macro_photo=self.macro_photo, rect=rect, id=len(self.slices), logger=self.logger)
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
        logger=self.logger
        del self.logger
        del self.parent
        del self.macro_photo

        for slice in self.slices:
            logger.debug(f"remove_non_serializable_objects {slice.id}")
            slice.remove_non_serializable_objects()
        for micro_photo in self.micro_photos:
            self.micro_photos[micro_photo].remove_non_serializable_objects()
        logger.debug(f"Done remove_non_serializable_objects ")


    def restore_non_serializable_objects(self, logger,  parent, macro_photo,slide_score_api):
        self.macro_photo=macro_photo
        self.logger = logger
        self.parent = parent
        for slice in self.slices:
            slice.restore_non_serializable_objects(macro_photo=macro_photo, logger=self.logger)
        for slice in self.slices:
            self.logger.info(f"Slide ID={slice.id} rect = {slice.rect}, macro_photo={macro_photo}")
        for micro_photo in self.micro_photos:
            self.micro_photos[micro_photo].restore_non_serializable_objects(logger=logger,slide_score_api=slide_score_api,parent=parent )



    def add_ruler_point(self, point):
        self.ruler_points.append(point)
        if len (self.ruler_points) > 2 :
            self.ruler_points=self.ruler_points[-2:]
