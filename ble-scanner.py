import asyncio
from bleak import BleakScanner
import datetime

# Specify the MAC address of the device of interest
target_device_address = "A4:C1:38:76:CC:05"

# Function to handle discovered BLE devices
def detection_callback(device, advertisement_data):
    if device.address == target_device_address:
        log_data = f"{datetime.datetime.now()}: Device {device.address}, RSSI: {device.rssi}\n"
        log_data += "Advertisement Data:\n"

        # Process local name
        if advertisement_data.local_name:
            log_data += f"  Local Name: {advertisement_data.local_name}\n"

        # Process manufacturer data
        if advertisement_data.manufacturer_data:
            manufacturer_data_str = ', '.join(f'{k}: {v.hex()}' for k, v in advertisement_data.manufacturer_data.items())
            log_data += f"  Manufacturer Data: {manufacturer_data_str}\n"

        # Process service UUIDs
        if advertisement_data.service_uuids:
            service_uuids_str = ', '.join(advertisement_data.service_uuids)
            log_data += f"  Service UUIDs: {service_uuids_str}\n"
        
        print(log_data)
        with open("ble_devices_log.txt", "a") as file:
            file.write(log_data)

async def main():
    # Start the BLE scanner with the detection callback
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()

    # Run for a certain duration, you can adjust this
    await asyncio.sleep(30)
    await scanner.stop()

# Run the main function in the asyncio event loop
asyncio.run(main())

