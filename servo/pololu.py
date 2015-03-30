#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Based closely on the maestro.py class.

Set servo ranges and establish serial connection.
"""


from getch import getch
import serial
import os

COUNT = 2
RANGES = [90 for _ in range(COUNT)]
BOUNDS = [(20, 160) for _ in range(COUNT)]


PORT = 0
TTY_STR = '/dev/'

USB_DEVS = [t for t in os.listdir('/dev/') if t.startswith('ttyUSB')]
if USB_DEVS:
    TTY_STR +=  USB_DEVS.pop()
else:
    TTY_STR += 'ttyACM0'

print(TTY_STR)

def open_serial(ranges=RANGES, tty_string=TTY_STR, count=COUNT):
    usb =serial.Serial(tty_string)

    for index, _ in enumerate(RANGES):
        set_target(usb, index, 90)

    return usb

def transform(input):
    """Map input angle to the servo's quarter-second angles"""
    min = 2500
    max = 9000 # quarterseconds (angles)
    scale = 180.0 # Angles
    mult = (max-min)/scale
    return int(min + mult * input)

def key_driver(servo):
    """Drive servos based on keyboard input.

    Loops indefinitely until 'q' (quit) is typed.
    """
    inc = 5

    while True:
        keypress = getch.getch()
        if keypress == 'q':
            go_home(servo)
            servo.close()
            break

        if keypress == 'j':
            RANGES[0] += inc
        elif keypress == 'l':
            RANGES[0] += -1*inc
        elif keypress == 'i':
            RANGES[1] += inc
        elif keypress == 'k':
            RANGES[1] += -1*inc

        for index, target in enumerate(RANGES):
            set_target(servo, index, target)

        servo_str = ""
        for idx, target in enumerate(RANGES):
            servo_str += "Servo {}: {:4}  ".format(idx, target)
        print(servo_str)

def constrain_ranges():
    for idx, target in enumerate(RANGES):
        low, high = BOUNDS[idx]
        if target < low:
            RANGES[idx] = low
        if target > high:
            RANGES[idx] = high

def set_target(controller, channel, target):
    """Set servo target angles, within pre-set bounds"""
    constrain_ranges()
    target = transform(target)
    lsb = target & 0x7f #7 bits for least significant byte
    msb = (target >> 7) & 0x7f #shift 7 and take next 7 bits for msb
    cmd = chr(0x84) + chr(channel) + chr(lsb) + chr(msb)
    controller.write(cmd)

def go_home(controller):
    """Move servos to home position"""
    cmd = chr(0x84) + chr(0xA2)
    controller.write(cmd)

if __name__ == '__main__':
    #usbport = '/dev/ttyUSB0'
    #arduino = serial.Serial(usbport, 19200, timeout=1)
    #move_arduino(arduino)
    servo = open_serial(COUNT)
    key_driver(servo)
