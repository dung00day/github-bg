import sys
import cv2
import os
import serial
import zxingcpp
from pyzbar import pyzbar
from pylibdmtx import pylibdmtx
from playsound import playsound
import time
from pyzbar.pyzbar import ZBarSymbol
import numpy as np
import qrcode_python_wechar
from configs import constants
from signall import *
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget
from GUI.rh189_ui import Ui_Form

exe_path = os.path.abspath(os.path.dirname(__file__))
# signal_path = os.path.join(exe_path, r"signall\signal_beep.mp3")
config_path = os.path.join(exe_path, r"D:\SD_CODE\configs\config-serial.txt")
icon_path = os.path.join(exe_path, r"GUI\Logo.ico")


class PlcThread(QThread):
    plc_signal = pyqtSignal(str)

    def __init__(self, ser_port, com_baud):
        super().__init__()
        self.ser_port = ser_port
        self.com_baud = com_baud
        try:
            self.ser_com = serial.Serial(
                port=ser_port,
                baudrate=com_baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.0009
            )
        except Exception as exx:
            print(exx, 'Error serial')

    def send_signal(self, data):
        self.ser_com.write(data.encode('utf-8'))

    def run(self):
        while True:
            signal = self.ser_com.readline()
            if len(signal) > 0:
                print(signal, 'signal')
                try:
                    self.plc_signal.emit(signal.decode('utf-8'))
                except Exception as e:
                    print('error ', e)


class SfcThread(QThread):
    sfc_signal = pyqtSignal(str)

    def __init__(self, ser_port, com_baud):
        super().__init__()
        self.ser_port = ser_port
        self.com_baud = com_baud
        try:
            self.ser_com = serial.Serial(
                port=ser_port,
                baudrate=com_baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.0009
            )
        except Exception as exx:
            print(exx, 'Error serial')

    def run(self):
        while True:
            signal = self.ser_com.readline()
            if len(signal) > 0:
                print(signal, 'signal')
                try:
                    self.sfc_signal.emit(signal.decode('utf-8'))
                except Exception as e:
                    print('error ', e)
            #   signal OK from sfc
            if signal == b'1':
                print('hello 1')
            if signal == b'2':
                print('hello 2')


# thread read qr code
class ScannerThread(QThread):
    scan_result_signal = pyqtSignal(str)  # Signal to emit scan results

    def __init__(self, parent=None):
        super(ScannerThread, self).__init__(parent)
        self.parent = parent

    def run(self):
        print('vào scan qr')
        while True:
            if self.parent.flag_scan and self.parent.camera_thread.ret:
                if self.parent.frame is not None:
                    code_scan = self.parent.read_WeChatQRCode(self.parent.frame)
                    if code_scan is not None and len(code_scan) > 8:
                        # You can emit the result signal to send data back to the main thread
                        self.scan_result_signal.emit(code_scan)
                        # Perform other actions as needed (e.g., update UI, play sound)
                        self.parent.count += 1
                        print(f'--------{self.parent.count}----------')
                        self.parent.ui.result.setText('PASS')
                        self.parent.ui.result.setStyleSheet(
                            "border: 1px solid rgb(85, 0, 0); background-color: rgb(69,208, 102);")
                        self.parent.flag_scan = False


# thread read datamatrix code
class ScannerThread2(QThread):
    scan_result_signal = pyqtSignal(str)  # Signal to emit scan results

    def __init__(self, parent=None):
        super(ScannerThread2, self).__init__(parent)
        self.parent = parent

    def run(self):
        print('vào scan data matrix')
        while True:
            if self.parent.flag_scan2 and self.parent.camera_thread2.ret:
                if self.parent.frame2 is not None:
                    i = 0
                    while i < 5:
                        code_scan = self.parent.read_data_pylibdmtx(self.parent.frame2)
                        if code_scan is not None and len(code_scan) > 8:
                            # You can emit the result signal to send data back to the main thread
                            self.scan_result_signal.emit(code_scan)

                            # Perform other actions as needed (e.g., update UI, play sound)
                            self.parent.count2 += 1
                            print(f'--------{self.parent.count2}----------')
                            self.parent.flag_scan2 = False
                            break
                        else:
                            i += 1


