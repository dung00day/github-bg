import serial
import cv2
name1 = "COM1"
name2 = "COM2"
name3 = "COM3"
name4 = "COM4"
name5 = "COM5"
name6 = "COM6"

baud = 9600

try:
    ser_com1 = serial.Serial(
        port=name1,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.0009
    )
except Exception as exx:
    print(exx, 'Error serial')

try:
    ser_com2 = serial.Serial(
        port=name2,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.0009
    )
except Exception as exx:
    print(exx, 'Error serial')

try:
    ser_com3 = serial.Serial(
        port=name3,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.0009
    )
except Exception as exx:
    print(exx, 'Error serial')

try:
    ser_com4 = serial.Serial(
        port=name4,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.0009
    )
except Exception as exx:
    print(exx, 'Error serial')

try:
    ser_com5 = serial.Serial(
        port=name5,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.0009
    )
except Exception as exx:
    print(exx, 'Error serial')

try:
    ser_com6 = serial.Serial(
        port=name6,
        baudrate=baud,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.0009
    )
except Exception as exx:
    print(exx, 'Error serial')

# ser_com1.write(b'3\r\n')
# ser_com1.write(b'8')
# ser_com1.write(b'5\r\n')
# ser_com1.write(b'6\r\n')
# ser_com1.write(b'7\r\n')
# ser_com1.write(b'8\r\n')

while True:
    signal1 = ser_com1.readline()
    signal2 = ser_com2.readline()
    # signal3 = ser_com3.readline()
    if len(signal1) > 0:
        print('tín hiệu 1:', signal1)

    # ser_com1.write(b'4\r\n')

    if len(signal2) > 0:
        print('tín hiệu 2:', signal2)
    # if len(signal3) > 0:
    #     print('tín hiệu 3:', signal3)
    signal4 = ser_com4.readline()
    signal5 = ser_com5.readline()
    signal6 = ser_com6.readline()
    if len(signal4) > 0:
        print('tín hiệu 4:', signal4)
    if len(signal5) > 0:
        print('tín hiệu 5:', signal5)
    if len(signal6) > 0:
        print('tín hiệu 6:', signal6)
