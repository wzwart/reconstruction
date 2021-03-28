import importlib
import logging
import sys
import traceback
import pickle

import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from sklearn.svm import SVC

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.model_selection import StratifiedShuffleSplit


from skimage.draw import polygon2mask
import numpy as np

import h5py
import numpy as np
import cv2

import copy


from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QPixmap, QColor, QPolygon, QBrush, QPen, QPainter

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
    def load_from_pickle(cls, file_name, parent, logger, path_macro_photo):
        try:
            logger.info(f"Reloading Reconstruction from {file_name}")
            obj = pickle.load(open(file_name, "rb"))
            logger.info(f"obj obtained")
            obj.restore_non_serializable_objects(parent=parent, logger=logger, macro_photo=QPixmap(path_macro_photo))
            logger.info(f"obj restored_non_serializable_objects")
            return obj
        except:
            logger.error(sys.exc_info()[0])
            logger.error(traceback.format_exc())
            return None


    def save_to_pickle(self, file_name):

        try:

            logger = self.logger
            parent= self.parent
            macro_photo=self.macro_photo
            self.logger.info("Saving")
            self.remove_non_serializable_objects()
            pickle.dump(self, open(file_name, "wb"))
            logger.info("Saved")

            self.restore_non_serializable_objects(logger=logger, parent=parent, macro_photo=macro_photo)
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
        logger.debug(f"Done remove_non_serializable_objects ")

    def restore_non_serializable_objects(self, logger,  parent, macro_photo):
        self.macro_photo=macro_photo
        self.logger = logger
        self.parent = parent
        for slice in self.slices:
            slice.restore_non_serializable_objects(macro_photo=macro_photo, logger=self.logger)
        for slice in self.slices:
            self.logger.info(f"Slide ID={slice.id} rect = {slice.rect}, macro_photo={macro_photo}")





