#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>

// ===== RFID PINS =====
#define SS_PIN 5
#define RST_PIN 22

MFRC522 rfid(SS_PIN, RST_PIN);

// ===== BUZZER =====
#define BUZZER_PIN 27

// ===== WIFI =====
const char* ssid = "munchie";
const char* password = "munchie201012";

// ===== N8N PRODUCTION WEBHOOK URL =====
const char* webhookURL = "http://192.168.1.9:5678/webhook/rfid-attendance";

// ===== BUZZER FUNCTIONS =====
void beepOnce() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(150);
  digitalWrite(BUZZER_PIN, LOW);
}

void beepError() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(80);
    digitalWrite(BUZZER_PIN, LOW);
    delay(80);
  }
}

void setup() {
  Serial.begin(115200);

  // Initialize Buzzer
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi Connected");

  // Initialize RFID
  SPI.begin();
  rfid.PCD_Init();

  byte version = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (version == 0x00 || version == 0xFF) {
    Serial.println("❌ RFID NOT detected");
  } else {
    Serial.println("✅ RFID detected");
  }

  Serial.println("Waiting for RFID card...");
}

void loop() {
  // Check for card
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  // Read UID
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();
  Serial.println("📌 Card UID: " + uid);

  // ===== STUDENT DATA =====
  String name = "";
  String studentID = "";
  String email = "";
  String photo = "";
  bool validCard = true;

  if (uid == "EE207E5") {
    name = "Jane Doe";
    studentID = "2023-001";
    email = "2321087@ub.edu.ph";
    photo = "https://lumenor.ai/cdn-cgi/imagedelivery/F5KOmplEz0rStV2qDKhYag/44c83fba-cfb9-4217-6f92-86be425e0300/tn";
  } 
  else if (uid == "BF6C5") {
    name = "John Doe";
    studentID = "2023-002";
    email = "b.abby406@gmail.com";
    photo = "https://easy-peasy.ai/cdn-cgi/image/quality=80,format=auto,width=700/https://media.easy-peasy.ai/27feb2bb-aeb4-4a83-9fb6-8f3f2a15885e/7977e4ce-f85a-434c-9e80-d0aa7de8c9a0.png";
  } 
  else {
    validCard = false;
  }

  // ===== BUZZER =====
  if (!validCard) {
    Serial.println("❌ Invalid Card");
    beepError();
    delay(2000);
    return;
  } else {
    beepOnce();
  }

  // ===== SEND DATA TO N8N =====
  String status = "CHECK-IN"; // You can expand to check-in/out logic

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(webhookURL);
    http.addHeader("Content-Type", "application/json");

    String json = "{\"uid\":\"" + uid + 
                  "\",\"name\":\"" + name + 
                  "\",\"studentID\":\"" + studentID + 
                  "\",\"status\":\"" + status + 
                  "\",\"photo\":\"" + photo + 
                  "\",\"email\":\"" + email + "\"}";

    int httpResponseCode = http.POST(json);
    Serial.println("Data sent. HTTP Code: " + String(httpResponseCode));
    http.end();
  } else {
    Serial.println("❌ WiFi not connected");
  }

  delay(3000); // Prevent multiple scans
}
