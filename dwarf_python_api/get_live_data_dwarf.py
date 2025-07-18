from ftplib import FTP, error_perm
import sys
import os
import shutil
import importlib
from time import sleep
import configparser
import time
from dwarf_python_api.lib.dwarf_utils import perform_takePhoto, perform_takeWidePhoto
# import data for config.py
import dwarf_python_api.get_config_data
# Import the module
import dwarf_python_api.lib.my_logger as log

# FTP connection details
global ftp_host
ftp_host = ""
# Local directory to copy files to
global local_directory
local_directory = ''
# Dwarf directory to copy files from
global last_directory
last_directory = ''
# Local Photo directory to copy files to
global local_photo_directory
local_photo_directory = ''
# Dwarf directory to copy photo file from
global last_photo_directory
last_photo_directory = ''

def fn_wait_for_user_input(seconds_to_wait,message):
    #print('waiting for',seconds_to_wait, 'seconds ...' )
    log.notice(message, seconds_to_wait)
    start_time = time.time()
    try:
        while (time.time() - start_time ) < seconds_to_wait:
            '''
            parenthesis, from inside out:
            time.time() which is current time    - start time, if it is more than 10 seconds, time's up :)
            int ; so we don't count 10 -1,02=8; instead we will count 10-1 = 9, meaning 9 seconds remaining, not 8
            seconds to wait - everything else ; so we get reverse count from 10 to 1, not from 1 to 10
            '''
            log.notice("%d" %  (  seconds_to_wait -   int(  (time.time() - start_time )   )    )    ) 
            time.sleep(1)
        log.notice('No keypress detected.')
        return 1 #no interrupt after x seconds
    except KeyboardInterrupt:
        log.notice('Keypress detected - exiting.')
        return 0 #interrupted
        
    

# Function to download a file from the FTP server
def download_file(ftp, remote_file, local_file):
    try:
        with open(local_file, 'wb') as local_file_obj:
            ftp.retrbinary('RETR ' + remote_file, local_file_obj.write)
    except Exception as e:
        log.error(f"Exception: {e}")
        log.error(f"During copy: {remote_file} -> {local_file}")

# Function to get the modification date of a file on the FTP server
def get_file_mtime(ftp, remote_file):
    return ftp.voidcmd(f"MDTM {remote_file}")

# Function to get the modification date of a directory on the FTP server
def get_dir_mtime(remote_dir):
    return remote_dir[-23:]

def getlistPhoto(cameraPhoto = "TELE", indexStart=0, indexEnd=10):
    global ftp_host
    global local_photo_directory

    # Create an FTP_TLS instance
    ftp = FTP()

    # return JSON List
    listPhotos = []

    # Connect to the FTP server
    log.notice (f"Try to connect to : {ftp_host}")
    # Connect to the FTP server
    try:
        ftp.connect(ftp_host)

        ftp.login("Anonymous","")
        ftp.set_pasv(True)
        log.success(f"Connected to {ftp_host}")
    except:
        log.error("Can't connect to the Dwarf Device.")
        return False

    # Remote directory on the FTP server to monitor
    remote_directoryD2 = '/DWARF_II/Normal_Photos'
    start_nameD2 = f"DWARF_{cameraPhoto}"
    remote_directoryD3 = '/Normal_Photos'
    start_nameD3 = f"DWARF3_{cameraPhoto}"
    remote_directory = remote_directoryD2
    start_name = start_nameD2

    # File extension to filter for (e.g., '.fits')
    file_extension = '.jpg'

    # Change to the Photo subdirectory
    # Try to change to remote_directoryD2, switch to remote_directoryD3 if D2 doesn't exist
    try:
        ftp.cwd(remote_directory)
        log.success(f"Dwarf 2 connected, Successfully changed to {remote_directoryD2}")
    except error_perm as e:
        remote_directory = remote_directoryD3
        start_name = start_nameD3
        try:
            ftp.cwd(remote_directory)
            log.success(f"Dwarf 3 connected, Successfully changed to {remote_directory}")
        except error_perm as e:
            log.error(f"Erreur getting files on FTP on the Dwarf, error: {e}")
            return False

    ftp.cwd(remote_directory)
    wait_number = 0
    old_wait_number = 0

    # Get the list of files in the directory
    remote_files = ftp.nlst()

    log.notice(f"Searching {cameraPhoto} Photo in directory: {remote_directory}")

    remote_telefiles = [f for f in remote_files if (f.startswith(start_name))]
    sorted_file_list = sorted(remote_telefiles, reverse=True)

    FindAllPhotos = False
    if str(indexStart).lower() == "all":
       indexStart = 0
       FindAllPhotos = True
       indexEnd = 0
    else:
        try:
            indexStart = int(indexStart)
        except ValueError:
            indexStart = 0
        try:
            indexEnd = int(indexEnd)
        except ValueError:
            indexEnd = 0

    # Verify
    log.notice(f"Total Photos found: {len(sorted_file_list)}")
    # return JSON List
    found_photo = 0
    for remote_file in sorted_file_list:
        if remote_file.endswith(file_extension):
            # Found a file
            if found_photo > indexEnd and not FindAllPhotos:
                log.notice("Found last photo file")
                break
            elif indexStart <= found_photo <= indexEnd or FindAllPhotos:
                log.notice(f"Found PhotoFile : {found_photo} - {remote_file}")
                listPhotos.append({'index': found_photo, 'file': remote_file})
            found_photo += 1

    # Move back to the parent directory
    ftp.cwd('..')

    log.notice(f"End of List")
    return listPhotos

