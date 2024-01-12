import time

import cv2

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_SETTINGS, 1)

while True:
    res, frame = cap.read()
    if res:
        cv2.imshow('camera', frame)
        if cv2.waitKey(1) and 0xFF == ord('c'):
            cv2.imwrite('image/%s.png' % (time.time()))


