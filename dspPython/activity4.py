from ultralytics import YOLO
import cv2
import math
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
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

# -------------------- Detection --------------------
def detect_image():
    image_path = filedialog.askopenfilename(filetypes=[("Image files","*.jpg *.png *.jpeg")])
    if not image_path:
        return

    img = cv2.imread(image_path)
    h, w, _ = img.shape
    scale = min((canvas.winfo_width())/w, (canvas.winfo_height())/h)
    img_resized = cv2.resize(img, (int(w*scale), int(h*scale)))

    results = model(img_resized)

    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            label_class = classNames[cls]
            if label_class != "value":
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped = img_resized[y1:y2, x1:x2]
            denom = guess_bill_denomination(cropped)
            conf = math.ceil((box.conf[0]*100))/100
            text = f"{denom} {conf}"
            color = denominations.get(denom, {"color": (255,255,255)})["color"]

            # Bounding box
            cv2.rectangle(img_resized, (x1, y1), (x2, y2), color, 3)

            # Text with semi-transparent background
            overlay = img_resized.copy()
            alpha = 0.6
            (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(overlay, (x1, y1-text_h-10), (x1+text_w+10, y1), (0,0,0), -1)
            cv2.addWeighted(overlay, alpha, img_resized, 1-alpha, 0, img_resized)
            cv2.putText(img_resized, text, (x1+5, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    img_tk = ImageTk.PhotoImage(img_pil)
    canvas.image = img_tk
    canvas.create_image(0,0, anchor=tk.NW, image=img_tk)

# -------------------- Bottom Button --------------------
detect_btn = tk.Button(
    root, 
    text="Select Image & Detect", 
    command=detect_image,
    font=("Arial", 14, "bold"),
    bg="#ff6f61",       # Button background color (orange)
    fg="white",         # Text color
    activebackground="#ff4c3b",  # Hover background color
    activeforeground="white",
    bd=0,               # No border
    relief=tk.RAISED,
    padx=20,
    pady=10
)
detect_btn.pack(side=tk.BOTTOM, pady=15)


root.mainloop()
