import importlib

DRIVERS = {
    "barcode": "drivers.barcode_scanner",
    "printer": "drivers.printer_driver",
    "fingerprint": "drivers.fingerprint_device",
    "camera": "drivers.camera_device",
    "analyzer": "drivers.lab_analyzer"
}

class DeviceManager:

    def __init__(self):
        self.devices = []

    def load_driver(self, device_type):

        if device_type not in DRIVERS:
            return None

        module = importlib.import_module(DRIVERS[device_type])

        return module.Driver()

    def register_device(self, device_type):

        driver = self.load_driver(device_type)

        if driver:
            self.devices.append(driver)

            print("Device registered:", device_type)

import serial.tools.list_ports

def discover_serial_devices():

    devices = []

    ports = serial.tools.list_ports.comports()

    for p in ports:
        devices.append({
            "port": p.device,
            "description": p.description
        })

    return devices
