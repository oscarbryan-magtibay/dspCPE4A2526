#include <SPI.h>
#include <MFRC522.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

const char* ssid = "PLDTHOMEFIBRfm7TH_2.4G";
const char* password = "Powppies_1921";
const char* serverURL = "http://192.168.1.16:5000"; 

#define SS_PIN 5
#define RST_PIN 27
MFRC522 mfrc522(SS_PIN, RST_PIN);

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED init failed!");
    while (1);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("Scan your RFID card...");
  display.display();

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" connected!");
}

void loop() {

  if ( ! mfrc522.PICC_IsNewCardPresent()) return;
  if ( ! mfrc522.PICC_ReadCardSerial()) return;

  String uidString = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if(mfrc522.uid.uidByte[i] < 0x10) uidString += "0";
    uidString += String(mfrc522.uid.uidByte[i], HEX);
  }
  uidString.toUpperCase();

  Serial.println("Card UID: " + uidString);

  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("RFID UID:");
  display.setTextSize(2);
  display.println(uidString);
  display.display();

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    String httpRequestData = "uid=" + uidString;
    int httpResponseCode = http.POST(httpRequestData);

    if (httpResponseCode > 0) {
      Serial.println("Server response: " + String(httpResponseCode));
    } else {
      Serial.println("Error sending to server");
    }
    http.end();
  } else {
    Serial.println("WiFi not connected!");
  }

  mfrc522.PICC_HaltA(); 
  delay(2000); 
}
