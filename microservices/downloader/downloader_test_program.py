import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:2026")

my_string = "please download me"
socket.send_string(my_string)

message = socket.recv()
code = message.decode()

print(code)
socket.send_string('Q')
