import paramiko
import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.get_config_data import update_config_data, CONFIG_FILE

def update_client_id_from_last_session(dwarf_ip, config_file = CONFIG_FILE):
    ssh_port = 22
    ssh_username = "root"
    ssh_password = "rockchip"
    remote_file_path = "/userdata/log/dwarf/dwarf.log"
    local_file_path = "dwarf.log"
    search_string = "master client id ="

    return_value = False

    # Test SSH connection
    if test_ssh_connection(dwarf_ip, ssh_port, ssh_username, ssh_password):
        log.info("connection successful to DWARF ")
            
        # Download the file from the SSH server
        download_file_via_ssh(dwarf_ip, ssh_port, ssh_username, ssh_password, remote_file_path, local_file_path)

        # Extract the last line containing the search string
        last_matching_line = extract_last_matching_line(local_file_path, search_string)

        # Extract the desired value after the search string
        if last_matching_line:
            new_client_id = extract_desired_value(last_matching_line, search_string)
            log.info(f"Extracted new CLIENT_ID: {new_client_id}")
            
            # Update the config file with the new client_id
            update_config_data("client_id", new_client_id, True, config_file)
            log.info(f"Updated CLIENT_ID to match DwarfLab app one")
        else:
            log.info("No line containing the search string was found. Retrying...")
    else:
        log.info("DWARF connection failed. Retrying...")

def download_file_via_ssh(ssh_host, ssh_port, ssh_username, ssh_password, remote_file_path, local_file_path):
    # Connect to the SSH server
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ssh_host, port=ssh_port, username=ssh_username, password=ssh_password)
    
    # Use SFTP to download the file
    sftp = ssh.open_sftp()
    sftp.get(remote_file_path, local_file_path)
    sftp.close()
    ssh.close()

def extract_last_matching_line(file_path, search_string):
    last_matching_line = ""
    # Open the local file to read its content
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        # Iterate through each line in the file
        for line in file:
            # If the search string is found in the line, update the last matching line
            if search_string in line:
                last_matching_line = line.strip()
    return last_matching_line

def extract_desired_value(line, search_string):
    # Find the starting index of the desired value in the line
    start_index = line.find(search_string) + len(search_string)
    # Return the extracted value after the search string
    return line[start_index:].strip()

def test_ssh_connection(ssh_host, ssh_port, ssh_username, ssh_password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ssh_host, port=ssh_port, username=ssh_username, password=ssh_password)
        ssh.close()
        return True
    except Exception as e:
        log.error(f"Failed to connect to SSH server: {e}")
        return False

