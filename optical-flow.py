from numpy import *
import cv2


def draw_flow(im, flow, step=16):
    h, w = im.shape[:2]
    y, x = mgrid[step/2:h:step, step/2:w:step].reshape(2, -1)
    fx, fy = flow[y, x].T

    lines = vstack([x, y, x+fx, y+fy]).T.reshape(-1, 2, 2)
    lines = int32(lines)

    vis = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    for (x1, y1), (x2, y2) in lines:
        cv2.line(vis, (x1, y1), (x2, y2), (0, 255, 0), 1)
        cv2.circle(vis, (x1, y1), 1, (0, 255, 0), -1)
    return vis

cap = cv2.VideoCapture(2)
ret, frame = cap.read()
prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

while(True):
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, gray, 0.5, 1, 3, 15, 3, 5, 1
    )
    prev_gray = gray
    cv2.imshow('optical flow', draw_flow(gray, flow))

    key = cv2.waitKey(1)
    if key == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
