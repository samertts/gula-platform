import ipaddress
import socket

from device_registry import save_devices
from drivers.registry import detect_device

# المنافذ الشائعة للأجهزة المخبرية
COMMON_PORTS = [5000, 4000, 3001, 2404, 10001]

NETWORK = "192.168.1.0/24"


def scan_ip(ip):

    for port in COMMON_PORTS:

        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)

            s.connect((str(ip), port))

            s.send(b"HELLO\n")

            data = s.recv(2048).decode(errors="ignore")

            driver = detect_device(data)

            if driver:

                print("Device found!")
                print("IP:", ip)
                print("Port:", port)
                print("Device:", driver.name)

                return {"ip": str(ip), "port": port, "device": driver.name}

            s.close()

        except:
            pass

    return None


def discover():

    net = ipaddress.ip_network(NETWORK)

    devices = []

    for ip in net.hosts():

        result = scan_ip(ip)

        if result:
            devices.append(result)

    return devices


if __name__ == "__main__":

    print("Scanning network for lab devices...")

    devices = discover()

    print("Found devices:")
    print(devices)

if __name__ == "__main__":

    print("Scanning network for lab devices...")

    devices = discover()

    save_devices(devices)

    print("Devices saved to registry")
