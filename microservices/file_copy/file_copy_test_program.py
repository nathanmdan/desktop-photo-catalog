import sys, time
from pathlib import Path
import zmq

# Prep ZeroMQ client for microservice communication
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5557")

# Make path objects for test
file1_src_path = Path("source_folder/file1.txt")
file2_src_path = Path("source_folder/file2.txt")
file1_dest_path = Path("dest_folder/file1.txt")
file2_dest_path = Path("dest_folder/file12.txt")

# Make source and destination directories for test
file1_src_path.parent.mkdir(parents=True, exist_ok=True)
file2_src_path.parent.mkdir(parents=True, exist_ok=True)
file1_dest_path.parent.mkdir(parents=True, exist_ok=True)
file2_dest_path.parent.mkdir(parents=True, exist_ok=True)

# Make dummy files in source directory
file1_src_path.touch(exist_ok=True)
file2_src_path.touch(exist_ok=True)

data = [(file1_src_path, file1_dest_path), (file2_src_path, file2_dest_path)]

# Call File Copy microservice
print("Sending a request to File Copy microservice...")
data = [data]
socket.send_pyobj(data)

# # Handle microservice hangups
# events = socket.poll(2000)
# if events == 0:
#     print("No response from server. Please investigate.\n")
#     time.sleep(1)
#     sys.exit(1)

# Decode reply from server
message = socket.recv()
print(f"Server sent back: {message.decode()}")

# Close ZeroMQ server
quit_code = ["Q"]
socket.send_pyobj(quit_code)
