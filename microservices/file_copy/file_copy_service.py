# CS361 Software Engineering I
# File Copy microservice
# Programmer: Nathan Dan

"""
Copy local files to a new location.

ZeroMQ messages sent to the service must be enclosed within a list.
Example: [ [ (src_path1, dest_path1), (src_path2, src_path2), ... ] ]

The shutdown signal "Q" must also be enclosed within a list: [ "Q" ]
"""

import shutil
import zmq

ADDRESS = "tcp://localhost:5557"

try:
    # Initialize ZeroMQ server to listen for requests
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(ADDRESS)

    while True:
        try:
            # Listen for request
            message = socket.recv_pyobj()
            # print("Received request from client.")
        except Exception as error:
            print("Server error:", error)
            context.destroy()

        # Close server if 'Quit' request received
        if message[0] == "Q":
            # print("Quit request received by server.")
            break
        
        paths = message[0]

        # Get list of tuples containing source and destination paths for
        # each file to be copied
        fail = False
        for path_pair in paths:
            # print("Path pair:", path_pair)
            src_path, dest_path = path_pair
            try:
                shutil.copy2(src_path, dest_path)
            except PermissionError as error:
                print("Copy cannot overwrite original files.")
                fail = True
            except Exception as error:
                print("Error occurred while copying files:", error)
                fail = True
        if fail:
            socket.send_string("Copy failed.")
        else:
            socket.send_string("Copy successful!")

except KeyboardInterrupt as error:
    print("Keyboard interrupt detected. Closing service.")
    print(error)

except zmq.ZMQError as error:
    print("Server error:", error)

finally:
    context.destroy()
