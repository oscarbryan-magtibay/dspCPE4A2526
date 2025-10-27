#include <ESP32Servo.h>

Servo myServo;
int servoPin = 23;
int currentPos = 90;   

void setup() {
  myServo.attach(servoPin);
  myServo.write(currentPos);
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    if (cmd == 'L' && currentPos > 0) {
      currentPos -= 2;   
    } 
    else if (cmd == 'R' && currentPos < 180) {
      currentPos += 2;  
    } 
    else if (cmd == 'C') {
      
    }

    myServo.write(currentPos);
    delay(20);  
  }
}
