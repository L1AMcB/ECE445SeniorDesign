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
const unsigned long READING_INTERVAL = 10; // Read sensors every 10ms

// Peak detection variables
unsigned long lastSendTime = 0;
const unsigned long SEND_INTERVAL = 500; // Regular heartbeat interval and hit detection window
float peakForce1 = 0.0;
float peakForce2 = 0.0;
bool hasPeakAboveThreshold = false;
const float FORCE_THRESHOLD = 220.0; // Hit threshold (220N)
bool inHitDetectionWindow = false;
unsigned long hitStartTime = 0;

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
          // Reset peak detection
          peakForce1 = 0.0;
          peakForce2 = 0.0;
          lastSendTime = millis();
          hasPeakAboveThreshold = false;
          inHitDetectionWindow = false;
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
  // Direct linear mapping without integer division/multiplication to avoid precision loss
  float force = (sensorValue - MIN_SENSOR_VAL) * MAX_FORCE_NEWTONS / (MAX_SENSOR_VAL - MIN_SENSOR_VAL);
  
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
  
  // If continuous reading is enabled and we're connected, monitor force readings
  if (deviceConnected && continuousReading) {
    unsigned long currentTime = millis();
    
    // Read sensors at READING_INTERVAL (every 10ms)
    if (currentTime - lastReadingTime >= READING_INTERVAL) {
      lastReadingTime = currentTime;
      
      // Read force sensor values with multiple samples to reduce noise
      int raw1 = 0;
      int raw2 = 0;
      const int numSamples = 5;  // Take 5 samples and average them
      
      for (int i = 0; i < numSamples; i++) {
        raw1 += analogRead(forceSensorPin1);
        raw2 += analogRead(forceSensorPin2);
        delayMicroseconds(500);  // Short delay between readings
      }
      
      raw1 /= numSamples;
      raw2 /= numSamples;
      
      // Calculate forces
      float force1 = calculateForce(raw1);
      float force2 = calculateForce(raw2);
      
      // Check if either force is above threshold
      bool isAboveThreshold = (force1 >= FORCE_THRESHOLD || force2 >= FORCE_THRESHOLD);
      
      // Start or continue hit detection window if above threshold
      if (isAboveThreshold) {
        if (!inHitDetectionWindow) {
          // Start a new hit detection window
          inHitDetectionWindow = true;
          hitStartTime = currentTime;
          peakForce1 = force1;  // Initialize peak values with current values
          peakForce2 = force2;
          hasPeakAboveThreshold = true;
        } else {
          // Already in a hit window, update peaks if needed
          if (force1 > peakForce1) {
            peakForce1 = force1;
          }
          if (force2 > peakForce2) {
            peakForce2 = force2;
          }
        }
      }
      
      // Check if hit detection window has expired
      if (inHitDetectionWindow && (currentTime - hitStartTime >= SEND_INTERVAL)) {
        // Hit window completed, send peak values
        char peakStr[20];
        sprintf(peakStr, "%.1f,%.1f", peakForce1, peakForce2);
        
        // Send peak values
        pTxCharacteristic->setValue(peakStr);
        pTxCharacteristic->notify();
        
        Serial.print("Hit window completed, sent peak readings: ");
        Serial.println(peakStr);
        
        // Reset for next hit
        inHitDetectionWindow = false;
        peakForce1 = 0.0;
        peakForce2 = 0.0;
        hasPeakAboveThreshold = false;
        lastSendTime = currentTime;  // Update last send time to avoid immediate heartbeat
      }
      
      // Debug print less frequently to avoid flooding Serial
      if ((currentTime / 1000) % 1 == 0) {
        Serial.print("Current reading: ");
        char currentStr[20];
        sprintf(currentStr, "%.1f,%.1f", force1, force2);
        Serial.print(currentStr);
        Serial.print(" (Raw values: ");
        Serial.print(raw1);
        Serial.print(",");
        Serial.print(raw2);
        Serial.println(")");
        
        if (inHitDetectionWindow) {
          Serial.print("In hit window, current peaks: ");
          Serial.print(peakForce1);
          Serial.print(",");
          Serial.println(peakForce2);
        }
      }
    }
    
    // Send heartbeat readings every SEND_INTERVAL when no hit is in progress
    if (!inHitDetectionWindow && (currentTime - lastSendTime >= SEND_INTERVAL)) {
      // Send a zero reading as heartbeat
      char heartbeatStr[20];
      sprintf(heartbeatStr, "0.0,0.0");
      
      pTxCharacteristic->setValue(heartbeatStr);
      pTxCharacteristic->notify();
      
      Serial.println("Sent heartbeat");
      
      // Reset send time
      lastSendTime = currentTime;
    }
  }
  
  delay(1);  // Minimal delay for fastest response
}