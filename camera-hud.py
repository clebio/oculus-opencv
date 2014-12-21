# ******************************************************************************
# Argon Design Ltd. Project P8008 Slam
# (c) Copyright 2014 Argon Design Ltd. All rights reserved.
#
# Module : oculusVideo2
# Author : Joel Goddard
# $Id: oculusVideo.py 6409 2014-08-18 14:26:50Z xxx $
# ******************************************************************************

"""
Oculus Video: streams two camera feeds into the Oculus Rift after having distorted
    them to account for pincushion effect
May require some calibration through sliders provided
    (They will appear on the Oculus Rift)
For this to work the oculus rift should be the main screen
Please note this code is not dynamic and will need to be calibrated manually
Requires OpenCV 2.4.9, numpy 1.8.1 and ovrsdk
"""

import timeit
import cv2
import numpy as np
import time
from ovrsdk import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import os
import threading

#timing stuff

t1=-1
t2=-1

frames = np.array([])
startTime = time.clock()
lastTime=time.clock()
i=0
loop=0

#fps counter (not integral to program
def fps(time):
        global frames
        global t1
        global t2

        continueFunc=False

        if t1<0:
                t1=time
                t2=-1
                continueFunc=False
        elif t2<0:
                t2=time
                continueFunc=True
        else:
                t1=t2
                t2=time
                continueFunc=True

        if continueFunc==True:
                x, = frames.shape
                if x<10:
                        frames = np.append(frames, [t2-t1])
                else:
                        frames = np.append(frames[1:], [t2-t1])
                        #print str(9/np.sum(frames))+" f/s"

#timestamper (disabled)
def timeDifference():
        pass
        #global i
        #global lastTime
        #print str(i) + ": " + str(loop) + ") " + str(time.clock()-lastTime)
        #lastTime=time.clock()
        #i=i+1

timeDifference()

#------------------------------------------------------------------------------
#Matrix coefficients for left eye barrel effect
fxL = 257
cxL = 207
fyL = 211
cyL = 138

#Matrix coefficients for right eye barrel effect
fxR = 257
cxR = 207
fyR = 211
cyR = 138

#offset to align images
xL = 23
yL = 15
xR = -xL
yR = -yL

#offsets to translate image before distortion
xO = 212-200
yO = 100-200

#offsets to translate image after distortion
xO2 = 245-200
yO2 = 217-200

#amount to crop image by (R values currently useless)
cropXL = 0
cropXR = 0
cropYL = 127
cropYR = 0

#width and height of image
width = 0
height = 0

#new------------------------------------------------------------------------------
ESCAPE = ''

window = 0



DIRECTION = 1

size = 640

img = None

cR = cv2.VideoCapture(1)
cL = cv2.VideoCapture(2)
timeDifference()

#openGL setup
def InitGL(width, height):
        timeDifference()
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)


#keypresss detection
def keyPressed(*args):
        if args[0] == ESCAPE:
                sys.exit()

#starts opengl and the main loop
#The GLUT renders the teapot in an invisible window so that the teapot can be read off
#the graphics card
def main():
        timeDifference()
        global window

        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
        glutInitWindowSize(640,480)
        glutInitWindowPosition(200,200)

        window = glutCreateWindow('Invisible window')
        glutHideWindow()
        glutDisplayFunc(DrawGLScene)
        glutIdleFunc(DrawGLScene)
        glutKeyboardFunc(keyPressed)
        InitGL(640, 480)
        glutMainLoop()
        timeDifference()
#------------------------------------------------------------------------------




#this is where positioning data should be gathered
def oculusLoop():
        timeDifference()

        """possitioning data gathered here"""
        ss = ovrHmd_GetSensorState(hmd, ovr_GetTimeInSeconds())
        pose = ss.Predicted.Pose
        global xO
        global yO

        global X_AXIS
        global Y_AXIS
        global Z_AXIS

        global xOffset
        global yOffset


#Transformation functions
#------------------------------------------------------------------------------
#this crops the image by the amounts specified returning cropped image
# (R values don't work)
def crop(image, xL, xR, yL, yR):
    """should crop image by specifying the parts of the image to remove"""
    return image[xL:width-xR, yL:height-yR]

#this creates the distortion matrix for barrel effect
def createDistortionMatrix(fx, cx, fy, cy):
    """creates a distortion matrix specific for the lens"""
    matrix = np.array([[fx, 0, cx],
                    [0, fy, cy],
                    [0, 0, 1]])

    return matrix

