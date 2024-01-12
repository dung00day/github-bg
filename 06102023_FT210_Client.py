import os
import cv2
import wx
import wx.xrc
from GUI import Resource
from GUI.GUI_FrameBase import GUI_FrameBase as GFB
from pyzbar import pyzbar
import zxingcpp
import serial
import numpy as np
import threading
import time
# import imutils
from pylibdmtx.pylibdmtx import decode
import datetime
import logging

def get_current_date():
    return datetime.datetime.now().strftime('%Y-%m-%d')

# Function to create a new log file with the current date as the filename
def create_new_log_file():
    log_filename = f'./logs/app_{get_current_date()}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    return file_handler
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)


# Create a new log file on program start
logger.addHandler(create_new_log_file())


class GUI_FrameSYS(GFB):
    defaultBG = cv2.imread(os.getcwd() + "/BG_camera.png")
    showIMG = defaultBG.copy()
    color_white = [255, 255, 255]
    cfg_config = os.getcwd() + "/config_client.txt"
    Flag_Unlock = False
    res = False
    res2 = False
    Flag_Start = True
    flag_plc = False
    RunProject = True
    flag_frame1 = True
    flag_frame2 = True
    list_barcode = [0, 0]
    list_docdc = [0, 0]
    count_frame = 0
    count_sfc = 0
    flag_NG = False
    flag_sfc = True
    path_dir = r"qrcode_python_wechar"
    detect_model = path_dir + "/detect.caffemodel"
    detect_protox = path_dir + "/detect.prototxt"
    sr_model = path_dir + "/sr.caffemodel"
    sr_protox = path_dir + "/sr.prototxt"
    detector = cv2.wechat_qrcode_WeChatQRCode(detect_protox, detect_model, sr_protox, sr_model)


    def __init__(self, parent):
        super(GUI_FrameSYS, self).__init__(parent)
        "maximize window"
        self.ShowFullScreen(True)
        self.data_config = self.get_config(self.cfg_config)
        # self.data_barcode = self.get_barcode(self.cfg_barcode)
        self.com_host = self.data_config[0]
        self.EXP_CAM_1 = int(self.data_config[1])
        self.EXP_CAM_2 = int(self.data_config[2])
        self.Count_None = int(self.data_config[3])
        self.min_threshold = int(self.data_config[4])
        self.max_threshold = int(self.data_config[5])
        self.min_max = int(self.data_config[6])
        self.time_sleep_send_host = float(self.data_config[7])
        self.time_sleep_send_pass = float(self.data_config[8])
        self.crop_y1 = int(self.data_config[9])
        self.crop_y2 = int(self.data_config[10])
        self.crop_x1 = int(self.data_config[11])
        self.crop_x2 = int(self.data_config[12])
        self.kernel_a = int(self.data_config[13])
        self.kernel_b = int(self.data_config[14])

        # time.sleep(2)
        self.ThreadSerial = threading.Thread(target=self.ReadSerial)
        self.ThreadSerial.start()
        self.ThreadCam = threading.Thread(target=self.Camera)
        self.ThreadCam.start()
        # self.Threadonrun = threading.Thread(target=self.OnRun)
        # self.Threadonrun.start()

        boxCam = wx.FlexGridSizer(1, 3, 5, 5)
        # boxCam = wx.BoxSizer(wx.HORIZONTAL)
        boxCam.AddGrowableCol(1)
        boxCam.AddGrowableCol(2)

        boxCam.AddGrowableRow(0)
        controlPart = self.controlPanel(self.mainPanel)
        boxCam.Add(controlPart, 0, wx.EXPAND | wx.ALL)

        panCam = self.panCampart(self.mainPanel)
        boxCam.Add(panCam, 0, wx.EXPAND | wx.ALL)

        panCam2 = self.panCampart2(self.mainPanel)
        boxCam.Add(panCam2, 0, wx.EXPAND | wx.ALL)

        self.mainPanel.SetSizer(boxCam)
        self.mainPanel.Layout()
        boxCam.FitInside(self.mainPanel)
        self.OnDatabyDev()
        self.OnRun()

    def controlPanel(self, parentPanel):
        boxPlatform = wx.BoxSizer(wx.VERTICAL)
        self.panControl = wx.Panel(parentPanel, size=(130, -1))
        self.panControl.SetBackgroundColour("gray")

        vbox = wx.FlexGridSizer(5, 0, 30, 30)
        # vbox.AddGrowableRow(5)
        vbox.AddGrowableRow(4)
        vbox.AddGrowableCol(0)

        self.titleResult = wx.StaticText(self.panControl, label="Result:")
        self.titleResult.SetForegroundColour((180, 180, 180))
        self.titleResult.SetFont(wx.Font(26, 74, 90, 92, False, "Tahoma"))

        self.showResult = wx.StaticText(self.panControl, label="")
        self.showResult.SetFont(wx.Font(18, 74, 90, 92, False, "Tahoma"))

        vbox.AddMany([(self.titleResult, 1, wx.ALIGN_CENTER), (self.showResult, 1, wx.ALIGN_LEFT)])

        self.panControl.SetSizer(vbox)
        self.panControl.Layout()
        boxPlatform.Add(self.panControl, 1, wx.EXPAND | wx.ALL)
        # self.unlock.Bind(wx.EVT_BUTTON, self.On_Unlock)
        return boxPlatform

    def panCampart(self, parentPanel):
        boxPlatform = wx.FlexGridSizer(2, 0, 0, 0)
        boxPlatform.AddGrowableRow(0)
        boxPlatform.AddGrowableCol(0)

        self.panCam1 = wx.Panel(parentPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.panCam1.SetBackgroundColour("Blue")
        self.panCam1.Bind(wx.EVT_PAINT, self.bitmapPanel)
        boxPlatform.Add(self.panCam1, 1, wx.EXPAND)
        return boxPlatform

    def panCampart2(self, parentPanel):
        boxPlatform = wx.FlexGridSizer(2, 0, 0, 0)
        boxPlatform.AddGrowableRow(0)
        boxPlatform.AddGrowableCol(0)

        self.panCam2 = wx.Panel(parentPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.panCam2.SetBackgroundColour("red")
        self.panCam2.Bind(wx.EVT_PAINT, self.bitmapPanel2)
        boxPlatform.Add(self.panCam2, 1, wx.EXPAND)
        return boxPlatform

    def bitmapPanel2(self, e):
        dc = wx.PaintDC(self.panCam2)
        size = self.panCam2.GetSize()
        img = self.showIMG2
        img = cv2.resize(img, (size[0], size[1]), interpolation=cv2.INTER_LINEAR)
        shiftColor = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = wx.Image(size[0], size[1], shiftColor)
        scaled = img.Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
        self.mainBitmap = wx.Bitmap(scaled)
        dc.DrawBitmap(self.mainBitmap, 0, 0)

    def bitmapPanel(self, e):
        dc = wx.PaintDC(self.panCam1)
        size = self.panCam1.GetSize()
        img = self.showIMG
        img = cv2.resize(img, (size[0], size[1]), interpolation=cv2.INTER_LINEAR)
        shiftColor = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = wx.Image(size[0], size[1], shiftColor)
        scaled = img.Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
        self.mainBitmap = wx.Bitmap(scaled)
        dc.DrawBitmap(self.mainBitmap, 0, 0)

    def OnGUIbyDev(self):
        # set pos to bottom right
        dw, dh = wx.DisplaySize()
        w, h = self.GetSize()
        x = dw - w
        y = dh - h
        self.SetPosition((x, y))

    def OnDatabyDev(self):
        pass

    def OnHideConsole(self, e):
        print('OnHideConsole')

    def OnRunEvent(self, event):
        if self.RunProject:
            print("stop")
            self.RunProject = False
            self.BTN_Run.SetBitmap(Resource.RUN())
        else:
            print('------------')
            self.RunProject = True
            self.BTN_Run.SetBitmap(Resource.STOP())
            # self.OnRun()

    def thongbaoloi(self, docduoc):
        ketqua = ""
        for index, i in enumerate(docduoc):
            index += 1
            if i == 0:
                ketqua += str(index)
        return ketqua

    def order_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        # diff = np.diff(pts, axis=1)
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def four_point_transform(self, image, pts):
        rect = self.order_points(pts)
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))

        dst = np.array([
            [10, 10],
            [maxWidth - 10, 10],
            [maxWidth - 10, maxHeight - 10],
            [10, maxHeight - 10]], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return warped

    def get_config(self, cfg_file):
        with open(cfg_file, 'r') as f:
            data = f.readlines()
        Listcof = []
        for i in range(len(data)):
            Listcof.append(str(data[i].split()[1]))
        return Listcof
    def read_barcode(self, frame, gray):
        data = pyzbar.decode(frame)
        if data != []:
            data = data[0][0]
            if len(data) == 12:
                print("-----frame_pyzbar-----")
                return data
            else:
                return None
        else:
            data = pyzbar.decode(gray)
            if data != []:
                print("-----gray_pyzbar-----")
                data = data[0][0]
                if len(data) == 12:
                    return data
                else:
                    return None
            else:
                return None

    def read_WeChatQRCode(self, frame, gray):
        data, points = self.detector.detectAndDecode(frame)
        if data != ():
            data = data[0].encode("UTF-8")
            if len(data) == 12:
                print("---------frame read_WeChatQRCode---------")
                return data
            else:
                return self.read_barcode(frame, gray)
        else:
            data, points = self.detector.detectAndDecode(gray)
            if data != ():
                data = data[0].encode("UTF-8")
                if len(data) == 12:
                    print("---------gray read_WeChatQRCode---------")
                    return data
                else:
                    return self.read_barcode(frame, gray)
            else:
                return self.read_barcode(frame, gray)

    def read_barcode_zxing(self, frame, gray):
        data = zxingcpp.read_barcode(frame)
        if data is not None:
            data = data.text
            if len(data) == 12:
                print("-----frame_zxing-----")
                data = data.encode("utf-8")
                return data
            else:
                return self.read_WeChatQRCode(frame, gray)
        else:
            data = zxingcpp.read_barcode(gray)
            if data is not None:
                data = data.text
                if len(data) == 12:
                    print("-----gray_zxing-----")
                    data = data.encode("utf-8")
                    return data
                else:
                    return self.read_WeChatQRCode(frame, gray)
            else:
                return self.read_WeChatQRCode(frame, gray)

    def read_datamatrix_zxing(self, frame, gray):
        data = zxingcpp.read_barcode(frame)
        if data is not None:
            data = data.text
            if len(data) == 17:
                print("-----frame_zxing data-----")
                data = data.encode("utf-8")
                return data
            else:
                return self.read_datamatrix(frame)
        else:
            data = zxingcpp.read_barcode(gray)
            if data is not None:
                data = data.text
                if len(data) == 17:
                    print("-----gray_zxing data-----")
                    data = data.encode("utf-8")
                    return data
                else:
                    return self.read_datamatrix(frame)
            else:
                return self.read_datamatrix(frame)

    def read_datamatrix(self, frame):
        img = frame[self.crop_y1:self.crop_y2, self.crop_x1:self.crop_x2]
        # img = frame[100:420,100:450]
        kernel = np.ones((self.kernel_a, self.kernel_b), np.uint8)
        filt = cv2.GaussianBlur(src=img, ksize=(3, 3), sigmaX=0, sigmaY=0)
        gray = cv2.cvtColor(filt, cv2.COLOR_BGR2GRAY)
        dilation = cv2.dilate(gray, kernel, iterations=1)
        for threshold in range(self.min_threshold, self.max_threshold, self.min_max):
            _, thresh = cv2.threshold(dilation, threshold, 255, cv2.THRESH_BINARY)
            data = decode(thresh, timeout=60)
            if len(data) > 0:
                print("threshold: ", threshold)
                logger.info(str(threshold) + 'Nguong doc duoc client')
                data = data[0][0]
                if len(data) == 17:
                    return data
        return None

    def Camera(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        # self.cap.set(cv2.CAP_PROP_SETTINGS, 1)
        self.cap.set(cv2.CAP_PROP_EXPOSURE, self.EXP_CAM_1)

        self.cap2 = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        self.cap2.set(cv2.CAP_PROP_EXPOSURE, self.EXP_CAM_2)
        # self.cap2.set(cv2.CAP_PROP_SETTINGS, 1)

        while 1:
            self.res, self.frame = self.cap.read()
            self.res2, self.frame2 = self.cap2.read()
            if self.res and self.res2:
                self.gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                self.gray2 = cv2.cvtColor(self.frame2, cv2.COLOR_BGR2GRAY)
            if self.Flag_Stop == False:
                break
            cv2.waitKey(1)
        self.cap.release()
        self.cap2.release()
        cv2.destroyAllWindows()


    def ReadSerial(self):
        try:
            self.ser = serial.Serial(
                port=self.com_host,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.0009
            )
        except Exception as ex:
            print(ex, 'Loi PLC')
        while True:
            dataPLC = self.ser.readline()
            if len(dataPLC) > 0:
                print("Tin Hieu PLC", dataPLC)
                logger.info(str(dataPLC) + 'Tin hieu host')
            if dataPLC == b'13':
                self.flag_sfc = False
                print("---Reset----")
                self.list_barcode = [0, 0]
                self.showResult.SetLabel("   RESET")
                self.showResult.SetForegroundColour(wx.GREEN)
                self.flag_plc = False
                self.flag_sfc = False
                self.list_docdc = [0, 0]
            if dataPLC == b'10':
                self.list_docdc = [0, 0]
                self.showResult.SetLabel("")
                self.flag_plc = True
                self.flag_sfc = True
                self.flag_frame1 = True
                self.flag_frame2 = True
                self.count_frame = 0
                self.count_sfc = 0
                self.flag_NG = False
            if self.Flag_Stop == False:
                break

    def OnRun(self):
        self.BTN_Run.SetBitmap(Resource.STOP())
        self.showResult.SetLabel("    NONE")

        while self.Flag_Start:
            if self.res and self.res2:
                self.Flag_Start = False
        while self.RunProject:
            self.showIMG = self.frame
            self.showIMG2 = self.frame2
            while self.flag_plc:
                # print("plc")
                self.count_frame += 1
                if self.flag_frame1:
                    # self.roi_warped = self.contours_warped(self.frame, self.frame)
                    # barcode = self.read_barcode_zxing(self.roi_warped, self.gray)
                    barcode = self.read_datamatrix_zxing(self.frame, self.gray)
                    if barcode is not None:
                        if barcode not in self.list_barcode:
                            self.list_barcode[0] = barcode
                            self.list_docdc[0] = barcode
                            print("barcode_Cam1:", barcode)
                            self.flag_frame1 = False
                if self.flag_frame2:
                    # roi_frame2 = self.contours_Qrcode(self.frame2)
                    img = self.frame2[50:460, 0:450]
                    barcode_2 = self.read_barcode_zxing(self.frame2, img)
                    if barcode_2 is not None:
                        if barcode_2 not in self.list_barcode:
                            self.list_barcode[1] = barcode_2
                            self.list_docdc[1] = barcode_2
                            print("datamatrix_Cam2:", barcode_2)
                            self.flag_frame2 = False
                if 0 not in self.list_docdc:
                    self.flag_plc = False
                if 0 in self.list_docdc and self.count_frame > self.Count_None:
                    self.flag_NG = True
                    self.flag_plc = False
            if 0 in self.list_docdc and self.flag_NG:
                ketquaNG = "    FAIL" + self.thongbaoloi(self.list_docdc)
                logger.error(str(ketquaNG) + 'NG TEM')
                self.ser.write(b'12')
                self.showResult.SetLabel(ketquaNG)
                self.showResult.SetForegroundColour(wx.RED)
                self.flag_NG = False
                self.list_docdc = [0, 0]
                cv2.imwrite("img_ng/%s.png"%time.time(), self.frame)
                cv2.imwrite("img_ng/%s.png"%time.time(), self.frame2)
            if 0 not in self.list_docdc:
                # cv2.imwrite("img_ok/%s.png" % time.time(), self.frame)
                # cv2.imwrite("img_ok/%s.png" % time.time(), self.frame2)
                logger.info(str(self.list_docdc) + 'list_docdc_Client')
                self.ser.write(self.list_docdc[0])
                time.sleep(self.time_sleep_send_host)
                self.ser.write(self.list_docdc[1])
                print("--gui data computer1---")
                time.sleep(self.time_sleep_send_pass)
                self.ser.write(b'10')
                self.showResult.SetLabel("   PASS")
                self.showResult.SetForegroundColour(wx.GREEN)
                self.flag_sfc = False
                self.list_docdc = [0, 0]
                self.flag_NG = False
                self.flag_plc = False

            cv2.waitKey(1)
            self.panCam1.Refresh(eraseBackground=False)
            self.panCam2.Refresh(eraseBackground=False)
        self.showIMG = self.defaultBG.copy()
        self.showIMG2 = self.defaultBG.copy()
        self.panCam1.Refresh(eraseBackground=False)
        self.panCam2.Refresh(eraseBackground=False)
        # cap.release()
        cv2.destroyAllWindows()

    def OnQuit(self):
        self.OnStopProject()
        self.Close()
        self.Destroy()


if __name__ == '__main__':
    app = wx.App()
    ex = GUI_FrameSYS(None)
    app.MainLoop()

