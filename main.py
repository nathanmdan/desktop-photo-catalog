# CS361 Course Project: Desktop Photo Catalog
# Author: Nathan Dan

import os, sys, time, subprocess
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import mysql.connector
import config   # MySQL database credentials
import zmq

def zmq_timeout_handler(wait_time):
    """
    Poll response from ZeroMQ server.
    If no response after n milliseconds, close main program.
    """

    events = socket.poll(wait_time)
    if events == 0:
        print("No response from server. Please investigate.\n")
        time.sleep(1)
        close_zmq(servers)
        sys.exit(1)


def list_albums():
    """ List the names of all albums in the catalog """

    # Query database for all albums and save as list
    cursor.execute("SELECT * FROM Albums")
    albums = cursor.fetchall()

    # Display all albums in catalog
    print( \
            "\nAlbums" \
            "\n------"
            )
    for album in albums:
        album_name = album[1]
        print(album_name)
    print("\n")
    
    return albums


def get_album(album_name, albums):
    """ Check if album exists. Returns album if so. """

    # Query database for all albums and save as list
    cursor.execute("SELECT * FROM Albums")
    albums = cursor.fetchall()
    
    for album in albums:
        if album[1] == album_name:
            return album
    
    print("Album not found. Please try again.")
    time.sleep(1)


def show_photo_tags(photo_id, tag_label):
    """ Display a photo's descriptive tags in a Tkinter window """

    query = ("SELECT Tags.name FROM PhotoTags\n"
             "LEFT JOIN Tags ON PhotoTags.tagID = Tags.tagID\n"
             "WHERE PhotoTags.photoID = %s;")
    params = (photo_id,)
    cursor.execute(query, params)
    photo_tags_rows = cursor.fetchall()

    # Unpack tuples in rows and concatenate tags into a string
    tags_list = [tag[0] for tag in photo_tags_rows]
    tags_str = ", ".join(tags_list)

    # Update tag_text label to show correct tags
    tag_label.config(text=f"Tags: {tags_str}")


def show_metadata(photo_id, metadata_keys_label, metadata_values_label):
    """ Display a photo's metadata in a Tkinter window """

    # Get photo's filename and path
    query = ("SELECT name, path FROM Photos\n"
             "WHERE photoId = %s;")
    params = (photo_id,)
    cursor.execute(query, params)
    query_results = cursor.fetchall()

    # Unpack name and path from row list
    photo_name, photo_path = query_results[0]

    # Call Metadata Reader microservice to get current photo's metadata
    socket.connect(METADATA_READER_ADDR)
    # print("Sending a request to Metadata Reader microservice...")

    data = [photo_name, photo_path]
    socket.send_pyobj(data)

    # Handle microservice hangups
    zmq_timeout_handler(2000)

    # Decode reply from server
    message = socket.recv_pyobj()
    # print(f"Server sent back a reply.")

    # Disconnect from server
    socket.disconnect(METADATA_READER_ADDR)
    
    metadata_dict = message
    metadata_basic = metadata_dict['metadata_basic']
    metadata_extended = metadata_dict['metadata_extended']

    # Convert metadata dicts to key and value strings for Tkinter labels
    metadata_basic_keys = ""
    metadata_basic_values = ""
    for key, value in metadata_basic.items():
        metadata_basic_keys = metadata_basic_keys + str(key) + "\n"
        metadata_basic_values = metadata_basic_values + str(value) + "\n"

    metadata_extended_keys = ""
    metadata_extended_values = ""
    for key, value in metadata_extended.items():
        metadata_extended_keys = metadata_extended_keys + str(key) + "\n"
        metadata_extended_values = metadata_extended_values + str(value) + "\n"

    metadata_keys = metadata_basic_keys + metadata_extended_values
    metadata_values = metadata_basic_values + metadata_extended_values
    
    metadata_keys_label.config(text=metadata_keys)
    metadata_values_label.config(text=metadata_values)


