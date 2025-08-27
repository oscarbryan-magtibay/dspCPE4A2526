#include <ESP32Servo.h>

Servo myServo;
const int servoPin = 18;
int currentPos = 90; 

void setup() {
  Serial.begin(115200);
  myServo.attach(servoPin);
  myServo.write(currentPos);
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    int colonIndex = command.indexOf(':');
    if (colonIndex != -1) {
      String direction = command.substring(0, colonIndex);
      String stepString = command.substring(colonIndex + 1);
      int step = stepString.toInt();

      step = max(1, step / 2);  

      if (direction == "LEFT") {
        currentPos = max(0, currentPos - step);
        myServo.write(currentPos);
      } 
      else if (direction == "RIGHT") {
        currentPos = min(180, currentPos + step);
        myServo.write(currentPos);
      } 

      delay(30);  
    }
  }
}
