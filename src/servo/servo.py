#!/usr/bin/env python

################################################
# Module:   servo.py
# Created:  2 April 2008
# Author:   Brian D. Wendt
#   http://principialabs.com/
# Version:  0.3
# License:  GPLv3
#   http://www.fsf.org/licensing/
'''
Provides a serial connection abstraction layer
for use with Arduino "MultipleSerialServoControl" sketch.
'''
################################################

import serial

# Assign Arduino's serial port address
#   Windows example
#     usbport = 'COM3'
#   Linux example
#     usbport = '/dev/ttyUSB0'
#   MacOSX example
#     usbport = '/dev/tty.usbserial-FTALLOK2'
usbport = '/dev/ttyACM0' #'/dev/ttyUSB0'

# Set up serial baud rate
ser = serial.Serial(usbport, 9600, timeout=1)

def move(servo, angle):
    '''Moves the specified servo to the supplied angle.

    Arguments:
        servo
          the servo number to command, an integer from 1-4
        angle
          the desired servo angle, an integer from 0 to 180

    (e.g.) >>> servo.move(2, 90)
           ... # "move servo #2 to 90 degrees"'''
    usbport = '/dev/ttyACM0' #'/dev/ttyUSB0'
    ser = serial.Serial(usbport, 9600, timeout=1)

    if (0 <= angle <= 180):
        ser.write(chr(0xAA))
        ser.write(chr(servo))
        ser.write(chr(angle))
    else:
        print "Servo angle must be an integer between 0 and 180.\n"


from getch import getch

def reader():
    range0 = 90
    range1 = 90

    move(1, range0)
    move(2, range1)

    while True:
        keypress = getch.getch()
        if keypress == 'j':
            range0 += 10
        elif keypress == 'l':
            range0 += -10
        elif keypress == 'i':
            range1 += -10
        elif keypress == 'k':
            range1 += 10

        elif keypress == 'q':
            break

        if range0 > 180:
            range0 = 180
        elif range0 < 0:
            range0 = 0

        if range1 > 165:
            range1 = 165
        elif range1 < 15:
            range1 = 15

        print("Servo 0 set to {}, servo 1 set to {}".format(range0, range1))
        move(1, range0)
        move(2, range1)

if __name__ == '__main__':
    reader()
