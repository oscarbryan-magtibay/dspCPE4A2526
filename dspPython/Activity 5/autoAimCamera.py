import cv2
import numpy as np
import serial
import time
import cvzone
# ---- SERIAL SETUP ----
ser = serial.Serial('/dev/tty.usbserial-0001', 115200, timeout=1)  # palitan kung anong port
time.sleep(2)

# ---- CAMERA ----
cap = cv2.VideoCapture(0)  # 0 = default camera

lower_color = np.array([18, 50, 180])   # lower bound for light yellow
upper_color = np.array([35, 255, 255])  # upper bound for light yellow

# Center tolerance
tolerance = 90

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Mask para sa kulay
    mask = cv2.inRange(hsv, lower_color, upper_color)

    # Hanapin contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    height, width, _ = frame.shape
    centerX = width // 2
    centerY = height // 2

    # --- Draw guide line (vertical sa gitna) ---
    cv2.line(frame, (centerX, 0), (centerX, height), (0, 0, 255), 2)  # pula na line sa gitna

    if contours:
        c = max(contours, key=cv2.contourArea)
        (x, y, w, h) = cv2.boundingRect(c)
        cx = int(x + w/2)

        # Draw tracking rectangle + center dot
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.circle(frame, (cx, y + h//2), 5, (255, 0, 0), -1)

        # Difference sa X-axis
        diffX = cx - centerX
        command = ""

        if abs(diffX) > tolerance:
            if diffX > 0:
                command = "R"  # Move right
            else:
                command = "L"  # Move left

        if command:
            ser.write(command.encode())
            print("Command Sent:", command)

  
    imgStacked = cvzone.stackImages([frame, mask,],2,1)

    cv2.imshow("Stacked", imgStacked)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
        break

cap.release()
cv2.destroyAllWindows()
ser.close()
