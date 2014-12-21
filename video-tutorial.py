import numpy as np
import cv2

cap = cv2.VideoCapture(2)

while(True):
    ret, frame = cap.read()
    vid = cv2.cvtColor(frame, cv2.COLOR_RGBA2RGB)
    cv2.imshow('frame', vid)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
