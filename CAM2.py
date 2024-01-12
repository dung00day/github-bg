import os

import cv2
from pyzbar import pyzbar
import zxingcpp

path_dir = r'qrcode_python_wechar'
detect_model = path_dir + "/detect.caffemodel"
detect_protox = path_dir + "/detect.prototxt"
sr_model = path_dir + "/sr.caffemodel"
sr_protox = path_dir + "/sr.prototxt"
detector = cv2.wechat_qrcode_WeChatQRCode(detect_protox, detect_model, sr_protox, sr_model)



def read_data_pyzbar(frame, gray, thresh):
    data = pyzbar.decode(frame)
    if len(data) > 0:
        print('-----pyzbar frame------')
        data = data[0].data.decode('utf-8')
        return data
    else:
        data = pyzbar.decode(gray)
        if len(data) > 0:
            print('-----pyzbar gray------')
            data = data[0].data.decode('utf-8')
            return data
        else:
            data = pyzbar.decode(thresh)
            if len(data) > 0:
                print('-----pyzbar thresh------')
                data = data[0].data.decode('utf-8')
                return data
            else:
                return None


def read_WeChatQRCode(frame):
    data, points = detector.detectAndDecode(frame)
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # blurred_img = cv2.GaussianBlur(gray, (5, 5), 0)
    # # (_, self.thresh) = cv2.threshold(self.gray, 80, 255, cv2.THRESH_BINARY)
    # thresh = cv2.adaptiveThreshold(blurred_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    if data != ():
        data = data[0]
        if len(data) > 8:
            print("---------frame read_WeChatQRCode---------")
            return data
        else:
            return read_data_pyzbar()
    else:
        data, points = detector.detectAndDecode(gray)
        if data != ():
            data = data[0]
            if len(data) > 8:
                print("---------gray read_WeChatQRCode---------")
                return data
            else:
                return read_data_pyzbar(frame, gray, thresh)
        else:
            return read_data_pyzbar(frame, gray, thresh)


def read_data_zxingcpp(image, gray, thresh):
    # frame scan
    data = zxingcpp.read_barcode(image)
    if data is not None:
        return data.text
    else:
        # gray
        data = zxingcpp.read_barcode(gray)
        if data is not None:
            return data.text
        else:
            data = zxingcpp.read_barcode(thresh)
            if data is not None:
                return data.text
            else:
                return read_data_pyzbar(image, gray, thresh)


# Đường dẫn đến thư mục chứa ảnh
folder_path = "D:/SD_CODE/images/test"

# Lấy danh sách các tệp tin trong thư mục
image_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

# Đọc và hiển thị từng ảnh
for image_file in image_files:
    # Đường dẫn đầy đủ của ảnh
    image_path = os.path.join(folder_path, image_file)

    # Đọc ảnh bằng OpenCV
    image = cv2.imread(image_path)

    # Kiểm tra xem ảnh đã được đọc thành công chưa
    if image is not None:
        # Hiển thị hoặc thực hiện các thao tác khác trên ảnh tại đây
        cv2.imshow("Image", image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred_img = cv2.GaussianBlur(gray, (5, 5), 0)
        (_, thresh) = cv2.threshold(gray, 75, 255, cv2.THRESH_BINARY)
        # thresh = cv2.adaptiveThreshold(blurred_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        i = 0
        data = None
        while i < 10:
            data = read_data_zxingcpp(image, gray, thresh)
            if data is not None:
                break
            else:
                i += 1
        print('detection: ', data)
        cv2.imshow("Gray", gray)
        cv2.imshow("Thresh", thresh)

        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print(f"Không thể đọc ảnh từ: {image_path}")