def _photo_viewer_next(labels, photo_list, photo_id_name_list):
    global photo_index

    photo_label, metadata_keys_label, metadata_values_label, tag_label = labels

    if photo_index < (len(photo_list) - 1):
        photo_index += 1
        photo_label.config(image=photo_list[photo_index])
    else:
        photo_index = 0
        photo_label.config(image=photo_list[photo_index])
    
    photo_id = photo_id_name_list[photo_index][0]
    show_photo_tags(photo_id, tag_label)
    show_metadata(photo_id, metadata_keys_label, metadata_values_label)


def _photo_viewer_prev(labels, photo_list, photo_id_name_list):
    global photo_index

    photo_label, metadata_keys_label, metadata_values_label, tag_label = labels

    if photo_index > 0:
        photo_index -= 1
        photo_label.config(image=photo_list[photo_index])
    else:
        photo_index = len(photo_list) - 1
        photo_label.config(image=photo_list[photo_index])

    photo_id = photo_id_name_list[photo_index][0]
    show_photo_tags(photo_id, tag_label)
    show_metadata(photo_id, metadata_keys_label, metadata_values_label)


def photo_viewer(album_name):
    """ Display album photos with file info and next/previous navigation """

    global photo_index

    window = tk.Tk()
    window.title(album_name)
    window.geometry("800x800")
    window.attributes("-topmost", True)

    # Query all photos in album
    query = ("SELECT photoID, Photos.name, path FROM Photos\n"
             "LEFT JOIN Albums ON Photos.albumID = Albums.albumID\n"
             "WHERE Albums.name = %s;")
    params = (album_name,)
    cursor.execute(query, params)
    query_results = cursor.fetchall()

    # Make a list of all photo objects for navigation
    photo_list = []

    # Make a list of all '(photo ID, photo name)' tuples so that the ID
    # and name will always match the current photo in the viewer via the
    # 'photo_index' global variable.
    photo_id_name_list = []

    # Open images and store in list
    for row in query_results:
        photoID, name, path = row
        photo_id_name_list.append((photoID, name))

        # Call Image Viewer microservice to render PIL Image from path
        socket.connect(IMAGE_VIEWER_ADDR)
        # print("Sending a request to Image Viewer microservice...")
        data = [path]
        socket.send_pyobj(data)

        # Handle microservice hangups
        zmq_timeout_handler(2000)

        # Get reply from server
        message = socket.recv_pyobj()
        # print(f"Server sent back a reply.")

        # Error handling: Photo not found
        if type(message) == FileNotFoundError:
            print(
                "\n" \
                "Error: Photo(s) not found. Files may have moved after " \
                "being added to your catalog.\n" \
                "Please restore all files to their original paths.")
            window.destroy()
            time.sleep(2)
            return

        img_pil = message
        
        # Disconnect from server
        socket.disconnect(IMAGE_VIEWER_ADDR)

        # Create Tk PhotoImage from PIL Image and add to list of album photos
        img_tk = ImageTk.PhotoImage(img_pil)
        photo_list.append(img_tk)
        
    # Make viewer UI
    photo_frame = tk.Frame(window, bg="#444444", width=800, height=800)
    photo_frame.pack(fill="both", expand=True)
    photo_label = tk.Label(photo_frame, image=photo_list[photo_index])
    photo_label.pack(expand=True)
    
    # Unpack current photo ID and photo name from tuple.
    # 'photo_name' is not currently being used, but could be used to add the
    # filename beneath the current photo.
    photo_id, photo_name = photo_id_name_list[photo_index]

    # Add Metadata window to photo viewer
    metadata_frame = tk.Frame(window)
    metadata_frame.pack(side=tk.BOTTOM)
    metadata_keys_label = tk.Label(
        metadata_frame, text="", justify=tk.RIGHT
    )
    metadata_values_label = tk.Label(
        metadata_frame, text="", justify=tk.LEFT
    )
    metadata_keys_label.pack(side=tk.LEFT, padx=10, pady=10)
    metadata_values_label.pack(side=tk.RIGHT, padx=10, pady=10)

    # Populate Metadata window with current photo's metadata
    show_metadata(photo_id, metadata_keys_label, metadata_values_label)

    # Add Tags window to photo viewer
    tag_frame = tk.Frame(window)
    tag_frame.pack(side=tk.BOTTOM)
    tag_label = tk.Label(tag_frame, text="")
    tag_label.pack()
    
    # Populate Tags window with current photo's tags
    show_photo_tags(photo_id, tag_label)

    # Add a text entry box for adding tags to the current photo.
    # If the tag doesn't exist, create it.
    add_tag_frame = tk.Frame(window)
    add_tag_frame.pack(side=tk.BOTTOM)
    add_tag_label = tk.Label(add_tag_frame, text="Add a tag: ")
    add_tag_label.pack()
    tag_entry = tk.Entry(add_tag_frame)
    tag_entry.pack()

    # Add confirmation button
    tk.Button(
        add_tag_frame, text="Add", command=lambda: add_tag_to_photo(
            photo_id_name_list, tag_entry, tag_label
        )
    ).pack(side=tk.RIGHT)

    # Add next/previous buttons
    button_frame = tk.Frame(window)
    button_frame.pack(side=tk.BOTTOM)
    labels = [
        photo_label, metadata_keys_label, metadata_values_label, tag_label
    ]
    tk.Button(
        button_frame, text="Next", command=lambda: _photo_viewer_next(
            labels, photo_list, photo_id_name_list
        )
    ).pack(side=tk.RIGHT)
    tk.Button(
        button_frame, text="Previous", command=lambda: _photo_viewer_prev(
            labels, photo_list, photo_id_name_list
        )
    ).pack(side=tk.LEFT)

    window.mainloop()


