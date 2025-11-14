import datetime
import socket
import sys
import threading
import time
from functools import partial
from pathlib import Path

import pandas as pd
import yaml
from PySide6 import QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from pynput import mouse, keyboard

try:
    import tobii_research
    TOBII_AVAILABLE = True
except ImportError:
    TOBII_AVAILABLE = False
    print("Warning: tobii-research not available. Tobii Pro Fusion support disabled.")

import pms_task_window


class PrecisionEmailSimulator(QtWidgets.QWidget):
    def __init__(self):
        super(PrecisionEmailSimulator, self).__init__()
        self.ui = QUiLoader().load('resources/UI_files/welcome.ui')
        self.config = None
        self.imotion_connection = True
        self.tobii_connection = True
        self.tobii_eyetracker = None
        self.mouse_and_keyboard = True

        self.ui.startBtn.clicked.connect(self.start)
        self.ui.loadConfigBtn.clicked.connect(self.load_config)

        self.ui.instructionText.setHidden(True)
        self.ui.pisText.setHidden(True)
        self.ui.sensorsWidget.hide()

        self.ui.imotionConnectBtn.clicked.connect(partial(self.start_imotion_connection, self.ui.imotionLabel))
        
        # Tobii Pro Fusion connection
        if TOBII_AVAILABLE:
            self.ui.tobiiConnectBtn.clicked.connect(partial(self.start_tobii_connection, self.ui.tobiiLabel))
        else:
            self.ui.tobiiConnectBtn.setEnabled(False)
            self.ui.tobiiLabel.setText("Tobii Pro Fusion: Library not available")

        self.user_results_dir = ''
        # eye tracker data is collected through iMotion
        self.eye_columns = ['timestamp', 'timestamp_device', 'GazeLeftX', 'GazeLeftY', 'GazeRightX', 'GazeRightY',
                           'LeftPupilDiameter', 'RightPupilDiameter', 'LeftEyeDistance', 'RightEyeDistance',
                           'LeftEyePosX', 'LeftEyePosY', 'RightEyePosX', 'RightEyePosY']
        self.eye_data = pd.DataFrame(columns=self.eye_columns)

        # shimmer data is collected through iMotion
        self.shimmer_columns = ['timestamp', 'timestamp_device', 'VSenseBatt RAW', 'VSenseBatt CAL',
                               'Internal ADC A13 PPG RAW', 'Internal ADC A13 PPG CAL', 'GSR RAW', 'GSR Resistance CAL',
                               'GSR Conductance CAL', 'Heart Rate PPG ALG', 'IBI PPG ALG']
        self.shimmer_data = pd.DataFrame(columns=self.shimmer_columns)

        self.mouse_columns = ['timestamp', 'mouse_event', 'x', 'y', 'button', 'pressed', 'scroll_x', 'scroll_y']
        self.mouse_data = pd.DataFrame(columns=self.mouse_columns)

        self.keyboard_columns = ['timestamp', 'keys']
        self.keyboard_data = pd.DataFrame(columns=self.keyboard_columns)

        self.start_time = datetime.datetime.now()

        self.start_recording = False

        def _on_click(x, y, button, pressed):
            if self.start_recording:
                self.mouse_data = self.mouse_data.append(
                    {'timestamp': time.time() * 1000, 'mouse_event': 'click', 'x': x, 'y': y, 'button': str(button),
                     'pressed': pressed, 'scroll_x': None,
                     'scroll_y': None}, ignore_index=True)

                if self.mouse_data.shape[0] > 20:
                    print(self.user_results_dir)
                    self.mouse_data.to_csv(
                        self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_mouse.csv',
                        mode='a', header=False,
                        index=False)
                    self.mouse_data = self.mouse_data.iloc[0:0]

        def _on_scroll(x, y, dx, dy):
            if self.start_recording:
                self.mouse_data = self.mouse_data.append(
                    {'timestamp': time.time() * 1000, 'mouse_event': 'scroll', 'x': x, 'y': y, 'button': None,
                     'pressed': None, 'scroll_x': dx,
                     'scroll_y': dy}, ignore_index=True)
                if self.mouse_data.shape[0] > 20:
                    self.mouse_data.to_csv(
                        self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_mouse.csv',
                        mode='a', header=False,
                        index=False)
                    self.mouse_data = self.mouse_data.iloc[0:0]

        def _on_press(key):
            if self.start_recording:
                try:
                    # Handle character keys
                    self.keyboard_data = self.keyboard_data.append({'timestamp': time.time() * 1000, 'keys': str(key.char)}, ignore_index=True)
                except AttributeError:
                    # Handle special keys (e.g., ctrl, alt, etc.)
                    self.keyboard_data = self.keyboard_data.append({'timestamp': time.time() * 1000, 'keys': str(key)}, ignore_index=True)

                if self.keyboard_data.shape[0] > 20:
                    print(self.user_results_dir)
                    self.keyboard_data.to_csv(
                        self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_keyboard.csv',
                        mode='a', header=False,
                        index=False)
                    self.keyboard_data = self.keyboard_data.iloc[0:0]

        self.mouse_listener = mouse.Listener(on_click=_on_click, on_scroll=_on_scroll)
        self.keyboard_listener = keyboard.Listener(on_press=_on_press)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def set_config(self, config):
        self.config = config
        self.update_ui()

    def load_config(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "*.yaml", options=options)
        if file_name:
            with open(file_name) as f:
                self.config = yaml.load(f, Loader=yaml.SafeLoader)
                self.update_ui()

    def update_ui(self):
        if self.config.get('welcomeText') != '':
            self.ui.welcomeText.setText(self.config.get('welcomeText'))
        self.user_results_dir = self.config.get('saveLocation')
        self.ui.sensorsWidget.show()

    def start(self):
        self.start_recording = True
        self.make_user_results_dir()
        self.setup_user_results_dir()

        study = pms_task_window.TaskWindow(self.ui.usernameBox.text(), self.config)

        study.ui.show()
        study.activateWindow()
        self.ui.close()

        # self.login_ui = QUiLoader().load('resources/UI_files/login.ui')
        # self.login_ui.show()
        #
        # self.ui.hide()
        #
        # self.login_ui.loginBtn.clicked.connect(self.verify_login)

    def make_user_results_dir(self):
        if self.ui.usernameBox.text() != '':
            user_results_dir = f"./{self.config.get('saveLocation')}/{self.ui.usernameBox.text()}"
            Path(user_results_dir).mkdir(parents=True, exist_ok=True)
            self.user_results_dir = user_results_dir + '/'
        else:
            user_results_dir = f"./{self.config.get('saveLocation')}/no_user_name/{self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}')}"
            Path(user_results_dir).mkdir(parents=True, exist_ok=True)
            self.user_results_dir = user_results_dir + '/'

    def setup_user_results_dir(self):
        # setup csv files in user results dir
        if self.imotion_connection or (TOBII_AVAILABLE and self.tobii_eyetracker is not None):
            self.eye_data.to_csv(self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_eye.csv', index=False)
            # self.shimmer_data.to_csv(self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_shimmer.csv',
            #                         index=False)
        if self.mouse_and_keyboard:
            self.mouse_data.to_csv(self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_mouse.csv',
                                   index=False)
            self.keyboard_data.to_csv(self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_keyboard.csv',
                                      index=False)

    def verify_login(self):
        if self.login_ui.username.text() == 'uoavrclub@auckland.ac.nz' and self.login_ui.password.text() == 'VrClub123':
            study = pms_task_window.TaskWindow(self.ui.usernameBox.text(), self.config)
            self.start_recording = True

            study.ui.show()
            study.activateWindow()
            self.login_ui.close()
            self.ui.close()
        else:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText(
                "The combination of credentials you have entered is incorrect. \nPlease check that you have entered a valid University username \nor an email previously registered with us and your correct \npassword.")
            msg_box.setWindowTitle("Warning")
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.show()
            _ = msg_box.exec()

    def start_imotion_connection(self, label):
        print(label)
        background_thread = threading.Thread(target=self.imotion_connect, args=(label,))
        background_thread.daemon = True
        background_thread.start()

    def imotion_connect(self, label):
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('localhost', 8088)
        print('connecting to %s port %s' % server_address)
        sock.connect(server_address)
        label.setText("iMotion: Connected")

        # make user results dir (if it does not exist) and set up the dir
        self.make_user_results_dir()
        self.setup_user_results_dir()

        try:
            while self.imotion_connection:
                incoming_data_str = sock.recv(1024)

                d = incoming_data_str.decode().split("\r\n")
                for data_str in d:
                    data = data_str.split(";")
                    if self.start_recording:
                        if len(data) == 18:  # eye tracker data
                            row_df = pd.DataFrame(
                                [[time.time() * 1000, data[3], data[6], data[7], data[8], data[9], data[10],
                                  data[11], data[12], data[13], data[14], data[15], data[16], data[17]]],
                                columns=self.eye_columns)
                            self.eye_data = pd.concat([self.eye_data, row_df]).reset_index(drop=True)
                            if self.eye_data.shape[0] > 1000:
                                self.eye_data.to_csv(
                                    self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_eye.csv',
                                    mode='a',
                                    header=False, index=False)
                                self.eye_data = self.eye_data.iloc[0:0]
                        # elif len(data) == 19:  # shimmer data
                        #     row_df = pd.DataFrame(
                        #         [[time.time() * 1000, data[3], data[7], data[8], data[9], data[10], data[11],
                        #           data[12], data[13], data[14], data[15]]],
                        #         columns=self.shimmer_columns)
                        #     self.shimmer_data = pd.concat([self.shimmer_data, row_df]).reset_index(drop=True)
                        #     if self.shimmer_data.shape[0] > 1000:
                        #         self.shimmer_data.to_csv(
                        #             self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}' + '_shimmer.csv',
                        #             mode='a', header=False,
                        #             index=False)
                        #         self.shimmer_data = self.shimmer_data.iloc[0:0]
                        elif len(data) == 10:  # mouse data
                            row_df = pd.DataFrame(
                                [[time.time() * 1000, data[3], data[5], data[6], data[7], data[8]]],
                                columns=self.mouse_columns)
                            self.mouse_data = pd.concat([self.mouse_data, row_df]).reset_index(drop=True)
                            if self.mouse_data.shape[0] > 5:
                                self.mouse_data.to_csv(
                                    self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_mouse.csv',
                                    mode='a', header=False,
                                    index=False)
                                self.mouse_data = self.mouse_data.iloc[0:0]
                            print("mouse data")
                            print(data)
                        elif len(data) == 6:  # keyboard data
                            row_df = pd.DataFrame(
                                [[time.time() * 1000, data[3], data[5]]],
                                columns=self.keyboard_columns)
                            self.keyboard_data = pd.concat([self.keyboard_data, row_df]).reset_index(drop=True)
                            if self.keyboard_data.shape[0] > 5:
                                self.keyboard_data.to_csv(
                                    self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_keyboard.csv',
                                    mode='a', header=False,
                                    index=False)
                                self.keyboard_data = self.keyboard_data.iloc[0:0]
                        # elif len(data) != 1:
                        #     print('unknown type of data')
                        #     print(data)
                    # eye tracking data has 18 columns
                    # mouse has 10 columns
                    # shimmer has 19 columns
        finally:
            sock.close()

    def start_tobii_connection(self, label):
        """Start Tobii Pro Fusion connection in a background thread"""
        if not TOBII_AVAILABLE:
            label.setText("Tobii Pro Fusion: Library not available")
            return
        
        background_thread = threading.Thread(target=self.tobii_connect, args=(label,))
        background_thread.daemon = True
        background_thread.start()

    def tobii_connect(self, label):
        """Connect to Tobii Pro Fusion eye tracker"""
        try:
            # Find all eye trackers
            eyetrackers = tobii_research.find_all_eyetrackers()
            
            if len(eyetrackers) == 0:
                label.setText("Tobii Pro Fusion: No device found")
                QMessageBox.warning(None, "Tobii Connection", 
                                   "No Tobii eye tracker found. Please ensure:\n"
                                   "1. The Tobii Pro Fusion is connected\n"
                                   "2. Tobii Pro Eye Tracker Manager is running")
                return
            
            # Use the first available eye tracker
            self.tobii_eyetracker = eyetrackers[0]
            device_name = self.tobii_eyetracker.device_name
            print(f"Found Tobii eye tracker: {device_name}")
            
            # Update label
            label.setText(f"Tobii Pro Fusion: {device_name} - Connected")
            
            # Make user results dir (if it does not exist) and set up the dir
            self.make_user_results_dir()
            self.setup_user_results_dir()
            
            # Subscribe to gaze data (calibration is done through Tobii Manager)
            self.tobii_eyetracker.subscribe_to(tobii_research.EYETRACKER_GAZE_DATA, 
                                               self.tobii_gaze_data_callback, 
                                               as_dictionary=True)
            
            label.setText(f"Tobii Pro Fusion: {device_name} - Recording")
            print("Tobii Pro Fusion: Subscribed to gaze data")
            
            # Keep connection alive
            while self.tobii_connection and self.tobii_eyetracker is not None:
                time.sleep(0.1)
                
        except Exception as e:
            error_msg = f"Tobii connection error: {str(e)}"
            print(error_msg)
            label.setText("Tobii Pro Fusion: Connection error")
            QMessageBox.critical(None, "Tobii Error", error_msg)
            self.tobii_eyetracker = None

    def tobii_gaze_data_callback(self, gaze_data):
        """Callback function for Tobii gaze data"""
        if not self.start_recording or self.tobii_eyetracker is None:
            return
        
        try:
            # Extract gaze data
            left_gaze_point = gaze_data['left_gaze_point_on_display_area']
            right_gaze_point = gaze_data['right_gaze_point_on_display_area']
            left_pupil = gaze_data['left_pupil_diameter']
            right_pupil = gaze_data['right_pupil_diameter']
            left_gaze_origin = gaze_data['left_gaze_origin_in_user_coordinate_system']
            right_gaze_origin = gaze_data['right_gaze_origin_in_user_coordinate_system']
            left_gaze_origin_validity = gaze_data['left_gaze_origin_validity']
            right_gaze_origin_validity = gaze_data['right_gaze_origin_validity']
            left_gaze_point_validity = gaze_data['left_gaze_point_validity']
            right_gaze_point_validity = gaze_data['right_gaze_point_validity']
            system_time_stamp = gaze_data['system_time_stamp']
            
            # Handle invalid data (set to None/NaN if invalid)
            GazeLeftX = left_gaze_point[0] if left_gaze_point_validity == 1 else None
            GazeLeftY = left_gaze_point[1] if left_gaze_point_validity == 1 else None
            GazeRightX = right_gaze_point[0] if right_gaze_point_validity == 1 else None
            GazeRightY = right_gaze_point[1] if right_gaze_point_validity == 1 else None
            
            LeftPupilDiameter = left_pupil if left_gaze_point_validity == 1 else None
            RightPupilDiameter = right_pupil if right_gaze_point_validity == 1 else None
            
            # Calculate eye distance (Z coordinate from gaze origin)
            LeftEyeDistance = left_gaze_origin[2] if left_gaze_origin_validity == 1 else None
            RightEyeDistance = right_gaze_origin[2] if right_gaze_origin_validity == 1 else None
            
            # Eye position (X, Y from gaze origin)
            LeftEyePosX = left_gaze_origin[0] if left_gaze_origin_validity == 1 else None
            LeftEyePosY = left_gaze_origin[1] if left_gaze_origin_validity == 1 else None
            RightEyePosX = right_gaze_origin[0] if right_gaze_origin_validity == 1 else None
            RightEyePosY = right_gaze_origin[1] if right_gaze_origin_validity == 1 else None
            
            # Convert system timestamp from microseconds to milliseconds
            timestamp_device = system_time_stamp / 1000.0
            
            # Create data row matching the existing format
            row_df = pd.DataFrame(
                [[time.time() * 1000, timestamp_device, GazeLeftX, GazeLeftY, GazeRightX, GazeRightY,
                  LeftPupilDiameter, RightPupilDiameter, LeftEyeDistance, RightEyeDistance,
                  LeftEyePosX, LeftEyePosY, RightEyePosX, RightEyePosY]],
                columns=self.eye_columns)
            
            self.eye_data = pd.concat([self.eye_data, row_df]).reset_index(drop=True)
            
            # Batch write to CSV (same as iMotions)
            if self.eye_data.shape[0] > 1000:
                self.eye_data.to_csv(
                    self.user_results_dir + self.start_time.strftime(f'{pms_task_window.DATE_FORMAT}_{pms_task_window.LONG_TIME_FORMAT}') + '_eye.csv',
                    mode='a',
                    header=False, index=False)
                self.eye_data = self.eye_data.iloc[0:0]
                
        except Exception as e:
            print(f"Error processing Tobii gaze data: {str(e)}")

    def __del__(self):
        """Cleanup: Unsubscribe from Tobii if connected"""
        if TOBII_AVAILABLE and self.tobii_eyetracker is not None:
            try:
                self.tobii_eyetracker.unsubscribe_from(tobii_research.EYETRACKER_GAZE_DATA, 
                                                       self.tobii_gaze_data_callback)
            except:
                pass


if __name__ == '__main__':
    app = QApplication(sys.argv + ["--no-sandbox"])
    main_window = PrecisionEmailSimulator()
    main_window.ui.show()
    app.exec()
