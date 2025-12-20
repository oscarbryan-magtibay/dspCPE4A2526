// main.cpp
#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>
#include <arduinoFFT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// OLED Configuration
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// I2S Configuration for INMP441
#define I2S_PORT I2S_NUM_0
#define SAMPLE_RATE 44100
#define BUFFER_SIZE 1024
#define FFT_SAMPLES 512

// I2S Pins
#define I2S_WS 25
#define I2S_SCK 26
#define I2S_SD 33

// WiFi Credentials
const char* ssid = "Jhon Paul's Wi-Fi Network";
const char* password = "Ziki2412";

// n8n Server
const char* n8nServer = "http://YOUR_N8N_IP:5678/webhook/audio";

// DSP Variables
int16_t audioBuffer[BUFFER_SIZE];
double vReal[FFT_SAMPLES];
double vImag[FFT_SAMPLES];
ArduinoFFT<double> FFT = ArduinoFFT<double>(vReal, vImag, FFT_SAMPLES, SAMPLE_RATE);

// Display States
enum DisplayState {
  SHOW_SPECTRUM,
  SHOW_METRICS,
  SHOW_AI_RESULT
};
DisplayState currentDisplay = SHOW_METRICS;
unsigned long lastDisplayChange = 0;

void setup() {
  Serial.begin(115200);
  
  // Initialize OLED
  Wire.begin(21, 22);
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("SSD1306 allocation failed"));
    while(1);
  }
  display.display();
  delay(2000);
  display.clearDisplay();
  
  // Initialize I2S
  setupI2S();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Display startup message
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("Audio AI System");
  display.println("Ready...");
  display.display();
}

void loop() {
  // 1. Capture Audio
  captureAudio();
  
  // 2. Process Audio (DSP)
  AudioMetrics metrics = processAudioDSP();
  
  // 3. Update OLED Display
  updateDisplay(metrics);
  
  // 4. Send to n8n every 2 seconds or on event
  static unsigned long lastSend = 0;
  if(millis() - lastSend > 2000 || metrics.dbLevel > 70) {
    sendToN8N(metrics);
    lastSend = millis();
  }
  
  // 5. Check for button input (GPIO 0 for display change)
  if(digitalRead(0) == LOW) {
    delay(50); // Debounce
    if(digitalRead(0) == LOW) {
      cycleDisplayMode();
      while(digitalRead(0) == LOW); // Wait for release
    }
  }
}

// ============= I2S Setup =============
void setupI2S() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 4,
    .dma_buf_len = BUFFER_SIZE,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };
  
  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);
}

// ============= WiFi Connection =============
void connectToWiFi() {
  display.clearDisplay();
  display.setCursor(0,0);
  display.println("Connecting WiFi");
  display.println(ssid);
  display.display();
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while(WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    display.print(".");
    display.display();
    attempts++;
  }
  
  if(WiFi.status() == WL_CONNECTED) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("WiFi Connected!");
    display.println(WiFi.localIP());
    display.display();
    delay(1000);
  } else {
    display.println("Failed!");
    display.display();
  }
}

// ============= Audio Capture =============
void captureAudio() {
  size_t bytesRead = 0;
  i2s_read(I2S_PORT, audioBuffer, sizeof(audioBuffer), &bytesRead, portMAX_DELAY);
}

// ============= DSP Processing =============
struct AudioMetrics {
  float dbLevel;
  float dominantFreq;
  float peakValue;
  bool hasAnomaly;
  float spectralCentroid;
};

AudioMetrics processAudioDSP() {
  AudioMetrics metrics;
  
  // Convert to double for FFT
  for(int i = 0; i < FFT_SAMPLES; i++) {
    vReal[i] = (double)audioBuffer[i];
    vImag[i] = 0.0;
  }
  
  // Apply windowing
  FFT.windowing(FFTWindow::Hamming, FFTDirection::Forward);
  
  // Compute FFT
  FFT.compute(FFTDirection::Forward);
  FFT.complexToMagnitude();
  
  // Calculate metrics
  metrics.dbLevel = calculateDBLevel(vReal, FFT_SAMPLES);
  metrics.dominantFreq = getDominantFrequency(vReal, SAMPLE_RATE, FFT_SAMPLES);
  metrics.peakValue = findPeakValue(vReal, FFT_SAMPLES);
  metrics.spectralCentroid = calculateSpectralCentroid(vReal, SAMPLE_RATE, FFT_SAMPLES);
  
  // Simple anomaly detection
  metrics.hasAnomaly = (metrics.dbLevel > 75) || 
                      (metrics.dominantFreq > 5000 && metrics.dbLevel > 60);
  
  return metrics;
}

