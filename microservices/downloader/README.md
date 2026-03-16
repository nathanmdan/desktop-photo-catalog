# Downloader Microservice

This microservice saves data provided by a client program to a file on the user's local device.

### How to send a request

You must add this following code to your main program:
```
import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)

socket.connect("tcp://localhost:2026")
```
You may then send a string or a JSON string to the microservice to be downloaded using one of the following commands:
```
socket.send_string("example")

socket.send_json({"example": value})
```
Of course, you may first store the data in a variable instead:
```
my_string = "please download me"
socket.send_string(my_string)

my_json = {"save": me}
socket.send_json(my_json)
```
The microservice will then save the data in a text file in the folder from which the microservice is running.

### How to receive a response

In addition to saving a local file, the microservice will send back to the client program a response code: '0' for successful; '1' for unsuccessful.

You may process the microservice's response code with the following command:
```
message = socket.recv()
code = message.decode()
```

### Additional information

To end the microservice from your main program, send it the string 'Q':
```
socket.send_string('Q')
```

### UML Sequence Diagram

![Downloader UML Sequence Diagram](downloader_uml.png)
