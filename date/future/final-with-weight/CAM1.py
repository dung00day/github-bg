import sys
import threading
import cv2
import os
import serial
from pyzbar import pyzbar
from playsound import playsound
import time
from configs import constants
from signall import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget

from GUI.ui_area_c import Ui_Form

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

exe_path = os.path.abspath(os.path.dirname(__file__))
signal_path = os.path.join(exe_path, "signall\signal_beep.mp3")
config_path = os.path.join(exe_path, "configs\config-serial.txt")


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


class CountDownThread(QThread):
    update_timer_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            self.update_timer_signal.emit()
            time.sleep(1)


class MyApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flag_reset = False
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.gray = None
        self.res = None
        self.frame = None
        self.thresh = None
        self.flag_scan = True
        self.code_scan = None

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.config = []
        self.configValue()
        self.remaining_time = 5
        self.timer = QTimer(self)
        self.timer.setInterval(1000)

        self.sfc_send = ReadSerial(self.config[0], 9600)
        self.ThreadCam = threading.Thread(target=self.Camera)

        self.ThreadScan = threading.Thread(target=self.scanCode)
        self.count_down_thread = CountDownThread()
        self.count_down_thread.update_timer_signal.connect(self.update_timer)
        self.count_down_thread.start()

        self.ThreadCam.start()
        self.ThreadScan.start()
        self.timer.start()

    def update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
        elif self.remaining_time == 0:
            self.flag_scan = True
            # self.ui.result.setText('WAIT')
            # self.ui.result.styleSheet(
            #     "border: 1px solid rgb(85, 0, 0);color:  rgb(30, 30, 30); background-color: rgb(221, 221, 110)")

    def Camera(self):
        while True:
            self.res, self.frame = self.cap.read()
            if self.res:
                height, width, channel = self.frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
                pixmap = QPixmap.fromImage(q_image)
                pixmap = pixmap.scaled(self.ui.camera.size(), Qt.AspectRatioMode.KeepAspectRatio)
                self.ui.camera.setPixmap(pixmap)
                self.gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                (_, self.thresh) = cv2.threshold(self.gray, 80, 255, cv2.THRESH_BINARY)
                QApplication.processEvents()

    def scanCode(self):
        while True:
            if self.flag_scan and self.res:
                self.code_scan = self.read_data_pyzbar()
                if self.code_scan is not None:
                    self.sfc_send.send_data(self.code_scan.encode('utf-8'))
                    print(self.code_scan)
                    # self.ui.result.setText('PASS')
                    # self.ui.result.styleSheet("border: 1px solid rgb(85, 0, 0);color: #fff; background-color: rgb(69, "
                    #                           "208, 102);")
                    start = time.time()
                    print('bắt đầu mở file âm thanh')
                    playsound(signal_path)
                    print('mở file âm thanh thành công')
                    print('finish: ', time.time() - start)
                    self.remaining_time = 5
                    print('start')

                    self.flag_scan = False

    def read_data_pyzbar(self):
        data = pyzbar.decode(self.frame)
        if len(data) > 0:
            data = data[0].data.decode('utf-8')
            return data
        else:
            return None
            # data = pyzbar.decode(self.gray)
            # if len(data) > 0:
            #     data = data[0].data.decode('utf-8')
            #     return data
            # else:
            #     data = pyzbar.decode(self.thresh)
            #     if len(data) > 0:
            #         data = data[0].data.decode('utf-8')
            #         return data
            #     else:
            #         return None

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
