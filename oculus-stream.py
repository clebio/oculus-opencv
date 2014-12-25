"""
Oculus Video: streams two camera feeds into the Oculus Rift after
  having distorted them to account for pincushion effect

Will display on whichever monitor is current when run.

Requires OpenCV 2.4.9, numpy 1.8.1 and ovrsdk

Based directly off of: http://www.argondesign.com/news/2014/aug/26/augmented-reality-oculus-rift/
"""

import sys
import cv2
import numpy as np
import ovrsdk as ovr

def crop(image, _xl, _xr, _yl, _yr, width, height):
    return image[_xl:width-_xr, _yl:height-_yr]

def create_distortion_matrix(_fx, _cx, _fy, _cy):
    matrix = np.array([
        [_fx, 0, _cx],
        [0, _fy, _cy],
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
    image_distortion = cv2.undistort(
        image,
        matrix,
        np.array([0.22, 0.24, 0, 0, 0])
    )
    return image_distortion

def join_images(image_left, image_right):
    return np.append(image_left, image_right, axis=1)

def translate(image, x, y):
    """Oculus DK2 is two images together equal to 2364 x 1461

    Also see the bottom of this page:
    http://www.3dtv.at/knowhow/EncodingDivx_en.aspx
    """
    rows, cols = 576, 720 #288, 384
    matrix = np.float32([[1, 0, x], [0, 1, y]])
    image_translate = cv2.warpAffine(image, matrix, (cols, rows))
    return image_translate

if __name__ == '__main__':
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
    xo = 0
    yo = 0

    #offsets to translate image after distortion
    xo2 = -70
    yo2 = 40

    cropXL = 0
    cropXR = 200
    cropYL = 0
    cropYR = 0

    key_mappings = dict(
        fxL=('f', 's'),
        fxR=('f', 's'),
        fyL=('e', 'd'),
        fyR=('e', 'd'),
        cxL=('l', 'j'),
        cxR=('l', 'j'),
        cyL=('k', 'i'),
        cyR=('k', 'i'),
        yo2=('o', 'u'),
        xo2=('m', 'n'),
        xo=('.', ','),
        yo=('h', ';'),
        cropXL=('z', 'x'),
        cropYL=('w', 'r'),
        cropXR=('c', 'v'),
        cropYR=('a', 'g'),
    )

    cR = cv2.VideoCapture(0)
    cL = cv2.VideoCapture(1)

    if not (cR.isOpened() and cL.isOpened()):
        print('Failed to find two cameras. Are they connected?')
        sys.exit()

    """initializes ovrsdk and starts tracking oculus"""
    ovr.ovr_Initialize()
    hmd = ovr.ovrHmd_Create(0)
    try:
        hmd.contents
    except ValueError as _ex:
        print('Failed to initialize Oculus, is it connected?')
        sys.exit()

    hmdDesc = ovr.ovrHmdDesc()
    ovr.ovrHmd_GetDesc(hmd, ovr.byref(hmdDesc))
    ovr.ovrHmd_StartSensor(
        hmd,
        ovr.ovrSensorCap_Orientation | ovr.ovrSensorCap_YawCorrection,
        0
    )

    # The device dimensions; should we use them for width/height?
    size0 = ovr.ovrHmd_GetFovTextureSize(
        hmd,
        ovr.ovrEye_Left,
        hmdDesc.MaxEyeFov[0],
        1.0
    )
    size1 = ovr.ovrHmd_GetFovTextureSize(
        hmd,
        ovr.ovrEye_Left,
        hmdDesc.MaxEyeFov[1],
        1.0
    )

    cv2.namedWindow('vid', 16 | cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(
        "vid",
        cv2.WND_PROP_FULLSCREEN,
        cv2.cv.CV_WINDOW_FULLSCREEN
    )

    while True:
        x, fraL = cL.read()
        x, fraR = cR.read()
        width, height = 720, 480 #, t = fraL.shape
        matrixL = create_distortion_matrix(fxL, cxL, fyL, cyL)
        matrixR = create_distortion_matrix(fxR, cxR, fyR, cyR)
        #translates, crops and distorts image
        fraLT = translate(fraL, xL+xo, yL+yo)
        fraRT = translate(fraR, xR+xo, yR+yo)
        fraLd = transform(fraLT, matrixL)
        fraRd = transform(fraRT, matrixR)
        fraLT2 = translate(fraLd, xo2, yo2)
        fraRT2 = translate(fraRd, xo2, yo2)
        fraLs = crop(
            fraLT2, cropXL, cropXR, cropYL, cropYR, width, height
        )
        fraRs = crop(
            fraRT2, cropXL, cropXR, cropYL, cropYR, width, height
        )

        fraCom = join_images(fraLs, fraRs)
        cv2.imshow('vid', fraCom)

        key = cv2.waitKey(1) & 255
        if key == ord('q'):
            cv2.destroyAllWindows()
            cR.release()
            cL.release()
            print(("fxL={fxl}, fxR={fxr}, cxL={cxl}, cxR={cxr}, "
                   "xo={xo}, yo={yo}, xo2={xo2}, yo2={yo2}").format(
                       fxl=fxL,
                       fxr=fxR,
                       cxl=cxL,
                       cxr=cxR,
                       xo=xo,
                       yo=yo,
                       xo2=xo2,
                       yo2=yo2,
                   ))
            break

        for metric, tup in key_mappings.iteritems():
            _add = tup[0]
            _sub = tup[1]
            if key == ord(_add):
                locals()[metric] += 10
            if key == ord(_sub):
                locals()[metric] -= 10

        # Don't let these go negative
        for metric in ['cropXL', 'cropYL', 'cropXR', 'cropYR']:
            if locals()[metric] < 0:
                print("Attempting to set {} below zero".format(
                    metric
                ))
                locals()[metric] = 0


# fxL=330, fxR=330, cxL=320, cxR=320, xo=0, yo=10, xo2=-80, yo2=60
# fxL=350, fxR=350, cxL=210, cxR=210, xo=-20, yo=40, xo2=-50, yo2=-10
# fxL=330, fxR=330, cxL=320, cxR=320, xo=0, yo=10, xo2=-80, yo2=60
