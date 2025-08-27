import cv2
import numpy as np
import serial
import time
import tkinter as tk
from PIL import Image, ImageTk
from collections import deque

# Connect to ESP32 (⚠️ Change COM5 to your port)
esp = serial.Serial('COM13', 115200, timeout=1)
time.sleep(2)

# HSV ranges for different colors
color_ranges = {
    "red1":   (np.array([0, 120, 70]), np.array([10, 255, 255])),
    "red2":   (np.array([170, 120, 70]), np.array([180, 255, 255])),
    "green":  (np.array([35, 100, 100]), np.array([85, 255, 255])),
    "blue":   (np.array([100, 150, 0]), np.array([140, 255, 255])),
    "yellow": (np.array([20, 100, 100]), np.array([30, 255, 255])),
    "orange": (np.array([10, 100, 100]), np.array([20, 255, 255])),
    "purple": (np.array([140, 100, 100]), np.array([160, 255, 255]))
}

# Open webcam
cap = cv2.VideoCapture(0)

# Tkinter GUI
root = tk.Tk()
root.title("Multi-Color Object Tracker")
root.geometry("700x500")

panel = tk.Label(root)
panel.pack()

# Buffer for smoothing (moving average of last N positions)
buffer_size = 5
positions = deque(maxlen=buffer_size)

def update_frame():
    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return

    frame = cv2.flip(frame, 1)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    h, w, _ = frame.shape
    center_x = w // 2
    cv2.line(frame, (center_x, 0), (center_x, h), (0, 0, 255), 2)

    mask_total = np.zeros(hsv.shape[:2], dtype="uint8")

    # Combine all color masks
    for (lower, upper) in color_ranges.values():
        mask_total |= cv2.inRange(hsv, lower, upper)

    contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if area > 800:  # Ignore small noise
            (x, y, cw, ch) = cv2.boundingRect(c)
            obj_x = x + cw // 2

            # Add to buffer for smoothing
            positions.append(obj_x)
            smooth_x = int(np.mean(positions))

            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x+cw, y+ch), (0, 255, 0), 2)
            cv2.circle(frame, (smooth_x, y + ch // 2), 5, (255, 0, 0), -1)

            # Follow with deadzone
            deadzone = 40
            if smooth_x < center_x - deadzone:
                esp.write(b"L")   # move left
            elif smooth_x > center_x + deadzone:
                esp.write(b"R")   # move right
            else:
                esp.write(b"C")   # stay

    # Show in Tkinter
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    imgtk = ImageTk.PhotoImage(image=img)
    panel.imgtk = imgtk
    panel.config(image=imgtk)

    root.after(30, update_frame)  # slower updates for stability

def on_closing():
    cap.release()
    esp.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
update_frame()
root.mainloop()