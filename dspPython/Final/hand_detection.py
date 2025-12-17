import cv2
import mediapipe as mp
import serial
import time
from collections import deque

# ================= SERIAL =================
ser = serial.Serial('COM3', 115200)
time.sleep(2)

# ================= MEDIAPIPE =================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# ================= STATE =================
stable_buffer = deque(maxlen=12)  # frames for stabilization
letter_buffer = deque(maxlen=5)   # rolling buffer, max 5 letters
input_locked = False
last_no_hand_time = None
NO_HAND_DELAY = 0.6  # seconds
last_accepted_letter = ""

# ================= LETTER DETECTION =================
def detect_letter(hand_landmarks):
    fingers = []

    # Thumb
    fingers.append(1 if hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x else 0)

    # Other fingers
    for tip in [8, 12, 16, 20]:
        fingers.append(1 if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y else 0)

    # Letters for "HELLO"
    if fingers == [0, 1, 1, 0, 0]:
        return "H"
    elif fingers == [0, 0, 0, 0, 0]:
        return "E"
    elif fingers == [1, 1, 0, 0, 0]:
        return "L"
    elif fingers == [1, 1, 1, 1, 1]:
        return "O"
    else:
        return ""

# ================= MAIN LOOP =================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    letter = ""

    # ---------- HAND DETECTED ----------
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            detected = detect_letter(hand_landmarks)
            if detected:
                stable_buffer.append(detected)

        if stable_buffer:
            # majority vote
            letter = max(set(stable_buffer), key=stable_buffer.count)

        # ACCEPT LETTER if not locked
        if letter and not input_locked:
            if len(letter_buffer) == letter_buffer.maxlen:
                letter_buffer.popleft()
            letter_buffer.append(letter)
            input_locked = True
            last_accepted_letter = letter
            ser.write(("".join(letter_buffer) + "\n").encode())

        # Reset no-hand timer since hand is detected
        last_no_hand_time = None

    # ---------- NO HAND = UNLOCK ----------
    else:
        stable_buffer.clear()
        if last_no_hand_time is None:
            # first frame without hand, start timer
            last_no_hand_time = time.time()
        elif time.time() - last_no_hand_time >= NO_HAND_DELAY:
            input_locked = False

    # ---------- DISPLAY ----------
    cv2.putText(frame, f"OLED: {''.join(letter_buffer)}", (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    cv2.putText(frame, f"Locked: {input_locked}", (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv2.imshow("ASL → OLED (Stable Rolling Buffer)", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# ================= CLEANUP =================
cap.release()
cv2.destroyAllWindows()
ser.close()
