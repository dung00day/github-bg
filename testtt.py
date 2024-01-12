import serial

baud = 115200
name1 = "COM4"
name2 = "COM10"
name3 = "COM12"
name4 = "COM14"
name5 = "COM16"

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

while True:
    signal1 = ser_com1.readline()
    signal2 = ser_com2.readline()
    signal3 = ser_com3.readline()
    signal4 = ser_com4.readline()
    signal5 = ser_com5.readline()

    if signal1 == b'5':
        ser_com3.write(b'4')
        ser_com4.write(b'4')
    if signal1 == b'4':
        ser_com1.write(b'4')
