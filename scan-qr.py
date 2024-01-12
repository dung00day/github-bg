import os

import cv2
from pyzbar import pyzbar
import zxingcpp
import numpy as np


from pylibdmtx.pylibdmtx import decode
from pyzbar.pyzbar import ZBarSymbol


image = cv2.imread('D:/SD_CODE/images/test/test_03.png')
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

folder_path = r'D:\SD_CODE\images\image-sn'

# Lấy danh sách tất cả các tệp tin trong thư mục
file_list = os.listdir(folder_path)

image_extensions = ['.jpg', '.jpeg', '.png']
# image_files = [file for file in file_list if any(file.lower().endswith(ext) for ext in image_extensions)]
image_files = []
for file in file_list:
    for ext in image_extensions:
        if file.endswith(ext):
            image_files.append(file)


def read_data_pyzbar(cleaned_image, thresholded_image, erode, dilation):
    # print('vao pyzbar')
    data = pyzbar.decode(cleaned_image, symbols=[ZBarSymbol.QRCODE])
    if len(data) > 0:
        # print('-----cleaned_image read_data_pyzbar------')
        data = data[0].data.decode('utf-8')
        return data
    else:
        data = pyzbar.decode(thresholded_image, symbols=[ZBarSymbol.QRCODE])
        if len(data) > 0:
            # print('-----thresholded_image read_data_pyzbar------')
            data = data[0].data.decode('utf-8')
            return data
        else:
            data = pyzbar.decode(erode, symbols=[ZBarSymbol.QRCODE])
            if len(data) > 0:
                # print('-----erode read_data_pyzbar------')
                data = data[0].data.decode('utf-8')
                return data
            else:
                data = pyzbar.decode(dilation, symbols=[ZBarSymbol.QRCODE])
                if len(data) > 0:
                    # print('-----dilation read_data_pyzbar------')
                    data = data[0].data.decode('utf-8')
                    return data
                else:
                    return None


def read_data_zxingcpp(cleaned_image, thresholded_image, erode, dilation):
    # print('vao zxingcpp')
    data = zxingcpp.read_barcode(cleaned_image)
    if data is not None:
        # print("---------cleaned_image read_data_zxingcpp---------")
        return data.text
    else:
        # gray
        data = zxingcpp.read_barcode(thresholded_image)
        if data is not None:
            # print("---------thresholded_image read_data_zxingcpp---------")
            return data.text
        else:
            data = zxingcpp.read_barcode(erode)
            if data is not None:
                # print("---------erode read_data_zxingcpp---------")
                return data.text
            else:
                data = zxingcpp.read_barcode(dilation)
                if data is not None:
                    # print("---------dilation read_data_zxingcpp---------")
                    return data.text
                else:
                    return read_data_pyzbar(cleaned_image, thresholded_image, erode, dilation)


path_dir = r'qrcode_python_wechar'
detect_model = path_dir + "/detect.caffemodel"
detect_protox = path_dir + "/detect.prototxt"
sr_model = path_dir + "/sr.caffemodel"
sr_protox = path_dir + "/sr.prototxt"
detector = cv2.wechat_qrcode_WeChatQRCode(detect_protox, detect_model, sr_protox, sr_model)


def read_WeChatQRCode(cleaned_image, thresholded_image, erode, dilation):
    data, points = detector.detectAndDecode(cleaned_image)
    if data != ():
        # print("---------cleaned_image read_WeChatQRCode---------")
        return data[0]
    else:
        data, points = detector.detectAndDecode(thresholded_image)
        if data != ():
            # print("---------thresholded_image read_WeChatQRCode---------")
            return data[0]
        else:
            data, points = detector.detectAndDecode(erode)
            if data != ():
                # print("---------erode read_WeChatQRCode---------")
                return data[0]
            else:
                data, points = detector.detectAndDecode(dilation)
                if data != ():
                    # print("---------dilation read_WeChatQRCode---------")
                    return data[0]
                else:
                    read_data_pyzbar(cleaned_image, thresholded_image, erode, dilation)


count = 0
count_pass = 0