class Slice():
    def __init__(self, logger):
        self.logger=logger
        self.rect=[0,0,0,0]
        self.macro_photo=None
        self.slice_photo=None
        self.id=0
        self.inner_points=[]
        self.outer_points=[]
        self.traces=[]
        self.tracing=False


        #some constants #todo : Where do we store these
        self.pen_width=20


    @classmethod
    def create_from_photo(cls, macro_photo, rect, id, logger):
        obj = cls(logger=logger)
        obj.macro_photo=macro_photo
        obj.slice_photo=macro_photo.copy(rect)
        obj.rect=rect
        obj.id=id
        return obj

    def remove_non_serializable_objects(self):
        del self.macro_photo
        del self.slice_photo
        del self.logger
        return

    def restore_non_serializable_objects(self, macro_photo, logger):
        self.macro_photo=macro_photo
        self.slice_photo=macro_photo.copy(self.rect)
        self.logger=logger
        return

    def paint(self, painter, size):
        try:
            photo = self.slice_photo
            size_draw = QSize(min(size.width(), photo.width()), min(size.height(), photo.height()))

            painter.drawPixmap(QRect(QPoint(0, 0), size_draw), photo, QRect(QPoint(0, 0), size_draw))

            painter.setPen(Qt.green)
            painter.setBrush(QBrush(QColor(0, 255, 0, 128)))

            painter.drawPolygon(QPolygon(self.inner_points))


            painter.setBrush(QBrush(QColor(255, 255, 255, 0)))
            painter.drawPolygon(QPolygon(self.outer_points))

            painter.setPen(Qt.green)


            pen=QPen()
            pen.setWidth(self.pen_width)
            pen.setBrush(Qt.green)
            pen.setCapStyle(Qt.RoundCap)

            painter.setPen(pen)

            for trace in self.traces:
                painter.drawPolyline(QPolygon(trace))


        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            return None


    def remove_latest_trace(self):
        if len(self.traces)>0:
            self.traces=self.traces[:-1]



    def add_to_trace(self,point):
        if not self.tracing:
            self.traces.append([])
        self.traces[-1].append(point)
        self.tracing=True

    def end_trace(self):
        self.tracing = False
        self.logger.info(f"{self.traces}")



    def getpixmap(self, pixmap=None):
        ## Get the size of the current pixmap
        if pixmap is None:
            pixmap = self.slice_photo
        size = pixmap.size()
        w = size.width()
        h = size.height()

        channels_count = 4

        image = pixmap.toImage()
        b = image.bits()
        b.setsize(h * w * channels_count)
        arr = np.frombuffer(b, np.uint8).reshape((h, w, channels_count))
        arr=cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        arr=arr[:,:,:3]
        return arr

    def calc_modes_2(self):
        try:

            max_num_train_pixels=500
            inner_mask, outer_mask = self.create_masks()
            pixels = self.getpixmap()
            X_in = pixels[inner_mask].reshape((-1, 3))
            X_out= pixels[outer_mask].reshape((-1, 3))

            X_in_sel=np.arange(len(X_in),dtype=np.int)
            X_out_sel=np.arange(len(X_out),dtype=np.int)
            num_train_pixels=min(len(X_in_sel),len(X_out_sel),max_num_train_pixels)

            np.random.shuffle(X_in_sel)
            X_in_sel=X_in_sel[:num_train_pixels]
            np.random.shuffle(X_out_sel)
            X_out_sel=X_out_sel[:num_train_pixels]

            X_in=X_in[X_in_sel]
            X_out=X_out[X_out_sel]
            Y_in=np.ones((X_in.shape[0],1))
            Y_out=np.zeros((X_out.shape[0],1))
            X = np.vstack((X_in, X_out))
            y = np.vstack((Y_in, Y_out))


            svm = SVC().fit(X=X, y=y)




            pred_svm = svm.predict(pixels.reshape((-1, 3))).reshape((pixels.shape[0],pixels.shape[1] ))
            prob_svm = svm.decision_function(pixels.reshape((-1, 3))).reshape((pixels.shape[0],pixels.shape[1] ))

            self.logger.info(f"Shape {svm.decision_function(pixels.reshape((-1, 3))).shape}")

            pred_svm=np.minimum(np.maximum(inner_mask,pred_svm),~outer_mask)
            prob_svm=np.minimum(np.maximum(inner_mask,prob_svm),~outer_mask)

            # Creating kernel
            kernel = np.ones((5, 5), np.uint8)



            # Using cv2.erode() method
            new_pred_svm = cv2.erode(cv2.dilate(pred_svm, kernel, cv2.BORDER_REFLECT), kernel, cv2.BORDER_REFLECT)
            from skimage import morphology

            new_pred_svm = morphology.remove_small_objects(pred_svm.astype(np.bool), min_size=100, connectivity=2).astype(int)
            new_pred_svm = morphology.remove_small_holes(new_pred_svm.astype(np.bool), area_threshold=100, connectivity=2).astype(int)

            color_inner= (pixels.reshape((-1, 3))[new_pred_svm.reshape((-1)).astype(np.bool)])
            color_inner=np.mean(color_inner, axis=0, dtype=np.int)
            color_outer= (pixels.reshape((-1, 3))[~new_pred_svm.reshape((-1)).astype(np.bool)])
            color_outer=np.mean(color_outer, axis=0, dtype=np.int)
            self.logger.info(f"inner_color {color_inner}")
            self.logger.info(f"inner_color {color_inner}")
            self.logger.info(f"color_outer {color_outer}")



            fig, axs = plt.subplots(3, 2)
            axs[0, 0].imshow(1*inner_mask-1*outer_mask)
            axs[0, 1].imshow(pixels)
            axs[1, 0].imshow(pred_svm, vmin=0, vmax=1)
            axs[1,1].imshow(new_pred_svm, vmin=0, vmax=1)
            axs[2,0].imshow(np.expand_dims(new_pred_svm,-1).astype(np.int)*pixels + np.expand_dims(1-new_pred_svm,-1).astype(np.int)*color_inner)
            axs[2,1].imshow(np.expand_dims(1-new_pred_svm,-1).astype(np.int)*pixels + np.expand_dims(new_pred_svm,-1).astype(np.int)*color_outer)

            for axh in axs:
                for ax in axh:
                    ax.set_aspect('equal')
                    ax.set_axis_off()


            fig.tight_layout()
            plt.show()

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            return None

    def calc_modes(self):
        try:
            inner_mask = self.create_mask(inner=True)
            outer_mask = self.create_mask(inner=False)


            pixels = self.getpixmap()
            X_in = pixels[inner_mask].reshape((-1, 3))
            X_out= pixels[outer_mask].reshape((-1, 3))
            Y_in=np.ones((X_in.shape[0],1))
            Y_out=np.zeros((X_out.shape[0],1))
            X = np.vstack((X_in, X_out))
            y = np.vstack((Y_in, Y_out))

            scaler = StandardScaler()
            # X = scaler.fit_transform(X)



            svm = SVC().fit(X=X, y=y)




            pred_svm = svm.predict(pixels.reshape((-1, 3))).reshape((pixels.shape[0],pixels.shape[1] ))
            prob_svm = svm.decision_function(pixels.reshape((-1, 3))).reshape((pixels.shape[0],pixels.shape[1] ))

            self.logger.info(f"Shape {svm.decision_function(pixels.reshape((-1, 3))).shape}")

            pred_svm=np.clip(pred_svm*255, 0, 255)



            fig, axs = plt.subplots(2, 2)
            axs[0, 0].imshow(1*inner_mask-1*outer_mask)
            axs[0, 1].imshow(pixels)
            axs[1,0].imshow(np.max(pred_svm,inner_mask*1),vmin=0,vmax=1)
            axs[1,1].imshow(prob_svm)


            for axh in axs:
                for ax in axh:
                    ax.set_aspect('equal')
                    ax.set_axis_off()


            fig.tight_layout()
            plt.show()

        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            return None



    def create_masks(self):

        self.logger.info("Calculate 2")
        pixmap = QPixmap(self.slice_photo.size())
        pixmap.fill(QColor(255, 255, 255))

        painter = QPainter()
        painter.begin(pixmap)

        pen = QPen()
        pen.setWidth(self.pen_width)
        pen.setBrush(Qt.black)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        for trace in self.traces:
            painter.drawPolyline(QPolygon(trace))
        arr = self.getpixmap(pixmap)
        arr = np.mean(arr, axis=-1, dtype=np.uint8)

        l = []
        for trace in self.traces:
            l = l + [[p.x(), p.y()] for p in trace]
        center = np.mean(np.array(l), axis=0, dtype=np.int)

        self.logger.info(f"l={l}")
        self.logger.info(f"c={center}")

        painter.drawEllipse(center[0], center[1], 10, 10)
        arr2 = self.getpixmap(pixmap)

        inner_mask = arr.copy()

        h, w = inner_mask.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(inner_mask, mask, (center[0], center[1]), 128);
        self.logger.info(f"{np.min(arr)}")
        self.logger.info(f"{np.max(arr)}")

        inner_mask = (inner_mask > 100).astype(np.bool)
        middle_mask = (arr < 32).astype(np.bool)
        outer_mask = np.logical_and(~inner_mask, ~middle_mask)
        painter.end()

        fig, axs = plt.subplots(2, 2)
        axs[0, 0].imshow(arr)
        axs[0, 1].imshow(middle_mask)
        axs[1, 0].imshow(inner_mask)
        axs[1, 1].imshow(outer_mask)

        for axh in axs:
            for ax in axh:
                ax.set_aspect('equal')
                # ax.set_axis_off()

        fig.tight_layout()
        plt.show()

        return inner_mask, outer_mask

    def create_mask(self, inner=True):
        try:
            if inner:
                q_poly=self.inner_points
            else:
                q_poly=self.outer_points

            np_poly=np.array([[point.y(),point.x() ]  for point in q_poly])
            self.logger.info(f"np_poly={np_poly}")
            size = (self.slice_photo.height(),self.slice_photo.width())
            self.logger.info(f"size={size}")
            mask = polygon2mask(image_shape=size, polygon=np_poly)
            if inner:
                return  mask
            else:
                return ~mask


        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
            return None
