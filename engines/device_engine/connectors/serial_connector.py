import serial

class SerialConnector:

    def connect(self, port):

        return serial.Serial(
            port,
            baudrate=9600,
            timeout=1
        )
