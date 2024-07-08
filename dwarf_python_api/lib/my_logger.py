CONFIG_FILE = 'config.py'

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
    return { 'debug' : config_values.get('DEBUG', '')}

def debug(*messages):
    data_config = get_current_data()

    if data_config['debug'] != "":
        for message in messages:
            print(message)

def error(*messages):
    for message in messages:
        print(message)
