import subprocess
import json

class DriverInstaller:

    def install_usb_driver(self, vendor_id, product_id):

        print("Searching driver for:", vendor_id, product_id)

        try:
            result = subprocess.check_output(
                ["lsusb", "-v"],
                stderr=subprocess.DEVNULL
            ).decode()

            if vendor_id in result and product_id in result:
                print("Device already supported by system")
                return True

        except:
            pass

        return False

    def install_printer_driver(self):

        print("Installing printer support...")

        subprocess.run(["sudo", "apt", "install", "-y", "cups"])

    def install_barcode_driver(self):

        print("Barcode scanners usually work as HID keyboard")

    def install_camera_driver(self):

        subprocess.run(["sudo", "apt", "install", "-y", "v4l-utils"])

    def install_fingerprint_driver(self):

        subprocess.run(["sudo", "apt", "install", "-y", "fprintd"])

    def install_smartcard_driver(self):

        subprocess.run(["sudo", "apt", "install", "-y", "pcscd"])
