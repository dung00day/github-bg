import serial

name1 = "COM4"
name2 = "COM14"
name3 = "COM12"
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
    signal_plc = ser_com1.readline()
    signal_m2 = ser_com2.readline()
    if signal_plc == b'4':
        ser_com1.write(b'4')
    if signal_m2 == b'4':
        ser_com2.write(b'1\n')