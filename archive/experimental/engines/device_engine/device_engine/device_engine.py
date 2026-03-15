import serial
import requests
import os

PORTS=["/dev/ttyUSB0","/dev/ttyUSB1"]

def read_device(port):

    try:

        s=serial.Serial(port,9600,timeout=2)

        line=s.readline().decode()

        return line

    except:

        return None

def parse(line):

    if not line:

        return None

    parts=line.split(",")

    return {

        "test":parts[0],
        "value":parts[1]

    }

def send(data):

    if not data:

        return

    requests.post(
        "http://localhost:8000/results",
        json=data
    )

def monitor():

    while True:

        for p in PORTS:

            line=read_device(p)

            data=parse(line)

            send(data)

if __name__=="__main__":

    monitor()
