from ftplib import FTP
import sys
import os
import shutil
import importlib
from time import sleep
import configparser
import time
import config
from .lib.dwarf_utils import perform_takePhoto

CONFIG_FILE = 'config.py'
# FTP connection details
global ftp_host
ftp_host = ""
# Local directory to copy files to
global local_directory
local_directory = ''
# Dwarf directory to copy files from
global last_directory
last_directory = 'DWARF_RAW_M42_EXP_6_GAIN_60_2024-01-11-23-37-19-246'
# Local Photo directory to copy files to
global local_photo_directory
local_photo_directory = ''
# Dwarf directory to copy photo file from
global last_photo_directory
last_photo_directory = ''

def read_config_values(config_file):
    config_values = {}
    with open(config_file, 'r') as file:
        for line in file:
            # Ignore lines starting with '#' (comments) and empty lines
            if line.strip() and not line.strip().startswith('#'):
                key, value = line.strip().split('=')
                config_values[key.strip()] = value.strip().strip('"')  # Remove extra spaces and quotes
    return config_values

# Function to dynamically import and reload the config module
def get_current_data():
    config_values = read_config_values(CONFIG_FILE)
    return { 'ip' : config_values.get('DWARF_IP','')}

def fn_wait_for_user_input(seconds_to_wait,message):
    #print('waiting for',seconds_to_wait, 'seconds ...' )
    print (message, seconds_to_wait)
    start_time = time.time()
    try:
        while (time.time() - start_time ) < seconds_to_wait:
            '''
            parenthesis, from inside out:
            time.time() which is current time    - start time, if it is more than 10 seconds, time's up :)
            int ; so we don't count 10 -1,02=8; instead we will count 10-1 = 9, meaning 9 seconds remaining, not 8
            seconds to wait - everything else ; so we get reverse count from 10 to 1, not from 1 to 10
            '''
            print("%d" %  (  seconds_to_wait -   int(  (time.time() - start_time )   )    )    ) 
            time.sleep(1)
        print('No keypress detected.')
        return 1 #no interrupt after x seconds
    except KeyboardInterrupt:
        print('Keypress detected - exiting.')
        return 0 #interrupted
        
    

# Function to download a file from the FTP server
def download_file(ftp, remote_file, local_file):
    try:
        with open(local_file, 'wb') as local_file_obj:
            ftp.retrbinary('RETR ' + remote_file, local_file_obj.write)
    except Exception as e:
        print (f"Exception: {e}")
        print (f"During copy: {remote_file} -> {local_file}")

# Function to get the modification date of a file on the FTP server
def get_file_mtime(ftp, remote_file):
    return ftp.voidcmd(f"MDTM {remote_file}")

# Function to get the modification date of a directory on the FTP server
def get_dir_mtime(remote_dir):
    return remote_dir[-23:]

def getLastTelePhoto(history):
    global ftp_host
    global local_photo_directory

    # Create an FTP_TLS instance
    ftp = FTP()

    # Connect to the FTP server
    print (f"Try to connect to : {ftp_host}")
    # Connect to the FTP server
    try:
        ftp.connect(ftp_host)

        ftp.login("Anonymous","")
        ftp.set_pasv(True)
        print(f"Connected to {ftp_host}")
    except:
        print("Can't connect to the Dwarf II.")
        return False

    # Remote directory on the FTP server to monitor
    remote_directory = '/DWARF_II/Normal_Photos'

    # File extension to filter for (e.g., '.fits')
    file_extension = '.jpg'

    # Change to the Photo subdirectory
    ftp.cwd(remote_directory)
    wait_number = 0
    old_wait_number = 0

    # Get the list of files in the directory
    remote_files = ftp.nlst()

    remote_telefiles = [f for f in remote_files if (f.startswith('DWARF_TELE'))]
    sorted_file_list = sorted(remote_telefiles, reverse=True)

    # Verify
    local_path = False
    found_photo = 0
    for remote_file in sorted_file_list:
        if remote_file.endswith(file_extension):
            # Found a files
            if (found_photo==0):
              print (f"Found last photo file")
            else:
              print (f"Found photo file {found_photo}")
            if (found_photo >= history):
                print ("Found the requested photo")
                print(f"Find File : {remote_file} from directory: {remote_directory}")
                remote_path = remote_directory + "/" + remote_file
                # Convert to absolute path
                local_photo_directory = os.path.abspath(local_photo_directory)
                local_path = os.path.join(local_photo_directory, remote_file)

                if (os.path.isfile(local_path)):
                    os.remove(local_path)

                download_file(ftp, remote_path, local_path)
                print(f"Downloaded file: {remote_file}")
                print(f"From directory: {remote_directory} to {local_path}")
                print(f"New File copied : {remote_file}") 
                break

            else:
                found_photo += 1

    # Move back to the parent directory
    ftp.cwd('..')

    print(f"File saved: {local_path}")
    print(f"End downloading files")
    return local_path

