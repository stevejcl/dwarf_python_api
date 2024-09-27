# import data for config.py
import logging
import types
import os
import sys
import shutil
from dwarf_python_api.get_config_data import get_config_data

# Load configuration data
data_config = get_config_data()

log_file = data_config.get('log_file', 'app.log')

# Backup old log file if it exists
old_log_file = log_file + '.old'
if os.path.exists(log_file):
    try:
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

# Configure the logger
logging.basicConfig(
    filename=log_file,  # Log file name
    filemode='w',        # Create a new log file
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG if data_config['debug'] else logging.INFO  # Use DEBUG level if in debug mode
)

# Add console logging handler separately
# Only logs NOTICE and Above level messages except if TRACE is Set
console_handler = logging.StreamHandler()
console_handle_level = logging.INFO if data_config.get('trace') else NOTICE_LEVEL_NUM
console_handler.setLevel(console_handle_level)

console_handler.setFormatter(logging.Formatter('%(message)s'))

# Add console handler to the root logger
logging.getLogger().addHandler(console_handler)

# Add handlers to logger
logging.getLogger().addHandler(console_handler)

# Bind the notice and success method to the logger
logger = logging.getLogger('my_logger')

logger.notice = types.MethodType(notice, logger)
logger.success = types.MethodType(success, logger)

def debug(*messages):
    if data_config['debug']:
        for message in messages:
            logging.debug(message) 

def error(*messages):
    for message in messages:
        logging.error(message) 

def warning(*messages):
    for message in messages:
        logging.warning(message) 

def info(*messages):
    for message in messages:
        logging.info(message) 

def notice(*messages):
    for message in messages:
        logger.notice(message)

def success(*messages):
    for message in messages:
        logger.success(message)
