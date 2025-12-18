import cv2
import numpy as np
import serial
import time
import tkinter as tk
from PIL import Image, ImageTk
from collections import deque


esp = serial.Serial('COM13', 115200, timeout=1)
time.sleep(2)


color_ranges = {
    "brown": (np.array([10, 100, 20]), np.array([25, 255, 150]))
}


cap = cv2.VideoCapture(1)


root = tk.Tk()
root.title("Brown Object Tracker")
root.geometry("700x500")

panel = tk.Label(root)
panel.pack()


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


    for (lower, upper) in color_ranges.values():
        mask_total |= cv2.inRange(hsv, lower, upper)

    contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if area > 2000: 
            (x, y, cw, ch) = cv2.boundingRect(c)
            obj_x = x + cw // 2

         
            positions.append(obj_x)
            smooth_x = int(np.mean(positions))

          
            cv2.rectangle(frame, (x, y), (x+cw, y+ch), (0, 255, 0), 2)
            cv2.circle(frame, (smooth_x, y + ch // 2), 5, (255, 0, 0), -1)

            
            deadzone = 40
            if smooth_x < center_x - deadzone:
                esp.write(b"L")   
            elif smooth_x > center_x + deadzone:
                esp.write(b"R")  
            else:
                esp.write(b"C")  

   
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    imgtk = ImageTk.PhotoImage(image=img)
    panel.imgtk = imgtk
    panel.config(image=imgtk)

    root.after(30, update_frame)  

def on_closing():
    cap.release()
    esp.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
update_frame()
root.mainloop()
