
import numpy as np
import cv2

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
    rows, cols = 480, 720 #288, 384
    matrix = np.float32([[1, 0, x], [0, 1, y]])
    image_translate = cv2.warpAffine(image, matrix, (cols, rows))
    return image_translate

def print_params():
    p = Parameters
    strings = []
    for item in [par for par in dir(p) if par.isalnum()]:
        strings.append("{name} = {value}".format(
            name=item,
            value=getattr(p, item),
        ))
    string = ', '.join(strings)
    print(string)

class Parameters():
    #Matrix coefficients for left eye barrel effect
    fxL = 350
    fyL = 300
    cxL = 310
    cyL = 260

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
    xo = -80
    yo = 20

    #offsets to translate image after distortion
    xo2 = -110
    yo2 = 0

    cropXL = 30
    cropXR = 170
    cropYL = 0
    cropYR = 80

    # width, height, t = left_frame.shape
    width = 720
    height = 480

    # frames per second
    fps = 24

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
