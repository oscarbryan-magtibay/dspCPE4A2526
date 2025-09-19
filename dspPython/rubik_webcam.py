

import cv2
from ultralytics import YOLO
import numpy as np
import matplotlib.pyplot as plt


model = YOLO(r"C:\Users\Administrator\Documents\GitHub\dspCPE4A2526\best2.pt")

#  Open webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open webcam.")
else:
    print("Webcam opened. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break

    #  Run YOLO detection
    results = model(frame, conf=0.8)
    annotated_frame = results[0].plot()

    #  Show in external OpenCV window
    cv2.imshow("Rubik Detection - Live", annotated_frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
