import sys
import time
import serial
import logging
import threading
import datetime
import zxingcpp
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget
from cv2 import cv2
from pyzbar import pyzbar
from GUI.ui_app import Ui_Form

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
        self.config = []
        self.configValue()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.serial_plc = ReadSerial(self.config[0], int(self.config[5]))
        self.sfc_send = ReadSerial(self.config[1], int(self.config[5]))
        self.sfc_receive = ReadSerial(self.config[2], int(self.config[5]))
        self.machine1 = ReadSerial(self.config[3], int(self.config[5]))
        self.machine3 = ReadSerial(self.config[4], int(self.config[5]))
        self.ThreadCam = threading.Thread(target=self.Camera)
        self.ThreadSfc = threading.Thread(target=self.signalSfc)
        self.ThreadPlc = threading.Thread(target=self.signalPlc)
        self.ThreadCam.start()
        self.ThreadPlc.start()
        self.ThreadSfc.start()
        self.changeStatus(status_wait)

    def Camera(self):
        while True:
            self.res, self.frame = self.cap.read()
            if self.res:
                height, width, channel = self.frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
                pixmap = QPixmap.fromImage(q_image)
                pixmap = pixmap.scaled(self.ui.label.size(), Qt.KeepAspectRatio)
                self.ui.label.setPixmap(pixmap)
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
        self.flag_cam_scan = True
        # máy 1 chờ cân xong
        while True:
            data_sfc = self.sfc_receive.get_data()
            if len(data_sfc) > 0:
                print('data tu sfc: ', data_sfc)
            if data_sfc == '0':
                self.changeStatus(status_wait)
                print('lỗi cân 1')
                logger.error('error weight 1')
            elif data_sfc == sfc_weighted:
                self.changeStatus(status_wait)
                print('đây là tín hiệu cân từ sfc', data_sfc)
                # chờ cân từ máy 2
                print('chờ máy 2 cân xong...')
                while True:
                    data_weight2 = self.machine1.get_data()
                    if data_weight2 == '0':
                        print('lỗi cân 2')
                        logger.error('error weight 2')
                        break
                    if data_weight2 == sfc_weighted:
                        print('Đã nhận được tín hiệu cân xong từ máy 2: ', data_weight2)
                        self.serial_plc.send_data(plc_scan)
                        break
            elif data_sfc == sfc_OK:
                self.result_item1 = sfc_OK
                self.changeStatus(status_pass)
                print('sfc trả về OK', data_sfc)
                logger.info('result from machine 1: ' + str(sfc_OK))
                # Chờ kết quả Cường
                self.waitResult3()
                break
            elif data_sfc == sfc_NG:
                self.changeStatus(status_ng_sfc)
                print('sfc trả về NG', data_sfc)
                self.saveImage('images/img_ng/cam1_%s.png' % time.time())
                logger.warning('result from sfc: ' + str(sfc_NG))
                break
            elif not self.flag_cam_scan:
                break
        # Chờ kết quả máy 2
        print('chờ máy 2 scan xong...')
        result_machine2 = self.waitResultMachine2()
        # Xử lý kết quả, gửi cho plc

        self.calcResult(self.result_item1, result_machine2)


    def receivePlc(self):
        print('Chờ tín hiệu từ plc....')
        while True:
            receive_signal_scan = self.serial_plc.get_data()
            if len(receive_signal_scan) > 0:
                print('tín hiệu từ plc: ', receive_signal_scan)
            if receive_signal_scan == plc_scan:
                print('Nhận tín hiệu scan từ plc, gửi tín hiệu scan cho máy 2')
                self.machine1.send_data(plc_scan)
                self.machine3.send_data(cuong_scan)
                print('máy 1 bắt đầu scan...')
                if self.res:
                    self.code_scan = self.read_data_pyzbar()
                    print('day la ma qr', self.code_scan)
                # Trường hợp quét qr lỗi
                if self.code_scan is None:
                    print('Lỗi không scan được')
                    self.flag_cam_scan = False
                    self.result_item1 = sfc_NG
                    self.changeStatus(status_ng_cam)
                    logger.error('error scan camera 1')
                    break
                # quét qr thành công
                elif len(self.code_scan) > 0:
                    self.changeStatus(status_pass)
                    print('máy 1 scan xong, gửi tín hiệu cho sfc...')
                    self.sfc_send.send_data(self.code_scan)
                    break

            elif receive_signal_scan == plc_reset:
                self.flag_reset = True
                print('-------RESET---------')
                self.machine1.send_data(plc_reset)
                self.flag_reset = False
                break

    def changeStatus(self, status):
        css_fail = "QLabel { border-color: red; color: red; background-color: #fff;}"
        css_ok = "QLabel { border-color: rgb(0, 85, 255); color: rgb(0, 85, 255); background-color: #fff;}"
        css_wait = "QLabel { color: rgb(0, 85, 255); background-color: lightgray; } "
        if status == status_ng_cam:
            self.ui.label_4.setText(status_ng_cam)
            self.ui.label_4.setStyleSheet(css_fail)
        elif status == status_wait:
            self.ui.label_4.setText(status_wait)
            self.ui.label_4.setStyleSheet(css_wait)
        elif status == status_pass:
            self.ui.label_4.setText(status_pass)
            self.ui.label_4.setStyleSheet(css_ok)
        elif status == status_ng_sfc:
            self.ui.label_4.setText(status_ng_sfc)
            self.ui.label_4.setStyleSheet(css_fail)

    def waitResult3(self):
        print('chờ kết quả machine 3.............')
        while True:
            signal_machine3 = self.machine3.get_data()
            if len(signal_machine3) > 0:
                print('tín hiệu từ machine 3: ', signal_machine3)
            if signal_machine3 == cuong_ok:
                self.result_item1 = sfc_OK
                break
            elif signal_machine3 == cuong_ng:
                self.result_item1 = sfc_NG
                break

    def waitResultMachine2(self):
        while True:
            result_machine2 = self.machine1.get_data()
            if result_machine2 == sfc_NG:
                print('máy 2 gửi NG', result_machine2)
                logger.warning('result from machine 2: ' + str(sfc_NG))
                break
            elif result_machine2 == sfc_OK:
                print('máy 2 gửi OK', result_machine2)
                logger.info('result from machine 2: ' + str(sfc_OK))
                break
        return result_machine2

    def calcResult(self, result_item1, result_machine2):
        if result_item1 == sfc_OK:
            if result_machine2 == sfc_OK:
                self.serial_plc.send_data(machine_OKOK)
                logger.info('send signal to plc: ' + str(machine_OKOK))
                print('gửi tín hiệu cho plc: ', machine_OKOK)
            else:
                self.serial_plc.send_data(machine_OKNG)
                logger.warning('send signal to plc: ' + str(machine_OKNG))
                print('gửi tín hiệu cho plc: ', machine_OKNG)
        elif result_item1 == sfc_NG:
            if result_machine2 == sfc_NG:
                self.serial_plc.send_data(machine_NGNG)
                logger.warning('send signal to plc: ' + str(machine_NGNG))
                print('gửi tín hiệu cho plc: ', machine_NGNG)
            else:
                self.serial_plc.send_data(machine_NGOK)
                logger.warning('send signal to plc: ' + str(machine_NGOK))
                print('gửi tín hiệu cho plc: ', machine_NGOK)

    def configValue(self):
        f = open('configs/config-serial.txt')
        arr = f.readlines()
        for i in arr:
            self.config.append(i.split()[1])
        f.close()

    def signalSfc(self):
        while True:
            if self.flag_reset:
                break
            self.receiveSignalSfc()

    def signalPlc(self):
        while True:
            self.receivePlc()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApplication()
    window.setWindowFlags(window.windowFlags() | Qt.WindowStaysOnTopHint)

    # Lấy đối tượng QDesktopWidget để lấy kích thước màn hình
    desktop = QDesktopWidget()
    screen_width = desktop.screenGeometry().width()
    screen_height = desktop.screenGeometry().height()

    # Lấy kích thước cửa sổ
    window_width = window.frameGeometry().width()
    window_height = window.frameGeometry().height()

    # Thiết lập vị trí xuất hiện ở góc dưới bên phải
    x = screen_width - window_width
    y = screen_height - window_height - 80
    window.move(x, y)
    window.show()
    sys.exit(app.exec_())