def scan_qr_code(image_path, threshold, count_pass=0):
    image = cv2.imread(image_path)
    height, width, channels = image.shape
    # crop_img = image[50:(height - 100), 50:(width - 100)]
    crop_img = image[50:(height - 120), 50:(width - 150)]

    # crop_img = image
    scale_image = cv2.resize(crop_img, dsize=None, fx=1.25, fy=1.25)

    gray_image = cv2.cvtColor(scale_image, cv2.COLOR_BGR2GRAY)

    blurred_image = cv2.GaussianBlur(gray_image, (3, 3), 1)

    _, thresholded_image = cv2.threshold(blurred_image, threshold, 255, cv2.THRESH_BINARY_INV)

    kernel_morph = np.ones((3, 3), np.uint8)

    closed_image = cv2.morphologyEx(thresholded_image, cv2.MORPH_CLOSE, kernel_morph)
    cleaned_image = cv2.morphologyEx(closed_image, cv2.MORPH_OPEN, kernel_morph)

    kernel_dilation = np.ones((1, 1), np.uint8)
    erode = cv2.erode(thresholded_image, kernel_dilation, iterations=1)
    dilation = cv2.dilate(erode, kernel_dilation, iterations=1)
    # cv2.imshow('image', crop_img)
    # cv2.imshow('cleaned_image', cleaned_image)
    # cv2.imshow('thresholded_image', thresholded_image)
    # cv2.imshow('erode', erode)
    # cv2.imshow('dilation', dilation)
    # scan qr code
    i = 0
    while i < 5:
        data = read_WeChatQRCode(cleaned_image, thresholded_image, erode, dilation)
        if data is not None:
            print(f'thresh inv: {threshold}, img: {image_path}')
            break
        else:
            i += 1
            threshold += 5
            _, thresholded_image = cv2.threshold(blurred_image, threshold, 255, cv2.THRESH_BINARY_INV)

            kernel_morph = np.ones((3, 3), np.uint8)

            closed_image = cv2.morphologyEx(thresholded_image, cv2.MORPH_CLOSE, kernel_morph)
            cleaned_image = cv2.morphologyEx(thresholded_image, cv2.MORPH_OPEN, kernel_morph)

            kernel_dilation = np.ones((1, 1), np.uint8)
            erode = cv2.erode(thresholded_image, kernel_dilation, iterations=1)
            dilation = cv2.dilate(erode, kernel_dilation, iterations=1)

            # _, thresholded_image = cv2.threshold(blurred_image, 120, 255, cv2.THRESH_BINARY)
            # closed_image = cv2.morphologyEx(thresholded_image, cv2.MORPH_CLOSE, kernel_morph)
            # cleaned_image = cv2.morphologyEx(closed_image, cv2.MORPH_OPEN, kernel_morph)
            # erode = cv2.erode(thresholded_image, kernel_dilation, iterations=1)
            # dilation = cv2.dilate(erode, kernel_dilation, iterations=1)
            # cv2.imshow('image1', crop_img)
            # cv2.imshow('cleaned_image1', cleaned_image)
            # cv2.imshow('thresholded_image1', thresholded_image)
            # cv2.imshow('erode1', erode)
            # cv2.imshow('dilation1', dilation)

    if data is None:
        # print('khong doc duoc ma khi inv: ', image_path)
        threshold_no_inv = 90
        i = 0
        while i < 22:
            data = read_WeChatQRCode(cleaned_image, thresholded_image, erode, dilation)
            if data is not None:
                print(f'thresh (no inv): {threshold_no_inv}, img: {image_path}')
                count_pass += 1
                break
            else:
                i += 1
                threshold_no_inv += 5
                _, thresholded_image = cv2.threshold(blurred_image, threshold_no_inv, 255, cv2.THRESH_BINARY)
                closed_image = cv2.morphologyEx(thresholded_image, cv2.MORPH_CLOSE, kernel_morph)
                cleaned_image = cv2.morphologyEx(closed_image, cv2.MORPH_OPEN, kernel_morph)
                erode = cv2.erode(thresholded_image, kernel_dilation, iterations=1)
                dilation = cv2.dilate(erode, kernel_dilation, iterations=1)
                # cv2.imshow('image1', crop_img)
                # cv2.imshow('cleaned_image1', cleaned_image)
                # cv2.imshow('thresholded_image1', thresholded_image)
                # cv2.imshow('erode1', erode)
                # cv2.imshow('dilation1', dilation)

    if data is None:
        print(f'khong doc duoc ma: -----------{image_path}----------', )
    # else:
    #     print('data: ', data)
    cv2.waitKey(0)
    return data
for image_file in image_files:
    image_path = os.path.join(folder_path, image_file)
    data = scan_qr_code(image_path, 150)
    count += 1
    if data is not None:
        count_pass += 1
print(f'pass {count_pass}/{count}')

# 101 -> 94, 106
# 102 -> xxx bo qua
# 105 -> xxx bo qua
# 2 -> 64
# 24 -> 145, 151, 152, 154, 155, 157
# 27 -> 118, 119, 120, 121, 122, 123, 125
# 30 -> xxx bo qua
# 35 -> 189, 190, 191, 192, 196, 197, 198, 199, 201, 202, 203, 204, 207
# 7 -> xxx
# 79 -> 101, 102
# 93 -> xxx  bo qua
# 94 -> xxx  bo qua
