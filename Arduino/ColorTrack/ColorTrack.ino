#include <Arduino.h>
#include <ESP32Servo.h>


static const int SERVO_PIN = 13;
static const int BAUD = 115200;
static const int ANGLE_MIN = 0;
static const int ANGLE_MAX = 180;
static const int START_ANGLE = 90;

Servo servo;
String line;

void safeWrite(int angle) {
  angle = constrain(angle, ANGLE_MIN, ANGLE_MAX);
  servo.write(angle);
}

void setup() {
  Serial.begin(BAUD);
  delay(200);


  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2400);
  safeWrite(START_ANGLE);

  Serial.println("ESP32 ready");
}

void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\r') continue;
    if (c == '\n') {
      if (line.startsWith("A:")) {
        int angle = line.substring(2).toInt();
        safeWrite(angle);
        Serial.print("ACK:");
        Serial.println(angle);
      }
      line = "";
    } else {
      if (line.length() < 16) line += c;
    }
  }
}