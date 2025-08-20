import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk

# HSV Ranges (multiple per bill)
ranges_100 = [  # violet
    (np.array([120, 50, 50]), np.array([140, 255, 255])),
    (np.array([140, 50, 50]), np.array([160, 255, 255]))
]

ranges_200 = [  # green
    (np.array([35, 60, 60]), np.array([70, 255, 255])),
    (np.array([70, 60, 60]), np.array([90, 255, 255]))
]

ranges_500 = [  # yellow
    (np.array([20, 80, 80]), np.array([30, 255, 255])),
    (np.array([30, 50, 80]), np.array([40, 255, 255]))
]

ranges_1000 = [  # light blue / cyan
    (np.array([85, 50, 70]), np.array([100, 255, 255])),
    (np.array([100, 50, 70]), np.array([115, 255, 255]))
]

def build_mask(hsv, ranges):
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lower, upper in ranges:
        mask |= cv2.inRange(hsv, lower, upper)
    return mask

# Bill class
def classify_bill(hsv):
    mask_100  = build_mask(hsv, ranges_100)
    mask_200  = build_mask(hsv, ranges_200)
    mask_500  = build_mask(hsv, ranges_500)
    mask_1000 = build_mask(hsv, ranges_1000)

    masks = {100: mask_100, 200: mask_200, 500: mask_500, 1000: mask_1000}

    total = 0
    detected = []

    for val, mask in masks.items():
        count = cv2.countNonZero(mask)
        if count > 5000:  # threshold
            total += val
            detected.append(val)

    return masks, detected, total

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Tkinter
root = tk.Tk()
root.title("Philippine Money Detector")

panels = []
for r in range(2):
    for c in range(3):
        lbl = tk.Label(root)
        lbl.grid(row=r, column=c, padx=5, pady=5)
        panels.append(lbl)

total_label = tk.Label(root, text="Total: 0 PHP", font=("Arial", 18), fg="red")
total_label.grid(row=2, column=0, columnspan=3, pady=10)

def update_frame():
    ret, frame = cap.read()
    if not ret:
        root.after(10, update_frame)
        return

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    masks, detected, total = classify_bill(hsv)

    # Output frame
    output = frame.copy()
    y_pos = 40
    for val in detected:
        cv2.putText(output, f"{val} Peso", (20, y_pos),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        y_pos += 40

    cv2.putText(output, f"Total: {total} PHP", (20, y_pos+20),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

    # Convert masks to RGB for display
    mask_100_rgb  = cv2.cvtColor(masks[100],  cv2.COLOR_GRAY2BGR)
    mask_200_rgb  = cv2.cvtColor(masks[200], cv2.COLOR_GRAY2BGR)
    mask_500_rgb  = cv2.cvtColor(masks[500], cv2.COLOR_GRAY2BGR)
    mask_1000_rgb = cv2.cvtColor(masks[1000], cv2.COLOR_GRAY2BGR)

    # Prepare images for GUI
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

    images = [frame_rgb, mask_100_rgb, mask_200_rgb, mask_500_rgb, mask_1000_rgb, output_rgb]
    titles = ["Raw", "₱100 Mask (Violet)", "₱200 Mask (Green)", "₱500 Mask (Yellow)", "₱1000 Mask(Light Blue)", "Detected Bills"]

    for i, (img, title) in enumerate(zip(images, titles)):
        im = Image.fromarray(img).resize((320, 240))
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
