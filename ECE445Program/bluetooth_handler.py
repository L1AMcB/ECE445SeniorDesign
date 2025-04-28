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
    time_since_last: int     = None
    time_since_hit: int      = None
    rx_char:     str         = None
    tx_char:     str         = None
    continuous_mode: bool    = False

class BluetoothHandler:
    """Public API identical to the old class: connect(), disconnect(), get_force_reading()"""
    def __init__(self, device_name: str):
        self.device_name   = device_name
        self.is_connected  = False
        self.simulated     = not BLE_READY
        self._ctx          = _BleContext()
        self._loop         = None   # background asyncio loop


    def get_both_force_readings(self):
        """Get readings from both force sensors and time since last message"""
        if not self.is_connected:
            return "N/A", "N/A", 0, 0

        # Return the last values received in continuous mode
        # If we don't have readings yet, wait a short time for them to come in
        if self._ctx.last_force is None:
            time.sleep(0.2)  # Short wait for initial readings
        return self._ctx.last_force or "N/A", self._ctx.last_force2 or "N/A", self._ctx.time_since_last or 0, self._ctx.time_since_hit or 0

    # ---------- public -----------
    def connect(self) -> bool:
        if self.is_connected:
            return True

        # spin up background event‑loop thread once
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            threading.Thread(target=self._loop.run_forever, daemon=True).start()

        fut = asyncio.run_coroutine_threadsafe(self._async_connect(), self._loop)
        self.is_connected = fut.result(timeout=15)
        
        # Start continuous readings if connected
        if self.is_connected and not self.simulated:
            fut = asyncio.run_coroutine_threadsafe(
                self._start_continuous_readings(), self._loop)
            fut.result(timeout=5)
            
        return self.is_connected

    def disconnect(self):
        if not self.is_connected:
            return


        # Stop continuous readings first
        if self._ctx.continuous_mode:
            fut = asyncio.run_coroutine_threadsafe(
                self._stop_continuous_readings(), self._loop)
            fut.result(timeout=5)

        # Now disconnect
        fut = asyncio.run_coroutine_threadsafe(self._async_disconnect(), self._loop)
        fut.result(timeout=5)
        self.is_connected = False

    def get_force_reading(self):
        """Blocking call used by Tk thread → returns float or 'N/A'."""
        if not self.is_connected:
            return "N/A"


        # Return the last value received in continuous mode
        # If we don't have a reading yet, wait a short time for it to come in
        if self._ctx.last_force is None:
            time.sleep(0.2)  # Short wait for initial readings
        return self._ctx.last_force or "N/A"

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
        self._ctx.last_force2 = None
        self._ctx.time_since_last = None
        self._ctx.time_since_hit = None
        self._ctx.continuous_mode = False

        # 4) subscribe for notifications
        await client.start_notify(tx_char, self._notify_cb)
        print(f"Successfully connected to {self.device_name}")
        return True

    async def _async_disconnect(self):
        if self._ctx.client and self._ctx.client.is_connected:
            await self._ctx.client.disconnect()
        self._ctx = _BleContext()
        
    async def _start_continuous_readings(self):
        """Start continuous force readings from the device"""
        if not self._ctx.client or not self._ctx.client.is_connected:
            return False
            
        try:
            # Send START_FORCE_READING command
            await self._ctx.client.write_gatt_char(self._ctx.rx_char, b"START_FORCE_READING\n")
            print(f"Started continuous readings for {self.device_name}")
            self._ctx.continuous_mode = True
            return True
        except Exception as e:
            print(f"Error starting continuous readings: {e}")
            return False
    
    async def _stop_continuous_readings(self):
        """Stop continuous force readings from the device"""
        if not self._ctx.client or not self._ctx.client.is_connected:
            return False
            
        try:
            # Send STOP_FORCE_READING command
            await self._ctx.client.write_gatt_char(self._ctx.rx_char, b"STOP_FORCE_READING\n")
            print(f"Stopped continuous readings for {self.device_name}")
            self._ctx.continuous_mode = False
            return True
        except Exception as e:
            print(f"Error stopping continuous readings: {e}")
            return False

    def _notify_cb(self, _char_uuid, data: bytearray):
        try:
            # Data now comes as "force1,force2,time_since_last,time_since_hit"
            values = data.decode().strip().split(',')
            if len(values) >= 1:
                self._ctx.last_force = float(values[0])
                # Store second value if available
                if len(values) >= 2:
                    self._ctx.last_force2 = float(values[1])
                # Store time since last send if available
                if len(values) >= 3:
                    self._ctx.time_since_last = int(values[2])
                # Store time since hit detection if available
                if len(values) >= 4:
                    self._ctx.time_since_hit = int(values[3])
                    if self._ctx.last_force > 200:  # Only print for significant force readings
                        print(f"[DEBUG] Received hit with time_since_last: {self._ctx.time_since_last}ms, time_since_hit: {self._ctx.time_since_hit}ms, forces: {self._ctx.last_force}, {self._ctx.last_force2}")
                else:
                    self._ctx.time_since_hit = 0
        except Exception as e:
            print(f"Error processing notification: {e}")
            pass