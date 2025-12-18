#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include "DHT.h"
#include <WiFi.h>
#include <HTTPClient.h>

#define LM35_PIN 34
#define DHTPIN 4
#define DHTTYPE DHT11
#define BODY_TEMP_OFFSET 14.0
#define FEVER_THRESHOLD 37.5
#define BUZZER_PIN 27
#define BUTTON_PIN 14

const char* ssid = "ZTE_2.4G_zzJ4P2";
const char* password = "MFpFP7Gc";
const char* webhookURL = "http://192.168.1.9:5678/webhook-test/temperature";

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 16, 4);

void setup() {
  Serial.begin(115200);
  dht.begin();
  lcd.init();
  lcd.backlight();
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Temp Monitor");
  delay(2000);

  WiFi.begin(ssid, password);
  lcd.setCursor(0, 3);
  lcd.print("Connecting WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  lcd.setCursor(0, 3);
  lcd.print("WiFi Connected!   ");
  delay(1000);
}

float readLM35() {
  int rawValue = analogRead(LM35_PIN);
  float voltage = rawValue * (3.3 / 4095.0);
  return voltage * 100;
}

float estimateBodyTemp(float handTemp) {
  return handTemp + BODY_TEMP_OFFSET;
}

float readHandTempAverage(int samples = 5) {
  float sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += readLM35();
    delay(100);
  }
  return sum / samples;
}

void beepBuzzer(bool isFever) {
  delay(3000);
  if (isFever) {
    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZER_PIN, HIGH);
      delay(500);
      digitalWrite(BUZZER_PIN, LOW);
      delay(300);
    }
  } else {
    for (int i = 0; i < 2; i++) {
      digitalWrite(BUZZER_PIN, HIGH);
      delay(150);
      digitalWrite(BUZZER_PIN, LOW);
      delay(150);
    }
  }
}

void waitForButtonPress() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("PUSH BUTTON FOR");
  lcd.setCursor(0, 1);
  lcd.print("TEMPERATURE");
  lcd.setCursor(0, 2);
  lcd.print("CHECKING");

  while (digitalRead(BUTTON_PIN) == HIGH) {
    delay(50);
  }
  while (digitalRead(BUTTON_PIN) == LOW) {
    delay(50);
  }
}

void sendToWebhook(float roomTemp, float handTemp, float bodyTemp) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(webhookURL);
    http.addHeader("Content-Type", "application/json");

    String jsonData = "{";
    jsonData += "\"roomTemperature\":" + String(roomTemp, 1) + ",";
    jsonData += "\"handTemperature\":" + String(handTemp, 1) + ",";
    jsonData += "\"bodyTemperature\":" + String(bodyTemp, 1);
    jsonData += "}";

    Serial.println("======================================");
    Serial.println("Sending JSON to n8n:");
    Serial.println(jsonData);
    Serial.println("======================================");

    int httpResponseCode = http.POST(jsonData);

    if (httpResponseCode > 0) {
      Serial.print("Data sent! Response: ");
      Serial.println(httpResponseCode);
      String response = http.getString();
      Serial.println("Server response: " + response);
    } else {
      Serial.print("Error sending data: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  }
}

void loop() {
  waitForButtonPress();

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("HOLD LM35");
  lcd.setCursor(0, 1);
  lcd.print("for 3 seconds");

  float handTemp = readHandTempAverage();
  float bodyTemp = estimateBodyTemp(handTemp);

  beepBuzzer(bodyTemp >= FEVER_THRESHOLD);

  float roomTemp = dht.readTemperature();
  if (isnan(roomTemp)) roomTemp = 0;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ROOM TEMP: ");
  lcd.print(roomTemp, 1);
  lcd.print((char)223); lcd.print("C");

  lcd.setCursor(0, 1);
  lcd.print("HAND TEMP: ");
  lcd.print(handTemp, 1);
  lcd.print((char)223); lcd.print("C");

  lcd.setCursor(0, 2);
  lcd.print("BODY TEMP: ");
  lcd.print(bodyTemp, 1);
  lcd.print((char)223); lcd.print("C");

  lcd.setCursor(0, 3);
  lcd.print("Sending to n8n...");

  sendToWebhook(roomTemp, handTemp, bodyTemp);

  lcd.setCursor(0, 3);
  lcd.print("Data sent!       ");

  delay(8000);
}