def import_photos(album_name):
    """ Import photo(s) into catalog """

    # Check if album exists
    album = get_album(album_name, albums)
    if album:
        album_id = album[0]

        # Use file browser to select photo(s) for import
        window = tk.Tk()
        window.title("Import Photos")
        window.attributes("-topmost", True)
        window.withdraw()

        image_paths = filedialog.askopenfilenames(
            parent=window,
            initialdir=os.getcwd(),
            title="Select Images to Import"
            )
        
        window.destroy()
        
        successful_imports = 0
        for i in range(len(image_paths)):
            # Create image object from path
            try:
                image = Image.open(image_paths[i])
                name = image.filename.split('/')[-1]
                photo_params = (name, image_paths[i], album_id, 0)
            except Image.UnidentifiedImageError as error:
                print(
                    f"\n{name} is in an incompatible file format. \
                    Skipping photo."
                )
                continue
            
            # Add photo to catalog
            try:
                print(f"Importing photo {i + 1} of {len(image_paths)}...")
                cursor.callproc("sp_import_photo", photo_params)
                cnx.commit()
                successful_imports += 1
            except mysql.connector.Error as error:
                print("Import cancelled due to error:", error)
                print("Please try again.")
                time.sleep(1)
                return
        
        failed_imports = len(image_paths) - successful_imports
        plural = "s" if successful_imports > 1 else ""

        print(f"\n{successful_imports} photo{plural} added to catalog.")
        if successful_imports != len(image_paths):
            plural = "" if failed_imports == 1 else "s"
            print(f"{failed_imports} photo{plural} failed to import.")
        
        time.sleep(1)


def create_album(album_params):
    """ Create new photo album """

    try:
        cursor.callproc('sp_create_album', album_params)
        cnx.commit()
        print(f"\nNew album '{album_params[0]}' created.")
        time.sleep(1)
    except mysql.connector.Error as error:
        print("\nThere was a problem creating your album.")
        print(error)
        time.sleep(1)


