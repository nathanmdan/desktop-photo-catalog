# CS361 Software Engineering I
# Downloader Microservice
# Programmers: Caleb Jacoby, Jessica Crews
# Modified by Nathan Dan to satisfy requirements of main program

"""
Save data provided by a client program to a file on the user's local device.

ZeroMQ messages sent to the service must be enclosed within a list.
Example: [ [ data, dest_path, filename ] ]

The shutdown signal "Q" must also be enclosed within a list: [ "Q" ]
"""

import time
import zmq

ADDRESS = "tcp://localhost:5558"

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
        
        export_details = message[0]
        column_names, data, dest_dir, name = export_details

        name = name.replace(" ", "-")
        column_names = ",".join(column_names)
    
        timestamp = time.strftime("%Y-%m-%d_%H%M%S")
        file_name = dest_dir + "/" + name + "-" + timestamp + ".csv"

        try:
            # Break out query rows into comma-separated values
            with open(file_name, "w") as out_file:
                out_file.write(column_names + "\n")
                for row in data:
                    row_str = ",".join(map(str, row)) + "\n"
                    out_file.write(row_str)

            socket.send_string("Export successful!")
        except Exception as error:
            print("Server error:", error)
            socket.send_string("Export failed.")

except KeyboardInterrupt as error:
    print("Keyboard interrupt detected. Closing service.")
    print(error)

except zmq.ZMQError as error:
    print("Server error:", error)

finally:
    context.destroy()
