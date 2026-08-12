from analyzer_detector import detect_analyzers
from serial_listener import listen

def start():

    analyzers = detect_analyzers()

    if not analyzers:

        print("No analyzers found")
        return

    for a in analyzers:

        print("Connecting to:", a["port"])

        listen(a["port"])

if __name__ == "__main__":

    start()
