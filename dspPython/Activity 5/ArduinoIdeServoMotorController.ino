#include <ESP32Servo.h>

Servo servoX;  // horizontal servo
int posX = 90; // start at center

void setup() {
  Serial.begin(115200);

  // Attach servo to a pin (example GPIO23, pili ka ng PWM pin ng ESP32)
  servoX.attach(23, 500, 2400);  // pin, min pulse, max pulse (standard servo range)
  servoX.write(posX);
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    if (cmd == 'R') {
      posX -= 2;   // move left
    } else if (cmd == 'L') {
      posX += 2;   // move right
    }

    // Limit values (0–180 degrees)
    posX = constrain(posX, 0, 180);

    servoX.write(posX);

    delay(20); // small delay for smooth motion
  }
}
