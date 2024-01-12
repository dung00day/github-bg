import os

import cv2
from pyzbar import pyzbar
import zxingcpp
import numpy as np
from pylibdmtx.pylibdmtx import decode

image = cv2.imread('D:/SD_CODE/images/test/test_03.png')
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

folder_path = r'D:\SD_CODE\images\image'

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
    data = pyzbar.decode(cleaned_image)
    if len(data) > 0:
        print('-----cleaned_image read_data_pyzbar------')
        data = data[0].data.decode('utf-8')
        return data
    else:
        data = pyzbar.decode(thresholded_image)
        if len(data) > 0:
            print('-----thresholded_image read_data_pyzbar------')
            data = data[0].data.decode('utf-8')
            return data
        else:
            data = pyzbar.decode(erode)
            if len(data) > 0:
                print('-----erode read_data_pyzbar------')
                data = data[0].data.decode('utf-8')
                return data
            else:
                data = pyzbar.decode(dilation)
                if len(data) > 0:
                    print('-----dilation read_data_pyzbar------')
                    data = data[0].data.decode('utf-8')
                    return data
                else:
                    return None


def read_data_zxingcpp(cleaned_image, thresholded_image, erode, dilation):
    # print('vao zxingcpp')
    data = zxingcpp.read_barcode(cleaned_image)
    if data is not None:
        print("---------cleaned_image read_data_zxingcpp---------")
        return data.text
    else:
        # gray
        data = zxingcpp.read_barcode(thresholded_image)
        if data is not None:
            print("---------thresholded_image read_data_zxingcpp---------")
            return data.text
        else:
            data = zxingcpp.read_barcode(erode)
            if data is not None:
                print("---------erode read_data_zxingcpp---------")
                return data.text
            else:
                data = zxingcpp.read_barcode(dilation)
                if data is not None:
                    print("---------dilation read_data_zxingcpp---------")
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
        print("---------cleaned_image read_WeChatQRCode---------")
        return data[0]
    else:
        data, points = detector.detectAndDecode(thresholded_image)
        if data != ():
            print("---------thresholded_image read_WeChatQRCode---------")
            return data[0]
        else:
            data, points = detector.detectAndDecode(erode)
            if data != ():
                print("---------erode read_WeChatQRCode---------")
                return data[0]
            else:
                data, points = detector.detectAndDecode(dilation)
                if data != ():
                    print("---------dilation read_WeChatQRCode---------")
                    return data[0]
                else:
                    read_data_zxingcpp(gray_image, cleaned_image, erode, dilation)


count = 0
count_pass = 0


def scan_qr_code(image_path, threshold):
    image = cv2.imread(image_path)
    height, width, channels = image.shape
    crop_img = image[70:(height - 100), 150:(width - 100)]
    # crop_img = image
    scale_image = cv2.resize(crop_img, dsize=None, fx=1.5, fy=1.5)

    gray_image = cv2.cvtColor(scale_image, cv2.COLOR_BGR2GRAY)

    blurred_image = cv2.GaussianBlur(gray_image, (3, 3), 1)


    kernel_morph = np.ones((3, 3), np.uint8)

    closed_image = cv2.morphologyEx(blurred_image, cv2.MORPH_CLOSE, kernel_morph)
    cleaned_image = cv2.morphologyEx(closed_image, cv2.MORPH_OPEN, kernel_morph)

    _, thresholded_image = cv2.threshold(cleaned_image, threshold, 255, cv2.THRESH_BINARY)


    kernel_dilation = np.ones((3, 3), np.uint8)
    erode = cv2.erode(thresholded_image, kernel_dilation, iterations=1)
    dilation = cv2.dilate(erode, kernel_dilation, iterations=1)

    # scan qr code
    i = 0
    while i < 5:
        data = read_WeChatQRCode(cleaned_image, thresholded_image, erode, dilation)
        if data is not None:
            print('data:', data)
            break
        else:
            i += 1

    if data is None:
        print('khong doc duoc ma: ', image_path)
    else:
        print('data: ', data)

    cv2.imshow('image', crop_img)
    cv2.imshow('cleaned_image', cleaned_image)
    cv2.imshow('thresholded_image', thresholded_image)
    cv2.imshow('erode', erode)
    cv2.imshow('dilation', dilation)
    cv2.waitKey(0)


for image_file in image_files:
    image_path = os.path.join(folder_path, image_file)
    scan_qr_code(image_path, 120)

    # image_path = os.path.join(folder_path, image_file)
    # # image = cv2.imread(image_path)
    # image = cv2.imread(r'D:\SD_CODE\images\image\ (101).png')
    # height, width, channels = image.shape
    # crop_img = image[70:(height-100), 150:(width - 100)]
    # # crop_img = image[150:(height - 180), 220:(width - 170)]
    # # crop_img = image
    # cv2.imshow('crop', crop_img)
    #
    # scale_image = cv2.resize(crop_img, dsize=None, fx=1.2, fy=1.2)
    # # brightness_factor = 0.5
    # gray_image = cv2.cvtColor(scale_image, cv2.COLOR_BGR2GRAY)
    #
    # blurred_image = cv2.GaussianBlur(gray_image, (3, 3), 1)
    # threshold_value = 127
    #
    # _, thresholded_image = cv2.threshold(blurred_image, threshold_value, 255, cv2.THRESH_BINARY_INV)
    #
    # kernel_morph = np.ones((3, 3), np.uint8)
    # closed_image = cv2.morphologyEx(thresholded_image, cv2.MORPH_CLOSE, kernel_morph)
    # cleaned_image = cv2.morphologyEx(closed_image, cv2.MORPH_OPEN, kernel_morph)
    #
    # kernel_dilation = np.ones((1, 1), np.uint8)
    # dilation = cv2.dilate(thresholded_image, kernel_dilation, iterations=1)
    # errosi = cv2.erode(thresholded_image, kernel_dilation, iterations=1)
    #
    # # cv2.imshow('crop Image', crop_img)
    # cv2.imshow('Thresholded Image', thresholded_image)
    # # cv2.imshow('gray_image', scale_image)
    # cv2.imshow('cleaned_image', cleaned_image)
    # cv2.imshow('dilation', dilation)
    # cv2.imshow('errosi', errosi)
    # i = 0
    # count += 1
    # while i < 10:
    #     data = read_WeChatQRCode(scale_image, dilation, errosi)
    #     if data is not None:
    #         print('data:', data)
    #         break
    #     else:
    #         i += 1
    #
    # if data is None:
    #     print('khong doc duoc ma: ', image_path)
    #
    # else:
    #     count_pass += 1

print(f'da doc duoc {count_pass}/{count} ma')
