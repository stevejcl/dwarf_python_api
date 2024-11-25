# import data for config.py
import logging
import types
import os
import sys
import shutil
# import data for config.py
import dwarf_python_api.get_config_data

# Define logger instance and initial variables
logger = logging.getLogger('my_logger')
file_handler = None  # Initialize file_handler as None
log_file = None  # Initialize log_file as None

# Define custom NOTICE and SUCCESS logging level
NOTICE_LEVEL_NUM = 22
SUCCESS_LEVEL_NUM = 25

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

# Function to update or create the log file handler
def update_log_file():
    """
    Dynamically update or create the log file handler.
    """
    global log_file  # To update the global variable
    global file_handler  # To reference the existing file handler

    # Reload configuration data
    data_config = dwarf_python_api.get_config_data.get_config_data()

    # Determine the new log file
    if data_config['log_file'] == "False":
        new_log_file = None
    else:
        new_log_file = "app.log" if data_config['log_file'] == "" else data_config['log_file']

    # Check if the log file has changed
    if new_log_file != log_file:
        log_file = new_log_file

        # Remove the existing file handler if it exists
        if file_handler and file_handler in logger.handlers:
            logger.removeHandler(file_handler)
            file_handler.close()  # Close the old file handler

        # Add the new file handler if log_file is not None
        if log_file is not None:
            try:
                # Backup old log file if it exists
                old_log_file = log_file + '.old'
                if os.path.exists(log_file):
                    try:
                        # Rename the old log file to app.log.old (or any other naming convention)
                        shutil.move(log_file, old_log_file)
                    except Exception as e:
                        print(f"Error moving log file: {e}")

                # Determine file log level based on 'debug' in data_config
                file_log_level = logging.DEBUG if data_config.get('debug') else logging.INFO
                print(f"file_log_level: {file_log_level}")

                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(file_log_level)
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                logger.addHandler(file_handler)
                logger.notice(f"Log file updated to: {log_file}")
            except Exception as e:
                logger.error(f"Failed to update log file: {e}")
        else:
            logger.info("Log file disabled.")

# Initial logger setup
def setup_logger():
    """
    Initialize the logger and configure handlers.
    """
    global logger

    # Set logger level to NOTSET, allowing handlers to filter logs
    logging.getLogger().setLevel(logging.NOTSET)  # Allow handlers to manage levels independently

    # Reload configuration data
    data_config = dwarf_python_api.get_config_data.get_config_data()

    # Set root logger level
    root_level = logging.DEBUG if data_config.get('debug') else logging.INFO
    logger.setLevel(root_level)
    print(f"root_level: {root_level}")

    # Add console logging handler separately
    console_handler = logging.StreamHandler()
    console_handle_level = logging.INFO if data_config.get('trace') else NOTICE_LEVEL_NUM
    if data_config['log_file'] == "False":
        console_handle_level = logging.DEBUG if data_config.get('debug') else logging.INFO

    console_handler.setLevel(console_handle_level)
    console_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(console_handler)

    # Add custom log levels
    logging.addLevelName(NOTICE_LEVEL_NUM, 'NOTICE')
    logging.addLevelName(SUCCESS_LEVEL_NUM, 'SUCCESS')

    # Bind custom log methods to the logger
    logger.notice = types.MethodType(notice, logger)
    logger.success = types.MethodType(success, logger)

    # Configure the log file handler using `update_log_file`
    update_log_file()

# Call the setup_logger function when the module is imported
setup_logger()

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
