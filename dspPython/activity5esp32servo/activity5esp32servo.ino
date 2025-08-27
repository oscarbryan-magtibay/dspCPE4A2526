#include <ESP32Servo.h>

Servo myServo;
const int servoPin = 18;
int currentPos = 90; // Start at center

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

      // Reduce step size to slow down movement
      step = max(1, step / 2);  // divide by 2, minimum 1 degree

      if (direction == "LEFT") {
        currentPos = max(0, currentPos - step);
        myServo.write(currentPos);
      } 
      else if (direction == "RIGHT") {
        currentPos = min(180, currentPos + step);
        myServo.write(currentPos);
      } 
      // CENTER does nothing

      delay(30);  // add delay for slower, smoother motion
    }
  }
}