def create_tag(tag_params):
    """ Create new descriptive tag """

    try:
        cursor.callproc("sp_create_tag", tag_params)
        cnx.commit()
        print(f"\nNew tag '{tag_params[0]}' created.")
        time.sleep(1)
    except mysql.connector.Error as error:
        print("\nThere was a problem creating your tag.")
        print(error)
        time.sleep(1)


def add_tag_to_photo(photo_id_name_list, tag_entry, tag_label):
    """ Add a descriptive tag to a photo """

    # Store user entry text into variable
    tag_name = tag_entry.get()

    # query database for tagID
    query = ("SELECT tagID FROM Tags\n"
             "WHERE name = %s")
    params = (tag_name,)
    cursor.execute(query, params)
    tag_id_row = cursor.fetchall()

    # If tag does not exist, create it. Then recursively call
    # current function to get its ID.
    if not tag_id_row:
        print(f"'{tag_name}' tag does not exist. Creating now.")
        create_tag((tag_name,0))
        add_tag_to_photo(photo_id_name_list, tag_entry, tag_label)
        return

    # Proceed to add tag to photo
    try:
        tag_id = tag_id_row[0][0]
        photo_id, photo_name = photo_id_name_list[photo_index]
        photo_tag_params = (photo_id, tag_id, 0)
        cursor.callproc("sp_add_photo_tag", photo_tag_params)
        cnx.commit()
        print(f"'{tag_name}' tag added to photo: {photo_name}")
        
        # Update tag list in photo viewer
        show_photo_tags(photo_id, tag_label)

        # Clear text entry box
        tag_entry.delete(0, tk.END)

    except mysql.connector.Error as error:
        print("There was a problem tagging your photo.")
        print(error)


def copy_photos(src_paths, dest_dir):
    """ Copy photos at different paths into a single location """
    
    path_pairs = []
    for path in src_paths:
        filename = path.split('/')[-1]
        dest_path = f"{dest_dir}/{filename}"
        path_pair = (path, dest_path)
        path_pairs.append(path_pair)

    # Call File Copy microservice to copy photos to new location
    socket.connect(FILE_COPY_ADDR)
    # print("Sending a request to File Copy microservice...")
    data = [path_pairs]
    socket.send_pyobj(data)

    # Handle microservice hangups
    zmq_timeout_handler(2000)

    # Decode reply from server
    message = socket.recv()
    print("\n" + message.decode())
    time.sleep(1)

    # Disconnect from server
    socket.disconnect(FILE_COPY_ADDR)


def export_catalog(dest_dir):
    """ Export catalog information to a .csv file """

    # Query v_all_photos for a clean table of essential catalog information  
    query = ("SELECT * FROM v_all_photos;")
    cursor.execute(query)
    column_names = cursor.column_names   
    query_results = cursor.fetchall()
    
    name = "My Catalog"
    export_details = [column_names, query_results, dest_dir, name]
    
    # Call Downloader microservice to export catalog info to .csv file
    socket.connect(DOWNLOADER_ADDR)
    # print("Sending a request to Downloader microservice...")
    data = [export_details]
    socket.send_pyobj(data)

    # Handle microservice hangups
    zmq_timeout_handler(2000)

    # Decode reply from server
    message = socket.recv()
    print("\n" + message.decode())
    time.sleep(1)

    # Disconnect from server
    socket.disconnect(DOWNLOADER_ADDR)


def close_zmq(servers):
    """ Close connection to ZeroMQ servers """

    global socket
    server = None
    print("Closing microservices...\n")
    time.sleep(1)
    try:
        for server in servers:
            print("Stopping server:", server)
            socket.close()
            socket = context.socket(zmq.REQ)
            socket.connect(server)
            quit_code = ["Q"]
            socket.send_pyobj(quit_code)
            time.sleep(0.1)
        
        print("\nAll microservices stopped.\n")
        socket.close()

    except zmq.ZMQError as error:
        print(f"Error while stopping server {server}:", error)

    finally:
        context.destroy()


