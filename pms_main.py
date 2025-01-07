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

import pms_task_window


class PrecisionEmailSimulator(QtWidgets.QWidget):

    def __init__(self):
        super(PrecisionEmailSimulator, self).__init__()
        self.ui = QUiLoader().load('resources/UI_files/welcome.ui')
        self.config = None
        self.imotion_connection = True
        self.mouse_and_keyboard = True

        self.ui.startBtn.clicked.connect(self.start)
        self.ui.loadConfigBtn.clicked.connect(self.load_config)

        self.ui.instructionText.setHidden(True)
        self.ui.pisText.setHidden(True)
        self.ui.sensorsWidget.hide()

        self.ui.imotionConnectBtn.clicked.connect(partial(self.start_imotion_connection, self.ui.imotionLabel))

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
        #
        self.start_recording = False

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
        if self.mouse_and_keyboard:
            self.mouse_activity()
            self.keyboard_activity()

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
            user_results_dir = f"./{self.config.get('saveLocation')}/no_user_name/{self.start_time.strftime('%d-%m-%Y_%H-%M-%S')}"
            Path(user_results_dir).mkdir(parents=True, exist_ok=True)
            self.user_results_dir = user_results_dir + '/'

    def setup_user_results_dir(self):
        # setup csv files in user results dir
        if self.imotion_connection:
            self.eye_data.to_csv(self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_eye.csv', index=False)
            # self.shimmer_data.to_csv(self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_shimmer.csv',
            #                         index=False)
        if self.mouse_and_keyboard:
            self.mouse_data.to_csv(self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_mouse.csv',
                                   index=False)
            self.keyboard_data.to_csv(self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_keyboard.csv',
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
        background_thread.deamon = True
        background_thread.start()

    def mouse_activity(self):

        def on_click(x, y, button, pressed):
            # print('c')
            if self.start_recording:
                self.mouse_data = self.mouse_data.append(
                    {'timestamp': time.time() * 1000, 'mouse_event': 'click', 'x': x, 'y': y, 'button': str(button),
                     'pressed': pressed, 'scroll_x': None,
                     'scroll_y': None}, ignore_index=True)

                if self.mouse_data.shape[0] > 20:
                    print(self.user_results_dir)
                    self.mouse_data.to_csv(
                        self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_mouse.csv',
                        mode='a', header=False,
                        index=False)
                    self.mouse_data = self.mouse_data.iloc[0:0]

        def on_scroll(x, y, dx, dy):
            if self.start_recording:
                self.mouse_data = self.mouse_data.append(
                    {'timestamp': time.time() * 1000, 'mouse_event': 'scroll', 'x': x, 'y': y, 'button': None,
                     'pressed': None, 'scroll_x': dx,
                     'scroll_y': dy}, ignore_index=True)
                if self.mouse_data.shape[0] > 20:
                    self.mouse_data.to_csv(
                        self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_mouse.csv',
                        mode='a', header=False,
                        index=False)
                    self.mouse_data = self.mouse_data.iloc[0:0]

        listener = mouse.Listener(on_click=on_click, on_scroll=on_scroll)
        listener.start()

    def keyboard_activity(self):
        def on_press(key):
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
                        self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_keyboard.csv',
                        mode='a', header=False,
                        index=False)
                    self.keyboard_data = self.keyboard_data.iloc[0:0]

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

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
                                    self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_eye.csv',
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
                        #             self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_shimmer.csv',
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
                                    self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_mouse.csv',
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
                                    self.user_results_dir + self.start_time.strftime("%d-%m-%Y_%H-%M-%S") + '_keyboard.csv',
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


if __name__ == '__main__':
    app = QApplication(sys.argv + ["--no-sandbox"])
    main_window = PrecisionEmailSimulator()
    main_window.ui.show()
    app.exec()
