from ultralytics import YOLO
import cv2
import numpy as np
import math
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# ----------------- Tkinter Window Setup -----------------
root = tk.Tk()
root.title("Philippine Coin Detection")
window_width = 900
window_height = 700
root.geometry(f"{window_width}x{window_height}")
root.configure(bg="#1e1e1e")

# ----------------- YOLO Model -----------------
model = YOLO("act4/weights/money.pt")  # Replace with your coin-trained weights

# ----------------- Canvas -----------------
canvas = tk.Canvas(root, width=window_width, height=window_height-100, bg="#1e1e1e", highlightthickness=0)
canvas.pack(pady=10)

# ----------------- Coin Detection Heuristic -----------------
def guess_coin_denomination(cropped_img):
    h, w = cropped_img.shape[:2]

    center_radius = int(min(h, w) * 0.4)
    center = cropped_img[h//2-center_radius:h//2+center_radius, w//2-center_radius:w//2+center_radius]
    outer_mask = np.ones(cropped_img.shape[:2], dtype=np.uint8) * 255
    cv2.circle(outer_mask, (w//2, h//2), center_radius, 0, -1)
    outer = cv2.bitwise_and(cropped_img, cropped_img, mask=outer_mask)

    center_hsv = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    outer_hsv = cv2.cvtColor(outer, cv2.COLOR_BGR2HSV)
    center_avg = cv2.mean(center_hsv)[:3]
    outer_avg = cv2.mean(outer_hsv)[:3]
    center_h, center_s, center_v = center_avg
    outer_h, outer_s, outer_v = outer_avg

    if outer_s < 30 and outer_v > 180:
        return "1 peso"
    if 10 <= outer_h <= 30 and 100 <= outer_s <= 200 and 150 <= outer_v <= 220:
        return "5 pesos"
    if 10 <= outer_h <= 30 and 50 <= outer_s <= 150 and 120 <= outer_v <= 200 and center_s < 50 and center_v > 180:
        return "10 pesos"
    if 15 <= outer_h <= 35 and 80 <= outer_s <= 200 and 130 <= outer_v <= 210:
        return "20 pesos"
    return "Unknown"

# ----------------- Image Detection -----------------
def detect_image():
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
    if not image_path:
        return
    
    img = cv2.imread(image_path)
    h, w, _ = img.shape
    scale = min(window_width/w, (window_height-100)/h)
    img = cv2.resize(img, (int(w*scale), int(h*scale)))

    results = model(img)
    for r in results:
        boxes = r.boxes
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cropped = img[y1:y2, x1:x2]

            denom = guess_coin_denomination(cropped)
            conf = math.ceil((box.conf[0]*100))/100
            text = f"{denom} {conf}"

            # Draw circle
            cx, cy = (x1 + x2)//2, (y1 + y2)//2
            radius = max((x2-x1)//2, (y2-y1)//2)
            cv2.circle(img, (cx, cy), radius, (0, 255, 255), 3)
            cv2.putText(img, text, (cx - radius, cy - radius - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

    # Convert for Tkinter
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    img_tk = ImageTk.PhotoImage(img_pil)
    canvas.image = img_tk
    canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

# ----------------- Camera Detection -----------------
def start_camera():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                cropped = frame[y1:y2, x1:x2]

                denom = guess_coin_denomination(cropped)
                conf = math.ceil((box.conf[0]*100))/100
                text = f"{denom} {conf}"

                # Draw circle
                cx, cy = (x1 + x2)//2, (y1 + y2)//2
                radius = max((x2-x1)//2, (y2-y1)//2)
                cv2.circle(frame, (cx, cy), radius, (0, 255, 255), 3)
                cv2.putText(frame, text, (cx - radius, cy - radius - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        cv2.imshow("Camera Coin Detection", frame)
        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

# ----------------- Buttons -----------------
btn_frame = tk.Frame(root, bg="#1e1e1e")
btn_frame.pack(pady=5)

upload_btn = tk.Button(btn_frame, text="Upload Image & Detect", command=detect_image,
                       font=("Arial", 14, "bold"), bg="#ff6f61", fg="white", padx=20, pady=10)
upload_btn.pack(side=tk.LEFT, padx=10)

camera_btn = tk.Button(btn_frame, text="Start Camera Detection", command=start_camera,
                       font=("Arial", 14, "bold"), bg="#4caf50", fg="white", padx=20, pady=10)
camera_btn.pack(side=tk.LEFT, padx=10)

root.mainloop()
