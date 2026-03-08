import serial

def listen(port):

    ser = serial.Serial(port, 9600, timeout=1)

    print("Listening on", port)

    while True:

        data = ser.readline()

        if data:

            print("DATA:", data.decode(errors="ignore"))
