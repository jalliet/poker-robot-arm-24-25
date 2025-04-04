from bleak import BleakScanner
import asyncio

async def discover_devices():
    # Start scanning for nearby Bluetooth devices
    devices = await BleakScanner.discover()
    
    # Print the found devices and their MAC addresses
    if devices:
        print("Found devices:")
        for device in devices:
            print(f"Device Name: {device.name}, MAC Address: {device.address}")
    else:
        print("No Bluetooth devices found.")

# Run the scanner
asyncio.run(discover_devices())
