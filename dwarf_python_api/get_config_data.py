import os
import shutil
from filelock import FileLock
import dwarf_python_api.lib.my_logger as log

# files must be in the main directory
CONFIG_FILE = 'config.py'
CONFIG_FILE_TMP = 'config.tmp'
LOCK_FILE = 'config.lock'
TAB_VALUE = { 'ip' : 'DWARF_IP', 'ui' : 'DWARF_UI', 'dwarf_id' : 'DWARF_ID', 'client_id' : 'CLIENT_ID', 'update_client_id' : 'UPDATE_CLIENT_ID', 'calibration' : 'TEST_CALIBRATION', 'debug' : 'DEBUG', 'trace' : 'TRACE', 'log_file' : 'LOG_FILE', 'timeout_cmd' : 'TIMEOUT_CMD' }

class ConfigFileNotFoundError(Exception):
    """Exception raised when the configuration file is not found."""
    pass

# Function to parse boolean values from config
def parse_bool(value):
    value = value.strip().strip('"').lower()
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        return None  # or handle it with a default, like False

def read_config_values(config_file = None):
    global CONFIG_FILE

    if config_file is None:
        config_file = CONFIG_FILE

    if not os.path.exists(config_file):
        raise ConfigFileNotFoundError(f"Configuration file {config_file} not found.")
    config_values = {}
    with open(config_file, 'r') as file:
        for line in file:
            # Ignore lines starting with '#' (comments) and empty lines
            if line.strip() and not line.strip().startswith('#'):
                key, value = line.strip().split('=')
                config_values[key.strip()] = value.strip().strip('"')  # Remove extra spaces and quotes
    return config_values

# Function to dynamically import and reload the config module
def get_config_data(config_file = None, print_log = False):
    global CONFIG_FILE

    if config_file is None:
        config_file = CONFIG_FILE

    try:
        config_values = read_config_values(config_file)
        # Convert specific keys to booleans
        if 'DEBUG' in config_values:
            config_values['DEBUG'] = parse_bool(config_values['DEBUG'])

        if 'TRACE' in config_values:
            config_values['TRACE'] = parse_bool(config_values['TRACE'])

        return {key: config_values.get(TAB_VALUE[key], '') for key in TAB_VALUE}

    except ConfigFileNotFoundError as e:
        if print_log:
            print(e)
        return {'ip': None, 'ui': None, 'dwarf_id': None, 'client_id': None, 'update_client_id' : None, 'calibration' : None,  'debug' : None, 'trace' : None, 'log_file' : None, 'timeout_cmd' : None}

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
        log.info(f"File copied from {source_filename} to {destination_filename}")
        return True
    except FileNotFoundError:
        log.error(f"Source file {source_filename} not found in the current directory.")
    except PermissionError:
        log.error(f"Permission denied. Unable to copy to {destination_filename}.")
    except Exception as e:
        log.error(f"Error copying file: {e}")

    return False

def verif_config_data( id_param, value, print_log = False):

    if (id_param not in TAB_VALUE):
        if print_log:
            log.error(f"id ({id_param}) is not a recognized value")
        return False
    else:
        return True

# Function to dynamically import and reload the config module
def update_config_data( id_param, value, print_log = False, config_file = None, tmp_file = None):
    global CONFIG_FILE, CONFIG_FILE_TMP, LOCK_FILE

    if config_file is None:
        config_file = CONFIG_FILE

    if tmp_file is None:
        tmp_file = CONFIG_FILE_TMP

    return_value = False
    find_value = False

    if not os.path.exists(config_file):
        raise ConfigFileNotFoundError(f"Configuration file {config_file} not found.")

    if not verif_config_data(id_param, value, print_log):
        return return_value

    lock = FileLock(LOCK_FILE, thread_local=False)  # Lock file with no timeout (wait indefinitely)

    with lock:
        if print_log:
            log.debug("(B) Lock ON")
        # Create or clear the temp file
        open(tmp_file, 'w').close()

        # Read the config file and update the IP address
        with open(config_file, 'r') as file:
            lines = file.readlines()
        
        with open(tmp_file, 'w') as file:
            for line in lines:
                if line.startswith(TAB_VALUE[id_param]):
                    find_value = True
                    file.write(f'{TAB_VALUE[id_param]} = "{value}"\n')
                    if print_log:
                        log.info("Value Updated")
                else:
                    file.write(line)

        if find_value:
            # Copy tmp file
            nb_try = 0
            return_value = copy_file_in_current_directory(tmp_file, config_file)
            while nb_try < 3 and not return_value:
                return_value = copy_file_in_current_directory(tmp_file, config_file)
                nb_try += 1
                time.sleep(0.25)
        else:
            return_value = True
            if print_log:
                log.info("Value not found, file not changed")

        if print_log:
            log.debug("(B) Lock OFF")

    return return_value

# Function to update CONFIGS value
def set_config_data(config_file, config_file_tmp, lock_file, print_log = False):
    global CONFIG_FILE, CONFIG_FILE_TMP, LOCK_FILE

    CONFIG_FILE = config_file;
    CONFIG_FILE_TMP = config_file_tmp;
    LOCK_FILE = lock_file;

    if print_log:
        print(f" CONFIGS variables have been updated: {CONFIG_FILE}: {config_file} {CONFIG_FILE_TMP}: {config_file_tmp} {LOCK_FILE}: {lock_file}")

