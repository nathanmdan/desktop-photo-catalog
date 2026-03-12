# CS361 Software Engineering I
# Metadata Reader microservice
# Programmer: Nathan Dan

"""
Display an image from a URL or a local file path specified in a JSON file 
"""

from sys import exit
from time import sleep
import json
import requests
from requests.exceptions import *
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk

MAX_SIZE = (1280, 1280)
JSON_FILE = 'message.json'

while True:
    sleep(10)

    data = None
    with open(JSON_FILE, 'r') as file:
        try:
            # Parse JSON data into dict
            data = json.load(file)
        except:
            continue

    if data['path'] != '':
        # Get image path from dict
        file_path = data['path']

        # Create Tk GUI
        root = tk.Tk()
        root.title('Image Viewer')

        # Check whether path is a URL or a local path
        response = None
        try:
            response = requests.get(file_path)
        except (MissingSchema, InvalidSchema):
            # Path is not a URL
            pass
        except ConnectionError as error:
            print('A connection error occurred.')
            print(error)
            with open(JSON_FILE, 'w') as file:
                    data = {'path': '', 'status': error}
                    json.dump(data, file)
            continue

        
        image = None
        if response:
            # Path is a URL
            if response.status_code == 200:
                # If URL contains an image, load image as an Image object
                content_type = response.headers.get('Content-Type')
                if content_type == 'image/jpeg':
                    image = Image.open(BytesIO(response.content))
        else:
            try:
                # Path is a local file path
                image = Image.open(file_path)
            except FileNotFoundError as error:
                # Update status in JSON file
                with open(JSON_FILE, 'w') as file:
                    data = {'path': '', 'status': error}
                    json.dump(data, file)
                continue

        # Downscale image if size is greater than max_size
        image.thumbnail(MAX_SIZE)
        tk_image = ImageTk.PhotoImage(image)

        # Create label widget to view image
        label = tk.Label(root, image=tk_image)
        label.pack()
        label.image = tk_image

        # Update status in JSON file
        with open(JSON_FILE, 'w') as file:
            data = {'path': '', 'status': 'success'}
            json.dump(data, file)

        # Display image
        root.mainloop()
