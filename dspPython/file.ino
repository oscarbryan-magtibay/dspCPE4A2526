#include <ESP32Servo.h>

// Servo objects
Servo panServo;
Servo tiltServo;

// Current servo positions
int currentPan = 90;
int currentTilt = 90;

// Target servo positions (from Python script)
int targetPan = 90;
int targetTilt = 90;

// GPIO pins for servos
const int panPin = 18;   // GPIO for pan servo (horizontal)
const int tiltPin = 19;  // GPIO for tilt servo (vertical)

// Movement parameters
const int stepDelay = 8;        // ms between servo steps (smoother movement)
const int maxStep = 2;          // maximum degrees per step for faster tracking
const int deadzone = 2;         // minimum difference before moving

// Timing variables
unsigned long lastMoveTime = 0;
unsigned long lastSerialTime = 0;
const unsigned long serialTimeout = 1000; // ms without serial = return to center

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  Serial.println("ESP32 Servo Tracker Starting...");
  
  // Attach servos to pins
  panServo.attach(panPin, 500, 2500);   // min/max pulse width for better range
  tiltServo.attach(tiltPin, 500, 2500);
  
  // Set initial positions
  panServo.write(currentPan);
  tiltServo.write(currentTilt);
  
  Serial.println("Servos initialized at center position (90, 90)");
  Serial.println("Ready to receive tracking data...");
  
  delay(1000); // Allow servos to reach initial position
}

void loop() {
  // Check for serial input
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim(); // Remove whitespace
    
    int commaIndex = data.indexOf(',');
    if (commaIndex > 0 && commaIndex < data.length() - 1) {
      // Parse pan and tilt values
      int newPan = data.substring(0, commaIndex).toInt();
      int newTilt = data.substring(commaIndex + 1).toInt();
      
      // Validate and constrain values
      if (newPan >= 0 && newPan <= 180 && newTilt >= 0 && newTilt <= 180) {
        targetPan = newPan;
        targetTilt = newTilt;
        lastSerialTime = millis();
        
        // Optional: Print received values for debugging
        // Serial.print("Received - Pan: ");
        // Serial.print(targetPan);
        // Serial.print(", Tilt: ");
        // Serial.println(targetTilt);
      }
    }
  }
  
  // Check for serial timeout - return to center if no data received
  if (millis() - lastSerialTime > serialTimeout) {
    targetPan = 90;
    targetTilt = 90;
  }
  
  // Update servo positions with timing control
  if (millis() - lastMoveTime >= stepDelay) {
    bool moved = false;
    
    // Smooth pan movement with variable step size
    if (abs(currentPan - targetPan) > deadzone) {
      int panDiff = targetPan - currentPan;
      int panStep = constrain(abs(panDiff), 1, maxStep);
      
      if (panDiff > 0) {
        currentPan += panStep;
      } else {
        currentPan -= panStep;
      }
      
      currentPan = constrain(currentPan, 0, 180);
      panServo.write(currentPan);
      moved = true;
    }
    
    // Smooth tilt movement with variable step size
    if (abs(currentTilt - targetTilt) > deadzone) {
      int tiltDiff = targetTilt - currentTilt;
      int tiltStep = constrain(abs(tiltDiff), 1, maxStep);
      
      if (tiltDiff > 0) {
        currentTilt += tiltStep;
      } else {
        currentTilt -= tiltStep;
      }
      
      currentTilt = constrain(currentTilt, 0, 180);
      tiltServo.write(currentTilt);
      moved = true;
    }
    
    // Update timing
    if (moved) {
      lastMoveTime = millis();
    }
  }
  
  // Small delay to prevent overwhelming the ESP32
  delay(1);
}

// Optional: Function to smoothly move to a specific position
void moveToPosition(int pan, int tilt) {
  targetPan = constrain(pan, 0, 180);
  targetTilt = constrain(tilt, 0, 180);
}