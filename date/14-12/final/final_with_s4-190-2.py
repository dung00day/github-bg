import os
import sys
import serial
import logging
import threading
import datetime
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QPushButton
import cv2
from pyzbar import pyzbar
from GUI.camera_final import Ui_Form
from configs.constants import *

icon = "D:/SD_CODE/GUI/Logo.ico"


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


class MyApplication():
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
        self.serial_sfc_send = ReadSerial(self.config[0], int(self.config[4]))
        self.serial_sfc_receive = ReadSerial(self.config[1], int(self.config[4]))
        self.machine1 = ReadSerial(self.config[2], int(self.config[4]))
        self.machine4 = ReadSerial(self.config[3], int(self.config[4]))
        # self.machine1.send_data(b'1\n')
        # self.ThreadCam = threading.Thread(target=self.Camera)
        # self.ThreadSfc = threading.Thread(target=self.signalSfc)
        # self.ThreadMachine1 = threading.Thread(target=self.signalMachine1)

        # self.ThreadCam.start()
        # self.ThreadMachine1.start()
        # self.ThreadSfc.start()

    def Camera(self):
        while True:
            self.res, self.frame = self.cap.read()
            if self.res:
                cv2.imshow('camera', self.frame)
                # height, width, channel = self.frame.shape
                # bytes_per_line = 3 * width
                # q_image = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
                # pixmap = QPixmap.fromImage(q_image)
                # pixmap = pixmap.scaled(self.ui.camera.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
                # self.ui.camera.setPixmap(pixmap)
                self.gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                (_, self.thresh) = cv2.threshold(self.gray, 80, 255, cv2.THRESH_BINARY)
                cv2.waitKey(1)

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
        # máy 2 chờ cân xong
        while True:
            signal_sfc = self.serial_sfc_receive.get_data()
            if len(signal_sfc) > 0:
                print('tin hieu sfc: ', signal_sfc)
            if signal_sfc == sfc_weighted:
                print('may 2 can xong', signal_sfc)
                self.machine1.send_data(sfc_weighted)
                self.flag_weighted = True

            elif signal_sfc == sfc_OK:
                # self.machine1.send_data(b'1\n')
                # cho s4-190
                self.machine4.send_data(self.code_scan.encode('utf-8'))
                self.flag_reset = False
                print('Chow s4-190')
                while True:
                    signal_machine4 = self.machine4.get_data()
                    # if self.flag_reset:
                    #     self.flag_reset = False
                    #     break
                    if len(signal_machine4) > 0:
                        print('tín hiệu machine 4:', signal_machine4)
                    if signal_machine4 == s4_190_OK:
                        self.machine1.send_data(b'1\n')
                        break
                    elif signal_machine4 == s4_190_NG:
                        self.machine1.send_data(b'1\n')
                        break
                    elif signal_machine4 == s4_190_NG_cam:
                        self.machine1.send_data(b'1\n')
                        break

                self.flag_scan2 = False
                print('sfc ok')

            elif (signal_sfc == sfc_NG) and self.flag_weighted:
                self.machine1.send_data(b'2\n')
                self.machine4.send_data(s4_200_NG)
                self.flag_scan2 = False
                print('sfc ng')
                # break


    def receiveSignalMachine1(self):
        print('Chờ tín hiệu máy 1')
        while True:
            signal_machine1 = self.machine1.get_data()
            if len(signal_machine1) > 0:
                print('Đây là tín hiệu từ máy 1: ', signal_machine1)
            if signal_machine1 == plc_scan:
                # self.machine4.send_data(s4_190_scan)
                print('machine 1 bắt đầu scan...')
                self.code_scan = None
                i = 0
                while i < 5:
                    self.code_scan = self.read_data_pyzbar()
                    if self.code_scan is None:
                        i += 1
                    else:
                        break
                print('máy 2: QR:', self.code_scan)
                self.quantity += 1
                # Trường hợp quét qr lỗi
                if self.code_scan is None:
                    print('Lỗi không scan được......')
                    self.code_scan = 'X6LPY7MCQX'
                    self.serial_sfc_send.send_data(b'X6LPY7MCQX')
                    self.machine4.send_data(s4_190_scan)

                    # self.saveImage('images/img_ng/cam2_%s.png' % time.time())
                    # self.machine1.send_data(b'2\n')
                    self.flag_scan2 = True
                    self.flag_weighted = False
                # quét qr thành công
                elif len(self.code_scan) > 0:
                    self.scan_pass += 1
                    self.serial_sfc_send.send_data(self.code_scan.encode('utf-8'))
                    self.machine4.send_data(s4_190_scan)

                    # self.machine1.send_data(b'1\n')
                    self.flag_scan2 = True
                    self.flag_weighted = False
                    # break

            elif signal_machine1 == plc_reset:
                self.flag_reset = True
                print('---------RESET----------')
                if self.flag_weighted:
                    self.serial_sfc_send.send_data(b'X6LPY7MCQX')
                self.machine4.send_data(plc_reset)
                # break


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
                self.machine1.send_data(sfc_NG)
                break
            elif signal_machine4 == s4_190_NG_cam:
                self.machine1.send_data(sfc_NG)
                break

    def configValue(self):
        f = open('configs/config-serial2.txt')
        arr = f.readlines()
        for i in arr:
            self.config.append(i.split()[1])
        f.close()

    def runThread(self):
        threadCam = threading.Thread(target=self.Camera)
        threadSfc = threading.Thread(target=self.receiveSignalSfc)
        threadMachine1 = threading.Thread(target=self.receiveSignalMachine1)
        threadCam.start()
        threadSfc.start()
        threadMachine1.start()


    def signalMachine1(self):
        while True:
            self.receiveSignalMachine1()


my_app = MyApplication()
my_app.runThread()
