import logging
import os
import sys
import time
import serial
import threading
import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QPushButton
import cv2
from pyzbar import pyzbar
from GUI.camera_final import Ui_Form

from configs.constants import *


class ReadSerial(threading.Thread):
    def __init__(self, ser_port, com_baud):
        threading.Thread.__init__(self)
        self.ser_port = ser_port
        self.com_baud = com_baud
        self.flag = False
        self.data = None
        try:
            self.ser_com = serial.Serial(
                port=self.ser_port,
                baudrate=self.com_baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.0009
            )
        except Exception as exx:
            print(exx, 'Error serial')

    def get_ser_com(self):
        return self.ser_com

    def get_ser_port(self):
        return self.ser_port

    def get_com_baud(self):
        return self.com_baud

    def get_data(self):
        return self.ser_com.readline()

    def send_data(self, data_send):
        self.ser_com.write(data_send)


def get_current_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

exe_path = os.path.abspath(os.path.dirname(__file__))
icon_path = os.path.join(exe_path, "GUI\Logo.ico")
log_path = os.path.join(exe_path, "logs")
config_path = os.path.join(exe_path, "configs\config-serial.txt")


def create_new_log_file():
    log_filename = f"./logs/app_{get_current_date()}.log"
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    return file_handler


logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

logger.addHandler(create_new_log_file())


class MyApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flag_reset = False
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.gray = None
        self.res = None
        self.frame = None
        self.thresh = None
        self.code_scan = None
        self.result_item1 = None
        self.flag_cam_scan = True
        self.flag_weighted = False
        self.flag_weighted1 = False
        self.quantity = 0
        self.scan_pass = 0
        self.config = []
        self.configValue()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)
        self.setWindowTitle('S4-200')
        self.serial_plc = ReadSerial(self.config[0], 9600)
        self.sfc_send = ReadSerial(self.config[1], 9600)
        self.sfc_receive = ReadSerial(self.config[2], 9600)
        self.machine2 = ReadSerial(self.config[3], 9600)
        self.machine3 = ReadSerial(self.config[4], 9600)
        self.ThreadCam = threading.Thread(target=self.Camera)
        self.ThreadSfc = threading.Thread(target=self.receiveSignalSfc)
        self.ThreadPlc = threading.Thread(target=self.receivePlc)
        self.ThreadCam.start()
        self.ThreadPlc.start()
        self.ThreadSfc.start()
        self.changeStatus(status_wait)
        self.close_button = QPushButton("Close Application")
        self.close_button.clicked.connect(self.close_application)
        # self.serial_plc.send_data(b'6')

    def close_application(self):
        self.close()

    def closeEvent(self, event):
        os._exit(0)
        event.accept()

    def Camera(self):
        while True:
            self.res, self.frame = self.cap.read()
            if self.res:
                height, width, channel = self.frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
                pixmap = QPixmap.fromImage(q_image)
                pixmap = pixmap.scaled(self.ui.camera.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
                self.ui.camera.setPixmap(pixmap)
                self.gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                (_, self.thresh) = cv2.threshold(self.gray, 80, 255, cv2.THRESH_BINARY)

    def saveImage(self, name):
        cv2.imwrite(name, self.frame)

    def read_data_pyzbar(self):
        data = pyzbar.decode(self.frame)
        if len(data) > 0:
            data = data[0].data.decode('utf-8')
            return data
        else:
            data = pyzbar.decode(self.gray)
            if len(data) > 0:
                data = data[0].data.decode('utf-8')
                return data
            else:
                data = pyzbar.decode(self.thresh)
                if len(data) > 0:
                    data = data[0].data.decode('utf-8')
                    return data
                else:
                    return None

    # B1: plc đặt hàng lên cân
    def receiveSignalSfc(self):
        print('... bắt đầu cân')
        # máy 1 chờ cân xong
        while True:
            data_sfc = self.sfc_receive.get_data()
            if len(data_sfc) > 0:
                print('data tu sfc: ', data_sfc)
            if data_sfc == sfc_weighted:
                try:
                    self.changeStatus(status_wait)
                except Exception as ex:
                    print('-----------Error UI ChangeStatus--------', ex)
                # chờ cân từ máy 2
                print('chờ máy 2 cân xong...')
                self.flag_reset = False
                self.flag_weighted1 = False
                while True:
                    data_weight2 = self.machine2.get_data()
                    if len(data_weight2) > 0:
                        print('tin hieu may 2: ', data_weight2)
                    if ((data_weight2 == sfc_weighted) | (
                            data_weight2 == sfc_weighted_demo)):
                        print('máy 2 ok, gửi cân xong cho plc...')
                        self.serial_plc.send_data(plc_scan)
                        self.flag_weighted = True
                        break
                    if self.flag_reset:
                        self.flag_reset = False
                        break
            # Cần cân xong thì mới đọc tín hiệu sfc trả về khi scan
            elif (data_sfc == sfc_OK) and self.flag_cam_scan:
                self.result_item1 = sfc_OK
                self.machine3.send_data(b'X6LPY7MCQX')
                self.flag_cam_scan = False
                # Cho s4-190
                # while True:
                #     signal_machine3 = self.machine3.get_data()
                #     if len(signal_machine3) > 0:
                #         print('tín hiệu từ machine 3: ', signal_machine3)
                #     if signal_machine3 == s4_190_OK:
                #         print('S4-190 PASS')
                #         self.result_item1 = sfc_OK
                #         break
                #     elif signal_machine3 == s4_190_NG:
                #         print('S4-190 NG SFC')
                #         self.changeStatus(status_ng_sfc_s4_190)
                #         self.result_item1 = sfc_NG
                #         break
                #     elif signal_machine3 == s4_190_NG_cam:
                #         print('S4-190 NG CAMERA')
                #         self.changeStatus(status_ng_cam_s4_190)
                #         self.result_item1 = sfc_NG
                #         break

                print('chờ máy 2 scan xong...')
                while True:
                    result_machine2 = self.machine2.get_data()
                    if len(result_machine2) > 0:
                        print('tin hieu may 2: ', result_machine2)
                    if result_machine2 == sfc_NG:
                        if self.result_item1 == sfc_OK:
                            self.serial_plc.send_data(b'7')
                        else:
                            self.serial_plc.send_data(b'8')
                        print('máy 2 gửi NG', result_machine2)
                        logger.warning('result from machine 2: ' + str(sfc_NG))
                        break
                    elif result_machine2 == sfc_OK:
                        if self.result_item1 == sfc_OK:
                            self.serial_plc.send_data(b'5')
                        else:
                            self.serial_plc.send_data(b'6')
                        print('máy 2 gửi OK', result_machine2)
                        logger.info('result from machine 2: ' + str(sfc_OK))
                        break
                    if self.flag_reset:
                        self.flag_reset = False
                        break
            elif data_sfc == sfc_NG:
                self.result_item1 = sfc_NG
                print('máy 1: chờ máy 2 scan xong...')
                while True:
                    result_machine2 = self.machine2.get_data()
                    if len(result_machine2) > 0:
                        print('tin hieu may 2')
                    if result_machine2 == sfc_NG:
                        print('máy 2 gửi NG', result_machine2)
                        self.serial_plc.send_data(b'8')
                        print('-----------NGNG-----------')
                        logger.warning('result from machine 2: ' + str(sfc_NG))
                        break
                    elif result_machine2 == sfc_OK:
                        self.serial_plc.send_data(b'6')
                        print('-----------NGOK-----------')
                        print('máy 2 gửi OK', result_machine2)
                        logger.info('result from machine 2: ' + str(sfc_OK))
                        break
                    if self.flag_reset:
                        self.flag_reset = False
                        break

    def receivePlc(self):
        print('Chờ tín hiệu từ plc....')
        while True:
            signal_plc = self.serial_plc.get_data()
            if len(signal_plc) > 0:
                print('tín hiệu từ plc: ', signal_plc)
            if signal_plc == plc_scan_receive:
                # print('máy 1: Nhận tín hiệu scan từ plc, gửi tín hiệu scan cho máy 2 và s4-190')
                self.code_scan = None
                print('gui scan cho may 2')
                self.machine2.send_data(b'4')
                # self.machine3.send_data(s4_190_scan)
                print('máy 1 bắt đầu scan...')
                # if self.res:
                if self.res:
                    i = 0
                    while i < 5:
                        self.code_scan = self.read_data_pyzbar()
                        if self.code_scan is None:
                            i += 1
                        else:
                            break
                    print('da vao scan ma QR')
                print('máy 1: QR:', self.code_scan)
                self.quantity += 1
                # Trường hợp quét qr lỗi
                if self.code_scan is None:
                    self.changeStatus(status_ng_cam)
                    # self.machine3.send_data(s4_200_NG_cam)
                    logger.error('error scan camera 1')
                    self.code_scan = 'X6LPY7MCQX'
                    self.sfc_send.send_data(b'X6LPY7MCQX')
                    self.result_item1 = sfc_NG
                    self.machine3.send_data(s4_190_scan)
                    # self.saveImage('images/img_ng/cam1_%s.png' % time.time())
                    self.flag_cam_scan = True
                    self.flag_weighted = False
                    try:
                        self.ui.quantity.setText('%s/%s' % (str(self.scan_pass), str(self.quantity)))
                    except Exception as ex:
                        print('-----------Error UI Quantity--------', ex)
                # quét qr thành công
                elif len(self.code_scan) > 0:
                    self.scan_pass += 1
                    print('máy 1 scan xong, gửi tín hiệu cho sfc...')
                    self.sfc_send.send_data(self.code_scan.encode('utf-8'))
                    self.result_item1 = sfc_OK
                    self.machine3.send_data(s4_190_scan)
                    self.flag_cam_scan = True
                    self.flag_weighted = False
                    try:
                        self.changeStatus(status_pass)
                        self.ui.quantity.setText('%s/%s' % (str(self.scan_pass), str(self.quantity)))
                    except Exception as ex:
                        print('----------- Error elif code scan > 0 --------', ex)

            elif (signal_plc == plc_reset_receive) | (signal_plc == plc_test_reset):
                self.flag_reset = True
                print('-------RESET---------')
                try:
                    self.changeStatus(status_reset)
                except Exception as ex:
                    print('-----------Error UI ChangeStatus reset--------', ex)
                self.machine2.send_data(plc_reset)
                self.serial_plc.send_data(plc_reset)
                if self.flag_weighted1:
                    self.sfc_send.send_data(b'X6LPY7MCQX')
                self.machine3.send_data(plc_reset)

    def changeStatus(self, status):
        # css_fail = "QLabel { border: 1px solid rgb(85, 0, 0);color: #fff; background-color: rgb(247, 56, 59);}"
        # css_ok = "QLabel { border: 1px solid rgb(85, 0, 0);color: #fff; background-color: rgb(69, 208, 102);}"
        # css_wait = "QLabel { border: 1px solid rgb(85, 0, 0);color:  rgb(30, 30, 30); background-color: rgb(221, 221, " \
        #            "110); } "
        # css_reset = "QLabel { border: 1px solid rgb(85, 0, 0);color: rgb(0, 85, 255); background-color: rgb(255, 228, " \
        #             "90); } "

        if status == status_wait:
            self.ui.result.setStyleSheet("QLabel { border: 1px solid rgb(85, 0, 0);color:  rgb(30, 30, 30); background-color: rgb(221, 221, " \
                   "110); } ")
        elif status == status_pass:
            self.ui.result.setStyleSheet("QLabel { border: 1px solid rgb(85, 0, 0);color: #fff; background-color: rgb(69, 208, 102);}")
        elif status == status_reset:
            self.ui.result.setStyleSheet("QLabel { border: 1px solid rgb(85, 0, 0);color: rgb(0, 85, 255); background-color: rgb(255, 228, " \
                    "90); } ")
        elif (status == status_ng_cam) | (status == status_ng_sfc) | (status == status_ng_cam_s4_190) | (
                status == status_ng_sfc_s4_190):
            self.ui.result.setStyleSheet("QLabel { border: 1px solid rgb(85, 0, 0);color: #fff; background-color: rgb(247, 56, 59);}")
        self.ui.result.setText(status)

    # Wait:  rgb(141, 141, 0)

    def configValue(self):
        f = open(config_path)
        arr = f.readlines()
        for i in arr:
            self.config.append(i.split()[1])
        f.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApplication()
    window.setWindowFlags(window.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    # lấy kích thước màn hình
    desktop = QDesktopWidget()
    screen_width = desktop.screenGeometry().width()
    screen_height = desktop.screenGeometry().height()

    # Lấy kích thước cửa sổ
    window_width = window.frameGeometry().width()
    window_height = window.frameGeometry().height()

    # Thiết lập vị trí xuất hiện ở góc dưới bên phải
    x = screen_width - window_width
    y = screen_height - window_height - 70
    window.move(x, y)
    window.show()
    sys.exit(app.exec_())
