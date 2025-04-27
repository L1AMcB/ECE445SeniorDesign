# bluetooth_handler.py  – BLE UART implementation (falls back to simulation)
import asyncio, threading, time, random, sys
from dataclasses import dataclass

# Nordic‑UART UUIDs
NUS_SERVICE      = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_RX_CHAR      = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
NUS_TX_CHAR      = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

try:
    from bleak import BleakScanner, BleakClient
    BLE_READY = True
except ImportError:
    BLE_READY = False
    print("Bleak not installed – using simulation.")

@dataclass
class _BleContext:
    client:      BleakClient = None
    last_force:  float       = None
    last_force2: float       = None
    rx_char:     str         = None
    tx_char:     str         = None

    # Add new method to get both force readings

class BluetoothHandler:
    """Public API identical to the old class: connect(), disconnect(), get_force_reading()"""
    def __init__(self, device_name: str):
        self.device_name   = device_name
        self.is_connected  = False
        self.simulated     = not BLE_READY
        self._ctx          = _BleContext()
        self._loop         = None   # background asyncio loop


    def get_both_force_readings(self):
        """Get readings from both force sensors"""
        if not self.is_connected:
            return "N/A", "N/A"
        if self.simulated:
            # Simple animation for both values
            val1 = getattr(self, "_sim_val1", 500)
            val1 = max(0, min(1500, val1 + random.uniform(-50, 50)))
            self._sim_val1 = val1
            
            val2 = getattr(self, "_sim_val2", 500)
            val2 = max(0, min(1500, val2 + random.uniform(-50, 50)))
            self._sim_val2 = val2
            
            return round(val1, 1), round(val2, 1)

        # BLE path: ask for one reading and wait for notification
        future = asyncio.run_coroutine_threadsafe(
            self._get_both_forces_ble(), self._loop)
        try:
            return future.result(timeout=2)  # seconds
        except Exception as e:
            print(f"Error getting force readings: {e}")
            return "Timeout", "Timeout"

    async def _get_both_forces_ble(self):
        # Reset values
        self._ctx.last_force = None
        self._ctx.last_force2 = None
        
        # Send request
        try:
            await self._ctx.client.write_gatt_char(self._ctx.rx_char, b"GET_FORCE\n")
        except Exception as e:
            print(f"Error sending command: {e}")
            return "Error", "Error"

        # Wait for response
        for _ in range(20):  # 20 × 50 ms = 1 s max wait
            await asyncio.sleep(0.05)
            if self._ctx.last_force is not None:
                # Return both values, or second as None if not available
                return self._ctx.last_force, getattr(self._ctx.last_force2, None)
        return "Timeout", "Timeout"

    # ---------- public -----------
    def connect(self) -> bool:
        if self.is_connected:
            return True
        if self.simulated:
            self.is_connected = True
            return True

        # spin up background event‑loop thread once
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            threading.Thread(target=self._loop.run_forever, daemon=True).start()

        fut = asyncio.run_coroutine_threadsafe(self._async_connect(), self._loop)
        self.is_connected = fut.result(timeout=15)
        return self.is_connected

    def disconnect(self):
        if not self.is_connected:
            return
        if self.simulated:
            self.is_connected = False
            return

        fut = asyncio.run_coroutine_threadsafe(self._async_disconnect(), self._loop)
        fut.result(timeout=5)
        self.is_connected = False

    def get_force_reading(self):
        """Blocking call used by Tk thread → returns float or 'N/A'."""
        if not self.is_connected:
            return "N/A"
        if self.simulated:
            # simple animation
            val = getattr(self, "_sim_val", 500)
            val = max(0, min(1000, val + random.uniform(-50, 50)))
            self._sim_val = val
            return round(val, 1)

        # BLE path: ask for one reading and wait for notification
        future = asyncio.run_coroutine_threadsafe(
            self._get_force_ble(), self._loop)
        try:
            return future.result(timeout=2)     # seconds
        except Exception:
            return "Timeout"

    # ---------- asyncio internals ----------
    async def _async_connect(self) -> bool:
        # 1) scan for the device
        devices = await BleakScanner.discover(timeout=4.0)
        target = next((d for d in devices if d.name == self.device_name), None)
        if not target:
            print(f"{self.device_name} not found.")
            return False

        # 2) connect
        client = BleakClient(target.address)
        try:
            await client.connect(timeout=5.0)
        except Exception as e:
            print(f"BLE connect error: {e}")
            return False

        # 3) cache characteristics
        # The issue is here - get_services() returns a dict-like object, not a list of UUIDs
        services = await client.get_services()
        
        # Debugging: Print all services
        print(f"Services found on device {self.device_name}:")
        for service in services:
            print(f"  Service: {service.uuid}")
        
        # Check if our NUS service exists
        nus_service = None
        for service in services:
            if service.uuid.lower() == NUS_SERVICE.lower():
                nus_service = service
                break
                
        if not nus_service:
            print(f"NUS service ({NUS_SERVICE}) not found on device!")
            await client.disconnect()
            return False
        
        print(f"Found NUS service: {nus_service.uuid}")
        
        # Find the characteristic UUIDs
        rx_char = None
        tx_char = None
        for char in nus_service.characteristics:
            if char.uuid.lower() == NUS_RX_CHAR.lower():
                rx_char = char.uuid
            elif char.uuid.lower() == NUS_TX_CHAR.lower():
                tx_char = char.uuid
        
        if not rx_char or not tx_char:
            print("Required characteristics not found!")
            await client.disconnect()
            return False
            
        self._ctx.client = client
        self._ctx.rx_char = rx_char
        self._ctx.tx_char = tx_char
        self._ctx.last_force = None

        # 4) subscribe for notifications
        await client.start_notify(tx_char, self._notify_cb)
        print(f"Successfully connected to {self.device_name}")
        return True

    async def _async_disconnect(self):
        if self._ctx.client and self._ctx.client.is_connected:
            await self._ctx.client.disconnect()
        self._ctx = _BleContext()

    async def _get_force_ble(self) -> float:
        # send GET_FORCE\n and wait for one notification
        self._ctx.last_force = None
        print(f"Sending GET_FORCE command...")
        
        try:
            await self._ctx.client.write_gatt_char(self._ctx.rx_char, b"GET_FORCE\n")
            print("Command sent successfully")
        except Exception as e:
            print(f"Error sending command: {e}")
            return "Error"

        # wait until _notify_cb fills in the value
        print("Waiting for response...")
        for i in range(20):   # 20 × 50 ms = 1 s max wait
            await asyncio.sleep(0.05)
            if self._ctx.last_force is not None:
                print(f"Received response: {self._ctx.last_force}")
                return self._ctx.last_force
            if i % 4 == 0:  # Every ~200ms
                print(f"Still waiting... ({i*50} ms)")
        return "Timeout"

    def _notify_cb(self, _char_uuid, data: bytearray):
        try:
            # Data now comes as "force1,force2"
            values = data.decode().strip().split(',')
            if len(values) >= 1:
                self._ctx.last_force = float(values[0])
                # Store second value if available
                if len(values) >= 2:
                    self._ctx.last_force2 = float(values[1])
        except Exception as e:
            print(f"Error processing notification: {e}")
            pass