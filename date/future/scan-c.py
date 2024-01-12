import sys
import threading
import cv2
import os
import serial
import zxingcpp
from pyzbar import pyzbar
from playsound import playsound
import time
from pyzbar.pyzbar import ZBarSymbol
import numpy as np
import qrcode_python_wechar
from configs import constants
from signall import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QWidget
from GUI.final_ui_area_c import Ui_Form

from pynput import keyboard

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
# auto_focus_enabled = cap.get(cv2.CAP_PROP_AUTOFOCUS)
# print("Tự động tiêu cự đã được kích hoạt:", auto_focus_enabled)

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
            time.sleep(0.5)


class ScannerThread(QThread):
    scan_result_signal = pyqtSignal(str)  # Signal to emit scan results

    def __init__(self, parent=None):
        super(ScannerThread, self).__init__(parent)
        self.parent = parent

    def run(self):
        while True:
            if self.parent.flag_scan and self.parent.camera_thread.ret:
                if self.parent.frame is not None:
                    code_scan = self.parent.read_WeChatQRCode()
                    if code_scan is not None and len(code_scan) > 8:
                        # You can emit the result signal to send data back to the main thread
                        self.scan_result_signal.emit(code_scan)

                        # Perform other actions as needed (e.g., update UI, play sound)
                        self.parent.count += 1
                        print(f'--------{self.parent.count}----------')
                        self.parent.ui.result.setText('PASS')
                        self.parent.ui.result.setStyleSheet(
                            "border: 1px solid rgb(85, 0, 0); background-color: rgb(69,208, 102);")

                        if (self.parent.count % 20) == 0:
                            print('update')
                            self.parent.update()

                        start = time.time()
                        print('bắt đầu mở file âm thanh')
                        # playsound(signal_path)
                        print('mở file âm thanh thành công')

                        self.parent.remaining_time = int(self.parent.config[7])
                        self.parent.flag_scan = False


class CameraThread(QThread):
    frame_signal = pyqtSignal(np.ndarray)  # Signal to emit the camera frame
    ret = pyqtSignal(np.ndarray)

    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Open the default camera (change index if needed)
        cap.set(cv2.CAP_PROP_SETTINGS, 1)
        while True:
            self.ret, frame = cap.read()  # Read a frame from the camera
            if not self.ret:
                break
            self.frame_signal.emit(frame)
        cap.release()


class MyApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flag_reset = False
        # self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        # self.cap.set(cv2.CAP_PROP_SETTINGS, 1)
        self.gray = None
        self.ret = True
        self.frame = None
        self.thresh = None
        self.flag_scan = True
        self.code_scan = None
        self.count = 0

        path_dir = r'qrcode_python_wechar'
        detect_model = path_dir + "/detect.caffemodel"
        detect_protox = path_dir + "/detect.prototxt"
        sr_model = path_dir + "/sr.caffemodel"
        sr_protox = path_dir + "/sr.prototxt"
        self.detector = cv2.wechat_qrcode_WeChatQRCode(detect_protox, detect_model, sr_protox, sr_model)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.result.setText('WAIT')
        self.ui.result.setStyleSheet("border: 1px solid rgb(85, 0, 0); background-color: rgb(221, 221, 110);")
        self.config = []
        self.configValue()
        self.remaining_time = 5

        self.camera_thread = CameraThread(self)
        self.camera_thread.frame_signal.connect(self.update_frame)
        self.camera_thread.start()

        self.scanner_thread = ScannerThread(self)
        self.scanner_thread.scan_result_signal.connect(self.handle_scan_result)
        self.scanner_thread.start()

        # self.sfc_send = ReadSerial(self.config[1], int(self.config[6]))
        # self.ThreadCam = threading.Thread(target=self.Camera)
        # self.ThreadScan = threading.Thread(target=self.scanCode)

        self.count_down_thread = CountDownThread()
        self.count_down_thread.update_timer_signal.connect(self.update_timer)
        self.count_down_thread.start()

        # self.ThreadCam.start()
        # self.ThreadScan.start()

    def update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
        elif self.remaining_time == 0:
            if not self.flag_scan:
                self.ui.result.setText('WAIT')
                self.ui.result.setStyleSheet("border: 1px solid rgb(85, 0, 0); background-color: rgb(221, 221, 110);")
                self.flag_scan = True

    def update_frame(self, frame):
        self.frame = frame
        height, width, channel = self.frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(q_image)
        pixmap = pixmap.scaled(self.ui.camera.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.ui.camera.setPixmap(pixmap)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            print(f'Kí tự nhấn: {chr(key)}')

    def handle_scan_result(self, result):
        print("Scan Result:", result)

    def scanCode(self):
        while True:
            if self.flag_scan and self.camera_thread.ret:
                if self.frame is not None:
                    self.code_scan = self.read_WeChatQRCode()
                if self.code_scan is None:
                    pass
                elif len(self.code_scan) > 8:
                    # self.sfc_send.send_data(self.code_scan.encode('utf-8'))
                    print(self.code_scan)
                    self.count += 1
                    print(f'--------{self.count}----------')
                    self.ui.result.setText('PASS')
                    self.ui.result.setStyleSheet("border: 1px solid rgb(85, 0, 0); background-color: rgb(69,208, 102);")
                    if (self.count % 20) == 0:
                        print('update')
                        self.update()
                    start = time.time()
                    print('bắt đầu mở file âm thanh')
                    # playsound(signal_path)
                    print('mở file âm thanh thành công')
                    # print('finish: ', time.time() - start)
                    self.remaining_time = int(self.config[7])
                    self.flag_scan = False

    def read_data_pyzbar(self):
        data = pyzbar.decode(self.frame, symbols=[ZBarSymbol.QRCODE])
        if len(data) > 0:
            print('-----pyzbar frame------')
            data = data[0].data.decode('utf-8')
            return data
        else:
            data = pyzbar.decode(self.gray, symbols=[ZBarSymbol.QRCODE])
            if len(data) > 0:
                print('-----pyzbar gray------')
                data = data[0].data.decode('utf-8')
                return data
            else:
                data = pyzbar.decode(self.thresh, symbols=[ZBarSymbol.QRCODE])
                if len(data) > 0:
                    print('-----pyzbar thresh------')
                    data = data[0].data.decode('utf-8')
                    return data
                else:
                    return None

    def read_WeChatQRCode(self):
        data, points = self.detector.detectAndDecode(self.frame)
        self.gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
        blurred_img = cv2.GaussianBlur(self.gray, (5, 5), 0)
        # (_, self.thresh) = cv2.threshold(self.gray, 80, 255, cv2.THRESH_BINARY)
        self.thresh = cv2.adaptiveThreshold(blurred_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        if data != ():
            data = data[0]
            if len(data) > 8:
                print("---------frame read_WeChatQRCode---------")
                return data
            else:
                return self.read_data_pyzbar()
        else:
            data, points = self.detector.detectAndDecode(self.gray)
            if data != ():
                data = data[0]
                if len(data) > 8:
                    print("---------gray read_WeChatQRCode---------")
                    return data
                else:
                    return self.read_data_pyzbar()
            else:
                return self.read_data_pyzbar()

    def read_data_zxingcpp(self):
        data = zxingcpp.read_barcode(self.frame)
        if data is not None:
            print('-----zxing frame------')
            return data.text
        else:
            data = zxingcpp.read_barcode(self.thresh)
            if data is not None:
                print('-----zxing thresh------')
                return data.text
            else:
                return self.read_data_pyzbar()

    def configValue(self):
        f = open(config_path)
        arr = f.readlines()
        for i in arr:
            self.config.append(i.split()[1])
        f.close()

    def resizeEvent(self, event):
        # Khi kích thước của widget thay đổi, cập nhật kích thước của QLabel
        new_width = event.size().width()
        new_height = event.size().height()
        new_label_size = self.ui.frame.size()
        new_label_size.setWidth(new_width)
        new_label_size.setHeight(new_height)
        self.ui.frame.setFixedSize(new_label_size)
        print('thay doi width, height')


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
    x = screen_width - window_width - int(window.config[8])
    y = screen_height - window_height - 70 - int(window.config[9])
    window.move(x, y)
    window.show()
    sys.exit(app.exec_())
