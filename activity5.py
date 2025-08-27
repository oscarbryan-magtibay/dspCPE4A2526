import cv2
import serial
import time
import numpy as np

# Connect to Arduino
arduino = serial.Serial('COM4', 9600, timeout=1)
time.sleep(2)

# Wait for Arduino to be ready
print(arduino.readline().decode().strip())

cap = cv2.VideoCapture(0)
cap.set(3, 320)  # width
cap.set(4, 240)  # height

servoX, servoY = 90, 90

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Example: Red color (adjust with trackbars later)
    lower1 = np.array([0, 120, 70])
    upper1 = np.array([10, 255, 255])
    lower2 = np.array([170, 120, 70])
    upper2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = mask1 | mask2

    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > 500:  # ignore small blobs
            (x, y, w, h) = cv2.boundingRect(c)
            objX = x + w // 2
            objY = y + h // 2

            height, width, _ = frame.shape
            centerX, centerY = width // 2, height // 2

            # Error between object and center
            errorX = centerX - objX
            errorY = centerY - objY

            # Map error to servo movement (small gain factor)
            servoX += int(errorX * 0.05)
            servoY -= int(errorY * 0.05)  # Y is inverted

            servoX = max(0, min(180, servoX))
            servoY = max(0, min(180, servoY))

            # Send to Arduino
            arduino.write(f"X{servoX}\n".encode())
            arduino.write(f"Y{servoY}\n".encode())

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (objX, objY), 5, (255, 0, 0), -1)

    cv2.imshow("Tracking", frame)
    cv2.imshow("Mask", mask)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
