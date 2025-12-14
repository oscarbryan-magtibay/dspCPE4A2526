include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <driver/i2s.h>
#include <ArduinoJson.h>
// --- 1. WIFI SETTINGS ---
const char* ssid = "SKYW_6156_2G";
const char* password = "Nndp5uHb";
// --- 2. N8N WEBHOOK URL ---
const char* serverName = "http://192.168.1.61:5678/webhook/focus-zone";
// --- 3. SAFETY THRESHOLDS (Adjust these for your room!) ---
// If sensors go outside these numbers, the RED LED turns on.
const float MAX_TEMP = 30.0; 
const float MIN_TEMP = 18.0; 
const float MAX_HUM = 70.0; 
const float MAX_NOISE = 500.0; // Adjust this based on your mic
sensitivity
// --- PIN DEFINITIONS ---
#define DHTPIN 4
#define DHTTYPE DHT11 
#define RED_LED 25
#define BLUE_LED 26
#define BUTTON_PIN 27
// I2S Mic Config
#define I2S_WS 33
#define I2S_SD 32
#define I2S_SCK 14
#define I2S_PORT I2S_NUM_0
#define bufferLen 64
int16_t sBuffer[bufferLen];
DHT dht(DHTPIN, DHTTYPE);
// --- TIMERS & AVERAGING VARIABLES ---
unsigned long lastSensorCheck = 0;
unsigned long lastAutoUpload = 0;
const long sensorInterval = 2000; // Check sensors every 2
seconds
const long uploadInterval = 30 * 60 * 1000; // Upload to AI every 30
minutes
// Variables to store the sum of readings (to calculate average later)
float sumTemp = 0;
float sumHum = 0;
float sumNoise = 0;
int readCount = 0;
void setup() {
 Serial.begin(115200);
 pinMode(RED_LED, OUTPUT);
 pinMode(BLUE_LED, OUTPUT);
 pinMode(BUTTON_PIN, INPUT_PULLUP);
 // Start Sensors
 dht.begin();
 i2s_install();
 i2s_setpin();
 i2s_start(I2S_PORT);
 // Connect to WiFi
 Serial.print("Connecting to WiFi");
 WiFi.begin(ssid, password);
 while (WiFi.status() != WL_CONNECTED) {
 delay(500);
 Serial.print(".");
 digitalWrite(RED_LED, !digitalRead(RED_LED));
 }
 Serial.println("\nWiFi Connected!");
 // Initialize Timers
 lastAutoUpload = millis();
}
void loop() {
 unsigned long currentMillis = millis();
 // --- TASK 1: LOCAL CHECK (Every 2 Seconds) ---
 if (currentMillis - lastSensorCheck >= sensorInterval) {
 lastSensorCheck = currentMillis;
 checkEnvironmentLocal();
 }
 // --- TASK 2: AUTO REPORT (Every 30 Minutes) ---
 if (currentMillis - lastAutoUpload >= uploadInterval) {
 lastAutoUpload = currentMillis;
 Serial.println("--- 30 Mins Passed: Sending Summary ---");
 sendAverageDataToAI();
 }
 // --- TASK 3: MANUAL BUTTON (Instant) ---
 if (digitalRead(BUTTON_PIN) == LOW) {
 Serial.println("Button Pressed! Sending Instant Snapshot...");
 
 // Visual feedback: Flash Red briefly
 digitalWrite(BLUE_LED, LOW);
 digitalWrite(RED_LED, HIGH);
 
 sendInstantDataToAI();
 
 delay(1000); // Wait 1 sec so we don't send twice
 // LEDs will reset automatically on the next 2-second check
 }
}
// ---------------------------------------------------------
// FUNCTION 1: Check Sensors locally & Update LEDs
// ---------------------------------------------------------
void checkEnvironmentLocal() {
 float t = dht.readTemperature();
 float h = dht.readHumidity();
 float noise = readMicVolume();
 // Error Check
 if (isnan(t) || isnan(h)) {
 Serial.println("Failed to read from DHT sensor!");
 return;
 }
 // Accumulate data for the 30-minute average
 sumTemp += t;
 sumHum += h;
 sumNoise += noise;
 readCount++;
 // --- LED LOGIC ---
 // Blue ON only if everything is perfect. Red ON if anything is bad.
 bool isHot = (t > MAX_TEMP);
 bool isCold = (t < MIN_TEMP);
 bool isHumid = (h > MAX_HUM);
 bool isNoisy = (noise > MAX_NOISE);
 if (isHot || isCold || isHumid || isNoisy) {
 digitalWrite(BLUE_LED, LOW);
 digitalWrite(RED_LED, HIGH); // Bad Environment
 } else {
 digitalWrite(RED_LED, LOW);
 digitalWrite(BLUE_LED, HIGH); // Good Environment
 }
}
// ---------------------------------------------------------
// FUNCTION 2: Send INSTANT Snapshot (Manual)
// ---------------------------------------------------------
void sendInstantDataToAI() {
 float t = dht.readTemperature();
 float h = dht.readHumidity();
 float noise = readMicVolume();
 // We add "[MANUAL CHECK]" so the AI knows this is happening NOW.
 String payload = "{\"data\": \"[MANUAL CHECK] Current Temp: " +
String(t) + "C, Hum: " + String(h) + "%, Noise: " + String(noise) + "\"}";
 postToN8N(payload);
}
// ---------------------------------------------------------
// FUNCTION 3: Send AVERAGE Summary (Auto)
// ---------------------------------------------------------
void sendAverageDataToAI() {
 if (readCount == 0) return; // Prevent divide by zero error
 float avgTemp = sumTemp / readCount;
 float avgHum = sumHum / readCount;
 float avgNoise = sumNoise / readCount;
 // We add "[30-MIN SUMMARY]" so the AI knows this is past data.
 String payload = "{\"data\": \"[30-MIN SUMMARY] Avg Temp: " +
String(avgTemp) + "C, Avg Hum: " + String(avgHum) + "%, Avg Noise: " +
String(avgNoise) + "\"}";
 postToN8N(payload);
 // RESET totals for the next 30 minutes
 sumTemp = 0;
 sumHum = 0;
 sumNoise = 0;
 readCount = 0;
}
// ---------------------------------------------------------
// HELPER: Send to N8N
// ---------------------------------------------------------
void postToN8N(String jsonPayload) {
 if(WiFi.status() == WL_CONNECTED){
 HTTPClient http;
 http.begin(serverName);
 http.addHeader("Content-Type", "application/json");
 
 Serial.println("Sending: " + jsonPayload);
 int httpResponseCode = http.POST(jsonPayload);
 
 if(httpResponseCode > 0){
 Serial.println("Sent Successfully!");
 } else {
 Serial.print("Error sending: ");
 Serial.println(httpResponseCode);
 }
 http.end();
 } else {
 Serial.println("WiFi Disconnected");
 }
}
// ---------------------------------------------------------
// HELPER: Read Mic
// ---------------------------------------------------------
float readMicVolume() {
 size_t bytesIn = 0;
 esp_err_t result = i2s_read(I2S_PORT, &sBuffer, bufferLen *
sizeof(int16_t), &bytesIn, portMAX_DELAY);
 if (result == ESP_OK) {
 long sum = 0;
 for (int i = 0; i < bufferLen; i++) sum += abs(sBuffer[i]);
 return sum / bufferLen;
 }
 return 0;
}
// ---------------------------------------------------------
// I2S Setup
// ---------------------------------------------------------
void i2s_install() {
 const i2s_config_t i2s_config = {
 .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
 .sample_rate = 44100,
 .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
 .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
 .communication_format = I2S_COMM_FORMAT_I2S,
 .intr_alloc_flags = 0,
 .dma_buf_count = 8,
 .dma_buf_len = bufferLen,
 .use_apll = false
 };
 i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
}
void i2s_setpin() {
 const i2s_pin_config_t pin_config = {
 .bck_io_num = I2S_SCK,
 .ws_io_num = I2S_WS,
 .data_out_num = -1,
 .data_in_num = I2S_SD
 };
 i2s_set_pin(I2S_PORT, &pin_config);
}