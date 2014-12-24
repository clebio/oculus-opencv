import numpy as np
import cv2

import os

devices = os.listdir('/dev/')
video_devices = [int(d[-1]) for d in devices if d.startswith('video')]

cv_cams = []
for video in video_devices:
    cam = cv2.VideoCapture(video)
    if cam.isOpened():
        cv_cams.append(cam)

while(True):

    key = cv2.waitKey(1)
    if key & 255 == ord('q'):
        break

    vid = dict()
    for idx, cam in enumerate(cv_cams):
        ret, frame = cam.read()

        if ret:
            vid[cam] = frame
            cv2.imshow(
                'frame{}'.format(idx),
                cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB),
            )

for video in video_devices:
    video.release()

cv2.destroyAllWindows()
