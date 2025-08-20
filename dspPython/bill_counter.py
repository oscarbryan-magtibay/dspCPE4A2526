import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import os

# -----------------------------
# Constants
# -----------------------------
BILL_INFO = {
    "20": {"color": (0, 165, 255)}, 
    "50": {"color": (0, 0, 255)}, 
    "100": {"color": (255, 0, 255)}, 
    "200": {"color": (0, 255, 0)}, 
    "500": {"color": (0, 255, 255)}, 
    "1000": {"color": (255, 0, 0)}, 
}

ASPECT_RATIO_RANGE = (1.45, 1.65)
MIN_CONTOUR_AREA = 2000
TEMPLATE_DIR = "templates"  # folder containing 20.jpg, 50.jpg, etc.
MIN_MATCH_COUNT = 10        # minimum ORB matches to consider a bill detected

# -----------------------------
# Load bill templates
# -----------------------------
TEMPLATES = {}
ORB = cv2.ORB_create(nfeatures=1000)
BF = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

for bill in BILL_INFO:
    path = os.path.join(TEMPLATE_DIR, f"{bill}.jpg")
    if os.path.exists(path):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        kp, des = ORB.detectAndCompute(img, None)
        TEMPLATES[bill] = {"image": img, "kp": kp, "des": des}
    else:
        print(f"Template missing for {bill}")

# -----------------------------
# Detect bills using ORB + shape
# -----------------------------
def detect_bills(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    bills_count = {}

    # Find contours for potential bills
    blurred = cv2.GaussianBlur(gray, (5,5), 1.5)
    _, thresh = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_CONTOUR_AREA:
            continue
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h)
        if ASPECT_RATIO_RANGE[0] <= aspect_ratio <= ASPECT_RATIO_RANGE[1]:
            roi = gray[y:y+h, x:x+w]
            roi_resized = cv2.resize(roi, (100, int(100/aspect_ratio)))

            for bill, data in TEMPLATES.items():
                kp2, des2 = ORB.detectAndCompute(roi_resized, None)
                if des2 is None or data["des"] is None:
                    continue
                matches = BF.match(data["des"], des2)
                matches = sorted(matches, key=lambda x: x.distance)
                if len(matches) >= MIN_MATCH_COUNT:
                    bills_count[bill] = bills_count.get(bill, 0) + 1
                    cv2.rectangle(frame, (x, y), (x+w, y+h), BILL_INFO[bill]["color"], 2)
                    cv2.putText(frame, f"{bill} PHP", (x, y-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, BILL_INFO[bill]["color"], 2)
                    break  # avoid double-counting same contour
    return frame, bills_count

# -----------------------------
# Tkinter GUI
# -----------------------------
def update_frame():
    ret, frame = cap.read()
    if ret:
        frame, counts = detect_bills(frame)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        lbl.imgtk = imgtk
        lbl.configure(image=imgtk)

        if counts:
            total_amount = sum(int(k)*v for k,v in counts.items())
            count_text = " | ".join([f"{k}₱:{v}" for k,v in counts.items()])
            lbl_counts.config(text=f"{count_text} | Total: {total_amount}₱")
        else:
            lbl_counts.config(text="No bills detected")

    root.after(10, update_frame)

# -----------------------------
# Main Tkinter window
# -----------------------------
root = tk.Tk()
root.title("Philippine Bill Detection")

lbl = tk.Label(root)
lbl.pack()

lbl_counts = tk.Label(root, text="", font=("Arial", 14))
lbl_counts.pack()

cap = cv2.VideoCapture(0)
update_frame()
root.mainloop()