def getLastPhoto(history, camera="TELE"):
    global ftp_host
    global local_photo_directory

    # Create an FTP_TLS instance
    ftp = FTP()

    # Connect to the FTP server
    log.notice (f"Try to connect to : {ftp_host}")
    # Connect to the FTP server
    try:
        ftp.connect(ftp_host)

        ftp.login("Anonymous","")
        ftp.set_pasv(True)
        log.success(f"Connected to {ftp_host}")
    except:
        log.error("Can't connect to the Dwarf Device.")
        return False

    # Remote directory on the FTP server to monitor
    remote_directoryD2 = '/DWARF_II/Normal_Photos'
    start_nameD2 = f"DWARF_{camera}"
    remote_directoryD3 = '/Normal_Photos'
    start_nameD3 = f"DWARF3_{camera}"
    remote_directory = remote_directoryD2
    start_name = start_nameD2

    # File extension to filter for (e.g., '.fits')
    file_extension = '.jpg'

    # Change to the Photo subdirectory
    # Try to change to remote_directoryD2, switch to remote_directoryD3 if D2 doesn't exist
    try:
        ftp.cwd(remote_directory)
        log.success(f"Dwarf 2 connected, Successfully changed to {remote_directoryD2}")
    except error_perm as e:
        remote_directory = remote_directoryD3
        start_name = start_nameD3
        try:
            ftp.cwd(remote_directory)
            log.success(f"Dwarf 3 connected, Successfully changed to {remote_directory}")
        except error_perm as e:
            log.error(f"Erreur getting files on FTP on the Dwarf, error: {e}")
            return False

    ftp.cwd(remote_directory)
    wait_number = 0
    old_wait_number = 0

    # Get the list of files in the directory
    remote_files = ftp.nlst()

    remote_telefiles = [f for f in remote_files if (f.startswith(start_name))]
    sorted_file_list = sorted(remote_telefiles, reverse=True)

    # Verify
    log.notice(f"Total Photos found: {len(sorted_file_list)}")
    local_path = False
    found_photo = 0
    for remote_file in sorted_file_list:
        if remote_file.endswith(file_extension):
            # Found a files
            if (found_photo==0):
              log.notice (f"Found last photo file")
            else:
              log.notice (f"Found photo file {found_photo}")
            if (found_photo >= history):
                log.notice ("Found the requested photo")
                log.notice(f"Found File : {remote_file} from directory: {remote_directory}")
                remote_path = remote_directory + "/" + remote_file
                # Convert to absolute path
                local_photo_directory = os.path.abspath(local_photo_directory)
                local_path = os.path.join(local_photo_directory, remote_file)

                if (os.path.isfile(local_path)):
                    os.remove(local_path)

                download_file(ftp, remote_path, local_path)
                log.notice(f"Downloaded file: {remote_file}")
                log.notice(f"From directory: {remote_directory} to {local_path}")
                log.notice(f"New File copied : {remote_file}") 
                break

            else:
                found_photo += 1

    # Move back to the parent directory
    ftp.cwd('..')

    log.notice(f"File saved: {local_path}")
    log.notice(f"End downloading files")
    return local_path

