import cv2
import numpy as np
import serial
import time

# ==============================
# CONFIGURATION
# ==============================
SERIAL_PORT = "COM3"       # Change if needed
BAUD_RATE = 115200
INITIAL_ANGLE = 90
FRAME_SCALE = 0.5          # Resize factor for display
TOLERANCE = 35             # Deadband for error
ANGLE_STEP = 1             # Servo adjustment per update
UPDATE_DELAY = 0.02        # Delay for servo update
SMOOTHING_FACTOR = 0.3     # For exponential moving average

# ==============================
# INITIALIZE SERIAL & CAMERA
# ==============================
arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)
arduino.write(f"{INITIAL_ANGLE}\n".encode())

cap = cv2.VideoCapture(1)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
servo_angle = INITIAL_ANGLE
smoothed_center = frame_width // 2  # Start at screen center
prev_time = time.time()

# ==============================
# HSV SLIDER SETUP
# ==============================
def create_hsv_trackbars():
    cv2.namedWindow("HSV Settings")
    cv2.createTrackbar("LH", "HSV Settings", 0, 179, lambda x: None)
    cv2.createTrackbar("LS", "HSV Settings", 0, 255, lambda x: None)
    cv2.createTrackbar("LV", "HSV Settings", 0, 255, lambda x: None)
    cv2.createTrackbar("UH", "HSV Settings", 179, 179, lambda x: None)
    cv2.createTrackbar("US", "HSV Settings", 255, 255, lambda x: None)
    cv2.createTrackbar("UV", "HSV Settings", 255, 255, lambda x: None)

def get_hsv_range():
    lh = cv2.getTrackbarPos("LH", "HSV Settings")
    ls = cv2.getTrackbarPos("LS", "HSV Settings")
    lv = cv2.getTrackbarPos("LV", "HSV Settings")
    uh = cv2.getTrackbarPos("UH", "HSV Settings")
    us = cv2.getTrackbarPos("US", "HSV Settings")
    uv = cv2.getTrackbarPos("UV", "HSV Settings")
    return np.array([lh, ls, lv]), np.array([uh, us, uv])

# ==============================
# SERVO UPDATE FUNCTION
# ==============================
def adjust_servo(error, angle):
    if abs(error) > TOLERANCE:
        if error > 0 and angle > 0:
            angle -= ANGLE_STEP
        elif error < 0 and angle < 180:
            angle += ANGLE_STEP
        arduino.write(f"{angle}\n".encode())
        time.sleep(UPDATE_DELAY)
    return angle

# ==============================
# MAIN FUNCTION
# ==============================
def main():
    global smoothed_center, servo_angle, prev_time

    create_hsv_trackbars()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower, upper = get_hsv_range()

        mask = cv2.inRange(hsv_frame, lower, upper)
        result = cv2.bitwise_and(frame, frame, mask=mask)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            current_center = x + w // 2

            # Exponential moving average for smoothing
            smoothed_center = int(SMOOTHING_FACTOR * current_center + (1 - SMOOTHING_FACTOR) * smoothed_center)

            # Draw rectangle and center line
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.line(result, (smoothed_center, 0), (smoothed_center, frame.shape[0]), (255, 0, 0), 2)

            # Servo adjustment
            center_frame = frame_width // 2
            error = smoothed_center - center_frame
            servo_angle = adjust_servo(error, servo_angle)

        # FPS calculation
        current_time = time.time()
        fps = 1 / (current_time - prev_time)
        prev_time = current_time

        # Display angle & FPS
        cv2.putText(result, f"Servo Angle: {servo_angle}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(result, f"FPS: {fps:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        # Combine views
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        frame_small = cv2.resize(frame, (0, 0), fx=FRAME_SCALE, fy=FRAME_SCALE)
        mask_small = cv2.resize(mask_bgr, (frame_small.shape[1], frame_small.shape[0]))
        result_small = cv2.resize(result, (frame_small.shape[1], frame_small.shape[0]))
        combined = cv2.vconcat([frame_small, mask_small, result_small])  # Vertical stack for variety

        cv2.imshow("Tracking View", combined)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    arduino.close()

# ==============================
# EXECUTE
# ==============================
if __name__ == "__main__":
    main()
