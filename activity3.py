import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk

# HSV Ranges
lower_silver = np.array([0, 0, 80])
upper_silver = np.array([180, 60, 255])
lower_gold = np.array([10, 80, 80])
upper_gold = np.array([40, 255, 255])

def classify_coin(hsv, silver_mask, gold_mask, x, y, r):
    mask_full = np.zeros(hsv.shape[:2], dtype=np.uint8)
    cv2.circle(mask_full, (x, y), r, 255, -1)

    mask_center = np.zeros(hsv.shape[:2], dtype=np.uint8)
    cv2.circle(mask_center, (x, y), int(r * 0.55), 255, -1)

    mask_ring = cv2.subtract(mask_full, mask_center)

    silver_full = cv2.countNonZero(cv2.bitwise_and(silver_mask, silver_mask, mask=mask_full))
    gold_full = cv2.countNonZero(cv2.bitwise_and(gold_mask, gold_mask, mask=mask_full))

    silver_center = cv2.countNonZero(cv2.bitwise_and(silver_mask, silver_mask, mask=mask_center))
    gold_center = cv2.countNonZero(cv2.bitwise_and(gold_mask, gold_mask, mask=mask_center))

    silver_ring = cv2.countNonZero(cv2.bitwise_and(silver_mask, silver_mask, mask=mask_ring))
    gold_ring = cv2.countNonZero(cv2.bitwise_and(gold_mask, gold_mask, mask=mask_ring))

    total_full = silver_full + gold_full + 1
    total_center = silver_center + gold_center + 1
    total_ring = silver_ring + gold_ring + 1

    silver_ratio_full = silver_full / total_full
    gold_ratio_full = gold_full / total_full
    silver_ratio_center = silver_center / total_center
    gold_ratio_center = gold_center / total_center
    silver_ratio_ring = silver_ring / total_ring
    gold_ratio_ring = gold_ring / total_ring

    if silver_ratio_full > 0.7:
        return "1 Peso", 1
    elif gold_ratio_full > 0.7:
        return "5 Peso", 5
    elif gold_ratio_center > 0.5 and silver_ratio_ring > 0.5:
        return "10 Peso", 10
    elif silver_ratio_center > 0.5 and gold_ratio_ring > 0.5:
        return "20 Peso", 20
    else:
        return "Unknown", 0

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

root = tk.Tk()
root.title("Coin Detector")

panels = []
for r in range(2):
    for c in range(2):
        lbl = tk.Label(root)
        lbl.grid(row=r, column=c, padx=5, pady=5)
        panels.append(lbl)

total_label = tk.Label(root, text="Total: 0 PHP", font=("Arial", 16), fg="red")
total_label.grid(row=2, column=0, columnspan=2, pady=10)

def update_frame():
    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    silver_mask = cv2.inRange(hsv, lower_silver, upper_silver)
    gold_mask = cv2.inRange(hsv, lower_gold, upper_gold)

    silver_vis = cv2.cvtColor(silver_mask, cv2.COLOR_GRAY2BGR)
    gold_vis = cv2.cvtColor(gold_mask, cv2.COLOR_GRAY2BGR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT,
        dp=1.2, minDist=40,
        param1=100, param2=25,
        minRadius=15, maxRadius=80
    )

    output = frame.copy()
    total = 0
    if circles is not None:
        for x, y, r in np.uint16(np.around(circles[0])):
            cv2.circle(output, (x, y), r, (0, 255, 0), 2)
            cv2.circle(output, (x, y), 2, (0, 0, 255), 3)
            coin, val = classify_coin(hsv, silver_mask, gold_mask, x, y, r)
            total += val
            cv2.putText(output, coin, (x - r, y - r - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    cv2.putText(output, f"Total: {total} PHP", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    silver_rgb = cv2.cvtColor(silver_vis, cv2.COLOR_BGR2RGB)
    gold_rgb = cv2.cvtColor(gold_vis, cv2.COLOR_BGR2RGB)
    output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

    images = [frame_rgb, silver_rgb, gold_rgb, output_rgb]
    titles = ["Raw", "Silver Mask", "Gold Mask", "Detected Coins"]

    for i, (img, title) in enumerate(zip(images, titles)):
        im = Image.fromarray(img).resize((320, 240))  # resize para magkasya
        imgtk = ImageTk.PhotoImage(image=im)
        panels[i].imgtk = imgtk
        panels[i].configure(image=imgtk, text=title, compound="top")

    total_label.config(text=f"Total: {total} PHP")

    root.after(10, update_frame)

def on_closing():
    cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
update_frame()
root.mainloop()