def stacking():
    global ftp_host
    global local_directory
    global last_directory

    # Create an FTP_TLS instance
    ftp = FTP()

    # Connect to the FTP server
    log.notice (f"Try to connect to : {ftp_host}")
    # Connect to the FTP server
    try:
        ftp.connect(ftp_host)

        ftp.login("Anonymous","")
        ftp.set_pasv(True)
        log.success(f"Connected to {ftp_host}")
    except:
        log.error("Can't connect to the Dwarf.")
        return

    # Remote directory on the FTP server to monitor
    remote_directoryD2 = '/DWARF_II/Astronomy/'
    remote_directoryD3 = '/Astronomy/'
    remote_directory = remote_directoryD2

    # Try to change to remote_directoryD2, switch to remote_directoryD3 if D2 doesn't exist
    try:
        ftp.cwd(remote_directory)
        log.notice(f"Dwarf 2 connected")
        # Move back to the parent directory
        ftp.cwd('/')

    except error_perm as e:
        remote_directory = remote_directoryD3
        try:
            ftp.cwd(remote_directory)
            log.notice(f"Dwarf 3 connected")
            # Move back to the parent directory
            ftp.cwd('/')
        except error_perm as e:
            log.error(f"Erreur getting files on FTP on the Dwarf, error: {e}")
            return False

    # Create Tmp directory if need
    local_path_tmp = os.path.join(local_directory, "tmp")

    if (not os.path.exists(local_path_tmp)):
        os.makedirs(local_path_tmp)

    # File extension to filter for (e.g., '.fits')
    file_extension = '.fits'
    file_tmp = '.tmp'

    # Set to keep track of downloaded files
    downloaded_files = set()

    #files = ftp.mlsd("/DWARF_II/Astronomy/DWARF_RAW_Manual_EXP_13_GAIN_90_2024-01-07-00-40-14-712")

    if (not last_directory):
        log.notice(f"Search the last directory...")

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

        if (len(remote_subdirectories) == 0):
            remote_directory = remote_directoryD3
            remote_subdirectories = [d for d in ftp.nlst(remote_directory) if (ftp.cwd(d).startswith("250") and d.startswith(remote_directory+'DWARF_RAW'))]

        log.notice(f"Found {len(remote_subdirectories)} directories")

        # Sort subdirectories by modification date (most recent first)
        remote_subdirectories.sort(key=lambda x: get_dir_mtime(x), reverse=True)

    else:
        remote_subdirectories = []
        remote_subdirectories.append(remote_directory + last_directory)
        log.notice(f"Using the directory : {remote_subdirectories[0]}")

    # Choose the most recent subdirectory
    if remote_subdirectories:
        most_recent_subdirectory = remote_subdirectories[0]
        log.notice(f"Processing files in directory: {most_recent_subdirectory}")

        # Change to the most recent subdirectory
        wait_number = 0
        old_wait_number = 0
        processing = True

        try:
            ftp.cwd(most_recent_subdirectory)

            while processing:

                # Get the list of files in the most recent subdirectory
                remote_files = ftp.nlst()

                # Sort files by modification date (oldest first)
                remote_files.sort(key=lambda x: get_file_mtime(ftp, x))

                # Find and download new files with the specified extension
                for remote_file in remote_files:
                    if remote_file.endswith(file_extension) and remote_file not in downloaded_files:
                        # Found new files
                        log.notice ("Found new file")
                        old_wait_number = wait_number

                        log.notice(f"Found File : {remote_file} from directory: {most_recent_subdirectory}")
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
                        log.notice(f"Downloaded file: {remote_file}")
                        log.notice(f"From directory: {most_recent_subdirectory} to {local_file_tmp}")
                        # rename tmp file
                        os.rename(local_file_tmp, local_path)
                        log.notice(f"New File copied : {remote_file}") 
                        downloaded_files.add(remote_file)

                wait_number += 15

                if (wait_number - old_wait_number)  > 3:
                    if fn_wait_for_user_input(5, "No more files since 30 seconds, the program will contine if you don't press CTRL-C within 5 seconds:" )  == 1:
                        old_wait_number = wait_number
                        log.notice('continuing ....')
                    else:
                        log.notice('not continuing.')
                        processing = False

                if (processing):
                    # Pause before checking again
                    sleep(2)  # You can adjust the frequency of checking

            # Move back to the parent directory
            ftp.cwd('..')

        except error_perm as e:
            log.error(f"Erreur getting files on FTP on the Dwarf, error: {e}")
        except KeyboardInterrupt:
            log.notice('Keypress detected - exiting.')

    log.notice(f"Stacking Finished")

