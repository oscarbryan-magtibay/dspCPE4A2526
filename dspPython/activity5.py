import cv2
import serial
import time
import numpy as np

# === Serial setup for ESP32 ===
COM_PORT = "COM8"  # Change to your ESP32 COM port
BAUD_RATE = 9600

try:
    esp32 = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    esp32.reset_input_buffer()
    esp32.reset_output_buffer()
    print(f"ESP32 Serial ready on {COM_PORT}")
except serial.SerialException as e:
    print(f"Error opening serial port {COM_PORT}: {e}")
    esp32 = None

# === Camera setup ===
cap = cv2.VideoCapture(1)  # Change to your camera index

# === Colors to track (HSV ranges) ===
COLOR_RANGES = {
    'red': [(0, 120, 70, 10, 255, 255), (170, 120, 70, 180, 255, 255)],
    'green': [(36, 50, 70, 89, 255, 255)],
    'blue': [(94, 80, 2, 126, 255, 255)],
    'yellow': [(15, 100, 100, 35, 255, 255)]
}

# List of colors to track
TRACK_COLORS = ['red', 'green', 'blue', 'yellow']

# Servo tracking parameters
deadzone_x = 20
deadzone_y = 20
motion_threshold = 5
servo_pan = 90    # Start at center position
servo_tilt = 90   # Start at center position

# Tracking variables
prev_center_x = None
prev_center_y = None
frame_center_x = None
frame_center_y = None
prev_time = time.time()

print(f"Camera started. Tracking colors: {TRACK_COLORS}")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    h, w, _ = frame.shape
    
    # Initialize frame center once
    if frame_center_x is None:
        frame_center_x = w // 2
        frame_center_y = h // 2
    
    # Convert to HSV for color detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Create combined mask for all tracked colors
    mask = None
    for color in TRACK_COLORS:
        hsv_ranges = COLOR_RANGES[color]
        for r in hsv_ranges:
            lower = np.array([r[0], r[1], r[2]])
            upper = np.array([r[3], r[4], r[5]])
            temp_mask = cv2.inRange(hsv, lower, upper)
            mask = temp_mask if mask is None else mask | temp_mask
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Track largest object
        c = max(contours, key=cv2.contourArea)
        
        if cv2.contourArea(c) > 500:  # Minimum area threshold
            x, y, bw, bh = cv2.boundingRect(c)
            obj_center_x = x + bw // 2
            obj_center_y = y + bh // 2
            
            # Draw bounding box and crosshairs
            cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
            cv2.line(frame, (obj_center_x, 0), (obj_center_x, h), (255, 0, 0), 2)
            cv2.line(frame, (0, obj_center_y), (w, obj_center_y), (255, 0, 0), 2)
            
            # Calculate errors from frame center
            error_x = obj_center_x - frame_center_x
            error_y = obj_center_y - frame_center_y
            
            # Horizontal pan control (FIXED: inverted direction)
            if prev_center_x is None or abs(obj_center_x - prev_center_x) > motion_threshold:
                if abs(error_x) > deadzone_x:
                    # FIXED: Subtract delta to move servo opposite to object movement
                    delta = int((error_x / frame_center_x) * 5)
                    servo_pan -= delta  # Changed from += to -=
                    servo_pan = max(0, min(180, servo_pan))
                prev_center_x = obj_center_x
            
            # Vertical tilt control (FIXED: inverted direction)
            if prev_center_y is None or abs(obj_center_y - prev_center_y) > motion_threshold:
                if abs(error_y) > deadzone_y:
                    # FIXED: Subtract delta to move servo opposite to object movement
                    delta = int((error_y / frame_center_y) * 5)
                    servo_tilt -= delta  # Changed from += to -=
                    servo_tilt = max(0, min(180, servo_tilt))
                prev_center_y = obj_center_y
            
            # Send servo angles to ESP32
            if esp32:
                command = f"{servo_pan},{servo_tilt}\n"
                esp32.write(command.encode())
                print(f"Pan: {servo_pan}°, Tilt: {servo_tilt}°")
    
    else:
        # No object detected - maintain current position
        if esp32:
            command = f"{servo_pan},{servo_tilt}\n"
            esp32.write(command.encode())
    
    # Draw frame center crosshairs
    cv2.line(frame, (frame_center_x, 0), (frame_center_x, h), (0, 0, 255), 1)
    cv2.line(frame, (0, frame_center_y), (w, frame_center_y), (0, 0, 255), 1)
    
    # Calculate and display FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time
    
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Display servo positions
    cv2.putText(frame, f"Pan: {servo_pan}° Tilt: {servo_tilt}°", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # Show the frame
    cv2.imshow("Object Tracking", frame)
    
    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
if esp32:
    esp32.close()
    print("Serial connection closed")