import cv2
import mediapipe as mp
import serial
import time
import numpy as np

esp = serial.Serial('COM6', 115200, timeout=1)  
time.sleep(2)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

def is_open_hand(landmarks):
    tips = [landmarks[i] for i in [8, 12, 16, 20]]  
    wrist = landmarks[0]
    return all(tip.y < wrist.y for tip in tips)

def is_fist(landmarks):
    tips = [landmarks[i] for i in [8, 12, 16, 20]]
    wrist = landmarks[0]
    return all(tip.y > wrist.y for tip in tips)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't grab frame")
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    gesture = "None"
    action = "None"

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
            landmarks = handLms.landmark

            if is_open_hand(landmarks):
                gesture = "OPEN"
                action = "TURN ON"
                esp.write(b'1\n')  
            elif is_fist(landmarks):
                gesture = "FIST"
                action = "TURN OFF"
                esp.write(b'0\n')  

    display_text = f"GESTURE: {gesture}  ACTION: {action}"
    cv2.putText(frame, display_text, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

    cv2.imshow("Hand Gesture Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:  
        break

cap.release()
cv2.destroyAllWindows()
esp.close()
