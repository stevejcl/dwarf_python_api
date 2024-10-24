# import data for config.py
import logging
import types
import os
import sys
import shutil
from dwarf_python_api.get_config_data import get_config_data

# Load configuration data
data_config = get_config_data()

if data_config['log_file'] == "False":
    log_file = None
else: 
    log_file = "app.log" if data_config['log_file'] == "" else data_config['log_file']

# Backup old log file if it exists
if log_file is not None:
    try:
        old_log_file = log_file + '.old'
        if os.path.exists(log_file):
            # Rename the old log file to app.log.old (or any other naming convention)
            shutil.move(log_file, old_log_file)
    except Exception as e:
        print(f"Error moving log file: {e}")

# Define custom NOTICE and SUCCESS logging level
NOTICE_LEVEL_NUM = 22
logging.addLevelName(NOTICE_LEVEL_NUM, 'NOTICE')
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, 'SUCCESS')

# Custom success logging method
def notice(self, message, *args, **kwargs):
    if self.isEnabledFor(NOTICE_LEVEL_NUM):
        # We must pass args explicitly as a tuple to avoid the missing argument error
        self._log(NOTICE_LEVEL_NUM, message, args, **kwargs)

logging.Logger.notice = notice  # Add notice method to logger class

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        # We must pass args explicitly as a tuple to avoid the missing argument error
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)

logging.Logger.success = success  # Add success method to logger class

# Set logger level to NOTSET, allowing handlers to filter logs
logging.getLogger().setLevel(logging.NOTSET)  # Allow handlers to manage levels independently

# Create logger instance
root_level = logging.DEBUG if data_config.get('debug') else logging.INFO
logger = logging.getLogger('my_logger')
logger.setLevel(root_level)
print(f"root_level: {root_level}")

# Determine file log level based on 'debug' in data_config
file_log_level = logging.DEBUG if data_config.get('debug') else logging.INFO
print(f"file_log_level: {file_log_level}")

# File handler for logging to a file
if log_file is not None:
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(file_log_level)  # Set the file handler level dynamically
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add console logging handler separately
# Only logs NOTICE and Above level messages except if TRACE is Set or file_log_level if no log file
console_handler = logging.StreamHandler()
console_handle_level = logging.INFO if data_config.get('trace') else NOTICE_LEVEL_NUM
if log_file is None:
    console_handle_level = file_log_level

console_handler.setLevel(console_handle_level)  # Set the console handler level dynamically
console_handler.setFormatter(logging.Formatter('%(message)s'))
print(f"console_handle_level: {console_handle_level}")

logger.addHandler(console_handler)

if log_file is not None:
    logger.addHandler(file_handler)

# Bind the notice and success method to the logger
logger.notice = types.MethodType(notice, logger)
logger.success = types.MethodType(success, logger)

def debug(*messages):
    for message in messages:
        logger.debug(message) 

def error(*messages):
    for message in messages:
        logger.error(message) 

def warning(*messages):
    for message in messages:
        logger.warning(message) 

def info(*messages):
    for message in messages:
        logger.info(message) 

def notice(*messages):
    for message in messages:
        logger.notice(message)

def success(*messages):
    for message in messages:
        logger.success(message)
