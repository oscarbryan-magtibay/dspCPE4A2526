import cv2
import numpy as np
import serial
import serial.tools.list_ports
import time


PORT_HINT = 'COM3' 
BAUD = 115200


CAM_INDEX = 0 

SERVO_MIN = 0
SERVO_MAX = 180
START_ANGLE = 90

DEADBAND_PX = 20
KP = 0.12
MAX_STEP_PER_UPDATE = 6
MIN_SEND_DELTA = 1
SEND_PERIOD_S = 0.04

KERNEL = np.ones((5,5), np.uint8)
MIN_CONTOUR_AREA = 1200
EMA_ALPHA = 0.4

def pick_port(port_hint=None):
    ports = list(serial.tools.list_ports.comports())
    if port_hint:
        for p in ports:
            if port_hint in p.device:
                return p.device
    if ports:
        return ports[0].device
    return None

ser = None
port = pick_port(PORT_HINT)
if port:
    try:
        ser = serial.Serial(port, BAUD, timeout=0)
        time.sleep(0.5)
        ser.write(f"A:{START_ANGLE}\n".encode())
    except Exception as e:
        print(f"[WARN] Could not open serial port {port}: {e}")
else:
    print("No serial port found. Set PORT_HINT manually.")

last_send_time = 0
last_sent_angle = START_ANGLE
servo_angle = START_ANGLE
ema_x = None

# ---------------------- HSV for Cyan ----------------------
lower_cyan = np.array([80, 100, 100])
upper_cyan = np.array([100, 255, 255])


cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    raise RuntimeError("Could not open camera. Change CAM_INDEX at the top.")

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1) 
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, lower_cyan, upper_cyan)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, KERNEL, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, KERNEL, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    target_cx = None
    if contours:
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) >= MIN_CONTOUR_AREA:
            M = cv2.moments(largest)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                target_cx = cx
                cv2.drawContours(frame, [largest], -1, (0,255,0), 2)
                cv2.circle(frame, (cx, cy), 6, (0,0,255), -1)

    h, w = frame.shape[:2]
    center_x = w // 2
    cv2.line(frame, (center_x, 0), (center_x, h), (255, 255, 255), 1)
    cv2.rectangle(frame, (center_x - DEADBAND_PX, 0), (center_x + DEADBAND_PX, h), (200,200,200), 1)

    if target_cx is not None:
        if ema_x is None:
            ema_x = target_cx
        else:
            ema_x = int(EMA_ALPHA * target_cx + (1 - EMA_ALPHA) * ema_x)

        error_px = ema_x - center_x
        norm = error_px / (w / 2)
        delta = KP * norm * 90
        delta = max(-MAX_STEP_PER_UPDATE, min(MAX_STEP_PER_UPDATE, delta))

        target_angle = int(round(servo_angle + delta))
        target_angle = max(SERVO_MIN, min(SERVO_MAX, target_angle))

        now = time.time()
        if ser and (abs(target_angle - last_sent_angle) >= MIN_SEND_DELTA) and (now - last_send_time >= SEND_PERIOD_S):
            try:
                ser.write(f"A:{target_angle}\n".encode())
                last_send_time = now
                last_sent_angle = target_angle
                servo_angle = target_angle
            except Exception as e:
                print(f"[WARN] Serial write failed: {e}")

        cv2.putText(frame, f"Err:{error_px:+d}px Angle:{servo_angle}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
    else:
        cv2.putText(frame, "No target", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

    cv2.imshow("Mask", mask)
    cv2.imshow("Tracker", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if ser:
    ser.close()