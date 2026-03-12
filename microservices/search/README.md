Microservice Description
The Search Microservice is a service designed to filter travel itinerary data from a JSON data file.It uses ZeroMQ to allow both web and dektop apps to query specific information. 
It can search for both text keywords and images. 

How to programmatically REQUEST data:
To request data, the calling program must create a ZeroMQ request socket and connect to the microservices address. The request must be sent as JSON string containing query and a target (text or image).

const zmq = require ("zeromq");
async function startMicroservice(query, target) {
    const sock = new zmq.Reply();
    //Connect to microservice address
    sock.connect("tcp://localhost:5555")
    //Request as JSON string
    const payload = JSON.stringify({ query: query, target: target });
    //Send the request
    await sock.send(payload)

How to programmatically RECEIVE data:
After request, program must wait to receive a response from the socekt. Microservice returns a JSON string containing an array of matched results and a count of those matches. 

 async function response(sock) {
   //wait for reply
   const [resultWait] = await sock.receive();
   //convert JSON
   const data = JSON.parse(resultWait.toString());
   //return data.results;

UML Sequence Diagram
<img width="686" height="370" alt="image" src="https://github.com/user-attachments/assets/b56e1352-1163-492b-a65c-cd6d34c39ba2" />

    