def stacking():
    global ftp_host
    global local_directory
    global last_directory

    # Create an FTP_TLS instance
    ftp = FTP()

    # Connect to the FTP server
    print (f"Try to connect to : {ftp_host}")
    # Connect to the FTP server
    try:
        ftp.connect(ftp_host)

        ftp.login("Anonymous","")
        ftp.set_pasv(True)
        print(f"Connected to {ftp_host}")
    except:
        print("Can't connect to the Dwarf II.")
        return

    # Remote directory on the FTP server to monitor
    remote_directory = '/DWARF_II/Astronomy/'

    # Create Tmp directory if need
    local_path_tmp = os.path.join(local_directory, "tmp")

    if (not os.path.exists(local_path_tmp)):
        os.makedirs(local_path_tmp)

    # File extension to filter for (e.g., '.fits')
    file_extension = '.fits'
    file_tmp = '.tmp'

    # Set to keep track of downloaded files
    downloaded_files = set()

    files = ftp.mlsd("/DWARF_II/Astronomy/DWARF_RAW_Manual_EXP_13_GAIN_90_2024-01-07-00-40-14-712")

    if (not last_directory):
        print(f"Search the last directory...")

        #remote_subdirectories = []
        #for d in ftp.nlst(remote_directory):
        #    print(f"Find {d}")
        #    print(f"{ftp.cwd(d)}")
        #    verif = ftp.cwd(d)
        #    if (ftp.cwd(d).startswith('250')):
        #        print("OK FTP")
        #        if (d.startswith(remote_directory+'DWARF_RAW')):
        #            print("OK")
        #            timestamp = d[-23:]
        #            print (timestamp)
        #            remote_subdirectories.append(d)

        # Get the list of subdirectories in the remote directory
        remote_subdirectories = [d for d in ftp.nlst(remote_directory) if (ftp.cwd(d).startswith("250") and d.startswith(remote_directory+'DWARF_RAW'))]
        print(f"Found {len(remote_subdirectories)} directories")

        # Sort subdirectories by modification date (most recent first)
        remote_subdirectories.sort(key=lambda x: get_dir_mtime(x), reverse=True)

    else:
        remote_subdirectories = []
        remote_subdirectories.append(remote_directory + last_directory)
        print(f"Using the directory : {remote_subdirectories[0]}")

    # Choose the most recent subdirectory
    if remote_subdirectories:
        most_recent_subdirectory = remote_subdirectories[0]
        print(f"Processing files in directory: {most_recent_subdirectory}")

        # Change to the most recent subdirectory
        ftp.cwd(most_recent_subdirectory)
        wait_number = 0
        old_wait_number = 0
        processing = True

        while processing:

            # Get the list of files in the most recent subdirectory
            remote_files = ftp.nlst()

            # Sort files by modification date (oldest first)
            remote_files.sort(key=lambda x: get_file_mtime(ftp, x))

            # Find and download new files with the specified extension
            for remote_file in remote_files:
                if remote_file.endswith(file_extension) and remote_file not in downloaded_files:
                    # Found new files
                    print ("Found new file")
                    old_wait_number = wait_number

                    print(f"Find File : {remote_file} from directory: {most_recent_subdirectory}")
                    remote_path = most_recent_subdirectory + "/" + remote_file
                    local_path = os.path.join(local_directory, remote_file)

                    # use a local tmp in a subdirectory : need for Sirl as the transfert is slow
                    local_tmp = remote_file.replace(file_extension, ".tmp")
                    local_file_tmp = os.path.join(local_path_tmp, local_tmp)

                    if (os.path.isfile(local_file_tmp)):
                        os.remove(local_file_tmp)
                    if (os.path.isfile(local_path)):
                        os.remove(local_path)

                    download_file(ftp, remote_path, local_file_tmp)
                    print(f"Downloaded file: {remote_file}")
                    print(f"From directory: {most_recent_subdirectory} to {local_file_tmp}")
                    # rename tmp file
                    os.rename(local_file_tmp, local_path)
                    print(f"New File copied : {remote_file}") 
                    downloaded_files.add(remote_file)

            wait_number += 15

            if (wait_number - old_wait_number)  > 3:
                if fn_wait_for_user_input(5, "No more files since 30 seconds, the program will contine if you don't press CTRL-C within 5 seconds:" )  == 1:
                    old_wait_number = wait_number
                    print('continuing ....')
                else:
                    print('not continuing.')
                    processing = False

            if (processing):
                # Pause before checking again
                sleep(2)  # You can adjust the frequency of checking

        # Move back to the parent directory
        ftp.cwd('..')

    print(f"Stacking Finished")
    display_menu()

