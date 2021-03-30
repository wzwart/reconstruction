import sys
import traceback

import matplotlib.pyplot as plt
from sklearn.svm import SVC
from skimage import morphology
import numpy as np
import cv2


from PyQt5.QtCore import QPoint, QRect, QSize, Qt
from PyQt5.QtWidgets import QLabel , QRubberBand ,QApplication
from PyQt5.QtGui import QPixmap, QColor , QPainter, QPolygon, QBrush, QImage, QPen



class Slice():
    def __init__(self, logger):
        self.logger=logger
        self.rect=[0,0,0,0]
        self.macro_photo=None
        self.slice_photo=None
        self.id=0
        self.traces=[]
        self.tracing=False
        self.mask=None
        #some constants #todo : Where do we store these
        self.pen_width=45
        self.max_num_train_pixels = 500

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


    def paint_2(self, painter, size):
        try:
            photo = self.slice_photo
            arr_photo=self.get_np_array(photo)
            arr_photo = cv2.cvtColor(arr_photo, cv2.COLOR_BGR2RGB)
            if not self.mask is None:
                self.logger.info(f"shape photo {arr_photo.shape}")
                exp_mask=np.expand_dims(self.mask, -1)
                self.logger.info(f"shape mask {exp_mask.shape}")



                arr_photo=np.concatenate((arr_photo,255*exp_mask),axis=2).astype(np.uint8)
                self.logger.info(f"arr_photo {arr_photo.shape}")


                qimage = QImage(arr_photo, arr_photo.shape[1], arr_photo.shape[0],
                                QImage.Format_ARGB32)
                pixmap = QPixmap(qimage)

            size_draw = QSize(min(size.width(), photo.width()), min(size.height(), photo.height()))
            painter.drawPixmap(QRect(QPoint(0, 0), size_draw), pixmap, QRect(QPoint(0, 0), size_draw))



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



    def get_np_array(self, pixmap=None):
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


    def calc_mask(self):
        try:
            inner_mask, outer_mask = self.create_inner_and_outer_mask()
            pixels = self.get_np_array()
            X_in = pixels[inner_mask].reshape((-1, 3))
            X_out= pixels[outer_mask].reshape((-1, 3))

            X_in_sel=np.arange(len(X_in),dtype=np.int)
            X_out_sel=np.arange(len(X_out),dtype=np.int)
            num_train_pixels=min(len(X_in_sel),len(X_out_sel),self.max_num_train_pixels)

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


            pred_svm=np.minimum(np.maximum(inner_mask,pred_svm),~outer_mask)
            prob_svm=np.minimum(np.maximum(inner_mask,prob_svm),~outer_mask)



            pred_svm = morphology.remove_small_objects(pred_svm.astype(np.bool), min_size=100, connectivity=2).astype(int)
            pred_svm = morphology.remove_small_holes(pred_svm.astype(np.bool), area_threshold=100, connectivity=2).astype(int)

            color_inner= (pixels.reshape((-1, 3))[pred_svm.reshape((-1)).astype(np.bool)])
            color_inner=np.mean(color_inner, axis=0, dtype=np.int)
            color_outer= (pixels.reshape((-1, 3))[~pred_svm.reshape((-1)).astype(np.bool)])
            color_outer=np.mean(color_outer, axis=0, dtype=np.int)
            self.mask=pred_svm



            fig, axs = plt.subplots(3, 2)
            axs[0, 0].imshow(1*inner_mask-1*outer_mask)
            axs[0, 1].imshow(pixels)
            axs[1, 0].imshow(self.mask, vmin=0, vmax=1)
            axs[1,1].imshow(self.mask, vmin=0, vmax=1)
            axs[2,0].imshow(np.expand_dims(self.mask,-1).astype(np.int)*pixels + np.expand_dims(1-self.mask,-1).astype(np.int)*color_inner)
            axs[2,1].imshow(np.expand_dims(1-self.mask,-1).astype(np.int)*pixels + np.expand_dims(self.mask,-1).astype(np.int)*color_outer)

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


    def create_inner_and_outer_mask(self):

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
        arr = self.get_np_array(pixmap)
        arr = np.mean(arr, axis=-1, dtype=np.uint8)

        l = []
        for trace in self.traces:
            l = l + [[p.x(), p.y()] for p in trace]
        center = np.mean(np.array(l), axis=0, dtype=np.int)


        painter.drawEllipse(center[0], center[1], 10, 10)

        inner_mask = arr.copy()

        h, w = inner_mask.shape[:2]
        mask = np.zeros((h + 2, w + 2), np.uint8)
        cv2.floodFill(inner_mask, mask, (center[0], center[1]), 128);

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

