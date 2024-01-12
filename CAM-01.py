import logging
import os
import sys
import time
import serial
import threading
import datetime
# import zxingcpp
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

#
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
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.gray = None
        self.res = None
        self.frame = None
        self.thresh = None
        self.result_item1 = None
        self.flag_cam_scan = True
        self.flag_weighted = False
        self.quantity = 0
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
        self.ThreadSfc = threading.Thread(target=self.signalSfc)
        self.ThreadPlc = threading.Thread(target=self.signalPlc)
        self.ThreadCam.start()
        self.ThreadPlc.start()
        self.ThreadSfc.start()
        self.changeStatus(status_wait)
        self.close_button = QPushButton("Close Application")
        self.close_button.clicked.connect(self.close_application)

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
            self.flag_reset = False
            data_sfc = self.sfc_receive.get_data()
            if len(data_sfc) > 0:
                print('data tu sfc: ', data_sfc)
            if self.flag_reset:
                self.flag_reset = False
                # elif (data_sfc == sfc_weighted) & (not self.flag_weighted):
            elif data_sfc == sfc_weighted:
                # self.flag_weighted = True
                self.changeStatus(status_wait)
                print('máy 1: đây là tín hiệu cân từ sfc', data_sfc)
                # chờ cân từ máy 2
                print('chờ máy 2 cân xong...')
                while True:
                    data_weight2 = self.machine2.get_data()
                    if self.flag_reset:
                        self.flag_reset = False
                        print('reset can')
                        break
                    if len(data_weight2) > 0:
                        print('data may 2', data_weight2)
                    if data_weight2 == sfc_weighted:
                        print('máy 1: Đã nhận được tín hiệu cân xong từ máy 2: ', data_weight2)
                        print('máy 1: Gửi tín hiệu đã cân xong cho plc', data_weight2)
                        self.serial_plc.send_data(plc_scan)
                        break
            # Cần cân xong thì mới đọc tín hiệu sfc trả về khi scan
            if data_sfc == sfc_OK:
                self.result_item1 = sfc_OK
                self.changeStatus(status_pass)
                print('máy 1: sfc trả về OK', data_sfc)
                print('máy 1 gửi mã QR cho s4-190', self.code_scan)
                logger.info('result from machine 1: ' + str(sfc_OK))
                # Chờ kết quả Cường
                self.machine3.send_data(self.code_scan.encode('utf-8'))
                print('Chờ kết quả của s4-190....')
                self.waitResult3()
                break
            elif data_sfc == sfc_NG:
                self.machine3.send_data(self.code_scan.encode('utf-8'))
                self.changeStatus(status_ng_sfc)
                self.result_item1 = sfc_NG
                print('máy 1: sfc trả về NG', data_sfc)
                print('máy 1 gửi kết quả sfc fail tới s4-190', data_sfc)
                self.machine3.send_data(s4_200_NG)
                self.saveImage('images/img_ng/cam1_%s.png' % time.time())
                logger.warning('result from sfc: ' + str(sfc_NG))
                break
            # Scan lỗi, không nhận tín hiệu sfc nữa
            # if not self.flag_cam_scan:
            #     self.flag_weighted = False
            #     break
        # Chờ kết quả máy 2
        print('máy 1: chờ máy 2 scan xong...')
        result_machine2 = self.waitResultMachine2()
        # Xử lý kết quả, gửi cho plc
        print('Xử lý kết quả để gửi cho plc')
        self.calcResult(self.result_item1, result_machine2)


    def receivePlc(self):
        print('Chờ tín hiệu từ plc....')
        # self.flag_reset = False
        while True:
            signal_plc = self.serial_plc.get_data()
            if len(signal_plc) > 0:
                print('tín hiệu từ plc: ', signal_plc)
            if (signal_plc == plc_scan_receive) | (signal_plc == plc_test_scan):
                print('máy 1: Nhận tín hiệu scan từ plc, gửi tín hiệu scan cho máy 2 và s4-190')
                self.machine2.send_data(plc_scan)
                self.machine3.send_data(s4_190_scan)
                print('máy 1 bắt đầu scan...')
                if self.res:
                    i = 0
                    while i < 10:
                        self.code_scan = self.read_data_zxingcpp()
                        if self.code_scan is None:
                            i += 1
                        else:
                            break
                    print('máy 1: QR:', self.code_scan)
                    self.quantity += 1
                    self.ui.quantity.setText('%s', self.quantity)
                # Trường hợp quét qr lỗi
                if self.code_scan is None:
                    print('máy 1: không scan được')
                    # self.flag_cam_scan = False
                    # self.result_item1 = NG_cam
                    self.changeStatus(status_ng_cam)
                    self.machine3.send_data(s4_200_NG_cam)
                    logger.error('error scan camera 1')
                    self.code_scan = 'abcsdefyh'
                    # self.sfc_send.send_data(self.code_scan.encode('utf-8'))
                    break
                # quét qr thành công
                elif len(self.code_scan) > 0:
                    self.changeStatus(status_pass)
                    print('máy 1 scan xong, gửi tín hiệu cho sfc...')
                    self.sfc_send.send_data(self.code_scan.encode('utf-8'))
                    break

            elif (signal_plc == plc_reset_receive) | (signal_plc == plc_test_reset):
                self.flag_reset = True
                print('-------RESET---------')
                self.changeStatus(status_reset)
                self.machine2.send_data(plc_reset)
                self.serial_plc.send_data(plc_reset)
                self.machine3.send_data(plc_reset)
                # self.flag_reset = False
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
        elif (status == status_ng_cam) | (status == status_ng_sfc) | (status == status_ng_cam_s4_190) | (status == status_ng_sfc_s4_190):
            self.ui.result.setStyleSheet(css_fail)

    def waitResult3(self):
        # self.machine3.send_data(self.code_scan.encode('utf-8'))
        while True:
            signal_machine3 = self.machine3.get_data()
            if len(signal_machine3) > 0:
                print('tín hiệu từ machine 3: ', signal_machine3)
            if signal_machine3 == s4_190_OK:
                print('S4-190 PASS')
                self.result_item1 = sfc_OK
                break
            elif signal_machine3 == s4_190_NG:
                print('S4-190 NG SFC')
                self.changeStatus(status_ng_sfc_s4_190)
                self.result_item1 = sfc_NG
                break
            elif signal_machine3 == s4_190_NG_cam:
                print('S4-190 NG CAMERA')
                self.changeStatus(status_ng_cam_s4_190)
                self.result_item1 = sfc_NG
                break
        print('Kết quả s4-190:...', self.result_item1)

    def waitResultMachine2(self):
        while True:
            result_machine2 = self.machine2.get_data()
            if result_machine2 == sfc_NG:
                print('máy 2 gửi NG', result_machine2)
                logger.warning('result from machine 2: ' + str(sfc_NG))
                break
            elif result_machine2 == sfc_OK:
                print('máy 2 gửi OK', result_machine2)
                logger.info('result from machine 2: ' + str(sfc_OK))
                break
            if self.flag_reset:
                self.flag_reset = False
                break
        print('Kết quả máy 2: ', result_machine2)
        return result_machine2

    def calcResult(self, result_item1, result_machine2):
        self.flag_weighted = False
        print('tính toán....')
        if result_machine2 == plc_reset:
            return
        if (result_item1 == sfc_OK) | (result_item1 == sfc_test_ok):
            if (result_machine2 == sfc_OK) | (result_machine2 == sfc_test_ok):
                self.serial_plc.send_data(machine_OKOK)
                logger.info('send signal to plc: ' + str(machine_OKOK))
                print('gửi tín hiệu cho plc: ', machine_OKOK)
            else:
                self.serial_plc.send_data(machine_OKNG)
                logger.warning('send signal to plc: ' + str(machine_OKNG))
                print('gửi tín hiệu cho plc: ', machine_OKNG)
        elif (result_item1 == sfc_NG) | (result_item1 == sfc_test_ng):
            if (result_machine2 == sfc_NG) | (result_machine2 == sfc_test_ng):
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
            self.receiveSignalSfc()

    def signalPlc(self):
        while True:
            self.receivePlc()


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
    y = screen_height - window_height - 80
    window.move(x, y)
    window.show()
    sys.exit(app.exec_())

