import importlib
import logging
import pickle
import sys
import traceback

from PyQt5.QtGui import QPixmap

from coupe import Coupe
from slice import Slice


class Reconstruction:
    """
    The actual reconstruction
    """

    def __init__(self, slide_score_api, slide_score_user, parent=None, logger=None) :
        """
        Initializes and empty feature object. For initialization with data, use @classmethod create_feature.
        :param parent: a pointer to the parent PatientData object, can be omitted
        :param logger: a pointer to the logger, can be omitted
        :param plotter: a pointer to the 3d plotter, can be omitted
        """
        self.parent = parent
        self.slices = []
        self.coupes={}
        self.macro_photo=None
        self.active_coupe=None
        self.ruler_points=[]
        self.slide_score_api=slide_score_api
        self.slide_score_user=slide_score_user
        self.slide_score_case_id=-1
        self.slide_score_study_id=-1


        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger('Feature Logger')
            self.logger.setLevel(logging.ERROR)
            ch = logging.StreamHandler()
            self.logger.addHandler(ch)


        self.macro_photo_path=None


    @classmethod
    def create_copy(cls, reconstruction, parent=None, logger=None, slide_score_api=None, slide_score_user=None):
        '''
        Create make a copy of the reconstruction, while reloading all objects
        :param reconstruction: the reconstruction object from which a copy is made
        :param parent: the parent
        :param logger: the logger
        :param slide_score_api:  the slide score api
        :param slide_score_user: the slide score user
        :return: the newly created object
        '''
        if reconstruction is None:
            return None
        # first create an empty reconstruction
        obj = cls(parent=parent, logger=logger,
                  slide_score_api=slide_score_api,
                  slide_score_user=slide_score_user)
        # set the study and case id
        obj.set_slide_score_study_and_case_id(  slide_score_study_id= reconstruction.slide_score_study_id,
                                                slide_score_case_id = reconstruction.slide_score_case_id)
        # reload the coupes
        import coupe
        obj.logger.warning("Reloading Coupes")
        importlib.reload(coupe)
        from coupe import Coupe
        for miro_photo_id in reconstruction.coupes:
            obj.coupes[miro_photo_id] = Coupe.create_copy(
                coupe=reconstruction.coupes[miro_photo_id],
                parent=parent,
                logger=logger)
        obj.active_coupe=reconstruction.active_coupe
        # same for the slices
        import slice
        obj.logger.warning("Reloading Slices")
        importlib.reload(slice)
        from slice import Slice
        for slice in reconstruction.slices:
            obj.slices.append(Slice.create_copy(slice=slice,logger=logger))

        # and finally the ruler
        obj.ruler_points=reconstruction.ruler_points
        return obj


    def set_slide_score_study_and_case_id(self,slide_score_study_id,slide_score_case_id):
        '''

        :param slide_score_study_id:study_id
        :param slide_score_case_id:case_id
        :return: None
        '''
        self.slide_score_study_id=slide_score_study_id
        self.slide_score_case_id=slide_score_case_id
        return


    def load_coupes(self, max_cnt_coupes=-1):
        '''
        loads the coupes from Slide Score
        :param max_cnt_coupes: maximum number of coupes to be reloaded
        :return:
        '''

        self.get_coupe_ids()
        self.get_coupes(max_cnt=max_cnt_coupes)


    def get_coupe_ids(self):
        '''
        get the id's of all the coupes in slide score
        :return:
        '''

        response = self.slide_score_api.perform_request("Scores",
                                                        {"studyid": self.slide_score_study_id, "question": None,
                                                         "email": self.slide_score_user, "imageid": None,
                                                         "caseid": self.slide_score_case_id})
        rjson = response.json()

        self.slide_score_image_ids = set()
        self.slide_score_case_name = ""
        for r in rjson:
            self.slide_score_image_ids.add(int(r['imageID']))
        return


    def get_coupes(self, max_cnt=-1):
        '''
        Reads all coupes from Slide Score, and stores the resulting Coupe object in the dictionary self.coupes
        :param max_cnt: the maximum number of coupes to load. -1 for all. Limiting the total amount of coupes is
        mainly a development feature to accelerate the reading
        :return:
        '''
        cnt=0
        try:
            for slide_score_image_id in self.slide_score_image_ids:
                if cnt < max_cnt or max_cnt==-1:
                    self.coupes[slide_score_image_id] = Coupe(
                        slide_score_image_id=slide_score_image_id,
                        slide_score_case_id=self.slide_score_case_id,
                        slide_score_study_id=self.slide_score_study_id,
                        slide_score_api=self.slide_score_api,
                        logger=self.logger,
                        parent=self.parent)
                    self.coupes[slide_score_image_id].get_metadata()
                    self.coupes[slide_score_image_id].get_image()

                    cnt +=1
                    self.active_coupe=slide_score_image_id
            return None


        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            return None


    def set_macro_photo(self, macro_photo_path):
        '''
        Create the macro photo from a file path pointing to the macro photo
        :param macro_photo_path: path to the macro_photo
        :return:
        '''
        self.macro_photo_path=macro_photo_path
        self.macro_photo=QPixmap(macro_photo_path)

        self.logger.info(f"Loaded macro_photo with size{self.macro_photo.size()}")

    @classmethod
    def load_from_pickle(cls, pickle_file_path, parent, logger, macro_photo_path):
        '''
        creating a reconstruction from a pickle file. This is a very fast method, especially convenient for development
        and debugging

        :param pickle_file_path: the full to the pickle file
        :param parent: the parent
        :param logger: the logger
        :param macro_photo_path: the path to the macro_photo
        :return: the reconstruction as loaded from the pickle file
        '''
        try:
            logger.info(f"Reloading Reconstruction from {pickle_file_path}")
            obj = pickle.load(open(pickle_file_path, "rb"))
            logger.info(f"obj obtained")
            obj.restore_non_serializable_objects(parent=parent, logger=logger, macro_photo=QPixmap(macro_photo_path),slide_score_api=obj.slide_score_api)
            logger.info(f"obj restored_non_serializable_objects")
            return obj
        except:
            logger.error(sys.exc_info()[0])
            logger.error(traceback.format_exc())
            return None


    def save_to_pickle(self, pickle_file_path):
        '''
        Saving the reconstruction to a pickle file
        :param pickle_file_path: file name of the pickle file
        :return: None
        '''

        try:
            slide_score_api=self.slide_score_api
            logger = self.logger
            parent= self.parent
            macro_photo=self.macro_photo
            # the macro_photo is currently not stored as part of the pickle object
            # we might decide to change this later on
            self.logger.info("Saving to pickle")
            # first remove all elements that can not be stored in in pickle
            self.remove_non_serializable_objects()
            pickle.dump(self, open(pickle_file_path, "wb"))
            logger.debug("Saved to pickle")
            self.restore_non_serializable_objects(logger=logger, parent=parent, macro_photo=macro_photo,slide_score_api=slide_score_api)
            logger.debug("Non-serializable items restored")
            return
        except:
            logger.error(sys.exc_info()[0])
            logger.error(traceback.format_exc())
            return None

    def add_slice_from_rect(self, rect):
        '''
        Create a new slice from bounding box (rect) based on self.macro_photo
        The newly createad slice is returned, but also added to the list of slices (self.slices)

        :param rect: The rectangle (using QRect) with the bounding box within the macro photo
        :return: the newly created slice
        '''

        try:
            new_slice = Slice.create_from_photo(macro_photo=self.macro_photo, rect=rect, id=len(self.slices), logger=self.logger)
            self.slices.append(new_slice)
            self.logger.info(f"Adding slice with rect {rect}")
            return new_slice
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            return None


    def delete_slice(self, id):
        '''
        deleting a slice, based on its id
        :param id:
        :return:
        '''
        self.logger.info(f"Deleting slice with id {id}")
        self.slices = [slice for slice in self.slices if not slice.id == id]

        if len(self.slices) > 0:
            new_active_slice=self.slices[0]
        else:
            new_active_slice = None
        return new_active_slice

    def remove_non_serializable_objects(self):
        '''
        removing the non serializable objects.
        Used for storing the overall reconstruction as a pickle object
        :return: None
        '''

        logger=self.logger
        del self.logger
        del self.parent
        del self.macro_photo

        for slice in self.slices:
            logger.debug(f"remove_non_serializable_objects {slice.id}")
            slice.remove_non_serializable_objects()
        for coupe in self.coupes:
            self.coupes[coupe].remove_non_serializable_objects()
        logger.debug(f"Done remove_non_serializable_objects ")


    def restore_non_serializable_objects(self, logger,  parent, macro_photo,slide_score_api):
        '''
        restoring the non serializable objects
        Used for storing the overall reconstruction as a pickle object
        :param parent: the parent
        :param logger: the logger
        :param slide_score_api: the slide score api
        :param macro_photo: the macro photo (a QPixmap)
        :return:
        '''

        self.macro_photo = macro_photo
        self.logger = logger
        self.parent = parent
        for slice in self.slices:
            slice.restore_non_serializable_objects(macro_photo=macro_photo, logger=self.logger)
        for coupe in self.coupes:
            self.coupes[coupe].restore_non_serializable_objects(logger=logger,
                                                                slide_score_api=slide_score_api,
                                                                parent=parent)



    def add_ruler_point(self, ruler_end_point):
        '''
        adds an end-point to the list self.ruler_points
        :param ruler_end_point: The point to be added, a QPoint
        :return:
        '''
        self.ruler_points.append(ruler_end_point)
        #only the last two points are kept in self.ruler_points
        self.ruler_points=self.ruler_points[-2:]

    @classmethod
    def create_from_dict(cls, data,
                         slide_score_api,
                         slide_score_user,
                         parent=None,
                         logger=None
                         ):
        '''
        :param data: input dictionary
        :param slide_score_api: the slide_score api
        :param slide_score_user: the slide socre user
        :param parent: parent object
        :param logger: logger
        :return: the reconstruction as created from the dict
        '''
        obj = cls(parent=parent,
                  logger=logger,
                  slide_score_api=slide_score_api,
                  slide_score_user=slide_score_user)
        obj.set_macro_photo(data['macro_photo_path'])
        obj.set_slide_score_study_and_case_id(slide_score_study_id=data['slide_score_study_id'],
                                              slide_score_case_id=data['slide_score_case_id'])
        for coupe_id in data['coupe_ids']:
            obj.coupes[coupe_id] = Coupe.create_from_slide_score(
                slide_score_api=slide_score_api,
                slide_score_study_id=obj.slide_score_study_id,
                slide_score_case_id=obj.slide_score_case_id,
                slide_score_image_id=coupe_id,
                parent=parent,
                logger=logger)

        for slice_data in data['slices']:
            obj.slices.append(Slice.create_from_dict(data=slice_data,
                                                     macro_photo=obj.macro_photo,
                                                     logger=logger))
        return obj

    def get_dict_for_serialisation(self):
        '''
        obtain a dictionary describing the reconstruction object.
        :return: a dict
        '''

        data = {}
        data['slices']=[slice.get_dict_for_serialisation() for slice in self.slices]
        data['ruler_points']=[[point.x(), point.y()] for point in self.ruler_points]
        data['macro_photo_path']=self.macro_photo_path
        data['slide_score_case_id']=self.slide_score_case_id
        data['slide_score_study_id']=self.slide_score_study_id
        data['coupe_ids']=[coupe_id for coupe_id in self.coupes]

        return data