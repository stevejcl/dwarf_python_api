import http.server
import socketserver
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading
import time
import json
import importlib
import config # Ensure config is imported

# Global PORT
PORT = 8000
CONFIG_FILE = 'config.py'

class MyHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        parameter = data['parameter']

        # Read the config file and update the IP address
        with open(CONFIG_FILE, 'r') as file:
            lines = file.readlines()
        
        with open(CONFIG_FILE, 'w') as file:
            for line in lines:
                if line.startswith('DWARF_IP'):
                    file.write(f'DWARF_IP = "{parameter}"\n')
                else:
                    file.write(line)

        # Reload the config module to ensure the new value is used
        importlib.reload(config)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))

class MyServer(threading.Thread):
    def run(self):
        self.server = ThreadingHTTPServer(('localhost', PORT), MyHandler)
        self.server.serve_forever()
    def stop(self):
        self.server.shutdown()

def open_browser(url):
    print(f"Opening web browser to URL: {url}")
    webbrowser.open(url)

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
        time.sleep(3)
        result = False
        exitAsked = False
        
        while not result:
            current_ip = config.DWARF_IP

            if current_ip != previous_ip:
                previous_ip = current_ip
                if current_ip == "":
                    print("Info: IP address setting cleared.")
                    if exitAsked :
                      result = True
                elif current_ip == "Exit":
                    print("Info: Exit processing.")
                    exitAsked = True
                else:
                    result = True
            time.sleep(1)

    except KeyboardInterrupt:
        # Handle Ctrl+C to stop the server
        pass
    finally:
        # Stop the server (set server_running flag)
        server.stop()

    # Optional: Add additional delay or cleanup steps if needed
    time.sleep(1)

    return not exitAsked 