##########################################
##                                      ##
##          BEGIN MAIN PROGRAM          ##
##                                      ##
##########################################

# ZeroMQ server addresses
IMAGE_VIEWER_ADDR       = "tcp://localhost:5555"
METADATA_READER_ADDR    = "tcp://localhost:5556"
FILE_COPY_ADDR          = "tcp://localhost:5557"
DOWNLOADER_ADDR         = "tcp://localhost:5558"

# Create MySQL connection and cursor for querying catalog database
cnx = mysql.connector.connect(**config.config)
cursor = cnx.cursor()

#############################################################
##                                                         ##
##  MYSQL PROCEDURE CALLS REFERENCE:                       ##
##  'CALL sp_import_photo(?, ?, ?, ?, ?, @new_id);'        ##
##  'CALL sp_create_album(?, ?, @new_id);'                 ##
##  'CALL sp_create_tag(?, @new_id);'                      ##
##  'CALL sp_add_photo_tag(?, ?, @new_id);'                ##
##                                                         ##
#############################################################

# Prep ZeroMQ client for microservice communication
context = zmq.Context()
socket = context.socket(zmq.REQ)
servers = [
    IMAGE_VIEWER_ADDR,
    METADATA_READER_ADDR,
    FILE_COPY_ADDR,
    DOWNLOADER_ADDR
]

# Run microservices in background
microservices = [
    ".\\microservices\\image_viewer\\image_viewer_service.py",
    ".\\microservices\\metadata_reader\\metadata_reader_service.py",
    ".\\microservices\\file_copy\\file_copy_service.py",
    ".\\microservices\\downloader\\downloader_service.py"
]

try:
    for microservice in microservices:
            subprocess.Popen(["python", microservice])
except Exception as error:
    print("There was a problem starting the microservice servers.", error)
    print("Exiting the program.")
    sys.exit(1)

# Welcome message
welcome = \
"\n" \
"**Welcome to your photo catalog!**" \
"\n" \
"Stay organized with photo albums and easily find the photos you're " \
    "looking for with custom descriptive tags." \
"\n" \
"Your catalog is a local database, so your files remain safe and " \
    "untouched on your computer, and nothing is uploaded to the cloud." \
"\n\n" \
"Albums - Organize your photos with albums. Create albums with the " \
    "'new album' command. Albums do not move the image files on your " \
    "computer." \
"\n" \
"When importing photos, you'll be asked to choose an album to import into. " \
    "If no albums are found, you will be asked to create one." \
"\n\n" \
"Gallery - Choose an album to view and its contents will display in a photo " \
    "viewer on your desktop." \
"\n" \
"Step through the album's photos and add descriptive tags to use when " \
    "searching your catalog." \
"\n\n" \
"Tags - Make your catalog searchable with custom descriptive tags." \
"\n" \
"Create new tags with the 'new tag' command, or create tags directly in the " \
    "gallery photo viewer." \
"\n\n" \
# "Search (coming soon...) - Search across your entire catalog by tags." \
# "\n" \
# "Add the results of your search to a new album, or export the image files " \
#     "themselves to a single location on your computer for easier sharing " \
#     "with others." \
# "\n"
print(welcome)

