from flask import Flask, request, jsonify
from transformers import pipeline
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import random

# ------------------------
# Configuration
# ------------------------
OWNER_NAME = "Queenie Magcawas"
OWNER_EMAIL = "2321197@ub.edu.ph"
SENDER_EMAIL = "kwinimagcawas@gmail.com"
SENDER_PASS = "KkaebsongBBH"  # Use Gmail App Password

# ------------------------
# Initialize Flask and AI
# ------------------------
app = Flask(__name__)

# Lightweight AI model (runs on CPU)
generator = pipeline(
    "text-generation",
    model="distilgpt2",
    device=-1
)

# ------------------------
# Email function
# ------------------------
def send_email(subject, content):
    msg = MIMEText(content)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = OWNER_EMAIL

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, OWNER_EMAIL, msg.as_string())
        server.quit()
        print("📧 Email sent successfully")
    except Exception as e:
        print("❌ Email error:", e)

# ------------------------
# AI report generation
# ------------------------
def generate_ai_report(card_id):
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    anomaly_score = random.randint(80, 99)

    prompt = (
        f"Suspicious access attempt detected.\n"
        f"Time: {time_now}\n"
        f"Card ID: {card_id}\n"
        f"Owner: {OWNER_NAME}\n"
        f"Anomaly Probability: {anomaly_score}%.\n"
        f"Write a short professional security incident report."
    )

    result = generator(prompt, max_length=150, do_sample=True, temperature=0.7)
    return result[0]["generated_text"]

# ------------------------
# Endpoint to receive ESP32 data
# ------------------------
@app.route('/event', methods=['POST'])
def event():
    data = request.get_json()
    print("📥 Received data:", data)

    if not data or "card_id" not in data:
        return jsonify({"error": "Invalid request"}), 400

    card_id = data["card_id"]

    # Generate AI report and send email
    report = generate_ai_report(card_id)
    send_email("🚨 Suspicious Access Attempt", report)

    return jsonify({
        "status": "received",
        "card_id": card_id,
        "owner": OWNER_NAME,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "report": report
    })

# ------------------------
# Test endpoint
# ------------------------
@app.route('/')
def home():
    return "ESP32 AI Access Control Server is running"

# ------------------------
# Run server
# ------------------------
if __name__ == "__main__":
    print("🚀 Starting AI Access Control Server...")
    app.run(host="0.0.0.0", port=5000)
