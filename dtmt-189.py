import os
import time
import cv2
from pyzbar import pyzbar
import zxingcpp
from pylibdmtx import pylibdmtx

image = cv2.imread(r'D:\SD_CODE\images\test\1704169361.5554802.png')
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

folder_path = r'D:\SD_CODE\images\test'

# Lấy danh sách tất cả các tệp tin trong thư mục
file_list = os.listdir(folder_path)

image_extensions = ['.jpg', '.jpeg', '.png']
# image_files = [file for file in file_list if any(file.lower().endswith(ext) for ext in image_extensions)]
image_files = []
for file in file_list:
    for ext in image_extensions:
        if file.endswith(ext):
            image_files.append(file)

print(len(image_files))
# Đọc và hiển thị tất cả các ảnh trong thư mục
for image_file in image_files:
    image_path = os.path.join(folder_path, image_file)
    image = cv2.imread(image_path)
    cv2.imshow('camera', image)
    height, width, channels = image.shape

    # Số pixel muốn cắt bên phải
    pixels_to_cut = 50

    # Tính toán tọa độ bắt đầu và kết thúc cho vùng cắt
    x_start = 250
    x_end = width - pixels_to_cut
    y_start = 100
    y_end = height - 50
    # Cắt (crop) ảnh
    cropped_image = image[y_start:y_end, x_start:x_end]
    # Hiển thị ảnh gốc

    scale_image = cv2.resize(image, dsize=None, fx=1.5, fy=1.5)
    cv2.imshow('Original Image', image)
    # Hiển thị ảnh đã cắt
    # cv2.imshow('Scale Image', cropped_image)
    gray_image = cv2.cvtColor(scale_image, cv2.COLOR_BGR2GRAY)
    # Callback function called when the trackbar value changes
    threshold_value = 128
    _, thresholded_image = cv2.threshold(gray_image, threshold_value, 255, cv2.THRESH_BINARY)
    i = 0
    while i < 5:
        data = pylibdmtx.decode(thresholded_image, timeout=50)
        if data:
            print('data:', data[0].data.decode('utf-8'))
            break
        else:
            i += 1
        # print('khong doc duoc ma')
    cv2.imshow('Thresholded Image', thresholded_image)
    cv2.waitKey(0)


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


def on_trackbar(val):
    height, width, channels = image.shape
    pixels_to_cut = 50
    # Tính toán tọa độ bắt đầu và kết thúc cho vùng cắt
    x_start = 250
    x_end = width - pixels_to_cut
    y_start = 100
    y_end = height - 50

    # Cắt (crop) ảnh
    cropped_image = image[y_start:y_end, x_start:x_end]


    scale_image = cv2.resize(image, dsize=None, fx=1.5, fy=1.5)

    # Hiển thị ảnh gốc
    cv2.imshow('Original Image', scale_image)

    # Hiển thị ảnh đã cắt

    # cv2.imshow('Scale Image', cropped_image)

    gray_image = cv2.cvtColor(scale_image, cv2.COLOR_BGR2GRAY)
    # Callback function called when the trackbar value changes

    threshold_value = val
    _, thresholded_image = cv2.threshold(gray_image, threshold_value, 255, cv2.THRESH_BINARY)
    data = pylibdmtx.decode(thresholded_image, timeout=50)
    cv2.imshow('Thresholded Image', thresholded_image)
    print('data:', data[0].data.decode('utf-8'))



