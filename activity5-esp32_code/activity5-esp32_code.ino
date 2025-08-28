const int SERVO_PIN = 13;      
const int LEDC_CH   = 4;       
const int FREQ_HZ   = 50;      
const int RES_BITS  = 16;      
const int PERIOD_US = 20000;   

const int PULSE_MIN = 500;     
const int PULSE_MAX = 2400;    

int currentAngle = 90;
int targetAngle  = 90;

uint32_t usToDuty(int us) {
  return (uint32_t)((uint64_t)us * ((1ULL << RES_BITS) - 1) / PERIOD_US);
}

void writeAngle(int angle) {
  angle = constrain(angle, 0, 180);
  int us = map(angle, 0, 180, PULSE_MIN, PULSE_MAX);
  ledcWrite(LEDC_CH, usToDuty(us));
}

void setup() {
  Serial.begin(115200);
  ledcSetup(LEDC_CH, FREQ_HZ, RES_BITS);
  ledcAttachPin(SERVO_PIN, LEDC_CH);

  writeAngle(currentAngle);
  Serial.println("Smooth servo ready. Send 0–180.");
}

void loop() {
  // Receive new target angle from Serial
  if (Serial.available() > 0) {
    int angle = Serial.parseInt();
    if (angle >= 0 && angle <= 180) {
      targetAngle = angle;
    }
  }

  // Smoothly approach target
  if (currentAngle < targetAngle) currentAngle++;
  else if (currentAngle > targetAngle) currentAngle--;

  writeAngle(currentAngle);
  delay(2);  // controls smoothness speed (higher = slower)
}