# Enclose main loop within a try-except block to handle KeyboardInterrupts
try:
    while True:
        # Show all available commands
        commands = \
        "\nCommand              Description" \
        "\n--------------------------------" \
        "\n" \
        "import                 import photos into an album in your catalog" \
        "\n" \
        "gallery                view your photos" \
        "\n" \
        "new album              add a new album to your catalog" \
        "\n" \
        "new tag                create new descriptive tags for your photos" \
        "\n" \
        "copy album photos      copy all photos in an album to a single "\
                                "folder on your hard drive" \
        "\n" \
        "export catalog         export your catalog information as a .csv " \
                                "spreadsheet" \
        "\n" \
        "exit                   exit the program" \
        "\n"
        # "search                 search your catalog using descriptive tags"
        # #                       # yet to be implemented
        print(commands)

        # Get input from user
        command_input = input("Enter a command: ")
        
        ## IMPORT PHOTOS ##
        if command_input == "import":
            # Show all album names
            albums = list_albums()

            if len(albums) == 0:
                print(f"You don't have any albums yet. Let's make one.")
                album_input = input("Enter the name of your new album: ")
                album_params = (album_input, None, 0)
                create_album(album_params)
                import_photos(album_input)
            else:
                # Choose album to import photo(s) into
                album_input = input(
                    "Select an album for your imported photos: "
                )
                import_photos(album_input)

        ## VIEW ALBUM PHOTOS ##
        elif command_input == "gallery":
            albums = list_albums()
            if len(albums) == 0:
                print(
                    "No albums in catalog. " \
                    "Choose 'new album' to make your first album."
                )
                time.sleep(2)
            else:
                album_input = input("Enter the name of the album to view: ")
                album = get_album(album_input, albums)
                if album:
                    photo_index = 0
                    photo_viewer(album_input)

        ## CREATE NEW ALBUM ##
        elif command_input == "new album":
            new_album_input = input("Enter the name of your new album: ")
            album_params = (new_album_input, None, 0)
            create_album(album_params)

        ## CREATE NEW TAG ##
        elif command_input == "new tag":
            new_tag_input = input("Enter the name of your new tag: ")
            tag_params = (new_tag_input, 0)
            create_tag(tag_params)

        ## SEARCH BY TAGS (USING "SEARCH" MICROSERVICE) ##
        # Yet to be implemented
        elif command_input == "search":
            pass

        ## COPY ALBUM PHOTOS ##
        elif command_input == "copy album photos":
            albums = list_albums()
            album_input = input("Enter the name of the album to copy: ")
            album = get_album(album_input, albums)
            if album:
                album_name = album[1]

                # Query all photos in album
                query = ("SELECT photoID, Photos.name, path FROM Photos\n"
                        "LEFT JOIN Albums ON Photos.albumID = Albums.albumID\n"
                        "WHERE Albums.name = %s;")
                params = (album_name,)
                cursor.execute(query, params)
                query_results = cursor.fetchall()

                # Get photo paths
                photo_paths = []
                for row in query_results:
                    photoID, name, path = row
                    photo_paths.append((path))
                
                # Use file browser to select copy destination
                window = tk.Tk()
                window.title("Copy Photos")
                window.attributes("-topmost", True)
                window.withdraw()

                print("Select a destination for your photos.")
                dest_dir = filedialog.askdirectory(
                    parent=window,
                    initialdir=os.getcwd(),
                    title="Copy Photos to..."
                )
                window.destroy()

                copy_photos(photo_paths, dest_dir)

        ## EXPORT CATALOG ##
        elif command_input == "export catalog":
            # Use file browser to select export location
            window = tk.Tk()
            window.title("Export Catalog")
            window.attributes("-topmost", True)
            window.withdraw()
            
            print("Select a destination for your catalog file.")
            dest_dir = filedialog.askdirectory(
                initialdir=os.getcwd(),
                title="Export Catalog to..."
                )
            export_catalog(dest_dir)

        ## EXIT PROGRAM ##
        elif command_input == "exit":
            print("\nClosing the program. Goodbye!\n\n")
            time.sleep(1)

            # Close connection to MySQL database
            cnx.close()

            # Close connections to ZeroMQ servers
            close_zmq(servers)

            sys.exit(0)
                
        else:
            print("Invalid input. Please try again.")
            time.sleep(1)

except KeyboardInterrupt:
    print("Exiting program.")
    close_zmq(servers)
    sys.exit(1)
