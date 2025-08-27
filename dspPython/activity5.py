#Libraries
import cv2
import numpy as np
import serial
import time

#Configurations
COM_PORT = 'COM9'
BAUD_RATE = 115200
CAMERA_INDEX = 2
INITIAL_ANGLE = 90
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180

#Servo Parameters
PIXEL_DEADBAND = 20
PROPORTIONAL_GAIN = 0.15
SERIAL_SEND_INTERVAL = 0.05
MAX_ANGLE_STEP = 5
MAX_FRAMES_MISSING = 5

#HSV Range
BLUE_LOWER = np.array([100, 150, 50])
BLUE_UPPER = np.array([130, 255, 255])

#Serial Initialization
serial_conn = None
try:
    serial_conn = serial.Serial(COM_PORT, BAUD_RATE, timeout=0)
    time.sleep(0.5)
    serial_conn.write(f"A:{INITIAL_ANGLE}\n".encode())
    print(f"Successfully connected to ESP32 on {COM_PORT}")
except Exception as e:
    print(f"Failed to connect to {COM_PORT}: {e}")

#Camera Initialization
camera = cv2.VideoCapture(CAMERA_INDEX)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not camera.isOpened():
    raise RuntimeError(f"Could not open camera at index {CAMERA_INDEX}")

#Tracking Variables
current_servo_angle = INITIAL_ANGLE
last_sent_angle = INITIAL_ANGLE
last_send_time = 0
previous_target_cx = None
frames_missing = 0

print("Press 's' to stop.")
while True:
    success, frame = camera.read()
    if not success:
        print("Frame not captured.")
        break

    frame = cv2.flip(frame, 1)
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_frame, BLUE_LOWER, BLUE_UPPER)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    target_cx = None

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > 1000:
            x, y, w, h = cv2.boundingRect(largest_contour)
            target_cx = x + w // 2
            previous_target_cx = target_cx
            frames_missing = 0

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (target_cx, y + h // 2), 5, (0, 0, 255), -1)
    else:
        frames_missing += 1
        if frames_missing <= MAX_FRAMES_MISSING and previous_target_cx is not None:
            target_cx = previous_target_cx
        else:
            target_cx = None

    #Draw center guide line
    frame_height, frame_width = frame.shape[:2]
    center_x = frame_width // 2
    cv2.line(frame, (center_x, 0), (center_x, frame_height), (255, 255, 255), 1)

    #Servo Control
    if target_cx is not None:
        error = target_cx - center_x

        if abs(error) > PIXEL_DEADBAND:
            delta_angle = int(PROPORTIONAL_GAIN * error)
            delta_angle = max(-MAX_ANGLE_STEP, min(MAX_ANGLE_STEP, delta_angle))

            new_servo_angle = current_servo_angle + delta_angle
            new_servo_angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, new_servo_angle))

            current_time = time.time()
            if serial_conn and (new_servo_angle != last_sent_angle) and (current_time - last_send_time > SERIAL_SEND_INTERVAL):
                serial_conn.write(f"A:{new_servo_angle}\n".encode())
                last_send_time = current_time
                last_sent_angle = new_servo_angle
                current_servo_angle = new_servo_angle

        cv2.putText(frame, "Blue object detected",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2)
    else:
        cv2.putText(frame, "No target detected",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2)

    #Display Frames
    cv2.imshow("Mask", mask)
    cv2.imshow("Tracker", frame)

    #Stop program if 'S' is pressed
    if cv2.waitKey(1) & 0xFF == ord('s'):
        break

#Cleanup
camera.release()
cv2.destroyAllWindows()
if serial_conn:
    serial_conn.close()
