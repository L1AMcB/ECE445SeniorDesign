#include <BluetoothSerial.h>

// Check if Bluetooth is properly enabled
#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` and enable Bluetooth
#endif

BluetoothSerial SerialBT;

// Force sensor pin
const int forceSensorPin = 34;  // ADC pin on ESP32
const float MAX_FORCE_NEWTONS = 100.0;  // Maximum force in Newtons (adjust based on your sensor)

// Calibration values (you'll need to calibrate for your specific sensor)
const int MIN_SENSOR_VAL = 0;     // Raw sensor value at 0 force
const int MAX_SENSOR_VAL = 4095;  // Raw sensor value at max force

// Device name - use "ESP32_1" or "ESP32_2" 
String deviceName = "ESP32_1"; // Change to match your device

// Buffer for received commands
char cmd[32];
int cmdIndex = 0;

void setup() {
  // Start serial communication
  Serial.begin(115200);
  
  // Start Bluetooth serial with the device name
  SerialBT.begin(deviceName);
  Serial.println("Bluetooth started. Device is ready to pair.");
}

void loop() {
  // Read force sensor
  int rawValue = analogRead(forceSensorPin);
  
  // Process commands from Bluetooth
  if (SerialBT.available()) {
    char c = SerialBT.read();
    
    // Add character to command buffer
    if (c != '\n' && c != '\r') {
      cmd[cmdIndex++] = c;
      if (cmdIndex >= sizeof(cmd) - 1) {
        cmdIndex = 0;  // Avoid buffer overflow
      }
    } else {
      // End of command, process it
      cmd[cmdIndex] = '\0';
      processCommand(cmd);
      cmdIndex = 0;
    }
  }
  
  // Small delay to avoid spamming
  delay(20);
}

void processCommand(const char* command) {
  Serial.print("Received command: ");
  Serial.println(command);
  
  // Process GET_FORCE command
  if (strcmp(command, "GET_FORCE") == 0) {
    float force = calculateForce(analogRead(forceSensorPin));
    Serial.print("Sending force value: ");
    Serial.println(force);
    SerialBT.println(force);
  } 
  else {
    Serial.println("Unknown command");
  }
}

float calculateForce(int sensorValue) {
  // Map the raw sensor value to force in Newtons
  // This is a simple linear mapping - you might need a more complex calibration
  float force = map(sensorValue, MIN_SENSOR_VAL, MAX_SENSOR_VAL, 0, MAX_FORCE_NEWTONS * 100) / 100.0;
  
  // Constrain force value
  if (force < 0) force = 0;
  if (force > MAX_FORCE_NEWTONS) force = MAX_FORCE_NEWTONS;
  
  return force;
} 