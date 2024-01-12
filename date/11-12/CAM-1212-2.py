import os
import sys
import time

import serial
import logging
import threading
import datetime
import zxingcpp
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QPushButton
import cv2
from pyzbar import pyzbar
from GUI.camera_final import Ui_Form
import random
from configs.constants import *



icon = "D:\SD_CODE\GUI\Logo.ico"
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

exe_path = os.path.abspath(os.path.dirname(__file__))
icon_path = os.path.join(exe_path, "GUI\Logo.ico")

class MyApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flag_reset = False
        self.flag_scan2 = True
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.img = None
        self.gray = None
        self.frame = None
        self.res = None
        self.thresh = None
        self.code_scan = None
        self.result_item2 = None
        self.flag_weighted = False
        self.quantity = 0
        self.scan_pass = 0
        self.config = []
        self.configValue()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)
        self.setWindowTitle('S4-200')
        self.serial_sfc_send = ReadSerial(self.config[0], int(self.config[4]))
        self.serial_sfc_receive = ReadSerial(self.config[1], int(self.config[4]))
        self.machine1 = ReadSerial(self.config[2], int(self.config[4]))
        # self.machine4 = ReadSerial(self.config[3], int(self.config[4]))
        self.ThreadCam = threading.Thread(target=self.Camera)
        self.ThreadSfc = threading.Thread(target=self.signalSfc)
        self.ThreadMachine1 = threading.Thread(target=self.signalMachine1)

        self.ThreadCam.start()
        self.ThreadMachine1.start()
        self.ThreadSfc.start()
        self.changeStatus(status_wait)
        # self.close_button = QPushButton("Close Application")
        # self.close_button.clicked.connect(self.close_application)

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
                pixmap = pixmap.scaled(self.ui.camera.size(), Qt.KeepAspectRatio)
                self.ui.camera.setPixmap(pixmap)
                self.img = self.frame[200:400,50:300]
                self.gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
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

    def read_data_zxingcpp(self):
        # frame scan
        data = zxingcpp.read_barcode(self.frame)
        if data is not None:
            return data.text
        else:
            # gray
            data = zxingcpp.read_barcode(self.gray)
            if data is not None:
                return data.text
            else:
                data = zxingcpp.read_barcode(self.thresh)
                if data is not None:
                    return data.text
                else:
                    return self.read_data_pyzbar()

    # B1: plc đặt hàng lên cân
    def receiveSignalSfc(self):
        print('... bắt đầu cân')
        self.flag_scan2 = False
        self.flag_weighted = False
        # máy 2 chờ cân xong
        while True:
            signal_sfc = self.serial_sfc_receive.get_data()
            if len(signal_sfc) > 0:
                print('tin hieu sfc: ', signal_sfc)
            if signal_sfc == '0':
                self.changeStatus(status_wait)
                print('lỗi cân 2')
                logger.error('error weight 2')
            elif signal_sfc == sfc_weighted:
                self.changeStatus(status_wait)
                print('đây là tín hiệu cân từ sfc', signal_sfc)
                self.machine1.send_data(sfc_weighted)
                self.flag_weighted = True

    def receiveSignalMachine1(self):
        print('Chờ tín hiệu máy 1')
        while True:
            signal_machine1 = self.machine1.get_data()
            if len(signal_machine1) > 0:
                print('Đây là tín hiệu từ máy 1: ', signal_machine1)
            if signal_machine1 == plc_scan:
                # self.machine4.send_data(s4_190_scan)
                print('machine 1 bắt đầu scan...')
                if self.res:
                    i = 0
                    while i < 10:
                        self.code_scan = self.read_data_zxingcpp()
                        if self.code_scan is None:
                            i += 1
                        else:
                            break
                    print('máy 2: QR:', self.code_scan)
                    self.quantity += 1
                    self.ui.quantity.setText('%s/%s' %(str(self.scan_pass), str(self.quantity)))
                # Trường hợp quét qr lỗi
                if self.code_scan is None:
                    # self.result_item2 = sfc_NG
                    # self.flag_scan2 = False
                    print('Lỗi không scan được......')
                    self.serial_sfc_send.send_data(b'X6LPY7MCQX')
                    self.changeStatus(status_ng_cam)
                    # self.machine4.send_data(s4_200_NG_cam)
                    # self.saveImage('images/img_ng/cam2_%s.png' % time.time())
                    self.machine1.send_data(sfc_NG)
                    break
                #     quét qr thành công
                elif len(self.code_scan) > 0:
                    self.changeStatus(status_pass)
                    self.scan_pass += 1
                    self.serial_sfc_send.send_data(self.code_scan.encode('utf-8'))
                    self.machine1.send_data(sfc_OK)
                    break

            elif signal_machine1 == plc_reset:
                self.flag_reset = True
                print('---------RESET----------')
                self.changeStatus(status_reset)
                # self.machine4.send_data(plc_reset)
                break

    def changeStatus(self, status):
        css_fail = "QLabel { border: 1px solid rgb(85, 0, 0);color: #fff; background-color: rgb(247, 56, 59);}"
        css_ok = "QLabel { border: 1px solid rgb(85, 0, 0);color: #fff; background-color: rgb(69, 208, 102);}"
        css_wait = "QLabel { border: 1px solid rgb(85, 0, 0);color:  rgb(30, 30, 30); background-color: rgb(221, 221, 110); } "
        css_reset = "QLabel { border: 1px solid rgb(85, 0, 0);color: rgb(0, 85, 255); background-color: rgb(255, 228, 90); } "

        self.ui.result.setText(status)
        if status == status_wait:
            self.ui.result.setStyleSheet(css_wait)
        elif status == status_pass:
            self.ui.result.setStyleSheet(css_ok)
        elif status == status_reset:
            self.ui.result.setStyleSheet(css_reset)
        elif (status == status_ng_cam) | (status == status_ng_sfc) | (status == status_ng_cam_s4_190) | (
                status == status_ng_sfc_s4_190):
            self.ui.result.setStyleSheet(css_fail)

    def waitResultMachine4(self):
        while True:
            signal_machine4 = self.machine4.get_data()
            # if self.flag_reset:
            #     self.flag_reset = False
            #     break
            if len(signal_machine4) > 0:
                print('tín hiệu machine 4:', signal_machine4)
            if signal_machine4 == s4_190_OK:
                self.machine1.send_data(sfc_OK)
                break
            elif signal_machine4 == s4_190_NG:
                self.changeStatus(status_ng_sfc_s4_190)
                self.machine1.send_data(sfc_NG)
                break
            elif signal_machine4 == s4_190_NG_cam:
                self.changeStatus(status_ng_cam_s4_190)
                self.machine1.send_data(sfc_NG)
                break
    def configValue(self):
        f = open('configs/config-serial2.txt')
        arr = f.readlines()
        for i in arr:
            self.config.append(i.split()[1])
        f.close()

    def signalSfc(self):
        while True:
            self.receiveSignalSfc()

    def signalMachine1(self):
        while True:
            self.receiveSignalMachine1()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApplication()
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)

    # Lấy kích thước màn hình
    desktop = QDesktopWidget()
    screen_width = desktop.screenGeometry().width()
    screen_height = desktop.screenGeometry().height()

    # Lấy kích thước cửa sổ
    window_width = window.frameGeometry().width()
    window_height = window.frameGeometry().height()

    # Thiết lập vị trí xuất hiện ở góc dưới bên phải
    x = screen_width - window_width
    y = screen_height - window_height - 60
    window.move(x, y)
    window.show()
    sys.exit(app.exec_())
