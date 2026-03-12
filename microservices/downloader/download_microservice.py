# CS 361
# Caleb Jacoby & Jessica Crews
# Downloader Microservice
# Saves data provided by a client program to a file on the user's local device.

import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.REP)

socket.bind("tcp://localhost:2026")

while True:
    message = socket.recv()

    if message.decode() == 'Q':
        break

    timestamp = time.strftime("%Y-%m-%d_%H%M%S")
    file_name = "download_" + timestamp + ".txt"

    try:
        with open(file_name, 'w') as out_file:
            out_file.write(message.decode())

        socket.send_string("0")
    except:
        socket.send_string("1")

context.destroy()
