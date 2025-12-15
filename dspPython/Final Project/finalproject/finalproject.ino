#define RELAY_PIN 26 
void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);

  
  digitalWrite(RELAY_PIN, LOW);
  Serial.println("Relay is OFF. Type 'ON' or 'OFF' to control the relay.");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 
    if (command.equalsIgnoreCase("ON")) {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("✅ Relay turned ON");
    }
    else if (command.equalsIgnoreCase("OFF")) {
      digitalWrite(RELAY_PIN, LOW);  
      Serial.println("❌ Relay turned OFF");
    }
    else {
      Serial.println("Unknown command. Type 'ON' or 'OFF'");
    }
  }
}
