#include <ESP32Servo.h>

Servo myServo;
int pos = 90;  
char command;

void setup() {
  Serial.begin(115200);
  myServo.attach(15);  
  myServo.write(pos);
}

void loop() {
  if (Serial.available()) {
    command = Serial.read();

    if (command == 'L') {
      pos += 2;
      if (pos > 180) pos = 180;
      myServo.write(pos);
    } else if (command == 'R') {
      pos -= 2;
      if (pos < 0) pos = 0;
      myServo.write(pos);
    } else if (command == 'C') {
  
    }
  }
}
