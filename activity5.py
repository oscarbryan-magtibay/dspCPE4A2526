import cv2
import numpy as np
import serial
import time
import cvzone


ser = serial.Serial('COM4', 115200, timeout=1) 
time.sleep(2)

cap = cv2.VideoCapture(1) 

lower_color = np.array([90, 50, 200])
upper_color = np.array([130, 150, 255])
tolerance = 90

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    height, width, _ = frame.shape
    centerX = width // 2
    centerY = height // 2

    cv2.line(frame, (centerX, 0), (centerX, height), (128, 128, 128), 2)  # gray line

    if contours:
        c = max(contours, key=cv2.contourArea)
        (x, y, w, h) = cv2.boundingRect(c)
        cx = int(x + w/2)

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.circle(frame, (cx, y + h//2), 5, (255, 0, 0), -1)

        diffX = cx - centerX
        command = ""

        if abs(diffX) > tolerance:
            command = "R" if diffX > 0 else "L"

        if command:
            ser.write(command.encode())
            print("Command:", command)

    imgStacked = cvzone.stackImages([frame, mask], 2, 1)
    cv2.imshow("Stacked", imgStacked)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
