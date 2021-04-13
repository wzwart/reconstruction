from PIL import Image
import numpy as np
import requests
import io
import sys,traceback
from PyQt5.QtGui import QPixmap, QImage


class Coupe:

    '''
    The Coupe Class contains the coupes (or "slides" as they are also called)
    Each coupe is defined by:
    a study_id
    a case_id
    an image_id


    The coupe can interact autonomously with the Slide Score API
    It uses  get_meta() to get the basic meta data from the API, plus additional data such that it can




    '''

    def __init__(self, slide_score_api,   slide_score_study_id, slide_score_case_id, slide_score_image_id,parent=None, logger=None):

        '''

        :param slide_score_api:
        :param slide_score_study_id:
        :param slide_score_case_id:
        :param slide_score_image_id:
        :param parent:
        :param logger:
        '''

        self.logger=logger
        self.parent=parent
        self.slide_score_image_id=slide_score_image_id
        self.slide_score_case_id=slide_score_case_id
        self.slide_score_study_id=slide_score_study_id
        self.slide_score_api=slide_score_api
        self.img=None
        self.meta_data={}




    @classmethod
    def create_copy(cls, coupe, parent=None, logger=None):
        obj=cls(slide_score_api=coupe.slide_score_api, slide_score_study_id=coupe.slide_score_study_id, slide_score_case_id=coupe.slide_score_case_id, slide_score_image_id=coupe.slide_score_image_id, parent = parent, logger = logger)
        obj.img=coupe.img
        obj.meta_data=coupe.meta_data
        obj.process_meta_data()
        obj.get_pixmaps_from_img()
        return obj

    def get_image(self):
        '''
        retreiving the image from slide score, using the tiles
        the image is stored in self.img, which is a numpy array
        then get_pixmaps_from_img()  is called to get the QPicMap
        :return:
        '''

        try:
            zoom_level = 8
            rect = [[0, 0], [self.width, self.height]]
            max_level = max(self.width, self.height).bit_length()
            x_from = int(rect[0][0] // (self.tile_width * 2 ** zoom_level))
            x_to = int((rect[1][0]) // (self.tile_width * 2 ** zoom_level)) + 1
            y_from = int(rect[0][1] // (self.tile_height * 2 ** zoom_level))
            y_to = int((rect[1][1]) // (self.tile_height * 2 ** zoom_level)) + 1
            img_width = (rect[1][0] - rect[0][0]) // (2 ** zoom_level) + 1
            img_height = (rect[1][1] - rect[0][1]) // (2 ** zoom_level) + 1
            self.img = np.zeros((img_height, img_width, 3), dtype=np.uint8)
            self.logger.info(f"Getting image {self.slide_score_image_id}. Size: {img_width} x {img_height}")

            for x in range(x_from, x_to):

                left_img = min(max((x * self.tile_width * 2 ** zoom_level - rect[0][0]) // (2 ** zoom_level), 0), img_width - 1)
                right_img = min(max((((x + 1) * self.tile_width - 1) * 2 ** zoom_level - rect[0][0]) // (2 ** zoom_level), 0),
                                img_width - 1)
                left_tile = (left_img + rect[0][0] // (2 ** zoom_level)) % self.tile_width
                right_tile = (right_img + rect[0][0] // (2 ** zoom_level)) % self.tile_width

                for y in range(y_from, y_to):

                    url = self.slide_score_api.end_point.replace("/Api/",
                                                f"/i/{self.slide_score_image_id}/{self.url}/i_files/{max_level - zoom_level}/{x}_{y}.jpeg")
                    if True:
                        r = requests.get(url, cookies={'t': self.cookie})
                    first = False
                    tile = Image.open(io.BytesIO(r.content))
                    tile = np.asarray(tile)
                    top_img = min(max((y * self.tile_height * 2 ** zoom_level - rect[0][1]) // (2 ** zoom_level), 0),
                                  img_height - 1)
                    bottom_img = min(
                        max((((y + 1) * self.tile_height - 1) * 2 ** zoom_level - rect[0][1]) // (2 ** zoom_level), 0),
                        img_height - 1)
                    top_tile = (top_img + rect[0][1] // (2 ** zoom_level)) % self.tile_height
                    bottom_tile = (bottom_img + rect[0][1] // (2 ** zoom_level)) % self.tile_height
                    self.logger.info(f"Left_image: {left_img}, Right_image {right_img} {2 ** zoom_level}")
                    self.logger.info(f"Left_tile: {left_tile}, Right_tile {right_tile}")
                    self.logger.info(f"Top_image: {top_img}, Bottom_image {bottom_img}")
                    self.logger.info(f"Top_tile: {top_tile}, Bottom_tile {bottom_tile}")

                    self.img[top_img:bottom_img + 1, left_img: right_img + 1] = tile[top_tile:bottom_tile + 1,
                                                                           left_tile: right_tile + 1]

        except:

            self.img=np.ones((100,100,3), dtype=np.uint8) * np.array([50,50,250], dtype=np.uint8).reshape((1,1,3))
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
        self.get_pixmaps_from_img()


    def get_pixmaps_from_img(self):
        '''
        Creates self.pixmap from numpy array self.img. self.pixmap is a QPixmap which can be used directly
        by PyQt for rendering.
        Also creates self.trans_pixmap. This is similar to self.pixmap, but now it is semi transparent, such that
        it can be used as overlay over the slices for positioning of the coupes.
        :return: None
        '''
        try:
            qimage = QImage(self.img, self.img.shape[1], self.img.shape[0], self.img.shape[1] * 3, QImage.Format_RGB888)
            self.pixmap = QPixmap(qimage)
            exp_mask = np.ones((self.img.shape[0], self.img.shape[1], 1)) * np.linalg.norm(
                self.img - np.array([241, 241, 241]).reshape((1, 1, 3)), axis=2, keepdims=True) / 20

            arr_photo = np.concatenate((self.img[:, :, 2:3], self.img[:, :, 1:2], self.img[:, :, 0:1], 255 * exp_mask),
                                       axis=2).astype(np.uint8)
            self.logger.info(f"arr_photo {arr_photo.shape}")

            qimage_trans = QImage(arr_photo, arr_photo.shape[1], arr_photo.shape[0],
                                  QImage.Format_ARGB32)
            self.pixmap_trans = QPixmap(qimage_trans)
            return
        except:

            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def get_metadata(self):
        '''
        reads the meta data for the coupe from the Slide Score API.
        :return:
        '''
        response = self.slide_score_api.perform_request("GetImageMetadata?imageId=" + str(self.slide_score_image_id), None, method="GET")
        rjson = response.json()
        self.meta_data = rjson['metadata']

        # also getting the url and cookie for reading the slices
        response = self.slide_score_api.perform_request("GetTileServer?imageId=" + str(self.slide_score_image_id), None, method="GET")
        rjson = response.json()
        self.meta_data['cookie']=rjson['cookiePart']
        self.meta_data['url']=rjson['urlPart']
        self.process_meta_data()
        return self.meta_data

    def process_meta_data(self):
        '''
        and now store the meta data we received from Slide Score as member variables
        :return:
        '''
        self.tile_width=self.meta_data['level0TileWidth']
        self.tile_height=self.meta_data['level0TileHeight']
        self.width=self.meta_data['level0Width']
        self.height=self.meta_data['level0Height']
        self.size=[self.width,self.height]
        self.mpp_x=self.meta_data['mppX']
        self.mpp_y=self.meta_data['mppY']
        self.cookie = self.meta_data['cookie']
        self.url=self.meta_data['url']


    def remove_non_serializable_objects(self):
        '''
        removing the non serializable objects.
        Used for storing the overall reconstruction as a pickle object
        :return: None
        '''
        del self.parent
        del self.logger
        del self.slide_score_api
        del self.pixmap_trans
        del self.pixmap
        return

    def restore_non_serializable_objects(self, parent, logger, slide_score_api):
        '''
        restoring the non serializable objects
        Used for storing the overall reconstruction as a pickle object
        :param parent: the parent
        :param logger: the logger
        :param slide_score_api: the slide score api
        :return: None
        '''
        self.parent=parent
        self.logger=logger
        self.slide_score_api=slide_score_api
        self.get_pixmaps_from_img()
        return


    @classmethod
    def create_from_slide_score(cls, slide_score_api, slide_score_study_id, slide_score_case_id,  slide_score_image_id,  parent=None, logger=None):
        obj=cls(slide_score_api=slide_score_api, slide_score_study_id=slide_score_study_id, slide_score_case_id=slide_score_case_id, slide_score_image_id=slide_score_image_id, parent = parent, logger = logger)
        obj.get_metadata()
        obj.get_image()
        return obj
