#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ESP32Servo.h>

// ================= OLED =================
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ================= PINS =================
#define BUTTON_PIN 0
#define LED_PIN 2
#define SERVO_PIN 15

// ================= WIFI =================
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
const char* N8N_URL = "http://YOUR_N8N_IP:5678/webhook/esp32-ai";

// ================= SERVO =================
Servo servo;

// ================= SETUP =================
void setup() {
  Serial.begin(115200);

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  servo.attach(SERVO_PIN);

  Wire.begin(21, 22);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  displayMessage("Connecting WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  displayMessage("AI Voice Ready");
}

// ================= LOOP =================
void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    displayMessage("Listening...");

    // ---- DSP + STT PLACEHOLDER ----
    // Real mic capture + DSP explained in paper
    String recognizedText = "turn on the light";

    String aiResponse;
    String intent;
    int value;

    sendToN8N(recognizedText, intent, value, aiResponse);
    executeCommand(intent, value);

    displayMessage("AI:\n" + aiResponse);
    delay(1500); // debounce
  }
}

// ================= FUNCTIONS =================

void displayMessage(String msg) {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println(msg);
  display.display();
}

void sendToN8N(String text, String &intent, int &value, String &response) {
  HTTPClient http;
  http.begin(N8N_URL);
  http.addHeader("Content-Type", "application/json");

  DynamicJsonDocument doc(256);
  doc["text"] = text;
  String body;
  serializeJson(doc, body);

  int httpCode = http.POST(body);
  if (httpCode <= 0) {
    response = "HTTP Error";
    return;
  }

  String payload = http.getString();
  http.end();

  DynamicJsonDocument res(512);
  deserializeJson(res, payload);

  intent = res["intent"].as<String>();
  value = res["value"] | 0;
  response = res["response"].as<String>();
}

void executeCommand(String intent, int value) {
  if (intent == "LED_ON") {
    digitalWrite(LED_PIN, HIGH);
  }
  else if (intent == "LED_OFF") {
    digitalWrite(LED_PIN, LOW);
  }
  else if (intent == "SERVO_MOVE") {
    servo.write(value);
  }
}
