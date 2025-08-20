from ultralytics import YOLO
import cv2
import math
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# -------------------- GUI Setup --------------------
root = tk.Tk()
root.title("💵 Money Security Detection")
window_width, window_height = 950, 700
root.geometry(f"{window_width}x{window_height}")
root.configure(bg="#1b1b2f")

# -------------------- Header --------------------
header = tk.Frame(root, bg="#162447", height=80)
header.pack(fill=tk.X)

title = tk.Label(header, text="INCLIDE BILLS DETECTION", font=("Arial", 22, "bold"),
                 fg="#f0f0f0", bg="#162447")
title.pack(pady=(5,0))

credit = tk.Label(header, text="BACROYA, JOSEPH W. - CPE4A - DSP", font=("Arial", 14),
                  fg="#f0f0f0", bg="#162447")
credit.pack(pady=(0,10))

# -------------------- Canvas --------------------
canvas_frame = tk.Frame(root, bg="#1b1b2f")
canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
canvas = tk.Canvas(canvas_frame, bg="#0f0f1f", highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

# -------------------- YOLO Model --------------------
model = YOLO("act4/weights/money.pt")
classNames = ['concealed_value', 'optically_variable_ink', 'security_thread',
              'see_through_mark', 'serial_number', 'value',
              'value_invisible_watermark', 'watermark']

# -------------------- Denomination HSV Ranges & Colors --------------------
denominations = {
    "20 pesos": {"h": (5, 15), "s": (100,255), "v": (100,255), "color": (0,140,255)},   # Orange
    "50 pesos": {"h": ((0,5),(170,180)), "s": (100,255), "v": (100,255), "color": (0,0,255)},  # Red
    "100 pesos": {"h": (125,150), "s": (50,255), "v": (50,255), "color": (128,0,128)},  # Purple
    "200 pesos": {"h": (40,80), "s": (50,255), "v": (50,255), "color": (0,255,0)},       # Green
    "500 pesos": {"h": (20,30), "s": (100,255), "v": (100,255), "color": (0,215,255)},   # Yellow/Gold
    "1000 pesos": {"h": (90,130), "s": (50,255), "v": (50,255), "color": (255,0,0)},     # Blue
}

# Map denomination names to numeric values
denomination_values = {
    "20 pesos": "20",
    "50 pesos": "50",
    "100 pesos": "100",
    "200 pesos": "200",
    "500 pesos": "500",
    "1000 pesos": "1000",
}

# -------------------- Functions --------------------
def guess_bill_denomination(cropped_img):
    hsv = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2HSV)
    h_mean = int(np.mean(hsv[:,:,0]))
    s_mean = int(np.mean(hsv[:,:,1]))
    v_mean = int(np.mean(hsv[:,:,2]))

    for denom, val in denominations.items():
        h_range, s_range, v_range = val["h"], val["s"], val["v"]
        if isinstance(h_range[0], tuple):
            if ((h_range[0][0] <= h_mean <= h_range[0][1]) or (h_range[1][0] <= h_mean <= h_range[1][1])) and s_range[0]<=s_mean<=s_range[1] and v_range[0]<=v_mean<=v_range[1]:
                return denom
        else:
            if h_range[0]<=h_mean<=h_range[1] and s_range[0]<=s_mean<=s_range[1] and v_range[0]<=v_mean<=v_range[1]:
                return denom
    return "Unknown"

def draw_detections(img, results):
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            label_class = classNames[cls]
            if label_class != "value":
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped = img[y1:y2, x1:x2]
            denom = guess_bill_denomination(cropped)
            color = denominations.get(denom, {"color": (255,255,255)})["color"]
            bill_value = denomination_values.get(denom, "Unknown")

            # Draw bounding box
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)

            # Semi-transparent label
            overlay = img.copy()
            alpha = 0.6
            (text_w, text_h), _ = cv2.getTextSize(bill_value, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(overlay, (x1, y1-text_h-10), (x1+text_w+10, y1), (0,0,0), -1)
            cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
            cv2.putText(img, bill_value, (x1+5, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    return img

# -------------------- Image Detection --------------------
def detect_image():
    image_path = filedialog.askopenfilename(filetypes=[("Image files","*.jpg *.png *.jpeg")])
    if not image_path:
        return

    img = cv2.imread(image_path)
    h, w, _ = img.shape
    scale = min((canvas.winfo_width())/w, (canvas.winfo_height())/h)
    img_resized = cv2.resize(img, (int(w*scale), int(h*scale)))

    results = model(img_resized)
    img_resized = draw_detections(img_resized, results)

    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    img_tk = ImageTk.PhotoImage(img_pil)
    canvas.image = img_tk
    canvas.create_image(0,0, anchor=tk.NW, image=img_tk)

# -------------------- Real-Time Camera Detection --------------------
camera_active = False
cap = None

def start_camera():
    global camera_active, cap
    if camera_active:
        camera_active = False
        camera_btn.config(text="Start Camera")
        if cap:
            cap.release()
        canvas.delete("all")
    else:
        camera_active = True
        camera_btn.config(text="Stop Camera")
        cap = cv2.VideoCapture(0)
        update_frame()

def update_frame():
    global camera_active, cap
    if camera_active:
        ret, frame = cap.read()
        if not ret:
            return

        h, w, _ = frame.shape
        scale = min(canvas.winfo_width()/w, canvas.winfo_height()/h)
        frame_resized = cv2.resize(frame, (int(w*scale), int(h*scale)))

        results = model(frame_resized)
        frame_resized = draw_detections(frame_resized, results)

        img_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)
        canvas.image = img_tk
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

        canvas.after(30, update_frame)

# -------------------- Bottom Buttons --------------------
btn_frame = tk.Frame(root, bg="#1b1b2f")
btn_frame.pack(side=tk.BOTTOM, pady=15)

detect_btn = tk.Button(
    btn_frame, 
    text="Select Image & Detect", 
    command=detect_image,
    font=("Arial", 14, "bold"),
    bg="#ff6f61",
    fg="white",
    activebackground="#ff4c3b",
    activeforeground="white",
    bd=0,
    relief=tk.RAISED,
    padx=20,
    pady=10
)
detect_btn.pack(side=tk.LEFT, padx=10)

camera_btn = tk.Button(
    btn_frame,
    text="Start Camera",
    command=start_camera,
    font=("Arial", 14, "bold"),
    bg="#4caf50",
    fg="white",
    activebackground="#45a049",
    activeforeground="white",
    bd=0,
    relief=tk.RAISED,
    padx=20,
    pady=10
)
camera_btn.pack(side=tk.LEFT, padx=10)

root.mainloop()
