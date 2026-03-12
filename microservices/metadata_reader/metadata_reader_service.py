# CS361 Software Engineering I
# Metadata Reader microservice
# Programmer: Nathan Dan

"""
Extract metadata from local image file and write to JSON file.

File path and delivery status provided as JSON (message.json).
Metadata written to JSON (metadata.json) as two objects: metadata_basic and metadata_extended.
"""

import sys, os
from time import sleep
import json
from PIL import Image, TiffImagePlugin
from PIL.ExifTags import TAGS

MESSAGE_JSON = 'message.json'
METADATA_JSON = 'metadata.json'

while True:
    sleep(1)

    data = None
    with open(MESSAGE_JSON, 'r') as file:
        try:
            # Parse JSON data into dict
            data = json.load(file)
        except FileNotFoundError as error:
            continue
    
    if data and data['path'] != '':
        # Get image path from dict
        file_path = data['path']

        # Build PIL image object
        image = None
        try:
            image = Image.open(file_path)
        except FileNotFoundError as error:
            # Update status in JSON file
            with open(MESSAGE_JSON, 'w') as file:
                data = {'path': file_path, 'status': str(error)}
                json.dump(data, file, indent=4)
            continue
        
        metadata_basic = {}
        metadata_extended = {}
        metadata_all = {'metadata_basic': metadata_basic, 'metadata_extended': metadata_extended}

        # Get absolute file path
        abs_path = os.path.abspath(file_path)

        # Get basic metadata
        metadata_basic['Filepath'] = abs_path
        metadata_basic['Filename'] = image.filename
        metadata_basic['Format'] = image.format
        metadata_basic['Format Description'] = image.format_description
        metadata_basic['Width'] = image.width
        metadata_basic['Height'] = image.height

        # Get EXIF camera metadata if present
        exif = image.getexif()
        if exif:
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id)
                if isinstance(value, TiffImagePlugin.IFDRational):
                    metadata_extended[tag_name] = float(value)
                else:
                    metadata_extended[tag_name] = value
        
        # # PRINT METADATA FOR TROUBLESHOOTING
        # print('Metadata - Basic:')
        # for k, v in metadata_basic.items():
        #     print(f'{k}: {v}')
        # if metadata_extended.items():
        #     print()
        #     print('Metadata - Extended:')
        #     for k, v in metadata_extended.items():
        #         print(f'{k}: {v}')
        
        # Write metadata to Metadata JSON file
        with open(METADATA_JSON, 'w') as file:
            json.dump(metadata_all, file, indent=4)
        
        # Update Message JSON file
        with open(MESSAGE_JSON, 'w') as file:
            data = {'path': file_path, 'status': 'success'}
            json.dump(data, file, indent=4)