#this applies the barrel effect to the image
def transform(image, matrix):
    """corrects for pincushion distortion by adding a barrel effect
        based on the matrix"""
    if matrix == None:
        matrix = np.array([[200, 0, 200],
                        [0.0, 200, 95],
                        [0.0, 0.0, 1]])

    imageDis = cv2.undistort(image, matrix, np.array([0.22, 0.2400, 0, 0, 0]))

    return imageDis

# this joins the left and right image together to make one image
def joinImages(imageL, imageR):
    """joins the images together with the append function"""
    return np.append(imageL, imageR, axis=1)

#this translates the image
def translate(image, x, y):
    """translates the image by the provided vector"""
    rows,cols = 288, 384
    matrix = np.float32([[1,0,x],[0,1,y]])

    imageT = cv2.warpAffine(image, matrix, (cols, rows))

    return imageT

#------------------------------------------------------------------------------


#Main loop function
def DrawGLScene():
        global loop


        loop+=1
        timeDifference()
        global X_AXIS,Y_AXIS,Z_AXIS
        global DIRECTION
        global size

        #gets the position data from the oculus rift
        oculusLoop()

        #openGL stuff
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(0, -200, 640, 800)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(35., 640 / float(800), .1, 1000.)
        glMatrixMode(GL_MODELVIEW)

        glLoadIdentity()
        glTranslatef(0.0,0.0,-50.0)

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        #gets the 3D model to use from another file
        glDisable(GL_LIGHTING)

        glutSwapBuffers()
        global width
        global height
        global img
        global cropXL
        global cropXR
        global cropYL
        global cropYR
        glFlush()
        glReadBuffer( GL_BACK )

        #reads the frame from the camera stream
        x,fraL = cL.read()
        x,fraR = cR.read()
        height, width, t = fraL.shape


        #creates distortion matrix
        matrixL = createDistortionMatrix(fxL, cxL, fyL, cyL)
        matrixR = createDistortionMatrix(fxR, cxR, fyR, cyR)
        #translates, crops and distorts image
        fraLT = translate(fraL, xL+xO, yL+yO)
        fraRT = translate(fraR, xR+xO, yR+yO)
        fraLd = transform(fraLT, matrixL)
        fraRd = transform(fraRT, matrixR)
        fraLT2 = translate(fraLd, xO2, yO2)
        fraRT2 = translate(fraRd, xO2, yO2)
        fraLs = crop(fraLT2, cropXL, cropXR, cropYL, cropYR)
        fraRs = crop(fraRT2, cropXL, cropXR, cropYL, cropYR)
        fraCom = joinImages(fraLs, fraRs)
        timeDifference()
        #displays image
        cv2.imshow('vid',fraCom)
        timeDifference()

        #fps counter
        fps(time.clock())

        #detects keypress
        key = cv2.waitKey(1)
        if key == ord('q'):
                cv2.destroyAllWindows()
                cR.release()
                cL.release()
                sys.exit()

#------------------------------------------------------------------------------
#calibration funtions

"""These functions create sliders that allow you to change variables as the program"""

def xOSliderChange(value):
    global xO
    xO = value-200

def yOSliderChange(value):
    global yO
    yO = value-200

def xO2SliderChange(value):
    global xO2
    xO2 = value-200

def yO2SliderChange(value):
    global yO2
    yO2 = value-200

def xSliderChange(value):
    global xL
    global xR
    xL = value
    xR = -value

def ySliderChange(value):
    global yL
    global yR
    yL = value
    yR = -value

def calibrateOffset():
    cv2.namedWindow('offset sliders', cv2.CV_WINDOW_AUTOSIZE)
    cv2.createTrackbar('xO', 'offset sliders', xO+200, 265, xOSliderChange)
    cv2.createTrackbar('yO', 'offset sliders', yO+200, 400, yOSliderChange)
    cv2.createTrackbar('xO2', 'offset sliders', xO2+200, 400, xO2SliderChange)
    cv2.createTrackbar('yO2', 'offset sliders', yO2+200, 400, yO2SliderChange)
    cv2.createTrackbar('x', 'offset sliders', xL, 200, xSliderChange)
    cv2.createTrackbar('y', 'offset sliders', yL, 200, ySliderChange)


def xOffsetSliderChange(value):
    global xOffset
    xOffset = value-200

def yOffsetSliderChange(value):
    global yOffset
    yOffset = value-200

def xTeaSliderChange(value):
    global xLTea
    global xRTea
    xLTea = value-100
    xRTea = -(value-100)

def yTeaSliderChange(value):
    global yLTea
    global yRTea
    yLTea = value-100
    yRTea = -(value-100)

