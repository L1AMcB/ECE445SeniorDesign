import asyncio
from bleak import BleakScanner, BleakClient

# Nordic UART UUIDs
NUS_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_TX_CHAR = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
NUS_RX_CHAR = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# Notification callback
def notification_handler(sender, data):
    try:
        print(f"Received: {data.decode()}")
    except Exception as e:
        print(f"Error decoding data: {e}")
        print(f"Raw data: {data}")

async def main():
    print("Scanning for ESP32_1...")
    devices = await BleakScanner.discover(timeout=5.0)
    
    # Print all found devices
    print(f"Found {len(devices)} devices:")
    for d in devices:
        print(f"  {d.name or 'Unknown'}: {d.address}")
    
    # Find our device
    device = next((d for d in devices if d.name == "ESP32_1"), None)
    if not device:
        print("ESP32_1 not found!")
        return
    
    print(f"Found ESP32_1 at {device.address}")
    
    # Connect to the device with timeout
    client = BleakClient(device.address)
    
    try:
        # Connect with longer timeout
        print("Connecting...")
        await client.connect(timeout=10.0)
        print("Connected!")
        
        # Print details about the connection
        print(f"Connected: {client.is_connected}")
        print(f"MTU size: {client.mtu_size}")
        
        # Print all services and characteristics
        print("\nDiscovering services...")
        for service in client.services:
            print(f"Service: {service.uuid}")
            for char in service.characteristics:
                print(f"  Characteristic: {char.uuid}, Props: {char.properties}")
        
        # Try to write to the RX characteristic
        print("\nSending test message...")
        await client.write_gatt_char(NUS_RX_CHAR, b"HELLO\n")
        print("Message sent")
        
        # Subscribe to notifications
        print("\nSubscribing to notifications...")
        await client.start_notify(NUS_TX_CHAR, notification_handler)
        print("Subscribed to notifications")
        
        # Send another message to trigger a response
        await client.write_gatt_char(NUS_RX_CHAR, b"TEST\n")
        
        # Keep the connection alive
        print("Waiting for notifications (Ctrl+C to exit)...")
        for i in range(60):  # Wait for 60 seconds max
            await asyncio.sleep(1)
            if i % 5 == 0:
                print(f"Still connected: {client.is_connected}")
                # Send a ping every 5 seconds
                await client.write_gatt_char(NUS_RX_CHAR, f"PING:{i}\n".encode())
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect
        if client.is_connected:
            await client.disconnect()
            print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())