def display_menu():
    global ftp_host
    # Reload the config module to ensure the new value is used
    # read at runtime
    data_config = dwarf_python_api.get_config_data.get_config_data()
    ftp_host = data_config['ip'] 

    log.notice("")
    log.notice("------------------")
    log.notice(f"1. Current Dwarf IP: {ftp_host}")
    log.notice(f"2. Current Siril Stacking Directory: {local_directory}")
    log.notice(f"3. Use Last Dwarf Session (empty) or Specify Session Directory: {last_directory}")
    log.notice(f"4. Launch Live Stacking")
    log.notice(f"5. Current Photo Directory: {local_photo_directory}")
    log.notice(f"6. Get Last Tele Photo (Photo Mode)")
    log.notice(f"7. Take a Tele Photo (Photo Mode)")
    log.notice(f"8. Get Last Wide Photo (Photo Mode)")
    log.notice(f"9. Take a Wide Photo (Photo Mode)")
    log.notice(f"10. Get Tele Photos List")
    log.notice(f"11. Get Wide Photos List")
    log.notice("0. Return to main menu")

def get_user_choice():
    choice = input("Enter your choice (1-11) or 0 to return to main menu: ")
    return choice

def get_user_choice_last_Photo():
    choice = input("You can choose a photo from the last photo history (0 (default) => last photo, 1 => previous photo and so on): ")
    return choice

def get_user_choice_index_start():
    choice = input("Set the starting  index based on history. (0 (default) => most recent photo, 1 => previous photo and so on or 'all'): ")
    return choice

def get_user_choice_index_end():
    choice = input("Set the ending index based on history. (0 (default) => last photo, 1 => previous photo and so on): ")
    return choice

def option_1():
    log.notice("You selected Option 1: Setting Current Dwarf IP")
    log.notice("")
    # Add your Option 1 functionality here
    input_data(1)

def option_2():
    log.notice("You selected Option 2:  Setting Current Siril Stacking Directory")
    log.notice("")
    # Add your Option 2 functionality here
    input_data(2)

def option_3():
    log.notice("You selected Option 3: Setting Use Last Dwarf Session (empty) or Specify Session Directory")
    log.notice("")
    # Add your Option 3 functionality here
    input_data(3)

def option_4():
    log.notice("You selected Option 4: Launch Live Stacking")
    log.notice("")
    # Add your Option 4 functionality here

    global ftp_host
    global local_directory
    global last_directory

    # Reload the config module to ensure the new value is used
    if not ftp_host:
        # read at runtime
        data_config = dwarf_python_api.get_config_data.get_config_data()
        ftp_host = data_config['ip'] 

    if (not ftp_host):
        log.error("The Dwarf IP can't be empty!")
        return 

    if (not local_directory):
        log.error("The Siril directory can't be empty!")
        return 

    update_config(ftp_host=ftp_host, local_directory=local_directory, last_directory=last_directory)

    stacking()

def option_5():
    log.notice("You selected Option 5:  Setting Current Photo Directory")
    log.notice("")
    # Add your Option 5 functionality here
    input_data(5)

def option_6():
    log.notice("You selected Option 6: Get Last Photo (not Astro)")
    # Add your Option 6 functionality here
    nb_last_photo = get_user_choice_last_Photo()

    getGetLastPhoto(nb_last_photo, "TELE")

def option_7():
    log.notice("You selected Option 7. Take one Photo Only")
    log.notice("")
    # Add your Option 7 functionality here
    perform_takePhoto()

def option_8():
    log.notice("You selected Option 8. Get Last Wide Photo (Photo Mode)")
    # Add your Option 8 functionality here
    nb_last_photo = get_user_choice_last_Photo()

    getGetLastPhoto(nb_last_photo, "WIDE")

def option_9():
    log.notice("You selected Option 9. Take one Wide Photo Only")
    # Add your Option 9 functionality here
    perform_takeWidePhoto()

def option_10():
    log.notice("You selected Option 10. Get Tele Photos List")
    # Add your Option 10 functionality here
    indexStart = get_user_choice_index_start()
    indexEnd = "0"
    if str(indexStart).lower() != "all": 
        indexEnd = get_user_choice_index_end()

    getlistPhoto("TELE", indexStart, indexEnd)

