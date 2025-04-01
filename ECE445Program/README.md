# ESP32 Force Sensor Display

This Python application displays force readings from two ESP32 devices, each connected to a FlexiForce force sensing resistor.

## Requirements

- Python 3.6+
- Bluetooth-enabled computer
- Two ESP32 microcontrollers with FlexiForce sensors
- PyBluez library

## Installation

1. Install the required dependencies:
```
pip install -r requirements.txt
```

Note: PyBluez may require additional system dependencies:
- For macOS: `brew install bluez`
- For Ubuntu/Debian: `sudo apt-get install libbluetooth-dev`
- For Windows: Additional setup may be required. See PyBluez documentation.

## Usage

1. Make sure your ESP32 devices are programmed to send force sensor data over Bluetooth.
2. Run the application:
```
python main.py
```
3. Use the "Connect" buttons to establish connection with each ESP32.
4. The application will display the connection status and force readings when connected.

## Simulated Mode

By default, the application runs in simulated mode, generating random force values instead of connecting to actual hardware. 

To use with real ESP32 devices:
1. Set `simulated_mode = False` in `bluetooth_handler.py`
2. Make sure your ESP32 devices are named "ESP32_1" and "ESP32_2" or modify the device names in `main.py`

## ESP32 Code

The ESP32 should be programmed to:
1. Set up as a Bluetooth server
2. Read force sensor values
3. Respond to "GET_FORCE" commands by sending the current force value

A sample Arduino sketch for the ESP32 will be provided separately. 