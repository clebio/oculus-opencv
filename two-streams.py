import numpy as np
import cv2

cap0 = cv2.VideoCapture(0)
cap1 = cv2.VideoCapture(1)

while(True):

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

    ret, frame0 = cap0.read()
    ret, frame1 = cap1.read()

    vid0 = cv2.cvtColor(frame0, cv2.COLOR_RGBA2RGB)
    vid1 = cv2.cvtColor(frame1, cv2.COLOR_RGBA2RGB)

    cv2.imshow('frame0', vid0)
    cv2.imshow('frame1', vid1)

cap0.release()
cap1.release()
cv2.destroyAllWindows()
