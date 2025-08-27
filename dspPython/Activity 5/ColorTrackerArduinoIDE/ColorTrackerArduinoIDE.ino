#include <ESP32Servo.h>

Servo myServo;
int servoPin = 23;
int pos = 90;  

void setup() {
  myServo.attach(servoPin);
  myServo.write(pos);
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    if (cmd == 'L') pos = max(0, pos - 2);
    if (cmd == 'R') pos = min(180, pos + 2);

    myServo.write(pos);
    delay(20);
  }
}