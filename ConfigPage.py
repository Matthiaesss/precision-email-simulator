import yaml
from PySide2 import QtWidgets
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QFileDialog, QMessageBox

from PrecisionEmailSimulator import PrecisionEmailSimulator


class ConfigPage(QtWidgets.QWidget):

    def __init__(self):
        super(ConfigPage, self).__init__()
        self.ui = QUiLoader().load('resources/UI_files/config_page2.ui')
        self.ui.resize(600, 600)
        # variables
        self.study = dict({
            'emailListLocation': '',
            'emailResourceLocation': '',
            'saveLocation': '',
            'sessions': {},

        })
        self.currentSession = 'session1'
        self.ui.sessionSelectDB.addItem(self.currentSession)

        # =================== file loading section =================================
        self.ui.BrowseBtn_E.clicked.connect(lambda: self.browse_file(self.ui.emailPath, self.study, 'emailListLocation'))
        self.ui.BrowseBtn_R.clicked.connect(
            lambda: self.browse_folder(self.ui.resourcePath, self.study, 'emailResourceLocation'))
        self.ui.BrowseBtn_S.clicked.connect(lambda: self.browse_folder(self.ui.savePath, self.study, 'saveLocation'))

        # test for text change
        self.ui.emailPath.editingFinished.connect(
            lambda: self.update_text_field(self.ui.emailPath, self.study, 'emailListLocation'))
        self.ui.resourcePath.editingFinished.connect(
            lambda: self.update_text_field(self.ui.resourcePath, self.study, 'emailResourceLocation'))
        self.ui.savePath.editingFinished.connect(
            lambda: self.update_text_field(self.ui.savePath, self.study, 'saveLocation'))


        # twice because one for update after click on button
        # self.ui.htmlPath.editingFinished.connect(
        #     lambda: self.update_text_field(self.ui.htmlPath, self.study, 'emailHtmlLocation'))
        # self.ui.attachmentPath.editingFinished.connect(
        #     lambda: self.update_text_field(self.ui.attachmentPath, self.study, 'attachmentsLocation'))
        # self.ui.pisPath.editingFinished.connect(
        #     lambda: self.update_text_field(self.ui.pisPath, self.study, 'PISLocation'))
        # self.ui.instructionPath.editingFinished.connect(
        #     lambda: self.update_text_field(self.ui.instructionPath, self.study, 'instructionLocation'))
        # self.ui.savePath.editingFinished.connect(
        #     lambda: self.update_text_field(self.ui.savePath, self.study, 'saveLocation'))
        # update if user choose to type manually

        # ========================== session tab ===================================

        self.ui.addSessionBtn.clicked.connect(self.add_new_session)
        self.ui.sessionSelectDB.currentTextChanged.connect(self.session_selection_db_update)

        self.ui.sessionName.editingFinished.connect(
            lambda: self.update_session_name(self.ui.sessionName, self.get_current_session(), 'name'))

        self.ui.sessionDuration.editingFinished.connect(
            lambda: self.update_text_field(self.ui.sessionDuration, self.get_current_session(), 'duration'))
        self.ui.audioNotifications.editingFinished.connect(
            lambda: self.update_text_field(self.ui.audioNotifications, self.get_current_session(), 'audioNotification'))
        self.ui.incomingInterval.editingFinished.connect(
            lambda: self.update_text_field(self.ui.incomingInterval, self.get_current_session(), 'incomingInterval'))
        self.ui.taskPath.editingFinished.connect(
            lambda: self.update_text_field(self.ui.taskPath, self.get_current_session(), 'primaryTaskHtml'))
        self.ui.endSessionPopup.editingFinished.connect(
            lambda: self.update_text_field(self.ui.endSessionPopup, self.get_current_session(), 'endSessionPopup'))

        self.ui.incomingCB.clicked.connect(self.update_check_box_related_fields)
        self.ui.incomingCB.clicked.connect(
            lambda: self.update_check_box(self.ui.incomingCB, self.get_current_session(), 'incomingEmails'))
        self.ui.phishEmailCB.clicked.connect(self.update_check_box_related_fields)
        self.ui.phishEmailCB.clicked.connect(
            lambda: self.update_check_box(self.ui.phishEmailCB, self.get_current_session(), 'hasPhishEmails'))
        self.ui.timeCountDownCB.clicked.connect(
            lambda: self.update_check_box(self.ui.timeCountDownCB, self.get_current_session(), 'timeCountDown'))

        self.ui.starBtn.clicked.connect(
            lambda: self.update_check_box(self.ui.starBtn, self.get_current_session(), 'starBtn'))
        self.ui.reportBtn.clicked.connect(
            lambda: self.update_check_box(self.ui.reportBtn, self.get_current_session(), 'reportBtn'))
        self.ui.deleteBtn.clicked.connect(
            lambda: self.update_check_box(self.ui.deleteBtn, self.get_current_session(), 'deleteBtn'))
        self.ui.unreadBtn.clicked.connect(
            lambda: self.update_check_box(self.ui.unreadBtn, self.get_current_session(), 'unreadBtn'))

        self.ui.BrowseBtn_T.clicked.connect(
            lambda: self.browse_file(self.ui.taskPath, self.get_current_session(), 'primaryTaskHtml'))

        # ========================= legit emails tab =================================

        self.ui.listStart_L.editingFinished.connect(
            lambda: self.update_text_field(self.ui.listStart_L, self.get_current_legit().get('emailListRange'), 'start'))
        self.ui.listEnd_L.editingFinished.connect(
            lambda: self.update_text_field(self.ui.listEnd_L, self.get_current_legit().get('emailListRange'), 'finish'))
        self.ui.incomingStart_L.editingFinished.connect(
            lambda: self.update_text_field(self.ui.incomingStart_L, self.get_current_legit().get('incomingRange'), 'start'))
        self.ui.incomingEnd_L.editingFinished.connect(
            lambda: self.update_text_field(self.ui.incomingEnd_L, self.get_current_legit().get('incomingRange'), 'finish'))

        self.ui.shuffleCB_L.clicked.connect(
            lambda: self.update_check_box(self.ui.shuffleCB_L, self.get_current_legit(), 'shuffleEmails'))

        # ========================= phish emails tab =================================

        self.ui.emailNum_P.editingFinished.connect(
            lambda: self.update_text_field(self.ui.emailNum_P, self.get_current_phish(), 'emailListNum'))
        self.ui.emailList_P.editingFinished.connect(
            lambda: self.update_text_field(self.ui.emailList_P, self.get_current_phish(), 'emailList'))
        self.ui.emailLoc_P.editingFinished.connect(
            lambda: self.update_text_field(self.ui.emailLoc_P, self.get_current_phish(), 'emailListLocations'))
        self.ui.incomingNum_P.editingFinished.connect(
            lambda: self.update_text_field(self.ui.incomingNum_P, self.get_current_phish(), 'incomingNum'))
        self.ui.incoming_P.editingFinished.connect(
            lambda: self.update_text_field(self.ui.incoming_P, self.get_current_phish(), 'incomingList'))
        self.ui.incomingLoc_P.editingFinished.connect(
            lambda: self.update_text_field(self.ui.incomingLoc_P, self.get_current_phish(), 'incomingLocations'))

        self.ui.shuffleCB_P.clicked.connect(self.update_check_box_related_fields)
        self.ui.shuffleCB_P.clicked.connect(
            lambda: self.update_check_box(self.ui.shuffleCB_P, self.get_current_phish(), 'shuffleEmails'))

        self.ui.RandomLocCB.clicked.connect(self.update_check_box_related_fields)
        self.ui.RandomLocCB.clicked.connect(
            lambda: self.update_check_box(self.ui.RandomLocCB, self.get_current_phish(), 'randomLoc'))

        # ========================= Question marks =================================

        self.ui.audioNotificationQ.clicked.connect(lambda: message_notification('Information',
                                                                               'List of notification time to finish.\nFormat: integer separated by comma. \ne.g. 1, 5 means will have notification when there is 1 mins and 5 mins left.'))

        self.ui.invervalQ.clicked.connect(lambda: message_notification('Information',
                                                                      'The time between two incoming emails.\nThe interval is consistant between all incoming emails\ne.g. interval of 2 minutes means the first incoming email will come 2 minutes into the session, then the second would come at 4 mins in, until all incoming emails have been sent. \nNote: 1) make sure the incoming emails are sent before the session ends, 2) both legit and phish incoming emails are included, 3) minumum input = 0.1, i.e. 6 seconds between two incoming emails .'))

        self.ui.emailRangeQ.clicked.connect(lambda: message_notification('Information',
                                                                        'Enter the first and last email\'s id.\nThe email id should be interger.'))

        self.ui.emailListQ.clicked.connect(lambda: message_notification('Information',
                                                                       'Enter the list of phish emails.\nFormat: integer (phish email id) separated by comma. \ne.g. 1, 2 means selecting phish email with id 1 and 2.'))

        self.ui.pLocQ.clicked.connect(lambda: message_notification('Information',
                                                                  'Enter the corresponding location of phish emails in the list.\nFormat: integer separated by comma. \ne.g.'
                                                                  ' 1, 3 means the phish emails will be inserted at the 1st and 3rd position from top down. \nNote: please make'
                                                                  ' sure the number is less or equal to the number of phishing emails.e.g. phishing emails: 1,2,3,4; location 2,4,6,'
                                                                  ' means will display the first three phishing emails in the corresponding location, and skip the last one (because '
                                                                  'location is not given)'))

        self.ui.shufflePQ.clicked.connect(lambda: message_notification('Information',
                                                                      'randomise the order of phishing emails, need to specify the number of phishing emails added to the '
                                                                      'inbox.\ne.g. out of the n phishing emails specified in "phishing emails", randomly select x of them '
                                                                      'and add into the inbox. When location of the phishing emails are specified, the number should be consistant.'
                                                                      '\nNote: shuffling emails would apply to both phishing emails in the inbox, and incoming phishing emails.'))


        self.ui.saveConfigBtn.clicked.connect(self.save_config)
        self.ui.openConfigBtn.clicked.connect(self.load_config)
        # self.ui.previewBtn.clicked.connect(self.get_current_session)

        self.ui.previewBtn.clicked.connect(self.preview_study)

        self.add_new_session()

    # *********************************** Functions *********************************************

    # ======== load files and update fields ===================

    def browse_file(self, text_field, target, field):
        fname = QFileDialog.getOpenFileName(self, 'open file', './')
        text_field.setText(fname[0])
        self.update_text_field(text_field, target, field)

    def browse_folder(self, text_field, target, field):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        text_field.setText(file)
        self.update_text_field(text_field, target, field)

    @staticmethod
    def update_text_field(trigger, target, field):
        target.update({field: trigger.text()})

    @staticmethod
    def update_text_edit_field(trigger, target, field):
        target.update({field: trigger.toPlainText()})

    def update_session_name(self, trigger, target, field):
        index = self.ui.sessionSelectDB.currentIndex()
        self.update_text_field(trigger, target, field)
        self.ui.sessionSelectDB.setItemText(index, trigger.text())

    @staticmethod
    def update_check_box(trigger, target, field):
        target.update({field: trigger.isChecked()})

    def preview_study(self):
        email_app = PrecisionEmailSimulator()
        email_app.set_config(self.study)
        email_app.ui.show()

    # ========== getter ===============
    def get_current_session(self):
        return self.study.get('sessions').get(self.currentSession)

    def get_current_legit(self):
        return self.get_current_session().get('legitEmails')

    def get_current_phish(self):
        return self.get_current_session().get('phishEmails')

    # ======== session tab ===========
    def session_selection_db_update(self):
        if self.ui.sessionSelectDB.currentText() != '':
            for session in self.study.get('sessions'):
                if self.study.get('sessions').get(session).get('name') == self.ui.sessionSelectDB.currentText():
                    self.currentSession = session

            self.update_session_tab_ui()
            self.update_legit_tab_ui()
            self.update_phish_tab_ui()
            self.update_check_box_related_fields()

    def add_new_session(self):
        print('clicked')
        sessions = self.study.get('sessions')
        print(len(sessions))
        session_name = 'session' + str(len(sessions) + 1)
        print(session_name)
        sessions[session_name] = {
            'name': session_name,
            'duration': '',
            'audioNotification': '',
            'timeCountDown': False,
            'hasPhishEmails': False,
            'incomingEmails': False,
            'incomingInterval': '',
            'primaryTaskHtml': '',
            'endSessionPopup': '',
            'starBtn': True,
            'reportBtn': True,
            'deleteBtn': True,
            'unreadBtn': True,
            'legitEmails': {},
            'phishEmails': {},

        }
        self.currentSession = session_name

        self.add_new_legit()
        self.add_new_phish()

        self.ui.sessionSelectDB.addItem(self.currentSession)
        self.ui.sessionSelectDB.setCurrentText(self.currentSession)
        # self.updateTable()

    def update_check_box_related_fields(self):

        if self.ui.phishEmailCB.isChecked():
            self.ui.phishEmailWidget.show()
        else:
            self.ui.phishEmailWidget.hide()

        # overall presence of incoming emails
        if self.ui.incomingCB.isChecked():
            self.ui.incomingIntervalBox.show()
            self.ui.incomingWidget_L.show()
            self.ui.incomingWidget_P.show()
        else:
            self.ui.incomingIntervalBox.hide()
            self.ui.incomingWidget_L.hide()
            self.ui.incomingWidget_P.hide()

        # phishing email shuffles
        if self.ui.shuffleCB_P.isChecked():
            self.ui.pListNumBox.show()
            self.ui.pIncomingNumBox.show()
        else:
            self.ui.pListNumBox.hide()
            self.ui.pIncomingNumBox.hide()

        # phishing email random locations
        if self.ui.RandomLocCB.isChecked():
            self.ui.pListLocBox.hide()
            self.ui.pIncomingLocBox.hide()
        else:
            self.ui.pListLocBox.show()
            self.ui.pIncomingLocBox.show()

    # ========================================================================
    def add_new_legit(self):

        self.get_current_session()['legitEmails'] = {
            'emailListRange': {'start': '', 'finish': ''},
            'shuffleEmails': False,
            'incomingRange': {'start': '', 'finish': ''},
        }

        print(self.get_current_session())

        self.update_check_box_related_fields()

        # update the dictionary

    def add_new_phish(self):

        self.get_current_session()['phishEmails'] = {
            'emailList': '',
            'randomLoc': False,
            'emailListLocations': '',
            'shuffleEmails': False,
            'emailListNum': '',

            'incomingList': '',
            'incomingLocations': '',
            'incomingNum': '',

        }
        self.update_check_box_related_fields()

    # ================================================================

    def check_data_type(self):
        integer_field = [self.ui.sessionDuration, self.ui.listStart_L, self.ui.listEnd_L,
                        self.ui.incomingStart_L, self.ui.incomingEnd_L, self.ui.emailNum_P, self.ui.incomingNum_P]
        integer_list_field = [self.ui.audioNotifications, self.ui.emailList_P, self.ui.emailLoc_P, self.ui.incoming_P,
                            self.ui.incomingLoc_P]
        float_field = [self.ui.incomingInterval]

        for element in integer_field:
            if (not element.text().isdigit()) and (element.text() != ''):
                message_notification('Error', 'input field ' + element.objectName() + ' should be integers only')
                return False

        for element in float_field:
            if element.text() != '':
                try:
                    float(element.text())

                except ValueError:
                    message_notification('Error', 'input field ' + element.objectName() + ' should be a number')
                    return False

            # if (not isinstance(element, (int,float))) and (element.text() != ''):
            #     print(element)
            #     print(ty)
            #     message_notification('Error', 'input field ' + element.objectName() + ' should be a number')
            #     return False

        for element in integer_list_field:
            if not element.text() == '':
                ls = element.text().split(',')
                print(element.objectName())
                print(ls)
                for item in ls:
                    if not item.strip().isdigit():
                        message_notification('Error',
                                            'input field ' + element.objectName() + ' should be integers separated by comma')
                        return False

        if self.ui.sessionDuration.text() != '':
            for audioNotificationTime in self.ui.sessionDuration.text().split(','):
                if int(audioNotificationTime) > int(self.ui.sessionDuration.text()):
                    message_notification('Error', 'All audio notification times most be less than the sesison duration')

                    return False

        return True

    def save_config(self):
        print(self.study)
        if self.check_data_type():

            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getSaveFileName(self, "Save config file", "./",
                                                      "All Files (*);;", options=options)
            if file_name:
                if file_name[-5:] != '.yaml':
                    file_name = file_name + '.yaml'

                with open(file_name, 'w') as file:
                    yaml.dump(self.study, file, sort_keys=False)

    def load_config(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if file_name:
            with open(file_name) as f:
                self.study = yaml.load(f, Loader=yaml.SafeLoader)

            self.currentSession = list(self.study.get('sessions').keys())[0]
            print('get current session')
            print(self.currentSession)

            self.update_load_file_section()
            self.update_session_select_db_text()
            self.ui.sessionSelectDB.setCurrentText(self.study.get('sessions').get(self.currentSession).get('name'))
            self.update_check_box_related_fields()
            # self.updateSessionTabUi()

    def update_load_file_section(self):

        self.ui.emailPath.setText(self.study.get('emailListLocation'))
        self.ui.resourcePath.setText(self.study.get('emailResourceLocation'))
        self.ui.savePath.setText(self.study.get('saveLocation'))

    def update_session_select_db_text(self):
        self.ui.sessionSelectDB.clear()
        for session in self.study.get('sessions'):
            self.ui.sessionSelectDB.addItem(self.study.get('sessions').get(session).get('name'))
        self.ui.sessionSelectDB.setCurrentText(self.currentSession)

    def update_session_tab_ui(self):
        self.ui.sessionName.setText(self.get_current_session().get('name'))
        self.ui.sessionDuration.setText(self.get_current_session().get('duration'))
        self.ui.audioNotifications.setText(self.get_current_session().get('audioNotification'))
        self.ui.incomingInterval.setText(self.get_current_session().get('incomingInterval'))
        self.ui.endSessionPopup.setText(self.get_current_session().get('endSessionPopup'))
        self.ui.taskPath.setText(self.get_current_session().get('primaryTaskHtml'))

        self.ui.phishEmailCB.setChecked(self.get_current_session().get('hasPhishEmails'))
        self.ui.incomingCB.setChecked(self.get_current_session().get('incomingEmails'))
        self.ui.timeCountDownCB.setChecked(self.get_current_session().get('timeCountDown'))

    def update_legit_tab_ui(self):

        self.ui.listStart_L.setText(self.get_current_legit().get('emailListRange').get('start'))
        self.ui.listEnd_L.setText(self.get_current_legit().get('emailListRange').get('finish'))
        self.ui.incomingStart_L.setText(self.get_current_legit().get('incomingRange').get('start'))
        self.ui.incomingEnd_L.setText(self.get_current_legit().get('incomingRange').get('finish'))

        self.ui.shuffleCB_L.setChecked(self.get_current_legit().get('shuffleEmails'))

    def update_phish_tab_ui(self):

        self.ui.emailNum_P.setText(self.get_current_phish().get('emailListNum'))
        self.ui.emailList_P.setText(self.get_current_phish().get('emailList'))
        self.ui.emailLoc_P.setText(self.get_current_phish().get('emailListLocations'))
        self.ui.incomingNum_P.setText(self.get_current_phish().get('incomingNum'))
        self.ui.incoming_P.setText(self.get_current_phish().get('incomingList'))
        self.ui.incomingLoc_P.setText(self.get_current_phish().get('incomingLocations'))

        self.ui.shuffleCB_P.setChecked(self.get_current_phish().get('shuffleEmails'))
        self.ui.RandomLocCB.setChecked(self.get_current_phish().get('randomLoc'))


def check_nums_between(num1, num2, data):
    return data.loc[(data['ID'] >= num1) & (data['ID'] <= num2)].shape[0]


def delete_items_of_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                delete_items_of_layout(item.layout())


def message_notification(message_type, text):
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Information)
    msg_box.setText(text)
    msg_box.setWindowTitle(message_type)
    msg_box.setStandardButtons(QMessageBox.Ok)
    return_value = msg_box.exec()
    if return_value == QMessageBox.Ok:
        print('OK clicked')


if __name__ == '__main__':
    app = QApplication([])
    mainWindow = ConfigPage()
    mainWindow.ui.show()
    app.exec_()
