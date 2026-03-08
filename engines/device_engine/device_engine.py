
import time
import usb.core

def scan_devices():
    print("Universal Device Engine started")

    while True:

        devices = usb.core.find(find_all=True)

        for dev in devices:
            print("Device detected:", dev.idVendor, dev.idProduct)

        time.sleep(10)

if __name__ == "__main__":
    scan_devices()
