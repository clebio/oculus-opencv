"""
Oculus Video: streams two camera feeds into the Oculus Rift after
  having distorted them to account for pincushion effect

Will display on whichever monitor is current when run.

Requires OpenCV 2.4.9, numpy 1.8.1 and ovrsdk
"""


import sys
import cv2
import ovrsdk as ovr

import gevent
from gevent import (
    monkey,
    queue,
    Greenlet,
)

import signal

from algos import print_params, Parameters
from camera import (
    CameraReader,
    CameraProcessor,
    InputHandler,
    OculusDriver,
)
from arg_parser import parser

monkey.patch_all()
args = parser.parse_args()

def oculus():
    """initializes ovrsdk and starts tracking oculus"""
    ovr.ovr_Initialize()
    hmd = ovr.ovrHmd_Create(0)

    try:
        hmd.contents
    except ValueError as _:
        print('Failed to initialize Oculus, is it connected?')
        if args.oculus:
            sys.exit()

    hmdDesc = ovr.ovrHmdDesc()
    ovr.ovrHmd_GetDesc(hmd, ovr.byref(hmdDesc))
    ovr.ovrHmd_StartSensor(
        hmd,
        ovr.ovrSensorCap_Orientation | ovr.ovrSensorCap_YawCorrection,
        0
    )

    # The device dimensions; should we use them for width/height?
    _ = ovr.ovrHmd_GetFovTextureSize(
        hmd,
        ovr.ovrEye_Left,
        hmdDesc.MaxEyeFov[0],
        1.0
    )
    _ = ovr.ovrHmd_GetFovTextureSize(
        hmd,
        ovr.ovrEye_Right,
        hmdDesc.MaxEyeFov[1],
        1.0
    )

    return hmd

def run():
    """Set up both Oculus tracking and Camera feeds, then iterate

    We use Gevent queues and greenlets to let the camera readers
    (left and right feeds) and the camera processor run
    asynchronously. The intent is that the I/O activities are not
    blocking and we can achieve higher throughput, though in the end,
    we may be limited by USB camera frame rates anyway.
    """
    if args.oculus:
        hmd = oculus()

    cv2.namedWindow('vid', 16 | cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(
        "vid",
        cv2.WND_PROP_FULLSCREEN,
        cv2.cv.CV_WINDOW_FULLSCREEN
    )

    left_queue = queue.Queue()
    right_queue = queue.Queue()

    camera_left = cv2.VideoCapture(args.left)
    camera_right = cv2.VideoCapture(args.right)

    if not (camera_left.isOpened() and camera_right.isOpened()):
        print('Failed to find two cameras. Are they connected?')
        sys.exit()

    left = CameraReader(camera_left, left_queue)
    right = CameraReader(camera_right, right_queue)
    processor = CameraProcessor(
        left_queue,
        right_queue,
        args.write,
    )

    if args.oculus:
        driver = OculusDriver(hmd)
    else:
        driver = None

    def close_callback():
        left.kill()
        right.kill()

        if args.oculus:
            driver.kill()

        camera_left.release()
        camera_right.release()

        if args.write:
            processor.video_out.release()
        cv2.destroyAllWindows()

        print_params()

    input_handler = InputHandler(close_callback)

    left.start()
    right.start()
    if args.oculus:
        driver.start()
    processor.start()
    input_handler.start()

    gevent.signal(signal.SIGQUIT, gevent.kill)
    if args.oculus:
        gevent.joinall([left, right, processor, input_handler, driver])
    else:
        gevent.joinall([left, right, processor, input_handler])

if __name__ == '__main__':
    run()