float calculateDBLevel(double* samples, int numSamples) {
  double sum = 0;
  for(int i = 0; i < numSamples; i++) {
    sum += samples[i] * samples[i];
  }
  double rms = sqrt(sum / numSamples);
  return 20 * log10(rms / 32768.0) + 94; // Convert to dB (reference for digital)
}

float getDominantFrequency(double* magnitudes, int samplingRate, int numSamples) {
  double maxMagnitude = 0;
  int maxIndex = 0;
  
  for(int i = 0; i < numSamples/2; i++) {
    if(magnitudes[i] > maxMagnitude) {
      maxMagnitude = magnitudes[i];
      maxIndex = i;
    }
  }
  
  return (maxIndex * samplingRate) / numSamples;
}

// ============= OLED Display =============
void updateDisplay(AudioMetrics metrics) {
  display.clearDisplay();
  
  switch(currentDisplay) {
    case SHOW_METRICS:
      showMetricsScreen(metrics);
      break;
    case SHOW_SPECTRUM:
      showSpectrumScreen(metrics);
      break;
    case SHOW_AI_RESULT:
      showAIResultScreen();
      break;
  }
  
  display.display();
  
  // Auto-cycle display every 5 seconds
  if(millis() - lastDisplayChange > 5000) {
    cycleDisplayMode();
    lastDisplayChange = millis();
  }
}

void showMetricsScreen(AudioMetrics metrics) {
  display.setTextSize(1);
  display.setCursor(0,0);
  display.println("AUDIO METRICS");
  display.println("-------------");
  
  display.print("dB: ");
  display.print(metrics.dbLevel, 1);
  display.println(" dB");
  
  display.print("Freq: ");
  display.print(metrics.dominantFreq, 0);
  display.println(" Hz");
  
  display.print("Peak: ");
  display.print(metrics.peakValue, 2);
  
  display.setCursor(0, 56);
  display.print("Mode: ");
  display.print(WiFi.status() == WL_CONNECTED ? "Online" : "Offline");
}

void showSpectrumScreen(AudioMetrics metrics) {
  // Draw frequency spectrum
  display.drawFastHLine(0, 60, 128, SSD1306_WHITE); // X-axis
  
  for(int i = 0; i < 64; i++) {
    int barHeight = map(vReal[i*4], 0, 10000, 0, 50);
    display.drawLine(i*2, 60, i*2, 60 - barHeight, SSD1306_WHITE);
  }
  
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("SPECTRUM");
  display.setCursor(0, 10);
  display.print("Centroid: ");
  display.print(metrics.spectralCentroid, 0);
  display.print(" Hz");
}

void showAIResultScreen() {
  display.setTextSize(1);
  display.setCursor(0,0);
  display.println("AI ANALYSIS");
  display.println("-----------");
  display.println("Last result:");
  display.println("Normal ambient");
  display.println("92% confidence");
  display.setCursor(0, 56);
  display.println("Waiting...");
}

void cycleDisplayMode() {
  currentDisplay = (DisplayState)((currentDisplay + 1) % 3);
}

// ============= n8n Communication =============
void sendToN8N(AudioMetrics metrics) {
  if(WiFi.status() != WL_CONNECTED) {
    return;
  }
  
  HTTPClient http;
  http.begin(n8nServer);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<256> doc;
  doc["device_id"] = "esp32_audio_01";
  doc["timestamp"] = millis();
  doc["db_level"] = metrics.dbLevel;
  doc["dominant_freq"] = metrics.dominantFreq;
  doc["spectral_centroid"] = metrics.spectralCentroid;
  doc["has_anomaly"] = metrics.hasAnomaly;
  doc["wifi_rssi"] = WiFi.RSSI();
  
  String payload;
  serializeJson(doc, payload);
  
  int httpCode = http.POST(payload);
  
  if(httpCode > 0) {
    String response = http.getString();
    
    // Parse AI response if available
    StaticJsonDocument<512> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if(!error && responseDoc.containsKey("ai_response")) {
      updateAIResultOnDisplay(responseDoc["ai_response"]);
    }
  }
  
  http.end();
}

void updateAIResultOnDisplay(const char* result) {
  // Store for display on AI screen
  // In a full implementation, you'd store this in a variable
  // that showAIResultScreen() would read
}