# CS361 Course Project: Desktop Photo Catalog
# Author: Nathan Dan

import os, sys, time
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageOps
import mysql.connector
import config

def list_albums():
    """ Lists the names of all albums in the catalog """
    cursor.execute("SELECT * FROM Albums")

    # Make list of albums from query results
    albums = cursor.fetchall()

    # Show all albums in catalog
    print( \
            "\nAlbums" \
            "\n------"
            )
    for album in albums:
        album_name = album[1]
        print(album_name)
    print("\n")
    
    return albums


def show_photo_tags(photo_id, tag_label):
    """ Prints a list of the current photo's tags """
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


def _photo_viewer_next(photo_label, photo_list, photo_id_name_list, tag_label):
    global photo_index
    
    if photo_index < (len(photo_list) - 1):
        photo_index += 1
        photo_label.config(image=photo_list[photo_index])
    else:
        photo_index = 0
        photo_label.config(image=photo_list[photo_index])
    
    photo_id = photo_id_name_list[photo_index][0]
    show_photo_tags(photo_id, tag_label)


def _photo_viewer_prev(photo_label, photo_list, photo_id_name_list, tag_label):
    global photo_index

    if photo_index > 0:
        photo_index -= 1
        photo_label.config(image=photo_list[photo_index])
    else:
        photo_index = len(photo_list) - 1
        photo_label.config(image=photo_list[photo_index])

    photo_id = photo_id_name_list[photo_index][0]
    show_photo_tags(photo_id, tag_label)


def photo_viewer(album_name):
    """ Displays all photos in an album with next/previous navigation """
    global photo_index

    window = tk.Tk()
    window.title(album_name)
    window.geometry("800x800")

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

        # Render image objects from paths
        image = Image.open(path)
        image = ImageOps.contain(image, (600, 600))
        photo = ImageTk.PhotoImage(image)
        photo_list.append(photo)
        
    # Make viewer UI
    photo_frame = tk.Frame(window, bg="#444444", width=700, height=700)
    photo_frame.pack()
    photo_label = tk.Label(photo_frame, image=photo_list[photo_index])
    photo_label.pack()
    
    # Unpack current photo ID and photo name from tuple.
    # 'photo_name' is not currently being used, but could be used to add the
    # filename beneath the current photo.
    photo_id, photo_name = photo_id_name_list[photo_index]

    # Add tag list to photo viewer
    tag_frame = tk.Frame(window)
    tag_frame.pack(side=tk.BOTTOM)
    tag_label = tk.Label(tag_frame, text="")
    tag_label.pack()
    
    # Update tag list with current photo's tags
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
    tk.Button(add_tag_frame, text="Add", command=lambda: add_tag_to_photo(photo_id_name_list, tag_entry, tag_label)).pack(side=tk.RIGHT)

    # Add next/previous buttons
    button_frame = tk.Frame(window)
    button_frame.pack(side=tk.BOTTOM)
    tk.Button(button_frame, text='Next', command=lambda: _photo_viewer_next(photo_label, photo_list, photo_id_name_list, tag_label)).pack(side=tk.RIGHT)
    tk.Button(button_frame, text='Previous', command=lambda: _photo_viewer_prev(photo_label, photo_list, photo_id_name_list, tag_label)).pack(side=tk.LEFT)

    window.mainloop()


def import_photos(album_name):
    """ Imports photo(s) into catalog """
    # Check if album exists
    albums = list_albums()
    album_found = False
    for album in albums:
        if album_found == False:
            album_id, album_name, album_folder = album
            if album_input == album_name:
                album_found = True

                # Use file browser to select photo(s) for import
                image_paths = filedialog.askopenfilenames(
                    initialdir=os.getcwd(),
                    title="Select Images to Import"
                    )
                
                for path in image_paths:
                    try:
                        image = Image.open(path)
                        name = image.filename.split('/')[-1]
                        photo_params = (name, path, album_id, 0)
                    except Image.UnidentifiedImageError as error:
                        print("\nIncompatible file format. Only image files are supported.")
                        print("Please try again.")
                        time.sleep(1)
                        return
                    
                    try:
                        cursor.callproc('sp_import_photo', photo_params)
                        cnx.commit()
                        print("Import successful!")
                        time.sleep(1)
                    except mysql.connector.Error as error:
                        print("There was a problem importing your photo(s).")
                        print(error)
                        time.sleep(1)

    if album_found == False:
        print("Album not found. Please try again.")
        time.sleep(1)


