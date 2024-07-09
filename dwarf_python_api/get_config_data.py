import os

CONFIG_FILE = 'config.py'

class ConfigFileNotFoundError(Exception):
    """Exception raised when the configuration file is not found."""
    pass

def read_config_values(config_file):
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
def get_config_data(print_error = False):
    try:
        config_values = read_config_values(CONFIG_FILE)
        return { 'ip' : config_values.get('DWARF_IP', ''), 'ui' : config_values.get('DWARF_UI',''), 'client_id' : config_values.get('CLIENT_ID', ''), 'calibration' : config_values.get('TEST_CALIBRATION', ''),'debug' : config_values.get('DEBUG', '')}
    except ConfigFileNotFoundError as e:
        if print_error:
            print (e)
        return {'ip': None, 'ui': None, 'client_id': None, 'calibration' : None,  'debug' : None}

