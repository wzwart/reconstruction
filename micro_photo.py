from PIL import Image
import numpy as np
import requests
import io
import logging,sys,traceback
import matplotlib.pyplot as plt
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import QPoint, QRect, QSize, Qt


class MicroPhoto:
    def __init__(self, slide_score_api,   slide_score_study_id, slide_score_case_id, slide_score_image_id,parent=None, logger=None):

        self.logger=logger
        self.parent=parent
        self.slide_score_image_id=slide_score_image_id
        self.slide_score_case_id=slide_score_case_id
        self.slide_score_study_id=slide_score_study_id
        self.slide_score_api=slide_score_api
        self.img=None
        self.meta_data={}




    @classmethod
    def create_copy(cls, micro_photo, parent=None, logger=None):
        obj=cls(slide_score_api=micro_photo.slide_score_api, slide_score_study_id=micro_photo.slide_score_study_id, slide_score_case_id=micro_photo.slide_score_case_id, slide_score_image_id=micro_photo.slide_score_image_id, parent = parent, logger = logger)
        obj.img=micro_photo.img
        obj.meta_data=micro_photo.meta_data
        obj.process_meta_data()
        obj.get_pixmaps_from_img()
        return obj

    def get_image(self):


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
        create pixmap and transparent pixmap from self.img
        :return:
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
        except:

            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())




    def get_metadata(self):
        response = self.slide_score_api.perform_request("GetImageMetadata?imageId=" + str(self.slide_score_image_id), None, method="GET")
        rjson = response.json()
        self.meta_data = rjson['metadata']

        # also getting the url and cookie for reading the slices
        response = self.slide_score_api.perform_request("GetTileServer?imageId=" + str(self.slide_score_image_id), None, method="GET")
        rjson = response.json()
        self.meta_data['cookie']=rjson['cookiePart']
        self.meta_data['url']=rjson['urlPart']
        return self.meta_data

    def process_meta_data(self):
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
        del self.parent
        del self.logger
        del self.slide_score_api
        del self.pixmap_trans
        del self.pixmap
        return

    def restore_non_serializable_objects(self, parent, logger, slide_score_api):
        self.parent=parent
        self.logger=logger
        self.slide_score_api=slide_score_api
        self.get_pixmaps_from_img()
        return