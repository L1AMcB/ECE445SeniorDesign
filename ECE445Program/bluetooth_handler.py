import time
import random

# Flag to determine if we should use real or simulated Bluetooth
USE_REAL_BLUETOOTH = False

try:
    if USE_REAL_BLUETOOTH:
        import bluetooth
        BLUETOOTH_AVAILABLE = True
    else:
        BLUETOOTH_AVAILABLE = False
except ImportError:
    print("PyBluez not installed. Using simulation mode only.")
    print("To use real Bluetooth, install with: pip install pybluez")
    print("For Mac: brew install bluez")
    print("For Ubuntu: sudo apt-get install libbluetooth-dev")
    BLUETOOTH_AVAILABLE = False

class BluetoothHandler:
    def __init__(self, device_name):
        self.device_name = device_name
        self.is_connected = False
        self.socket = None
        self.device_address = None
        
        # For demo purposes only (simulated values)
        self.simulated_mode = True  # Even if Bluetooth is available, we can simulate
        self.last_force_value = 0
    
    def discover_devices(self):
        """
        Discover nearby Bluetooth devices.
        Returns a list of (device_address, device_name) tuples.
        """
        try:
            if self.simulated_mode:
                # Simulate finding the device
                print(f"Simulating discovery of {self.device_name}")
                return [(f"00:11:22:33:44:{ord(self.device_name[-1]):02x}", self.device_name)]
            
            print("Scanning for Bluetooth devices...")
            nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
            print(f"Found {len(nearby_devices)} devices")
            return nearby_devices
        except Exception as e:
            print(f"Error discovering devices: {e}")
            return []
    
    def connect(self):
        """
        Connect to the ESP32 device.
        Returns True if connection is successful, False otherwise.
        """
        if self.is_connected:
            return True
        
        if self.simulated_mode or not BLUETOOTH_AVAILABLE:
            # Simulate connection
            print(f"Simulating connection to {self.device_name}")
            time.sleep(1)  # Simulate connection delay
            self.is_connected = True
            self.device_address = f"00:11:22:33:44:{ord(self.device_name[-1]):02x}"
            return True
        
        try:
            # Find the ESP32 in the list of available devices
            found_devices = self.discover_devices()
            target_address = None
            
            for addr, name in found_devices:
                if name == self.device_name:
                    target_address = addr
                    break
            
            if not target_address:
                print(f"Device {self.device_name} not found")
                return False
            
            # Connect to the device
            self.device_address = target_address
            self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.socket.connect((target_address, 1))  # Use RFCOMM channel 1
            self.is_connected = True
            print(f"Connected to {self.device_name} at {target_address}")
            return True
        
        except Exception as e:
            print(f"Error connecting to {self.device_name}: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """
        Disconnect from the ESP32 device.
        """
        if not self.is_connected:
            return
        
        if self.simulated_mode or not BLUETOOTH_AVAILABLE:
            # Simulate disconnection
            print(f"Simulating disconnection from {self.device_name}")
            self.is_connected = False
            return
        
        try:
            if self.socket:
                self.socket.close()
            self.is_connected = False
            print(f"Disconnected from {self.device_name}")
        except Exception as e:
            print(f"Error disconnecting from {self.device_name}: {e}")
    
    def get_force_reading(self):
        """
        Get the current force reading from the ESP32.
        Returns the force value in Newtons.
        """
        if not self.is_connected:
            return "N/A"
        
        if self.simulated_mode or not BLUETOOTH_AVAILABLE:
            # Generate simulated force readings from 0-1000 N
            change = random.uniform(-50, 50)
            self.last_force_value = max(0, min(1000, self.last_force_value + change))
            return round(self.last_force_value, 1)
        
        try:
            # Send command to request force reading
            self.socket.send("GET_FORCE")
            
            # Wait for response
            data = self.socket.recv(1024)
            
            # Parse the received data (assuming it's a string with the force value)
            force_value = float(data.decode().strip())
            return force_value
        
        except Exception as e:
            print(f"Error getting force reading from {self.device_name}: {e}")
            return "Error" 