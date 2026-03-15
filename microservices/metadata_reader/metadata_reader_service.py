# CS361 Software Engineering I
# Metadata Reader microservice
# Programmer: Nathan Dan

"""
Extract metadata from a local image file.
"""

import os
from PIL import Image, TiffImagePlugin
from PIL.ExifTags import TAGS
import zmq

ADDRESS = "tcp://localhost:5556"

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

        img_path = message[0]

        # Construct PIL image object to access metadata
        image = None
        image = Image.open(img_path)
        
        if image:
            metadata_basic = {}
            metadata_extended = {}
            metadata_all = {
                "metadata_basic": metadata_basic,
                "metadata_extended": metadata_extended
            }

            # Get absolute file path
            abs_path = os.path.abspath(img_path)

            # Get basic metadata
            metadata_basic["Filepath"] = abs_path
            metadata_basic["Filename"] = image.filename
            metadata_basic["Format"] = image.format
            metadata_basic["Format Description"] = image.format_description
            metadata_basic["Width"] = image.width
            metadata_basic["Height"] = image.height

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
            
            # Reply with metadata dict
            socket.send_pyobj(metadata_all)

except KeyboardInterrupt as error:
    print("Keyboard interrupt detected. Closing service.")
    print(error)

except zmq.ZMQError as error:
    print("Server error:", error)

finally:
    context.destroy()
