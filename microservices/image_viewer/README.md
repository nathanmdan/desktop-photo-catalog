# Communication Contract
1. The ImageViewer microservice receives a file path in the form of either a URL or a local file path and displays the image at that path.
2. To **REQUEST** data from the microservice, write a URL or local file path to the message.json file using the following format:
```
path_json = {'path': 'your/file/path/here.jpg', 'status': 'pending'}
with open(JSON_FILE, 'w') as file:
    json.dump(path_json, file)
```
3. To **RECEIVE** data from the microservice, i.e. a status update confirming whether the microservice displayed the image successfully or not, use the following format:
```
status_pending = True
print('Loading image...')
while status_pending:
    sleep(1)
    with open(JSON_FILE, 'r') as file:
        data = json.load(file)
        if data['status'] == 'success':
            status_pending = False
            print("Image loaded successfully!")
        elif data['status'] != 'pending':
            status_pending = False
            print('Image failed to load.')
            print(data['status'])
```
4. UML sequence diagram:
> <img width="593" height="488" alt="NathanDan_ImageViewer_UML" src="https://github.com/user-attachments/assets/192f7a3d-b4de-4b3e-aa0e-887d6cfe66b5" />
