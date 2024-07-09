import http.server
import socketserver
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading
import time
import json
import importlib
import os
import shutil
from filelock import FileLock

# import data for config.py
from dwarf_python_api.get_config_data import get_config_data,CONFIG_FILE

# Global PORT
PORT = 8000
CONFIG_FILE_TMP = 'config.tmp'
LOCK_FILE = 'config.lock'

def copy_file_in_current_directory(source_filename, destination_filename):
    """
    Copies a file from source_filename to destination_filename in the current directory.
    :param source_filename: The name of the source file to copy.
    :param destination_filename: The name where the file should be copied to.
    """
    try:
        current_directory = os.getcwd()
        source_path = os.path.join(current_directory, source_filename)
        destination_path = os.path.join(current_directory, destination_filename)
        shutil.copy(source_path, destination_path)
        print(f"File copied from {source_filename} to {destination_filename}")
        return True
    except FileNotFoundError:
        print(f"Source file {source_filename} not found in the current directory.")
    except PermissionError:
        print(f"Permission denied. Unable to copy to {destination_filename}.")
    except Exception as e:
        print(f"Error copying file: {e}")

    return False

class MyHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
      try:
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        interface = data['interface']
        parameter = data['parameter']

        lock = FileLock(LOCK_FILE, thread_local=False)  # Lock file with no timeout (wait indefinitely)

        with lock:
            print("(B) Lock ON")
            # Create or clear the temp file
            open(CONFIG_FILE_TMP, 'w').close()

            # Read the config file and update the IP address
            with open(CONFIG_FILE, 'r') as file:
                lines = file.readlines()
        
            with open(CONFIG_FILE_TMP, 'w') as file:
                for line in lines:
                    if (interface == "IP"):
                      if line.startswith('DWARF_IP'):
                          file.write(f'DWARF_IP = "{parameter}"\n')
                      else:
                          file.write(line)
                    if (interface == "UI"):
                      if line.startswith('DWARF_UI'):
                          file.write(f'DWARF_UI = "{parameter}"\n')
                      else:
                          file.write(line)

            # Copy tmp file
            nb_try = 0
            result_copy = copy_file_in_current_directory(CONFIG_FILE_TMP, CONFIG_FILE)
            while nb_try < 3 and not result_copy:
                result_copy = copy_file_in_current_directory(CONFIG_FILE_TMP, CONFIG_FILE)
                nb_try += 1
                time.sleep(0.25)

            if result_copy:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))

            else: 
                # Handle file Error
                self.send_response(204)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': 'file not updated'}).encode('utf-8'))
  
        print("(B) Lock OFF")

      except ConnectionAbortedError:
        # Log the error or handle it as needed
        print("Connection was aborted by the client.")
      except Exception as e:
        # Handle other exceptions
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))

class MyServer(threading.Thread):
    def run(self):
        self.server = ThreadingHTTPServer(('localhost', PORT), MyHandler)
        self.server.serve_forever()
    def stop(self):
        self.server.shutdown()

def open_browser(url):
    print(f"Opening web browser to URL: {url}")
    webbrowser.open(url)

def get_file_modification_time(file_path):
    return os.path.getmtime(file_path)

def connect_bluetooth():
    URL = f"http://127.0.0.1:{PORT}/dwarf_ble_connect/connect_dwarf.html"
    
    # Start processing requests
    server = MyServer()
    server.start()

    time.sleep(2)  # Adjust delay as needed

    try:
        # Open the web page in the default web browser
        open_browser(URL)

        # Wait for user input to stop the server
        previous_ip = None
        previous_ui = None
        time.sleep(3)
        resultIP = False
        resultUI = False
        exitAsked = False
        # read at runtime
        data_config = get_config_data()
        # in case of wifi error restart the process
        if data_config['ip'] != "":
          previous_ip = data_config['ip']
        if data_config['ui'] != "":
          previous_ui = data_config['ui']
        check_file = True
        last_check_time = None

        # not((resultIP and resultUI) or (not resultIP and resultUI))
        while (not resultUI):

            # Reload the config module when changing to ensure the new value is used
            current_mod_time = get_file_modification_time(CONFIG_FILE)
            check_file = (last_check_time is None or last_check_time!= current_mod_time)
            if check_file :
              try:
                lock = FileLock(LOCK_FILE, thread_local=False, timeout=5)
                with lock:
                    print("(BC)Lock On")
                    # read at runtime
                    data_config = get_config_data()
                    last_check_time = current_mod_time

                    current_ip = data_config['ip']
                    print(f"(B) current_ip: {current_ip}")
                    current_ui = data_config['ui']
                    print(f"(B) current_ui: {current_ui}")
                    print("(BC)Lock Off")

                if current_ip != previous_ip:
                    previous_ip = current_ip
                    if current_ip == "":
                        print("(B) Info: IP address setting cleared.")
                    else:
                        print("(B) Info: IP address updated.")
                        resultIP = True
                if current_ui != previous_ui:
                    previous_ui = current_ui
                    if current_ui == "":
                        print("(B) Info: UI setting cleared.")
                        if exitAsked :
                          resultUI = True
                    elif current_ui == "Exit":
                        print("(B) Info: Exit processing.")
                        exitAsked = True
                    elif current_ui == "Close":
                        print("(B) Info: Close processing.")
                        resultUI = True
              except Timeout:
                pass 
                
            time.sleep(1.5)

    except KeyboardInterrupt:
        # Handle Ctrl+C to stop the server
        pass
    finally:
        # Stop the server (set server_running flag)
        print("(B) Info: Server Stops.")
        server.stop()

    # Optional: Add additional delay or cleanup steps if needed
    time.sleep(1)

    return resultIP 