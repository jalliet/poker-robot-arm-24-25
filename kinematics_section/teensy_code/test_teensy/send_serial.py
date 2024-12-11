import serial
ser = serial.Serial("COM4", 9600, timeout=0)
ser.open()
   
# Send character 'S' to start the program
ser.write(bytearray('S','utf-8'))

counter = 0
# Read line   
while True:
    line = ser.readline()
    print(line)

    if counter == 100:
        counter = 0
        ser.write(b'hello')
    counter += 1