def create_album(album_params):
    """ Creates new photo album """
    try:
        cursor.callproc('sp_create_album', album_params)
        cnx.commit()
        print(f"New album '{album_params[0]}' created.")
        time.sleep(1)
    except mysql.connector.Error as error:
        print("There was a problem creating your album.")
        print(error)
        time.sleep(1)


def create_tag(tag_params):
    """ Creates new descriptive tag """
    try:
        cursor.callproc('sp_create_tag', tag_params)
        cnx.commit()
        print(f"New tag '{tag_params[0]}' created.")
        time.sleep(1)
    except mysql.connector.Error as error:
        print("There was a problem creating your tag.")
        print(error)
        time.sleep(1)


def add_tag_to_photo(photo_id_name_list, tag_entry, tag_label):
    """ Adds a descriptive tag to a photo """
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
        cursor.callproc('sp_add_photo_tag', photo_tag_params)
        cnx.commit()
        print(f"'{tag_name}' tag added to photo: {photo_name}")
        
        # Update tag list in photo viewer
        show_photo_tags(photo_id, tag_label)

        # Clear text entry box
        tag_entry.delete(0, tk.END)

        time.sleep(1)
    except mysql.connector.Error as error:
        print("There was a problem tagging your photo.")
        print(error)
        time.sleep(1)


cnx = mysql.connector.connect(**config.config)
cursor = cnx.cursor()

# PROCEDURE CALLS:
# 'CALL sp_import_photo(?, ?, ?, ?, ?, @new_id);'
# 'CALL sp_create_album(?, ?, @new_id);'
# 'CALL sp_create_tag(?, @new_id);'
# 'CALL sp_add_photo_tag(?, ?, @new_id);'

# Welcome message
welcome = \
"\n**Welcome to your photo catalog!**" \
"\nStay organized with photo albums and easily find the photos you're looking for with custom descriptive tags." \
"\nYour catalog is a local database, so your files remain safe and untouched on your computer, and nothing is uploaded to the cloud." \
"\n" \
"\nAlbums - Organize your photos with albums. Create albums with the 'new album' command. Albums do not move the image files on your computer." \
"\nWhen importing photos, you'll be asked to choose an album to import into. If no albums are found, you will be asked to create one." \
"\n" \
"\nGallery - Choose an album to view and its contents will display in a photo viewer on your desktop." \
"\nStep through the album's photos and add descriptive tags to use when searching your catalog." \
"\n" \
"\nTags - Make your catalog searchable with custom descriptive tags. Create new tags with the 'new tag' command, or create tags directly in the gallery photo viewer." \
"\nTags allow you to search across your entire catalog regardless of " \
"\n" \
"\nSearch (coming soon...) - Search across your entire catalog by tags." \
"\nAdd the results of your search to a new album, or export the image files themselves to a single location on your computer for easier sharing with others." \
"\n"
print(welcome)

while True:
    # Show all available commands
    commands = \
    "\nCommand      Description" \
    "\n------------------------" \
    "\nimport       import photos into an album in your catalog" \
    "\ngallery      view your photos" \
    "\nsearch       search your catalog using descriptive tags" \
    "\nnew album    add a new album to your catalog" \
    "\nnew tag      create new descriptive tags for your photos" \
    "\nexit         exit the program\n"
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
            album_input = input("Select an album for your imported photos: ")
            import_photos(album_input)

    ## VIEW PHOTOS ##
    elif command_input == "gallery":
        list_albums()
        album_input = input("Enter the name of the album to view: ")
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

    ## SEARCH BY TAGS ##
    ## -- Not yet implemented -- ##
    elif command_input == "search":
        pass

    ## EXIT PROGRAM ##
    elif command_input == "exit":
        print("\nClosing the program. Goodbye!\n")
        cnx.close()
        sys.exit(0)
    
    else:
        print("Invalid input. Please try again.")
        time.sleep(1)
