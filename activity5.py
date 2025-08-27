import cv2
import numpy as np
import serial
import time
import collections

ser = serial.Serial("COM3", 115200, timeout=1)
time.sleep(2)

servo_angle = 90
ser.write(f"{servo_angle}\n".encode())

cap = cv2.VideoCapture(0)
frame_width = int(cap.get(3))

DEADBAND = 40                          # tolerance para hindi wiggle
history = collections.deque(maxlen=5)  # moving average over last 5 detections
STEP = 1                               # servo step per correction (smooth slow and steady)
DELAY = 0.02                           # delay per step (para hindi patigil-tigil)

# HSV Slider
def nothing(x):
    pass

cv2.namedWindow("HSV Slider Tool")
cv2.createTrackbar("LH", "HSV Slider Tool", 0, 179, nothing)
cv2.createTrackbar("LS", "HSV Slider Tool", 0, 255, nothing)
cv2.createTrackbar("LV", "HSV Slider Tool", 0, 255, nothing)
cv2.createTrackbar("UH", "HSV Slider Tool", 179, 179, nothing)
cv2.createTrackbar("US", "HSV Slider Tool", 255, 255, nothing)
cv2.createTrackbar("UV", "HSV Slider Tool", 255, 255, nothing)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # HSV values sa sliders
    lh = cv2.getTrackbarPos("LH", "HSV Slider Tool")
    ls = cv2.getTrackbarPos("LS", "HSV Slider Tool")
    lv = cv2.getTrackbarPos("LV", "HSV Slider Tool")
    uh = cv2.getTrackbarPos("UH", "HSV Slider Tool")
    us = cv2.getTrackbarPos("US", "HSV Slider Tool")
    uv = cv2.getTrackbarPos("UV", "HSV Slider Tool")

    lower = np.array([lh, ls, lv])
    upper = np.array([uh, us, uv])

    # Mask and result
    mask = cv2.inRange(hsv, lower, upper)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Contours
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)
        (x, y, w, h) = cv2.boundingRect(c)
        obj_center = x + w // 2

        # history smoothing (para smooth yung camera)
        history.append(obj_center)
        smooth_center = int(sum(history) / len(history))

        # box sa object
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.line(result, (smooth_center, 0), (smooth_center, frame.shape[0]), (255, 0, 0), 2)

        # servo
        center_frame = frame_width // 2
        error = smooth_center - center_frame

        if abs(error) > DEADBAND:       # para hindi mabaliw ang camera sa konting error
            if error > 0 and servo_angle > 0:
                servo_angle -= STEP
            elif error < 0 and servo_angle < 180:
                servo_angle += STEP

            ser.write(f"{servo_angle}\n".encode())
            time.sleep(DELAY)

    # Convert mask to BGR
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    # Resize all images
    scale = 0.5   # 0.5 = 50% size
    frame_resized = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    mask_resized = cv2.resize(mask_bgr, (frame_resized.shape[1], frame_resized.shape[0]))
    result_resized = cv2.resize(result, (frame_resized.shape[1], frame_resized.shape[0]))

    # Combine horizontally the screens
    combined = cv2.hconcat([frame_resized, mask_resized, result_resized])

    cv2.imshow("Frame | Mask | Result", combined)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
