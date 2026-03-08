import subprocess
from driver_installer import DriverInstaller

installer = DriverInstaller()

def detect_usb_devices():

    devices = subprocess.check_output(["lsusb"]).decode().split("\n")

    found = []

    for d in devices:

        if d.strip():

            parts = d.split()

            vendor = parts[5].split(":")[0]
            product = parts[5].split(":")[1]

            found.append((vendor, product))

    return found

def auto_setup():

    devices = detect_usb_devices()

    for v, p in devices:

        print("Detected device:", v, p)

        installer.install_usb_driver(v, p)

if __name__ == "__main__":

    auto_setup()