def option_11():
    log.notice("You selected Option 11. Get Wide Photos List")
    # Add your Option 10 functionality here
    indexStart = get_user_choice_index_start()
    indexEnd = "0"
    if str(indexStart).lower() != "all": 
        indexEnd = get_user_choice_index_end()

    getlistPhoto("WIDE", indexStart, indexEnd)

def getGetLastPhoto(history = 0, camera="TELE", get_config = False):
    global ftp_host
    global local_photo_directory

    # Reload the config module to ensure the new value is used
    if not ftp_host:
        # read at runtime
        data_config = dwarf_python_api.get_config_data.get_config_data()
        ftp_host = data_config['ip'] 

    if (not ftp_host):
        log.error("The Dwarf IP can't be empty!")
        return False

    if (get_config):
        read_config()

    if (not local_photo_directory):
        log.error("The Current Photo Directory can't be empty!")
        return False

    try:
        history = int(history)
    except ValueError:
        history = 0

    update_config(local_photo_directory=local_photo_directory)

    return getLastPhoto(history, camera)

def update_config(ftp_host=None, local_directory=None, last_directory=None, local_photo_directory=None ):
    config = configparser.ConfigParser()

    if (not os.path.isfile('config.ini')):
        config.add_section('CONFIG')
        config.set('CONFIG','FTP_HOST','')
        config.set('CONFIG','LOCAL_DIRECTORY','')
        config.set('CONFIG','LAST_DIRECTORY','')
        config.set('CONFIG','LOCAL_PHOTO_DIRECTORY','')
        log.notice("Create the Config file!")

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
    log.notice("Read Config File.")

    try:
        ftp_host = config.get('CONFIG', 'FTP_HOST') 	
    except configparser.NoSectionError:
        log.error("ConfigFile not found.")
    except configparser.NoOptionError:
        log.error("Data not found.")

    try:
        local_directory = config.get('CONFIG', 'LOCAL_DIRECTORY')
    except configparser.NoSectionError:
        log.error("ConfigFile not found.")
    except configparser.NoOptionError:
        log.error("Data not found.")

    try:
        last_directory = config.get('CONFIG', 'LAST_DIRECTORY')
    except configparser.NoSectionError:
        log.error("ConfigFile not found.")
    except configparser.NoOptionError:
        log.error("Data not found.")

    try:
        local_photo_directory = config.get('CONFIG', 'LOCAL_PHOTO_DIRECTORY')
    except configparser.NoSectionError:
        log.error("ConfigFile not found.")
    except configparser.NoOptionError:
        log.error("Data not found.")

    try:
        if not local_photo_directory:
            local_photo_directory = os.getcwd()
    except configparser.NoSectionError:
        log.error("ConfigFile not found.")
    except configparser.NoOptionError:
        log.error("Data not found.")

def input_data(type):
    global ftp_host
    global local_directory
    global last_directory
    global local_photo_directory

    if (type == 1):
        ftp_host_input = input("Enter the Dwarf IP: ")
        log.notice("You entered:", ftp_host_input)
        if (ftp_host_input):
            log.notice("You entered:", ftp_host_input)
            ftp_host = ftp_host_input
            update_config(ftp_host=ftp_host)
        else:
            log.error("Can't be empty, no change")

    if (type == 2):
        local_directory_input = input("Enter the Siril Stacking Directory: ")
        log.notice("You entered:", local_directory_input)
        if (local_directory_input):
            local_directory = local_directory_input
            update_config(local_directory=local_directory)
        else:
            log.error("Can't be empty, no change")

    if (type == 3):
        last_directory = input("Set Last Dwarf Session (empty) or Specify Session Directory: ")
        log.notice("You entered:", last_directory)
        update_config(last_directory=last_directory)

    if (type == 5):
        local_photo_directory_input = input("Enter the Local Photo Directory: (")
        if (local_photo_directory_input):
            log.notice("You entered:", local_photo_directory_input)
            local_photo_directory = local_photo_directory_input
            update_config(local_photo_directory=local_photo_directory)
        else:
            log.error("Can't be empty, no change")

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

        elif user_choice == '8':
            option_8()

        elif user_choice == '9':
            option_9()

        elif user_choice == '10':
            option_10()

        elif user_choice == '11':
            option_11()

        elif user_choice == '0':
            log.notice("return to main menu")
            break

        else:
            log.error("Invalid choice. Please enter a number between 0 and 11.")