def calibrateOffset2():
    cv2.namedWindow('offset2 sliders', cv2.CV_WINDOW_AUTOSIZE)
    cv2.createTrackbar('xTea', 'offset2 sliders', xLTea+100, 200, xTeaSliderChange)
    cv2.createTrackbar('yTea', 'offset2 sliders', yLTea+100, 200, yTeaSliderChange)
    cv2.createTrackbar('x', 'offset2 sliders', xOffset+200, 400, xOffsetSliderChange)
    cv2.createTrackbar('y', 'offset2 sliders', yOffset+200, 400, yOffsetSliderChange)

def fxLSliderChange(value):
    global fxL
    fxL = value

def cxLSliderChange(value):
    global cxL
    cxL = value

def fyLSliderChange(value):
    global fyL
    fyL = value

def cyLSliderChange(value):
    global cyL
    cyL = value

def calibrateMatrixLeft():
    cv2.namedWindow('left matrix sliders', cv2.CV_WINDOW_AUTOSIZE)
    cv2.createTrackbar('fxL', 'left matrix sliders', fxL, 500, fxLSliderChange)
    cv2.createTrackbar('cxL', 'left matrix sliders', cxL, 400, cxLSliderChange)
    cv2.createTrackbar('fyL', 'left matrix sliders', fyL, 500, fyLSliderChange)
    cv2.createTrackbar('cyL', 'left matrix sliders', cyL, 400, cyLSliderChange)

def fxRSliderChange(value):
    global fxR
    fxR = value

def cxRSliderChange(value):
    global cxR
    cxR = value

def fyRSliderChange(value):
    global fyR
    fyR = value

def cyRSliderChange(value):
    global cyR
    cyR = value

def calibrateMatrixRight():
    cv2.namedWindow('right matrix sliders', cv2.CV_WINDOW_AUTOSIZE)
    cv2.createTrackbar('fxR', 'right matrix sliders', fxR, 500, fxRSliderChange)
    cv2.createTrackbar('cxR', 'right matrix sliders', cxR, 400, cxRSliderChange)
    cv2.createTrackbar('fyR', 'right matrix sliders', fyR, 500, fyRSliderChange)
    cv2.createTrackbar('cyR', 'right matrix sliders', cyR, 400, cyRSliderChange)

def cropxRSliderChange(value):
    global cropXR
    cropXR = value

def cropxLSliderChange(value):
    global cropXL
    cropXL = value

def cropyRSliderChange(value):
    global cropYR
    cropYR = value

def cropyLSliderChange(value):
    global cropYL
    cropYL = value

def calibrateCrop():
    cv2.namedWindow('crop sliders', cv2.CV_WINDOW_AUTOSIZE)
    cv2.createTrackbar('cropxL', 'crop sliders', cropXR, 200, cropxRSliderChange)
    cv2.createTrackbar('cropxR', 'crop sliders', cropXL, 200, cropxLSliderChange)
    cv2.createTrackbar('cropyL', 'crop sliders', cropYR, 200, cropyRSliderChange)
    cv2.createTrackbar('cropyR', 'crop sliders', cropYL, 200, cropyLSliderChange)

def rotaionSliderChange(value):
    global rotationC
    rotationC = value

def translationSliderChange(value):
    global translationC
    translationC = value

def rollSliderChange(value):
    global rollC
    rollC = value-1000

def calibrateMovement():
    cv2.namedWindow('movement sliders', cv2.CV_WINDOW_AUTOSIZE)
    cv2.createTrackbar('rotaion', 'movement sliders', rotationC, 1000,
        rotaionSliderChange)
    cv2.createTrackbar('translation', 'movement sliders', translationC, 2000,
        translationSliderChange)
    cv2.createTrackbar('roll', 'movement sliders', rollC, 2000, rollSliderChange)

def movementSliderSize(value):
    global size
    size = value

def calibrateSize():
    cv2.namedWindow('size sliders', cv2.CV_WINDOW_AUTOSIZE)
    cv2.createTrackbar('size', 'size sliders', size, 1000, movementSliderSize)

def calibrate():
    """runs the calibration functions"""
    calibrateOffset()
    calibrateMatrixLeft()
    calibrateMatrixRight()
    calibrateCrop()
    calibrateOffset2()
    calibrateMovement()
#------------------------------------------------------------------------------

"""initializes ovrsdk and starts tracking oculus"""
ovr_Initialize()
hmd = ovrHmd_Create(0)
hmdDesc = ovrHmdDesc()
ovrHmd_GetDesc(hmd, byref(hmdDesc))
ovrHmd_StartSensor( hmd,
    ovrSensorCap_Orientation |
    ovrSensorCap_YawCorrection,
    0
)


#open camera and start streaming

cv2.namedWindow('vid', 16 | cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("vid", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
#remove hashes and everyting between to calibrate#calibrate()
main()
