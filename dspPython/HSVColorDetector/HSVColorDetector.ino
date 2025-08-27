#include <Arduino.h>
#include <ESP32Servo.h>

//Servo & Serial Configurations
const int SERVO_PIN    = 13;
const int BAUD_RATE    = 115200;
const int ANGLE_MIN    = 0;
const int ANGLE_MAX    = 180;
const int START_ANGLE  = 90;

//Global Variables
Servo servo;
String serialBuffer;

//Write
void safeWrite(int angle) {
    angle = constrain(angle, ANGLE_MIN, ANGLE_MAX);
    servo.write(angle);
}

//Setup
void setup() {
    Serial.begin(BAUD_RATE);
    delay(200);

    servo.setPeriodHertz(50);
    servo.attach(SERVO_PIN, 500, 2400);
    safeWrite(START_ANGLE);

    Serial.println("ESP32 ready");
}

//Main Loop
void loop() {
    while (Serial.available()) {
        char incomingChar = (char)Serial.read();

        if (incomingChar == '\r') continue;

        if (incomingChar == '\n') {
            if (serialBuffer.startsWith("A:")) {
                int angle = serialBuffer.substring(2).toInt();
                safeWrite(angle);
                Serial.print("ACK:");
                Serial.println(angle);
            }
            serialBuffer = "";
        } 
        
        else {
            if (serialBuffer.length() < 16) serialBuffer += incomingChar;
        }
    }
}
