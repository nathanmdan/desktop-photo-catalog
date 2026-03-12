# A test program demonstrating the Image Viewer microservice

from time import sleep
import json

JSON_FILE = 'message.json'

print('\nHello! Enter the path for the image you would like to see.')
print('This path can be a web URL or a local file path on your computer.')
print('If entering a web URL, make sure that the path ends with ".jpg"\n')

while True:
    path = input('Path: ')
    path_json = {'path': path, 'status': 'pending'}

    with open(JSON_FILE, 'w') as file:
        json.dump(path_json, file)

    # Check JSON file for status update
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
    
    print("Enter another path, or quit with ctrl-c")
