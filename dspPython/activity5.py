import cv2
import numpy as np
import serial, time
import tkinter as tk
from PIL import Image, ImageTk
from collections import deque

# Connect to ESP32 (⚠️ Change port if needed)
esp = serial.Serial('COM5', 115200, timeout=1)
time.sleep(2)

# HSV color ranges
color_ranges = [
    (np.array([0, 120, 70]), np.array([10, 255, 255])),
    (np.array([170, 120, 70]), np.array([180, 255, 255])),
    (np.array([35, 100, 100]), np.array([85, 255, 255])),
    (np.array([100, 150, 0]), np.array([140, 255, 255])),
    (np.array([20, 100, 100]), np.array([30, 255, 255])),
    (np.array([10, 100, 100]), np.array([20, 255, 255])),
    (np.array([140, 100, 100]), np.array([160, 255, 255]))
]

# Webcam
cap = cv2.VideoCapture(1)

# GUI
root = tk.Tk()
root.title("Object Tracker")
panel = tk.Label(root)
panel.pack()

# Position buffer (smoothing)
positions = deque(maxlen=5)

def update_frame():
    ret, frame = cap.read()
    if not ret:
        root.after(20, update_frame)
        return

    frame = cv2.flip(frame, 1)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, w, _ = frame.shape
    cx = w // 2
    cv2.line(frame, (cx, 0), (cx, h), (0, 0, 255), 2)

    # Combine color masks
    mask = sum([cv2.inRange(hsv, l, u) for l, u in color_ranges])
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > 800:
            x, y, cw, ch = cv2.boundingRect(c)
            obj_x = x + cw // 2
            positions.append(obj_x)
            smooth_x = int(np.mean(positions))

            cv2.rectangle(frame, (x, y), (x+cw, y+ch), (0, 255, 0), 2)
            cv2.circle(frame, (smooth_x, y + ch//2), 5, (255, 0, 0), -1)

            deadzone = 40
            if smooth_x < cx - deadzone:
                esp.write(b"L")
            elif smooth_x > cx + deadzone:
                esp.write(b"R")
            else:
                esp.write(b"C")

    # Display
    imgtk = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    panel.config(image=imgtk)
    panel.imgtk = imgtk

    root.after(30, update_frame)

def on_close():
    cap.release()
    esp.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
update_frame()
root.mainloop()