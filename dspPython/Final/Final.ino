#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

String receivedLetter = "";

void setup() {
  Serial.begin(115200);

  Wire.begin();  // ESP32 I2C

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED not found");
    while (true);
  }

  display.clearDisplay();
  display.setTextSize(3);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(20, 20);
  display.println("READY");
  display.display();
}

void loop() {
  if (Serial.available()) {
    receivedLetter = Serial.readStringUntil('\n');
    receivedLetter.trim();

    display.clearDisplay();
    display.setTextSize(5);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(40, 20);
    display.println(receivedLetter);
    display.display();
  }
}
