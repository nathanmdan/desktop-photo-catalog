const fs = require('fs/promises');
const express = require ('express');
const zmq = require ("zeromq");

const app = express();
app.use(express.json());

const FILE_PATH = './data.json';

async function startMicroservice(query, target) {
    const sock = new zmq.Reply();

    try{
        await sock.bind("tcp://127.0.0.1:5556");
        console.log("Microservice active on port 5556");

        for await (const [msg] of sock) {
            console.log("Receive request")
            const { query, target } = JSON.parse(msg.toString());
            const rawData = await fs.readFile(FILE_PATH, 'utf8');
            const data = JSON.parse(rawData);
 
            const results = data.filter(item => {
                const queryLower = query.toLowerCase();
            
                if (target === 'text') {
                    const searcheableText = (item.title + " " + JSON.stringify(item.itinerary)).toLowerCase();
                    return searcheableText.includes(queryLower);
                }

                if (target === 'image') {
                    return item.imageFile && item.imageFile.toLowerCase().includes(queryLower);
                }
                return false;
            });

            await sock.send( JSON.stringify({ results, count: results.length }));
        }
    } catch (err) {
        console.error ("Microservice Error:", err);
    }
}

startMicroservice();



