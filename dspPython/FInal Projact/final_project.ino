#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

const char* ssid = "WIFI WII";
const char* password = "noodlldes";

#define BUZZER_PIN 18
#define LED_PIN    19
#define BUTTON_PIN 5

LiquidCrystal_I2C lcd(0x27, 16, 2);

WebServer server(80);

bool isAlarmActive = false;       
unsigned long previousMillis = 0; 
const long beepSpeed = 200;       
int state = LOW;                  

void updateLCD(String line1, String line2) {
  lcd.clear();
  lcd.setCursor(0, 0); 
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

void handleRoot() {
  server.send(200, "text/plain", "Driver Guardian Online");
  updateLCD("System Online", "Waiting for AI..");
}

void handleAlertOn() {
  if (!isAlarmActive) { 
      isAlarmActive = true; 
      updateLCD("!!! WAKE UP !!!", "DRIVER ASLEEP!");
  }
  server.send(200, "text/plain", "ALARM_ON");
}

void handleAlertOff() {
  isAlarmActive = false; 
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
  updateLCD("Driver Status:", "Safe & Awake");
  server.send(200, "text/plain", "ALARM_OFF");
}

void handleSay() {
  if (server.hasArg("text")) {
    String message = server.arg("text");
    
    String line1 = "AI Message:";
    String line2 = message;
    if (message.length() > 16) {
        line1 = message.substring(0, 16);
        line2 = message.substring(16);
    }
    
    updateLCD(line1, line2);
    server.send(200, "text/plain", "Message Displayed");
  } else {
    server.send(400, "text/plain", "Error: No Text");
  }
}

void setup() {
  Serial.begin(115200);
  
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP); 

  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_PIN, LOW);

  Wire.begin(21, 22); 
  lcd.init();
  lcd.backlight();
  
  updateLCD("Connecting to", "WiFi...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  String ipAddr = WiFi.localIP().toString();
  Serial.println("\nConnected!");
  Serial.println(ipAddr);
  updateLCD("Connected! IP:", ipAddr);

  server.on("/", handleRoot);
  server.on("/alert_on", handleAlertOn);
  server.on("/alert_off", handleAlertOff);
  server.on("/say", handleSay);
  server.begin();
}

void loop() {
  server.handleClient();

  if (digitalRead(BUTTON_PIN) == LOW) {
    if (isAlarmActive) {
      isAlarmActive = false;
      digitalWrite(BUZZER_PIN, LOW);
      digitalWrite(LED_PIN, LOW);
      updateLCD("ALARM STOPPED", "Manual Override");
      delay(500); 
    }
  }

  if (isAlarmActive) {
    unsigned long currentMillis = millis();

    if (currentMillis - previousMillis >= beepSpeed) {
      previousMillis = currentMillis;

      if (state == LOW) {
        state = HIGH;
      } else {
        state = LOW;
      }
      
      digitalWrite(BUZZER_PIN, state);
      digitalWrite(LED_PIN, state);
    }
  } else {
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_PIN, LOW);
  }
}