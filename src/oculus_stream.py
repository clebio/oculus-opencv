"""
Oculus Video: streams two camera feeds into the Oculus Rift after
  having distorted them to account for pincushion effect

Will display on whichever monitor is current when run.

Requires OpenCV 2.4.9, numpy 1.8.1 and ovrsdk

Based directly off of: http://www.argondesign.com/news/2014/aug/26/augmented-reality-oculus-rift/
"""


import sys
import cv2
import ovrsdk as ovr

import gevent
from gevent import (
    monkey,
    Greenlet,
    queue,
)
import signal

from algos import *
from arg_parser import parser

monkey.patch_all()
args = parser.parse_args()

class CameraReaderGreenlet(Greenlet):
    def __init__(self, camera, queue):
        Greenlet.__init__(self)
        self.camera = camera
        self.queue = queue

    def _run(self):
        par = Parameters
        while True:
            _, frame = self.camera.read()

            matrix = create_distortion_matrix(
                par.fxL, par.cxL, par.fyL, par.cyL
            )
            frame = translate(frame, par.xL + par.xo, par.yL + par.yo)
            frame = transform(frame, matrix)
            frame = translate(frame, par.xo2, par.yo2)

            frame = crop(
                frame,
                par.cropXL,
                par.cropXR,
                par.cropYL,
                par.cropYR,
                par.width,
                par.height,
            )
            self.queue.put(frame)
            gevent.sleep(0)

    def __str__(self):
        return 'CameraReaderGreenlet for {}'.format(self.camera)

class CameraProcessorGreenlet(Greenlet):
    def __init__(self, left_queue, right_queue, callback):
        Greenlet.__init__(self)
        print('Processor init')
        self.left = left_queue
        self.right = right_queue
        self.callback = callback

        self.video_out = False
        if args.write:
            fourcc = cv2.cv.CV_FOURCC(*'XVID')
            self.video_out = cv2.VideoWriter(
                'output.avi',
                fourcc,
                Parameters.fps,
                (800, 450), # TODO: make this dynamic
                True # color, not grayscale
            )

    def _run(self):
        while True:
            self.iterate()
            gevent.sleep(0)

    def iterate(self):
        if not (self.left.empty() and self.right.empty()):
            composite_frame = join_images(
                self.left.get(),
                self.right.get(),
            )
            cv2.imshow('vid', composite_frame)

            if self.video_out:
                self.video_out.write(composite_frame)

        key = cv2.waitKey(1) & 255
        if key == ord('q'):
            self.callback()
            if self.video_out:
                self.video_out.release()
            self.kill()

        elif key == ord('p'):
            print_params()

        for metric, tup in Parameters.key_mappings.iteritems():
            _add = tup[0]
            _sub = tup[1]
            if key == ord(_add):
                setattr(
                    Parameters,
                    metric,
                    getattr(Parameters, metric) + 10
                )
            if key == ord(_sub):
                setattr(
                    Parameters,
                    metric,
                    getattr(Parameters, metric) - 10
                )

        # Don't let these go negative
        for metric in ['cropXL', 'cropYL', 'cropXR', 'cropYR']:
            p_m = getattr(Parameters, metric)
            if p_m < 0:
                print("Attempting to set {} below zero".format(
                    metric
                ))
                setattr(Parameters, metric, 0)

def run():

    """initializes ovrsdk and starts tracking oculus"""
    ovr.ovr_Initialize()
    hmd = ovr.ovrHmd_Create(0)

    try:
        hmd.contents
    except ValueError as _:
        print('Failed to initialize Oculus, is it connected?')
        if args.oculus:
            sys.exit()

    if args.oculus:
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

    def close_callback():
        cv2.destroyAllWindows()
        camera_left.release()
        camera_right.release()

        left.kill()
        right.kill()
        print_params()

    left = CameraReaderGreenlet(camera_left, left_queue)
    right = CameraReaderGreenlet(camera_right, right_queue)
    processor = CameraProcessorGreenlet(
        left_queue,
        right_queue,
        close_callback
    )

    left.start()
    right.start()
    processor.start()

    gevent.signal(signal.SIGQUIT, gevent.kill)
    gevent.joinall([left, right, processor])

if __name__ == '__main__':
    run()
