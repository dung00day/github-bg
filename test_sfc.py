import serial

name1 = "COM3"
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

while True:
    signal_sfc = ser_com1.readline()
    if len(signal_sfc) > 0:
        print('tín hiệu plc: ', signal_sfc)
    if signal_sfc == b'4':
        ser_com1.write(b'123456')