import cv2
import numpy as np
import serial
import time

ser = serial.Serial('COM3', 115200, timeout=1)
time.sleep(2)

camera_index = 1   
cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

if not cap.isOpened():
    raise RuntimeError(f"Camera at index {camera_index} could not be opened")

# HSV RANGE
lower_color = np.array([35, 100, 100])  
upper_color = np.array([85, 255, 255]) 

frame_center = None
tolerance = 50   
last_command = None
stable_count = 0
stable_threshold = 5  

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    height, width, _ = frame.shape
    frame_center = width // 2

    # Convert to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, lower_color, upper_color)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    command = None
    if contours:
   
        c = max(contours, key=cv2.contourArea)
        (x, y, w, h) = cv2.boundingRect(c)

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

        obj_center_x = x + w // 2

        cv2.line(frame, (obj_center_x, 0), (obj_center_x, height), (255,0,0), 2)
        cv2.line(frame, (frame_center, 0), (frame_center, height), (0,0,255), 2)

        if obj_center_x < frame_center - tolerance:
            command = b'R'  
        elif obj_center_x > frame_center + tolerance:
            command = b'L'  
        else:
            command = b'C'  


    if command is not None:
        if command == last_command:
            stable_count += 1
        else:
            stable_count = 0
        if stable_count >= stable_threshold:
            ser.write(command)
            print(f"Sent: {command.decode()}")
            stable_count = 0
        last_command = command

    cv2.imshow("Color Tracker", frame)

    key = cv2.waitKey(1)
    if key == 27:  
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
