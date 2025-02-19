import serial
import time
ser = serial.Serial("COM4", 9600, timeout=0)
ser.open()
   
# Send character 'S' to start the program
ser.write(bytearray('S','utf-8'))

def set_pin(pin, status):
    #first 2 numbers: pin number in denary
    #last number: binary true or false for the pin
    #e.g.: 00 1
    pin_str = '%02d' % pin
    stat_str = 0
    if status:
        stat_str = 1
    full_str = pin_str+ ' '+stat_str    
    ser.write(b'set_pin '+full_str+'\n')

def suck():
    ser.write(b'suck\n')

def unsuck():
    ser.write(b'unsuck\n')

def set_angles(angles, relative_speeds): #both are arrays
    #"set_angles <angle0> <angle1> <angle2> <angle3> <r.speed 0> <r.speed 1> <r.speed 2> <r.speed 3>\n"
    message = "set_angles"
    if len(angles) != 4 or len(relative_speeds) != 4:
        print("wrong size dummy")
        return
    for i in angles:
        if i < -135 or i > 135:
            print("wrong angle bounds dummy")
            return
        message += str(i)
    for i in relative_speeds:
        if i < -135 or i > 135:
            print("wrong speed bounds dummy")
            return
        message += str(i)
    message = message+ '\n'
    ser.write(message.encode('utf-8'))

# Read line
while True:
    time.sleep(1)
    set_pin(23, 1)
    time.sleep(1)
    set_pin(23, 0)
    