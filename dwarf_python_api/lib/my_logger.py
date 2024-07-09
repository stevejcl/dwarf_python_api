# import data for config.py
from dwarf_python_api.get_config_data import get_config_data

def debug(*messages):
    data_config = get_config_data()

    if data_config['debug']:
        for message in messages:
            print(message)

def error(*messages):
    for message in messages:
        print(message)