def display_menu():
    global ftp_host
    # Reload the config module to ensure the new value is used
    if not ftp_host:
        # read at runtime
        data_config = get_current_data()
        ftp_host = data_config['ip'] 

    print("")
    print("------------------")
    print(f"1. Current Dwarf IP: {ftp_host}")
    print(f"2. Current Siril Stacking Directory: {local_directory}")
    print(f"3. Use Last Dwarf Session (empty) or Specify Session Directory: {last_directory}")
    print(f"4. Launch Live Stacking")
    print(f"5. Current Photo Directory: {local_photo_directory}")
    print(f"6. Get Last Tele Photo (Photo Mode)")
    print(f"7. Take a Tele Photo (Photo Mode)")
    print("0. Return to main menu")

def get_user_choice():
    choice = input("Enter your choice (1-7) or 0 to return to main menu: ")
    return choice

def get_user_choice_last_Photo():
    choice = input("You can choose a photo from the last photo history (0 (default) => last photo, 1 => penultimate and so on): ")
    return choice

def option_1():
    print("You selected Option 1: Setting Current Dwarf IP")
    print("")
    # Add your Option 1 functionality here
    input_data(1)

def option_2():
    print("You selected Option 2:  Setting Current Siril Stacking Directory")
    print("")
    # Add your Option 2 functionality here
    input_data(2)

def option_3():
    print("You selected Option 3: Setting Use Last Dwarf Session (empty) or Specify Session Directory")
    print("")
    # Add your Option 3 functionality here
    input_data(3)

def option_4():
    print("You selected Option 4: Launch Live Stacking")
    print("")
    # Add your Option 4 functionality here

    global ftp_host
    global local_directory
    global last_directory

    # Reload the config module to ensure the new value is used
    if not ftp_host:
        # read at runtime
        data_config = get_current_data()
        ftp_host = data_config['ip'] 

    if (not ftp_host):
        print("The Dwarf IP can't be empty!")
        return 

    if (not local_directory):
        print("The Siril directory can't be empty!")
        return 

    update_config(ftp_host=ftp_host, local_directory=local_directory, last_directory=last_directory)

    stacking()

def option_5():
    print("You selected Option 5:  Setting Current Photo Directory")
    print("")
    # Add your Option 5 functionality here
    input_data(5)

def option_6():
    print("You selected Option 6: Get Last Photo (not Astro)")
    # Add your Option 6 functionality here
    nb_last_photo = get_user_choice_last_Photo()

    getGetLastPhoto(nb_last_photo)
    display_menu()

def option_7():
    print("You selected Option 7. Take one Photo Only")
    print("")
    # Add your Option 7 functionality here
    perform_takePhoto()
    display_menu()

def getGetLastPhoto(history = 0, get_config = False):
    global ftp_host
    global local_photo_directory

    # Reload the config module to ensure the new value is used
    if not ftp_host:
        # read at runtime
        data_config = get_current_data()
        ftp_host = data_config['ip'] 

    if (not ftp_host):
        print("The Dwarf IP can't be empty!")
        return False

    if (get_config):
        read_config()

    if (not local_photo_directory):
        print("The Current Photo Directory can't be empty!")
        return False

    try:
        history = int(history)
    except ValueError:
        history = 0

    update_config(local_photo_directory=local_photo_directory)

    return getLastTelePhoto(history)

