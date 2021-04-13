import configparser
import importlib
import json
import logging
import re
import sys
import traceback
from pathlib import Path

from reconstruction import Reconstruction
from slide_score_api.slidescore import APIClient


class Application():
    '''

    The Application class is the interface between the Reconstruction Object and the ReconstructionGui object
    The Application is the only means for the Reconstruction object and the ReconstructionGui object to interact with each other

    All methods in the application object use a try: /except: structure.
    This is to catch  errors . It allows the gui to stay alive, even when something goes wrong in the
    application or the reconstruction below it.

    The application is configured through the config file (config.ini)


    '''

    def __init__(self, gui, config_file="config.ini", logger=None):
        '''
        :param gui: the gui
        :param config_file:
        :param logger: The logger should be left to None, unless we are re-using an existing logger,
        when performing a reload.
        '''

        self.gui = gui
        self.config_file = config_file
        self.read_config()
        self.write_config()

        # the reconstruction object
        self.reconstruction = None
        # the active slice is used, to track which slice is being rendered on the slice_photo_widget
        self.active_slice = None

        if logger is None:
            self.logger = logging.getLogger('session data main')
            self.logger.setLevel(logging.DEBUG)
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
            self.logger = logger

        self.init_slidescore_api()

    @classmethod
    def create_copy(cls, application):
        '''
        creating a copy of the application while reloading the code for the reconstruction
        :param application: the application to copy
        :return:
        '''
        try:
            obj = cls(gui=application.gui, config_file=application.config_file, logger=application.logger)

            import reconstruction
            obj.logger.info("Reloading Reconstruction")
            importlib.reload(reconstruction)
            from reconstruction import Reconstruction
            obj.reconstruction = Reconstruction.create_copy(reconstruction=application.reconstruction, parent=obj,
                                                            logger=application.logger,
                                                            slide_score_api=application.slide_score_api,
                                                            slide_score_user=application.slide_score_user)
            obj.reconstruction.set_macro_photo(macro_photo_path=application.macro_photo_path)
            if application.active_slice is None:
                obj.set_active_slice_by_id(-1)
            else:
                obj.set_active_slice_by_id(application.active_slice.id)
            return obj
        except:
            application.logger.error(
                f'Unexpected error: {sys.exc_info()[0]} \n {traceback.format_exc()}')
            return None

    def init_slidescore_api(self):
        try:
            self.slide_score_api = APIClient(self.slide_score_server, self.slide_score_api_token)
        except:
            self.logger.error(
                f'Unexpected error: {sys.exc_info()[0]} \n {traceback.format_exc()}')
            pass

    def start(self):
        try:
            self.logger.info("Starting Application..")

            if self.auto_reload:
                self.load_reconstruction_from_pickle()

            else:
                self.reconstruction = Reconstruction(slide_score_api=self.slide_score_api,
                                                     slide_score_user=self.slide_score_user, parent=self,
                                                     logger=self.logger)
                self.reconstruction.set_slide_score_study_and_case_id(slide_score_study_id=self.slide_score_study_id,
                                                                      slide_score_case_id=self.slide_score_case_id)
                self.reconstruction.set_macro_photo(macro_photo_path=self.macro_photo_path)
                self.reconstruction.load_coupes(max_cnt_coupes=self.max_cnt_coupes)
        except:
            self.logger.error(
                f'Unexpected error: {sys.exc_info()[0]} \n {traceback.format_exc()}')
            pass

    def read_config(self):
        parser = configparser.ConfigParser()

        if Path(self.config_file).is_file():
            try:
                f = open(self.config_file, "r")
                parser.read_file(f)
                f.close()
            except RuntimeError:
                pass

        try:
            self.slide_score_server = parser.get("SLIDESCORE", "server")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.slide_score_server = 'https://slidescore.angiogenesis-analytics.nl'
            pass

        try:
            self.slide_score_user = parser.get("SLIDESCORE", "user")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.slide_score_user = "wim.zwart@angiogenesis-analytics.nl"
            pass

        try:
            self.slide_score_api_token = parser.get("SLIDESCORE", "api_token")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.slide_score_api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJOYW1lIjoiV2ltIEFQSSBhY2Nlc3MiLCJJRCI6IjQwIiwiVmVyc2lvbiI6IjEuMCIsIkNhbkNyZWF0ZVVwbG9hZEZvbGRlcnMiOiJGYWxzZSIsIkNhblVwbG9hZCI6IkZhbHNlIiwiQ2FuRG93bmxvYWRTbGlkZXMiOiJUcnVlIiwiQ2FuRGVsZXRlU2xpZGVzIjoiRmFsc2UiLCJDYW5VcGxvYWRPbmx5SW5Gb2xkZXJzIjoiIiwiQ2FuUmVhZE9ubHlTdHVkaWVzIjoiIiwiQ2FuTW9kaWZ5T25seVN0dWRpZXMiOiIiLCJDYW5HZXRDb25maWciOiJUcnVlIiwiQ2FuR2V0UGl4ZWxzIjoiVHJ1ZSIsIkNhblVwbG9hZFNjb3JlcyI6IkZhbHNlIiwiQ2FuQ3JlYXRlU3R1ZGllcyI6IkZhbHNlIiwiQ2FuUmVpbXBvcnRTdHVkaWVzIjoiRmFsc2UiLCJDYW5EZWxldGVPd25lZFN0dWRpZXMiOiJGYWxzZSIsIkNhbkdldFNjb3JlcyI6IlRydWUiLCJDYW5HZXRBbnlTY29yZXMiOiJUcnVlIiwibmJmIjoxNjE2NDkxNTE1LCJleHAiOjE2NDc5OTAwMDAsImlhdCI6MTYxNjQ5MTUxNX0.duMtd4ZHkyfDSEP2E5MHvnamggZutoCFuYuARn_M_xo"
            pass

        try:
            self.slide_score_study_id = int(parser.get("SLIDESCORE", "study_id"))
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.slide_score_study_id = 2
            pass

        try:
            self.slide_score_case_id = int(parser.get("SLIDESCORE", "case_id"))
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.slide_score_case_id = 13
            pass

        try:
            self.auto_reload = (parser.get("APPLICATION", "auto_reload")) in ["true",
                                                                              "True", "1",
                                                                              "yes",
                                                                              "Yes"]
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.auto_reload = False
            pass

        try:
            self.macro_photo_path = parser.get("RECONSTRUCTION", "macro_photo_path")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.macro_photo_path = r".\macro_photos\Patient 1 Macrofoto anoniem.jpg"
            pass

        try:
            self.max_cnt_coupes = int(parser.get("RECONSTRUCTION", "max_cnt_coupes"))
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.max_cnt_coupes = 2
            pass

        try:
            self.json_file_path = parser.get("FILES", "json_file_path")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.json_file_path = r"reconstruct.json"
            pass

        try:
            self.pickle_file_path = parser.get("FILES", "pickle_file_path")
        except (configparser.NoOptionError, configparser.NoSectionError):
            self.pickle_file_path = r"reconstr.pkl"
            pass

    def write_config(self):
        try:
            parser = configparser.ConfigParser()
            parser.add_section("SLIDESCORE")
            parser.set("SLIDESCORE", "server", str(self.slide_score_server))
            parser.set("SLIDESCORE", "user", str(self.slide_score_user))
            parser.set("SLIDESCORE", "api_token", str(self.slide_score_api_token))
            parser.set("SLIDESCORE", "study_id", str(self.slide_score_study_id))
            parser.set("SLIDESCORE", "case_id", str(self.slide_score_case_id))
            parser.add_section("APPLICATION")
            parser.set("APPLICATION", "auto_reload", str(self.auto_reload))
            parser.add_section("RECONSTRUCTION")
            parser.set("RECONSTRUCTION", "macro_photo_path", str(self.macro_photo_path))
            parser.set("RECONSTRUCTION", "max_cnt_coupes", str(self.max_cnt_coupes))
            parser.add_section("FILES")
            parser.set("FILES", "json_file_path", str(self.json_file_path))
            parser.set("FILES", "pickle_file_path", str(self.pickle_file_path))
            f = open(self.config_file, "w")
            parser.write(f)
            f.close()
        except:
            self.logger.error(
                f'Unexpected error: {sys.exc_info()[0]} \n {traceback.format_exc()}')
            pass

    def add_slice(self, rect):
        '''
        Add a slice to the slices, based on the rect bbox. Also sets the newly created slices to be the active slice.
        :param rect:QRect object containing the bbox of the slice in the macro_photo
        :return:
        '''
        try:
            new_slice = self.reconstruction.add_slice_from_rect(rect=rect)
            self.set_active_slice_by_id(new_slice.id)
            self.logger.info(f"adding slice with rect {rect}")
            # note that set_active_slice already performs a gui update
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def delete_slice(self, id):
        try:
            new_active_slice = self.reconstruction.delete_slice(id)
            if new_active_slice is None:
                self.set_active_slice_by_id(-1)
            else:
                self.set_active_slice_by_id(new_active_slice.id)
        # note that set_active_slice already performs a gui update
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def set_active_slice_by_id(self, id=-1):
        try:
            if id < 0:
                self.gui.slice_photo_widget.set_slice(slice=None)
                self.gui.update()
            else:
                for slice in self.reconstruction.slices:
                    if slice.id == id:
                        self.active_slice = slice
                        self.logger.info(f"setting slice to {self.active_slice.id}")
                        self.gui.slice_photo_widget.set_show_traces(True)
                        self.gui.slice_photo_widget.set_slice(slice=self.active_slice)
                        self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def remove_latest_trace_from_active_slice(self):
        '''

        :return:
        '''
        try:
            self.active_slice.remove_latest_trace()
            self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def load_reconstruction_from_pickle(self):
        try:

            self.reconstruction = Reconstruction.load_from_pickle(pickle_file_path=self.pickle_file_path, parent=self, logger=self.logger,
                                                                  macro_photo_path=self.macro_photo_path)
            self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def save_reconstruction_to_pickle(self):
        try:
            self.reconstruction.save_to_pickle(pickle_file_path=self.pickle_file_path)
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())


    def calc_foreground_background_mask(self):
        try:
            self.logger.info("Calc Foreground/Background Mask")
            self.active_slice.calc_foreground_background_mask()
            self.gui.slice_photo_widget.set_show_traces(False)
            self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def add_ruler_end(self, ruler_end_point):
        '''
        :param ruler_end_point: the ruler_end_point to be added to the reconstruction
        :return: None
        '''
        try:
            self.logger.info(f"{ruler_end_point}")
            self.reconstruction.add_ruler_point(ruler_end_point)
            self.gui.update()
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def save_reconstruction_as_json(self):
        '''
        Saving the reconstruction as json
        :return:
        '''
        try:
            data = self.reconstruction.get_dict_for_serialisation()

            s = json.dumps(data, indent='\t')
            # the section below removes some of the white spacing and new lines to make the json shorter and more readable
            s = re.sub(',$\n^([\t]+)(\w+)', r",\2", s, flags=re.M)
            s = re.sub('\[$\n^([\t]+)', r"[", s, flags=re.M)
            s = re.sub('$\n^([\t]+)\]', r"]", s, flags=re.M)

            with open(self.json_file_path, 'w') as outfile:
                outfile.write(s)

                self.logger.info(f"Wrote reconstruction to  {self.json_file_path}")
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())

    def load_reconstruction_from_json(self):
        '''
        Loading the reconstruction from the json_file_path, and update the GUI
        :return: None
        '''
        try:
            self.logger.info(f"Loading reconstruction from {self.json_file_path}")
            with open(self.json_file_path) as json_file:
                data = json.load(json_file)
            self.reconstruction = Reconstruction.create_from_dict(data,
                                                                  slide_score_api=self.slide_score_api,
                                                                  slide_score_user=self.slide_score_user,
                                                                  parent=self,
                                                                  logger=self.logger)
            self.active_slice = None
            self.gui.update()
            return
        except:
            self.logger.error(sys.exc_info()[0])
            self.logger.error(traceback.format_exc())
