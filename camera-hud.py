"""
Oculus Video: streams two camera feeds into the Oculus Rift after having distorted
    them to account for pincushion effect

Will display on whichever monitor is current when run.

Requires OpenCV 2.4.9, numpy 1.8.1 and ovrsdk

Based directly off of http://www.argondesign.com/news/2014/aug/26/augmented-reality-oculus-rift/
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

def InitGL(width, height):
        glClearColor(0.0, 0.0, 0.0, 1)
        glEnable(GL_DEPTH_TEST)

def crop(image, xL, xR, yL, yR):
    """should crop image by specifying the parts of the image to remove"""
    return image[xL:width-xR, yL:height-yR]

def createDistortionMatrix(fx, cx, fy, cy):
    """creates a distortion matrix specific for the lens"""
    matrix = np.array([
            [fx, 0, cx],
            [0, fy, cy],
            [0, 0, 1]
    ])
    return matrix

def transform(image, matrix):
    """corrects for pincushion distortion by adding a barrel effect"""
    if matrix == None:
        matrix = np.array([
                [200, 0, 200],
                [0.0, 200, 95],
                [0.0, 0.0, 1]
        ])
    imageDis = cv2.undistort(image, matrix, np.array([0.22, 0.2400, 0, 0, 0]))
    return imageDis

def joinImages(imageL, imageR):
    """joins the images together with the append function"""
    return np.append(imageL, imageR, axis=1)

def translate(image, x, y):
    """translates the image by the provided vector"""
    rows,cols = 288, 384
    matrix = np.float32([[1,0,x],[0,1,y]])
    imageT = cv2.warpAffine(image, matrix, (cols, rows))
    return imageT

def DrawGLScene():
        global loop

        loop+=1
        global X_AXIS,Y_AXIS,Z_AXIS
        global DIRECTION
        global size

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

        if fraL.all() and fraR.all():
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
                cv2.imshow('vid',fraCom)

        key = cv2.waitKey(1)
        if key & 255 == ord('q'):
                cv2.destroyAllWindows()
                cR.release()
                cL.release()
                sys.exit()


if __name__ == '__main__':
    t1=-1
    t2=-1
    frames = np.array([])
    startTime = time.clock()
    lastTime=time.clock()
    i=0
    loop=0

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

    cropXL = 0
    cropXR = 0
    cropYL = 127
    cropYR = 0

    width = 0
    height = 0

    ESCAPE = ''
    window = 0
    DIRECTION = 1

    size = 640

    img = None

    cR = cv2.VideoCapture(0)
    cL = cv2.VideoCapture(1)

    """initializes ovrsdk and starts tracking oculus"""
    ovr_Initialize()
    hmd = ovrHmd_Create(0)
    hmdDesc = ovrHmdDesc()
    ovrHmd_GetDesc(hmd, byref(hmdDesc))
    ovrHmd_StartSensor(
        hmd,
        ovrSensorCap_Orientation | ovrSensorCap_YawCorrection,
        0
    )

    cv2.namedWindow('vid', 16 | cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(
        "vid",
        cv2.WND_PROP_FULLSCREEN,
        cv2.cv.CV_WINDOW_FULLSCREEN
    )

    global window

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(640,480)
    glutInitWindowPosition(200,200)

    def keyPressed(*args):
        key = args[0]
        if key & 255 == ord('q'):
                cv2.destroyAllWindows()
                cR.release()
                cL.release()
                sys.exit()

    window = glutCreateWindow('Invisible window')
    glutHideWindow()
    glutDisplayFunc(DrawGLScene) #
    glutIdleFunc(DrawGLScene)
    glutKeyboardFunc(keyPressed)
    InitGL(640, 480)
    glutMainLoop()
