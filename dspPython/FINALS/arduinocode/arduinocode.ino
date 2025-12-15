// SIMPLE TEST VERSION - Adjust thresholds first
#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "pldtWifi";
const char* password = "zQrst232";
const char* n8nWebhook = "http://172.20.10.5:5678/webhook-test/055f12e6-ca7d-4363-a94a-1e7c8444f7f9";

#define MIC_PIN 34
#define LED_PIN 2

// ADJUST THESE AFTER TESTING:
#define LOUD_THRESHOLD 2500    // Start with this value
#define ALERT_SECONDS 30      // 

unsigned long loudStart = 0;
bool loudActive = false;
int alertNumber = 1;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  analogReadResolution(12);
  
  Serial.println("Testing Noise Detector...");
  Serial.print("Alert threshold: ");
  Serial.println(LOUD_THRESHOLD);
  Serial.print("Alert after: ");
  Serial.print(ALERT_SECONDS);
  Serial.println(" seconds");
  
  connectWiFi();
}

void loop() {
  int noise = getNoise();
  
  Serial.print("Noise: ");
  Serial.print(noise);
  
  if (noise > LOUD_THRESHOLD) {
    Serial.println(" - LOUD");
    
    if (!loudActive) {
      loudStart = millis();
      loudActive = true;
      Serial.println("Timer started!");
    } else {
      unsigned long duration = (millis() - loudStart) / 1000;
      Serial.print(" (");
      Serial.print(duration);
      Serial.println("s)");
      
      if (duration >= ALERT_SECONDS) {
        sendAlert(noise, duration);
        loudActive = false;
      }
    }
    
    digitalWrite(LED_PIN, HIGH);
  } else {
    if (loudActive) {
      Serial.println(" - Back to normal");
      loudActive = false;
    } else {
      Serial.println(" - Normal");
    }
    digitalWrite(LED_PIN, LOW);
  }
  
  delay(1000);
}

int getNoise() {
  int maxVal = 0, minVal = 4095;
  
  for (int i = 0; i < 20; i++) {
    int val = analogRead(MIC_PIN);
    if (val > maxVal) maxVal = val;
    if (val < minVal) minVal = val;
    delay(5);
  }
  
  return maxVal - minVal;
}

void connectWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 20) {
    delay(500);
    Serial.print(".");
    tries++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nFailed to connect");
  }
}

void sendAlert(int noiseLevel, unsigned long duration) {
  Serial.println("\n🚨🚨🚨 ALERT! 🚨🚨🚨");
  Serial.print("Noise: ");
  Serial.print(noiseLevel);
  Serial.print(" for ");
  Serial.print(duration);
  Serial.println(" seconds");
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot send: No WiFi");
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  
  String payload = "{\"alert\": " + String(alertNumber) + 
                   ", \"noise\": " + String(noiseLevel) + 
                   ", \"duration\": " + String(duration) + 
                   ", \"message\": \"30-seconds noise alert\"}";
  
  http.begin(client, n8nWebhook);
  http.addHeader("Content-Type", "application/json");
  
  int response = http.POST(payload);
  
  if (response > 0) {
    Serial.println("✅ Sent to n8n! Response: " + String(response));
    alertNumber++;
  } else {
    Serial.println("❌ Failed: " + String(response));
  }
  
  http.end();
  
  // Blink LED to confirm
  for (int i = 0; i < 10; i++) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    delay(200);
  }
}