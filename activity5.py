import cv2
import numpy as np
import serial
import time
import cvzone


ser = serial.Serial('COM12', 115200, timeout=1) 
time.sleep(2)

cap = cv2.VideoCapture(1) 

lower_red1 = np.array([0, 120, 70])   
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 120, 70])  
upper_red2 = np.array([180, 255, 255])


tolerance = 90

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 | mask2

    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width, _ = frame.shape
    centerX = width // 2
    centerY = height // 2


    cv2.line(frame, (centerX, 0), (centerX, height), (0, 0, 255), 2)  
    if contours:
        c = max(contours, key=cv2.contourArea)
        (x, y, w, h) = cv2.boundingRect(c)
        cx = int(x + w / 2)

        
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.circle(frame, (cx, y + h // 2), 5, (255, 0, 0), -1)

        
        diffX = cx - centerX
        command = ""

        if abs(diffX) > tolerance:
            if diffX > 0:
                command = "R"  
            else:
                command = "L" 

        if command:
            ser.write(command.encode())
            print("Command Sent:", command)

   
    imgStacked = cvzone.stackImages([frame, mask], 2, 1)

    cv2.imshow("Stacked", imgStacked)

    if cv2.waitKey(1) & 0xFF == 27: 
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
