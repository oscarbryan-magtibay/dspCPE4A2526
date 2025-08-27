import cv2
import numpy as np
import serial
import time

# Settings

PORT = 'COM3'         # COM PORT IN USE
BAUD = 115200
CAM_INDEX = 2         # 2 FOR EXTERNAL CAMERA
SERVO_MIN = 0
SERVO_MAX = 180
START_ANGLE = 90      # STARTING POSITION FOR SERVO 

# Servo motor Section
DEADBAND_PX = 20      # ERROR VALUE BEFORE MOVING POSITION
KP = 0.15             # STABILIZATION IF SHAKY
MAX_STEP = 5          # MAX ANGLE STEP PER UPDATE
SEND_PERIOD_S = 0.05  # SEND UPDATE AFTER SPECIFIC DURATION

# HSV range for detecting BLUE object
lower_blue = np.array([100, 150, 50])   
upper_blue = np.array([130, 255, 255]) 

# Serial Section
ser = None
try:
    ser = serial.Serial(PORT, BAUD, timeout=0)
    time.sleep(0.5)
    ser.write(f"A:{START_ANGLE}\n".encode())
    print(f"✅ Connected to ESP32 on {PORT}")
except Exception as e:
    print(f"[WARN] Could not connect to {PORT}: {e}")

# Camera Section
cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    raise RuntimeError(f"❌ Could not open camera at index {CAM_INDEX}. "
                       "Try changing CAM_INDEX (0,1,2,...)")

# Main Code Section
servo_angle = START_ANGLE
last_sent_angle = START_ANGLE
last_send_time = 0

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[WARN] Frame not captured.")
        break

    frame = cv2.flip(frame, 1)  # MIRROR FOR EASIER TRACKING

    # Convert to HSV and apply mask
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    target_cx = None

    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) > 1000:  # ignore noise
            M = cv2.moments(largest)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                target_cx = cx

                # Draw target
                cv2.drawContours(frame, [largest], -1, (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    # Draw center guide
    h, w = frame.shape[:2]
    center_x = w // 2
    cv2.line(frame, (center_x, 0), (center_x, h), (255, 255, 255), 1)

    # Servo Control Section
    if target_cx is not None:
        error = target_cx - center_x

        if abs(error) > DEADBAND_PX:
            # P-controller
            delta = int(KP * error)
            delta = max(-MAX_STEP, min(MAX_STEP, delta))

            new_angle = servo_angle + delta
            new_angle = max(SERVO_MIN, min(SERVO_MAX, new_angle))

            now = time.time()
            if ser and (new_angle != last_sent_angle) and (now - last_send_time > SEND_PERIOD_S):
                ser.write(f"A:{new_angle}\n".encode())
                last_send_time = now
                last_sent_angle = new_angle
                servo_angle = new_angle

            cv2.putText(frame, f"Error:{error:+d}px Angle:{servo_angle}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
        else:
            cv2.putText(frame, "Centered", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    else:
        cv2.putText(frame, "No target detected", (10,30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

    # Display Section
    cv2.imshow("Mask", mask)
    cv2.imshow("Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if ser:
    ser.close()
