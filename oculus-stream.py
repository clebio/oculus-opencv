"""
Oculus Video: streams two camera feeds into the Oculus Rift after having distorted
    them to account for pincushion effect

Will display on whichever monitor is current when run.

Requires OpenCV 2.4.9, numpy 1.8.1 and ovrsdk

Based directly off of http://www.argondesign.com/news/2014/aug/26/augmented-reality-oculus-rift/
"""


import cv2
import numpy as np
import time
from ovrsdk import *

def crop(image, xL, xR, yL, yR, width, height):
    return image[xL:width-xR, yL:height-yR]

def createDistortionMatrix(fx, cx, fy, cy):
    matrix = np.array([
        [fx, 0, cx],
        [0, fy, cy],
        [0, 0, 1]
    ])
    return matrix

def transform(image, matrix):
    if matrix == None:
        matrix = np.array([
            [200, 0, 200],
            [0.0, 200, 95],
            [0.0, 0.0, 1]
        ])
    imageDis = cv2.undistort(image, matrix, np.array([0.22, 0.24, 0, 0, 0]))
    return imageDis

def joinImages(imageL, imageR):
    return np.append(imageL, imageR, axis=1)

def translate(image, x, y):
    """Oculus DK2 is two images together equal to 2364 x 1461

    Also see the bottom of this page:
    http://www.3dtv.at/knowhow/EncodingDivx_en.aspx
    """
    rows, cols = 576, 720 #288, 384
    matrix = np.float32([[1, 0, x], [0, 1, y]])
    imageT = cv2.warpAffine(image, matrix, (cols, rows))
    return imageT

if __name__ == '__main__':
    t1 = -1
    t2 = -1
    startTime = time.clock()
    lastTime = time.clock()

    #Matrix coefficients for left eye barrel effect
    fxL = 300
    fyL = 200
    cxL = 300
    cyL = 240

    #Matrix coefficients for right eye barrel effect
    fxR = fxL #257
    fyR = fyL #211
    cxR = cxL #207
    cyR = cyL #138

    #offset to align images
    xL = 0
    yL = 0
    xR = -xL
    yR = -yL

    #offsets to translate image before distortion
    xO = 0
    yO = 0

    #offsets to translate image after distortion
    xO2 = -70
    yO2 = 40


    ESCAPE = ''
    window = 0

    cR = cv2.VideoCapture(0)
    cL = cv2.VideoCapture(1)

    """initializes ovrsdk and starts tracking oculus"""
    ovr_Initialize()
    hmd = ovrHmd_Create(0)
    try:
        hmd.contents
    except ValueError as _ex:
        print('Failed to initialize Oculus, is it connected?')
        sys.exit()

    hmdDesc = ovrHmdDesc()
    ovrHmd_GetDesc(hmd, byref(hmdDesc))
    ovrHmd_StartSensor(
        hmd,
        ovrSensorCap_Orientation | ovrSensorCap_YawCorrection,
        0
    )

    # The device dimensions; should we use them for width/height?
    size0 = ovrHmd_GetFovTextureSize(hmd, ovrEye_Left, hmdDesc.MaxEyeFov[0], 1.0)
    size1 = ovrHmd_GetFovTextureSize(hmd, ovrEye_Left, hmdDesc.MaxEyeFov[1], 1.0)

    cv2.namedWindow('vid', 16 | cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(
        "vid",
        cv2.WND_PROP_FULLSCREEN,
        cv2.cv.CV_WINDOW_FULLSCREEN
    )

    cropXL = 0
    cropXR = 200
    cropYL = 0
    cropYR = 0

    while True:
        x,fraL = cL.read()
        x,fraR = cR.read()
        width, height = 720, 480 #, t = fraL.shape
        matrixL = createDistortionMatrix(fxL, cxL, fyL, cyL)
        matrixR = createDistortionMatrix(fxR, cxR, fyR, cyR)
        #translates, crops and distorts image
        fraLT = translate(fraL, xL+xO, yL+yO)
        fraRT = translate(fraR, xR+xO, yR+yO)
        fraLd = transform(fraLT, matrixL)
        fraRd = transform(fraRT, matrixR)
        fraLT2 = translate(fraLd, xO2, yO2)
        fraRT2 = translate(fraRd, xO2, yO2)
        fraLs = crop(fraLT2, cropXL, cropXR, cropYL, cropYR, width, height)
        fraRs = crop(fraRT2, cropXL, cropXR, cropYL, cropYR, width, height)
        fraCom = joinImages(fraLs, fraRs)
        cv2.imshow('vid',fraCom)

        key =  cv2.waitKey(1) & 255

        if key == ord('q'):
            cv2.destroyAllWindows()
            cR.release()
            cL.release()
            break

        elif key == ord('e'):
            fyL += 10
            fyR += 10
        elif key == ord('d'):
            fyL += -10
            fyR += -10
        elif key == ord('s'):
            fxL += -10
            fxR += -10
        elif key == ord('f'):
            fxL += 10
            fxR += 10
        elif key == ord('i'):
            cyL += -10
            cyR += -10
        elif key == ord('k'):
            cyL += 10
            cyR += 10
        elif key == ord('j'):
            cxL += -10
            cxR += -10
        elif key == ord('l'):
            cxL += 10
            cxR += 10

        elif key == ord('o'):
            yO2 += 10
        elif key == ord('u'):
            yO2 += -10

        elif key == ord('m'):
            xO2 += 10
        elif key == ord('n'):
            xO2 += -10

        elif key == ord(','):
            xO += -10
        elif key == ord('.'):
            xO += 10
        elif key == ord('h'):
            yO += 10
        elif key == ord(';'):
            yO += -10

        elif key == ord('p'):
            print("fxL={fxl}, fxR={fxr}, cxL={cxl}, cxR={cxr}, xO={xo}, yO={yo}, xO2={xo2}, yO2={yo2}".format(
                fxl=fxL,
                fxr=fxR,
                cxl=cxL,
                cxr=cxR,
                xo=xO,
                yo=yO,
                xo2=xO2,
                yo2=yO2,
                )
            )
        # fxL=330, fxR=330, cxL=320, cxR=320, xO=0, yO=10, xO2=-80, yO2=60
        # fxL=350, fxR=350, cxL=210, cxR=210, xO=-20, yO=40, xO2=-50, yO2=-10
        # fxL=330, fxR=330, cxL=320, cxR=320, xO=0, yO=10, xO2=-80, yO2=60
