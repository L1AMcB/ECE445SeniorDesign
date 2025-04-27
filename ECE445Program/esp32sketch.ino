#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// Nordic UART Service UUIDs
#define SERVICE_UUID        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define CHARACTERISTIC_UUID_RX "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
#define CHARACTERISTIC_UUID_TX "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

// Force sensor pins
const int forceSensorPin1 = 17;  // GPIO 10
const int forceSensorPin2 = 12;  // GPIO 2

// Calibration values
const int MIN_SENSOR_VAL = 0;     // Raw sensor value at 0 force
const int MAX_SENSOR_VAL = 4095;  // Raw sensor value at max force (3V on ESP32)
const float MAX_FORCE_NEWTONS = 1500.0;  // Maximum force in Newtons at 3V

// Continuous reading control
bool continuousReading = false;
unsigned long lastReadingTime = 0;
const unsigned long READING_INTERVAL = 100; // Send readings every 100ms (10 Hz)

BLEServer *pServer = NULL;
BLECharacteristic *pTxCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

// Function declaration (needs to be before it's used)
float calculateForce(int sensorValue);

class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println("Client connected!");
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      continuousReading = false; // Stop continuous reading when disconnected
      Serial.println("Client disconnected!");
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      // Get the value as a String and convert to C-style string for comparison
      String rxValue = pCharacteristic->getValue().c_str();

      if (rxValue.length() > 0) {
        Serial.print("Received: ");
        Serial.println(rxValue);
        
        // Process START_FORCE_READING command
        if (rxValue == "START_FORCE_READING\n" || rxValue == "START_FORCE_READING") {
          continuousReading = true;
          Serial.println("Starting continuous force readings");
        }
        // Process STOP_FORCE_READING command
        else if (rxValue == "STOP_FORCE_READING\n" || rxValue == "STOP_FORCE_READING") {
          continuousReading = false;
          Serial.println("Stopping continuous force readings");
        }
      }
    }
};

float calculateForce(int sensorValue) {
  // Map the raw sensor value to force in Newtons
  // This is a simple linear mapping from 0-4095 (0-3.3V) to 0-1500N
  float force = map(sensorValue, MIN_SENSOR_VAL, MAX_SENSOR_VAL, 0, MAX_FORCE_NEWTONS * 10) / 10.0;
  
  // Constrain force value
  if (force < 0) force = 0;
  if (force > MAX_FORCE_NEWTONS) force = MAX_FORCE_NEWTONS;
  
  return force;
}

void setup() {
  Serial.begin(115200);
  Serial.println("Starting BLE Force Sensor");

  // Initialize the BLE device
  BLEDevice::init("ESP32_1");

  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create a BLE Characteristic for RX
  BLECharacteristic *pRxCharacteristic = pService->createCharacteristic(
                      CHARACTERISTIC_UUID_RX,
                      BLECharacteristic::PROPERTY_WRITE |
                      BLECharacteristic::PROPERTY_WRITE_NR);

  pRxCharacteristic->setCallbacks(new MyCallbacks());

  // Create a BLE Characteristic for TX
  pTxCharacteristic = pService->createCharacteristic(
                        CHARACTERISTIC_UUID_TX,
                        BLECharacteristic::PROPERTY_NOTIFY);

  // Add a descriptor to the characteristic
  pTxCharacteristic->addDescriptor(new BLE2902());

  // Start the service
  pService->start();

  // Start advertising
  pServer->getAdvertising()->start();
  Serial.println("Bluetooth device active, waiting for connections...");
}

void loop() {
  // Handle disconnection and reconnection
  if (!deviceConnected && oldDeviceConnected) {
    delay(500); // Give the Bluetooth stack time to get ready
    pServer->startAdvertising(); // Restart advertising
    oldDeviceConnected = deviceConnected;
  }
  
  // Handle new connection
  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
  }
  
  // If continuous reading is enabled and we're connected, send force readings at regular intervals
  if (deviceConnected && continuousReading) {
    unsigned long currentTime = millis();
    if (currentTime - lastReadingTime >= READING_INTERVAL) {
      lastReadingTime = currentTime;
      
      // Read force sensor values
      float force1 = calculateForce(analogRead(forceSensorPin1));
      float force2 = calculateForce(analogRead(forceSensorPin2));
      
      // Format response string: "force1,force2"
      char forceStr[20];
      sprintf(forceStr, "%.1f,%.1f", force1, force2);
      
      // Send response
      pTxCharacteristic->setValue(forceStr);
      pTxCharacteristic->notify();
      
      // Debug print every 10 readings (1 second) to avoid flooding Serial
      if ((currentTime / 1000) % 1 == 0) {
        Serial.print("Continuous reading: ");
        Serial.println(forceStr);
      }
    }
  }
  
  delay(10);
}