class CameraThread(QThread):
    frame_signal = pyqtSignal(np.ndarray)  # Signal to emit the camera frame
    ret = pyqtSignal(np.ndarray)

    def run(self):
        print('mo cam 1')
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_SETTINGS, 1)
        while True:
            self.ret, frame = cap.read()  # Read a frame from the camera
            if not self.ret:
                break
            self.frame_signal.emit(frame)
        cap.release()


class CameraThread2(QThread):
    frame_signal2 = pyqtSignal(np.ndarray)  # Signal to emit the camera frame
    ret2 = pyqtSignal(np.ndarray)

    def run(self):
        print('mo cam 2')
        cap2 = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        cap2.set(cv2.CAP_PROP_SETTINGS, 1)
        while True:
            self.ret2, frame2 = cap2.read()  # Read a frame from the camera
            if not self.ret2:
                break
            self.frame_signal2.emit(frame2)
        cap2.release()


class MyApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.flag_reset = False
        self.flag_reset2 = False
        self.frame = None
        self.frame2 = None
        self.flag_scan = True
        self.flag_scan2 = True
        self.code_scan = None
        self.code_scan2 = None
        self.count = 0

        path_dir = r'D:\SD_CODE\qrcode_python_wechar'
        detect_model = path_dir + "/detect.caffemodel"
        detect_protox = path_dir + "/detect.prototxt"
        sr_model = path_dir + "/sr.caffemodel"
        sr_protox = path_dir + "/sr.prototxt"
        self.detector = cv2.wechat_qrcode_WeChatQRCode(detect_protox, detect_model, sr_protox, sr_model)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)
        self.setWindowTitle('RH-189')
        self.ui.result.setText('WAIT')
        self.ui.result.setStyleSheet("border: 1px solid rgb(85, 0, 0); background-color: rgb(221, 221, 110);")
        self.config = []
        self.configValue()

        self.camera_thread = CameraThread()
        self.camera_thread.frame_signal.connect(self.update_frame)
        self.camera_thread.start()

        self.camera_thread2 = CameraThread2()
        self.camera_thread2.frame_signal2.connect(self.update_frame2)
        self.camera_thread2.start()

        # self.scanner_thread = ScannerThread(self)
        # self.scanner_thread.scan_result_signal.connect(self.handle_scan_result)
        # self.scanner_thread.start()

        # self.scanner_thread2 = ScannerThread2(self)
        # self.scanner_thread2.scan_result_signal.connect(self.handle_scan_result2)
        # self.scanner_thread2.start()

        self.plc_thread = PlcThread("COM9", 9600)
        self.plc_thread.plc_signal.connect(self.plc_signal)
        self.plc_thread.start()

        self.sfc_thread = PlcThread("COM11", 9600)
        self.sfc_thread.plc_signal.connect(self.sfc_signal)
        self.sfc_thread.start()

    def update_frame(self, frame):
        self.frame = frame
        height, width, channel = self.frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(self.frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(q_image)
        pixmap = pixmap.scaled(self.ui.camera.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.ui.camera.setPixmap(pixmap)

    def update_frame2(self, frame2):
        self.frame2 = frame2
        height, width, channel = self.frame2.shape
        bytes_per_line = 3 * width
        q_image = QImage(self.frame2.data, width, height, bytes_per_line, QImage.Format_BGR888)
        pixmap = QPixmap.fromImage(q_image)
        pixmap = pixmap.scaled(self.ui.camera_2.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.ui.camera_2.setPixmap(pixmap)

    def handle_scan_result(self, result):
        print("Scan Result:", result)
        # self.code_scan = result
        # self.camera_thread.quit()

    def handle_scan_result2(self, result):
        print("Scan Result 2:", result)
        # self.code_scan2 = result
        # self.camera_thread2.quit()

    def plc_signal(self, signal):
        if len(signal) > 0:
            print('signal from plc: ', signal)
        #    Nhận tín hiệu từ plc, bắt đầu scan
        if signal == '1':
            print('start scan')
            # self.flag_scan = True
            # self.flag_scan2 = True
            # bắt đầu scan
            try:
                self.code_scan = self.read_WeChatQRCode(self.frame)
                self.code_scan2 = self.read_data_pylibdmtx(self.frame2)
            except Exception as e:
                print('error: ', e)
            print('code 1', self.code_scan)
            print('code 2', self.code_scan2)
            # self.scanner_thread.start()
            # self.scanner_thread2.start()

        # Khi đủ 2 mã code thì gửi dữ liệu tới sfc
        if self.code_scan2 is not None and self.code_scan is not None:
            print('gui cho sfc')
            # Gửi tín hiệu tới sfc
            self.sfc_thread.ser_com.write(self.code_scan.encode('utf-8'))
            self.code_scan = None
            time.sleep(0.5)
            self.sfc_thread.ser_com.write(self.code_scan2.encode('utf-8'))
            self.code_scan2 = None

    def sfc_signal(self, signal):
        if len(signal) > 0:
            print('signal from sfc: ', signal)

        # sfc trả về tín hiệu, gửi tín hiệu NG OK cho plc
        if signal == '1':
            self.ui.result.setText('SFC PASS')
            self.ui.result.setStyleSheet("border: 1px solid rgb(85, 0, 0); background-color: rgb(69,208, 102);")
            self.plc_thread.send_signal(signal)

        elif signal == '2':
            self.ui.result.setText('SFC FAIL')
            self.ui.result.setStyleSheet("border: 1px solid rgb(85, 0, 0); background-color: rgb(69,208, 102);")
            self.plc_thread.send_signal(signal)

    def read_data_pyzbar(self, frame, gray, thresh):
        data = pyzbar.decode(frame, symbols=[ZBarSymbol.QRCODE])
        if len(data) > 0:
            print('-----pyzbar frame------')
            data = data[0].data.decode('utf-8')
            return data
        else:
            data = pyzbar.decode(gray, symbols=[ZBarSymbol.QRCODE])
            if len(data) > 0:
                print('-----pyzbar gray------')
                data = data[0].data.decode('utf-8')
                return data
            else:
                data = pyzbar.decode(thresh, symbols=[ZBarSymbol.QRCODE])
                if len(data) > 0:
                    print('-----pyzbar thresh------')
                    data = data[0].data.decode('utf-8')
                    return data
                else:
                    return None

    def read_WeChatQRCode(self, frame):
        data, points = self.detector.detectAndDecode(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred_img = cv2.GaussianBlur(gray, (5, 5), 0)
        # (_, self.thresh) = cv2.threshold(self.gray, 80, 255, cv2.THRESH_BINARY)
        thresh = cv2.adaptiveThreshold(blurred_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        if data != ():
            data = data[0]
            if len(data) > 8:
                print("---------frame read_WeChatQRCode---------")
                return data
            else:
                return self.read_data_pyzbar(frame, gray, thresh)
        else:
            data, points = self.detector.detectAndDecode(gray)
            if data != ():
                data = data[0]
                if len(data) > 8:
                    print("---------gray read_WeChatQRCode---------")
                    return data
                else:
                    return self.read_data_pyzbar(frame, gray, thresh)
            else:
                return self.read_data_pyzbar(frame, gray, thresh)

    def read_data_zxingcpp(self, frame, gray, thresh):
        data = zxingcpp.read_barcode(frame)
        if data is not None:
            print('-----zxing frame------')
            return data.text
        else:
            data = zxingcpp.read_barcode(thresh)
            if data is not None:
                print('-----zxing thresh------')
                return data.text
            else:
                return self.read_data_pyzbar(frame, gray, thresh)

    def read_data_pylibdmtx(self, frame):
        data = pylibdmtx.decode(frame, timeout=50)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
        if data is not None:
            print('-------frame pylibdmtx-------')
            return data[0].data.decode('utf-8')
        else:
            data = pylibdmtx.decode(gray, timeout=10)
            if data is not None:
                print('-------gray pylibdmtx-------')
                return data[0].data.decode('utf-8')
            else:
                data = pylibdmtx.decode(thresh, timeout=10)
                if data is not None:
                    print('-------gray pylibdmtx-------')
                    return data[0].data.decode('utf-8')
                else:
                    return None

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
        print(new_width)
        print(new_height)
        new_label_size = self.ui.frame.size()
        new_label_size.setWidth(new_width)
        new_label_size.setHeight(new_height)
        self.ui.frame.setFixedSize(new_label_size)


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

    print(window_width, 'width')
    print(window_height, 'height')

    # Thiết lập vị trí xuất hiện ở góc dưới bên phải
    x = screen_width - window_width - int(window.config[8])
    y = screen_height - window_height - 70 - int(window.config[9])
    window.move(x, y)
    window.show()
    sys.exit(app.exec_())
