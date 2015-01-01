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

class CameraReader(Greenlet):
    """Read frames from a camera and apply distortions"""
    def __init__(self, camera, queue):
        """Save the camera (to read from) and queue (to write to)"""
        Greenlet.__init__(self)
        self.camera = camera
        self.queue = queue

    def _run(self):
        """Iterate and process frames indefinitely

        Assumes the application will be shutdown through other means
        (namely, the CameraProcessor greenlet, which handles user
        input).

        Reads a frame in from the camera, applies translations and
        distortions based on the Parameters class, then writes the
        final image to the output queue.
        """
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
        return 'CameraReader for {}'.format(self.camera)

class CameraProcessor(Greenlet):
    """Parse video frames from two queues and stitch them together.

    Uses algos.join_images to stitch the left and right video frames
    into one wider image and displays that image via `cv2.imshow`.

    If args.write is set, creates an OpenCV VideoWriter and saves
    the composited frames on each iteration.

    Also handles keyboard input, allowing for `q`uiting the program
    and changing parameters during run-time.
    """
    def __init__(self, left_queue, right_queue, callback):
        """Stores queues and callback (for shutdown)

        Args:
            left_queue (gevent.queue): queue for left image frames
            right_queue (gevent.queue): queue for right image frames
            callback (function): the method to run on application
               shutdown (holds references to objects that this class
               doesn't necessarily know about (e.g. the cv2 cameras)
        """
        Greenlet.__init__(self)
        print('Processor init')
        self.left = left_queue
        self.right = right_queue
        self.callback = callback

        self.video_out = False
        if args.write:
            fourcc = cv2.cv.CV_FOURCC(*'XVID')
            self.video_out = cv2.VideoWriter(
                'output.avi', # TODO: Use a program argument
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
        """Consumes frames from the queues and display

        If the two queues contain frames, read them in and create
        the composited image, then display to the user. Also handles
        user input.
        """
        if not (self.left.empty() and self.right.empty()):
            composite_frame = join_images(
                self.left.get(),
                self.right.get(),
            )
            cv2.imshow('vid', composite_frame)

            if self.video_out:
                self.video_out.write(composite_frame)

        self.handle_input()

    def handle_input(self):
        """Read user input and react

        Allow for `q`uiting the application and changing run-time
        parameters. We use the `Parameters.key_mappings` and iterate
        over them to increment or decrement the associated parameter
        (see also the documentation in the Parameters class).
        """
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

    def __str__(self):
        return 'CameraProcessor'

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

def run():
    """Set up both Oculus tracking and Camera feeds, then iterate

    We use Gevent queues and greenlets to let the camera readers
    (left and right feeds) and the camera processor run
    asynchronously. The intent is that the I/O activities are not
    blocking and we can achieve higher throughput, though in the end,
    we may be limited by USB camera frame rates anyway.
    """
    oculus()

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

    left = CameraReader(camera_left, left_queue)
    right = CameraReader(camera_right, right_queue)
    processor = CameraProcessor(
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
