import serial.tools.list_ports

def detect_analyzers():

    analyzers = []

    ports = serial.tools.list_ports.comports()

    for p in ports:

        device = {
            "port": p.device,
            "name": p.description
        }

        analyzers.append(device)

    return analyzers

if __name__ == "__main__":

    devices = detect_analyzers()

    for d in devices:

        print("Analyzer detected:", d)
