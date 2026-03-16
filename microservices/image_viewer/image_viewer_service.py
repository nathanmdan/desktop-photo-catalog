# Image Viewer microservice
# Programmers: Nathan Dan, Gabriela Aquino

"""
Generate a PhotoImage object for viewing in a Tkinter GUI.

ZeroMQ messages sent to the service must be enclosed within a list.
Example: [ "path/to/file.jpg" ]

The shutdown signal "Q" must also be enclosed within a list: [ "Q" ]
"""

from PIL import Image, ImageOps
import zmq

ADDRESS = "tcp://localhost:5555"

try:
    # Initialize ZeroMQ server to listen for requests
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(ADDRESS)

    while True:
        # Listen for request
        message = socket.recv_pyobj()
        # print("Received request from client.")

        # Close server if 'Quit' request received
        if message[0] == "Q":
            # print("Quit request received by server.")
            break
            
        img_path = message[0]

        # Generate and resize an Image object for Tkinter
        try:
            img_pil = Image.open(img_path)
            img_pil = ImageOps.contain(img_pil, (500, 500))

            # Reply with PhotoImage object
            socket.send_pyobj(img_pil)

        except FileNotFoundError as error:
            socket.send_pyobj(error)

except KeyboardInterrupt as error:
    print("Keyboard interrupt detected. Closing service.")
    print(error)

except zmq.ZMQError as error:
    print("Server error:", error)

finally:
    context.destroy()