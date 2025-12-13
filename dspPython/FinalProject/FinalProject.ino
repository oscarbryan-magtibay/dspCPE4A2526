#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

#define LED_PIN 2

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  Wire.begin(21, 22);  
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    while (true);
  }

  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("Gesture:");
  display.display();
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    String gestureText = "None";
    String actionText = "None";

    if (command == "1") {
      digitalWrite(LED_PIN, HIGH);
      gestureText = "OPEN";
      actionText = "TURN ON";
    } else if (command == "0") {
      digitalWrite(LED_PIN, LOW);
      gestureText = "FIST";
      actionText = "TURN OFF";
    }

    display.fillRect(0, 16, SCREEN_WIDTH, 48, SSD1306_BLACK);

    display.setTextSize(1);
    display.setCursor(0, 16);
    display.print("GESTURE: ");
    display.println(gestureText);

    display.setCursor(0, 32);
    display.print("ACTION : ");
    display.println(actionText);

    display.display();
  }
}

