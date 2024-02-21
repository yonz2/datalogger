import asyncio
from bleak import BleakClient

device_address = "A4:C1:38:76:CC:05"  # Replace with your device's address
service_uuid = "0000ec88-0000-1000-8000-00805f9b34fb"  # Replace with your service UUID
characteristic_uuid = "your-characteristic-uuid"  # Replace with the correct characteristic UUID

""" 
characteristics:
handle: 0x0002, char properties: 0x12, char value handle: 0x0003, uuid: 00002a00-0000-1000-8000-00805f9b34fb
handle: 0x0004, char properties: 0x02, char value handle: 0x0005, uuid: 00002a01-0000-1000-8000-00805f9b34fb
handle: 0x0006, char properties: 0x02, char value handle: 0x0007, uuid: 00002a04-0000-1000-8000-00805f9b34fb
handle: 0x0009, char properties: 0x20, char value handle: 0x000a, uuid: 00002a05-0000-1000-8000-00805f9b34fb
handle: 0x000d, char properties: 0x02, char value handle: 0x000e, uuid: 00002a50-0000-1000-8000-00805f9b34fb
handle: 0x0010, char properties: 0x1a, char value handle: 0x0011, uuid: 494e5445-4c4c-495f-524f-434b535f2011
handle: 0x0014, char properties: 0x1a, char value handle: 0x0015, uuid: 494e5445-4c4c-495f-524f-434b535f2012
handle: 0x0018, char properties: 0x12, char value handle: 0x0019, uuid: 494e5445-4c4c-495f-524f-434b535f2013
handle: 0x001d, char properties: 0x16, char value handle: 0x001e, uuid: 00010203-0405-0607-0809-0a0b0c0d2b12

"""

async def main():
    async with BleakClient(device_address) as client:
        if client.is_connected:
            print(f"Connected to {device_address}")

            # Get services and print them (optional, for debugging)
            services = await client.get_services()
            print("Services:")
            for service in services:
                print(service)

            try:
                # Read the characteristic
                value = await client.read_gatt_char(characteristic_uuid)
                print(f"Received value: {value}")

            except Exception as e:
                print(f"Error: {e}")

        else:
            print("Failed to connect")

asyncio.run(main())