def update_config(ftp_host=None, local_directory=None, last_directory=None, local_photo_directory=None ):
    config = configparser.ConfigParser()

    if (not os.path.isfile('config.ini')):
        config.add_section('CONFIG')
        config.set('CONFIG','FTP_HOST','')
        config.set('CONFIG','LOCAL_DIRECTORY','')
        config.set('CONFIG','LAST_DIRECTORY','')
        config.set('CONFIG','LOCAL_PHOTO_DIRECTORY','')
        print("Create the Config file!")

    else: 
        config.read('config.ini')

    # Update the value in the CONFIG section
    if ftp_host is not None:
        config['CONFIG']['FTP_HOST'] = ftp_host
    if local_directory is not None:
        config['CONFIG']['LOCAL_DIRECTORY'] = local_directory
    if last_directory is not None:
        config['CONFIG']['LAST_DIRECTORY'] = last_directory
    if local_photo_directory is not None:
        config['CONFIG']['LOCAL_PHOTO_DIRECTORY'] = local_photo_directory

    with open('config.ini', 'w') as config_file:
        config.write(config_file)

def read_config():
    global ftp_host
    global local_directory
    global last_directory
    global local_photo_directory

    config = configparser.ConfigParser()
    config.read('config.ini')
    print("Read Config File.")

    try:
        ftp_host = config.get('CONFIG', 'FTP_HOST') 	
    except configparser.NoSectionError:
        print("ConfigFile not found.")
    except configparser.NoOptionError:
        print("Data not found.")

    try:
        local_directory = config.get('CONFIG', 'LOCAL_DIRECTORY')
    except configparser.NoSectionError:
        print("ConfigFile not found.")
    except configparser.NoOptionError:
        print("Data not found.")

    try:
        last_directory = config.get('CONFIG', 'LAST_DIRECTORY')
    except configparser.NoSectionError:
        print("ConfigFile not found.")
    except configparser.NoOptionError:
        print("Data not found.")

    try:
        local_photo_directory = config.get('CONFIG', 'LOCAL_PHOTO_DIRECTORY')
    except configparser.NoSectionError:
        print("ConfigFile not found.")
    except configparser.NoOptionError:
        print("Data not found.")

    try:
        if not local_photo_directory:
            local_photo_directory = os.getcwd()
    except configparser.NoSectionError:
        print("ConfigFile not found.")
    except configparser.NoOptionError:
        print("Data not found.")

def input_data(type):
    global ftp_host
    global local_directory
    global last_directory
    global local_photo_directory

    if (type == 1):
        ftp_host_input = input("Enter the Dwarf IP: ")
        print("You entered:", ftp_host_input)
        if (ftp_host_input):
            print("You entered:", ftp_host_input)
            ftp_host = ftp_host_input
            update_config(ftp_host=ftp_host)
        else:
            print("Can't be empty, no change")

    if (type == 2):
        local_directory_input = input("Enter the Siril Stacking Directory: ")
        print("You entered:", local_directory_input)
        if (local_directory_input):
            local_directory = local_directory_input
            update_config(local_directory=local_directory)
        else:
            print("Can't be empty, no change")

    if (type == 3):
        last_directory = input("Set Last Dwarf Session (empty) or Specify Session Directory: ")
        print("You entered:", last_directory)
        update_config(last_directory=last_directory)

    if (type == 5):
        local_photo_directory_input = input("Enter the Local Photo Directory: (")
        if (local_photo_directory_input):
            print("You entered:", local_photo_directory_input)
            local_photo_directory = local_photo_directory_input
            update_config(local_photo_directory=local_photo_directory)
        else:
            print("Can't be empty, no change")

def get_live_data():

    read_config()

    while True:
        display_menu()
        user_choice = get_user_choice()

        if user_choice == '1':
            option_1()

        elif user_choice == '2':
            option_2()

        elif user_choice == '3':
            option_3()

        elif user_choice == '4':
            option_4()

        elif user_choice == '5':
            option_5()

        elif user_choice == '6':
            option_6()

        elif user_choice == '7':
            option_7()

        elif user_choice == '0':
            print("return to main menu")
            break

        else:
            print("Invalid choice. Please enter a number between 0 and 7.")

