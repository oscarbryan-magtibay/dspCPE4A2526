import cv2
from ultralytics import YOLO
import pytesseract
import re
import requests
import pymongo
import time


print("🚀 LICENSE PLATE SYSTEM - NumPy 2.0 READY")

# MongoDB & ESP32
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
db = mongo_client["license_plates"]
collection = db["plates"]
ESP32_IP = "192.168.1.13"
model = YOLO('best.pt')


def extract_plate(roi):
    """Extract plate text from ROI"""
    if roi.size == 0:
        return None
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # Simple OCR config for plates
    config = '--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text = pytesseract.image_to_string(gray, config=config)
    text = re.sub(r'[^A-Z0-9]', '', text.strip().upper())
    return text if len(text) >= 3 else None


def send_esp32(plate):
    """Send to ESP32 display"""
    try:
        url = f"http://{ESP32_IP}:80/plate?text={plate}"
        requests.get(url, timeout=2)
        print(f"📺 ESP32: Welcome {plate}")
    except:
        print("⚠️ ESP32: Offline (check IP)")


def save_mongo(plate):
    """Save to MongoDB"""
    doc = {
        "plate": plate,
        "timestamp": time.time(),
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    collection.insert_one(doc)
    print(f"💾 MongoDB: {plate} saved")


# MAIN SYSTEM LOOP
print("🎥 Camera starting... Ctrl+C to stop")

# Use the same working camera index as your test (0 instead of 1)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

last_detection = 0
DETECTION_COOLDOWN = 10  # seconds

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # YOLO Detection (NumPy 2.0 safe)
        results = model.predict(source=frame, conf=0.5, verbose=False)

        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                for box in r.boxes:
                    # NumPy 2.0 SAFE coordinate extraction
                    xyxy = box.xyxy[0].cpu()
                    x1, y1, x2, y2 = map(int, xyxy.tolist())

                    # Draw detection box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Extract plate ROI safely
                    roi = frame[max(0, y1):min(480, y2), max(0, x1):min(640, x2)]

                    plate_text = extract_plate(roi)
                    now = time.time()

                    # Process valid plate with cooldown
                    if (
                        plate_text and
                        len(plate_text) >= 3 and
                        now - last_detection > DETECTION_COOLDOWN
                    ):
                        print(f"\n🎉 PLATE DETECTED: {plate_text}")
                        print(f"   📍 Coords: ({x1},{y1},{x2},{y2})")

                        # Trigger full system
                        send_esp32(plate_text)
                        save_mongo(plate_text)
                        last_detection = now

        # === DISPLAY WINDOW (fixed part) ===
        cv2.imshow("License Plate System", frame)

        # Let OpenCV process GUI events and allow quit with 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.05)  # ~20 FPS

except KeyboardInterrupt:
    print("\n⏹️ User stopped system")

finally:
    cap.release()
    cv2.destroyAllWindows()
    mongo_client.close()
    print("✅ SYSTEM SHUTDOWN COMPLETE")
