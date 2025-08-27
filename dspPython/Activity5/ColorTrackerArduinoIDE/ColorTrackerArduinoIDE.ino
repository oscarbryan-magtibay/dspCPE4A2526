#include <ESP32Servo.h>

Servo myServo;
int servoPin = 23;
int currentPos = 90;   // Start at center

void setup() {
  myServo.attach(servoPin);
  myServo.write(currentPos);
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    if (cmd == 'L' && currentPos > 0) {
      currentPos -= 1;   // move slowly left
    } 
    else if (cmd == 'R' && currentPos < 180) {
      currentPos += 1;   // move slowly right
    } 
    else if (cmd == 'C') {
      // do nothing (stay centered)
    }

    myServo.write(currentPos);
    delay(20);  // smooth movement
  }
}
