from .websockets_utils import connect_socket
from .websockets_utils import disconnect_socket
from .websockets_testV2 import fct_show_test
from .websockets_testV2 import fct_decode_wireshark

from .data_utils import get_exposure_index_by_name
from .data_utils import get_gain_index_by_name

from .data_wide_utils import get_wide_exposure_index_by_name
from .data_wide_utils import get_wide_gain_index_by_name

import dwarf_python_api.lib.my_logger as log

import dwarf_python_api.proto.astro_pb2 as astro
import dwarf_python_api.proto.system_pb2 as system
import dwarf_python_api.proto.camera_pb2 as camera
import dwarf_python_api.proto.focus_pb2 as focus
import dwarf_python_api.proto.protocol_pb2 as protocol
import dwarf_python_api.proto.motor_control_pb2 as motor
import dwarf_python_api.proto.ble_pb2 as ble

import configparser
import time
from datetime import datetime
import math
import re

def perform_disconnect():
    disconnect_socket()

def read_longitude():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        longitude = config.getfloat('CONFIG', 'LONGITUDE')
        return longitude
    except configparser.NoOptionError:
        print("longitude not found.")
        return None
    except configparser.NoSectionError:
        print("Data not found.")
        return None

def read_latitude():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        latitude = config.getfloat('CONFIG', 'LATITUDE')
        return latitude
    except configparser.NoOptionError:
        print("latitude not found.")
        return None
    except configparser.NoSectionError:
        print("Data not found.")
        return None

def read_timezone():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        timezone = config.get('CONFIG', 'TIMEZONE')
        return timezone
    except configparser.NoOptionError:
        print("timezone not found.")
        return None
    except configparser.NoSectionError:
        print("Data not found.")
        return None

def read_camera_exposure():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_exposure = config.get('CONFIG', 'EXPOSURE')
        return camera_exposure
    except configparser.NoOptionError:
        print("camera exposure not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_camera_gain():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_gain = config.get('CONFIG', 'GAIN')
        return camera_gain
    except configparser.NoOptionError:
        print("camera gain not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_camera_IR():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_IR = config.get('CONFIG', 'IRCUT')
        return camera_IR
    except configparser.NoOptionError:
        print("camera IRCUT value not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_camera_binning():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_binning = config.get('CONFIG', 'BINNING')
        return camera_binning
    except configparser.NoOptionError:
        print("camera binning not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_camera_format():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_format = config.get('CONFIG', 'FORMAT')
        return camera_format
    except configparser.NoOptionError:
        print("camera format of image not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_camera_count():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_count = config.get('CONFIG', 'COUNT')
        return camera_count
    except configparser.NoOptionError:
        print("Nb of images to take not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_camera_wide_exposure():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_wide_exposure = config.get('CONFIG', 'WIDE_EXPOSURE')
        return camera_wide_exposure
    except configparser.NoOptionError:
        print("camera wide exposure not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_camera_wide_gain():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_wide_gain = config.get('CONFIG', 'WIDE_GAIN')
        return camera_wide_gain
    except configparser.NoOptionError:
        print("camera wide gain not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_bluetooth_ble_wifi_type():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_wifi_type = config.get('CONFIG', 'BLE_WIFI_TYPE')
        return ble_wifi_type
    except configparser.NoOptionError:
        print("ble wifi type value not found")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False
 
def read_bluetooth_autoAP():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_autoAP = config.get('CONFIG', 'BLE_AUTO_AP')
        return ble_autoAP
    except configparser.NoOptionError:
        print("ble autostart AP value not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_bluetooth_country_list():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_country_list = config.get('CONFIG', 'BLE_COUNTRY_LIST')
        return ble_country_list
    except configparser.NoOptionError:
        print("ble country list set value not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False
 
def read_bluetooth_country():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_country = config.get('CONFIG', 'BLE_COUNTRY')
        return ble_country
    except configparser.NoOptionError:
        print("ble country value not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False
 
def read_bluetooth_ble_psd():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_psd = config.get('CONFIG', 'BLE_PSD')
        return ble_psd
    except configparser.NoOptionError:
        print("ble pwd value not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False
 
def read_bluetooth_autoSTA():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_autoSTA = config.get('CONFIG', 'BLE_AUTO_STA')
        return ble_autoSTA
    except configparser.NoOptionError:
        print("ble autostart STA value not found.")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def read_bluetooth_ble_STA_ssid():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_STA_ssid = config.get('CONFIG', 'BLE_STA_SSID')
        return ble_STA_ssid
    except configparser.NoOptionError:
        print("STA ssid value not found")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False
 
def read_bluetooth_ble_STA_pwd():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_STA_pwd = config.get('CONFIG', 'BLE_STA_PWD')
        return ble_STA_pwd
    except configparser.NoOptionError:
        print("STA pwd value not found")
        return False
    except configparser.NoSectionError:
        print("Data not found.")
        return False

def save_bluetooth_config_from_ini_file():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_psd = config.get('CONFIG', 'BLE_PSD')
        ble_STA_pwd = config.get('CONFIG', 'BLE_STA_PWD')
        ble_STA_ssid = config.get('CONFIG', 'BLE_STA_SSID')
    except configparser.NoOptionError:
        print("Wifi infos value not defined")
        return False
    except configparser.NoSectionError:
        print("Wifi Data not found.")
        return False
 
    # check value
    if ble_psd=="" or ble_STA_pwd=="" or ble_STA_ssid=="":
        print("Wifi infos empty value detected")
        return False
 
    # Specify the path to your HTML file
    html_file_path = 'dwarf_ble_connect/connect_dwarf.html'

    # Read the HTML file
    with open(html_file_path, 'r') as html_file:
      lines = html_file.readlines()

    # Define the pattern to match JavaScript variable assignments
    pattern1 = re.compile(r'let BluetoothPWD = ".*?";')
    pattern2 = re.compile(r'let BleSTASSIDDwarf = ".*?";')
    pattern3 = re.compile(r'let BleSTAPWDDwarf = ".*?";')

    # Loop through each line and replace the target line if found
    modified_lines = []
    for line in lines:
      if pattern1.match(line):
        # Replace the line with the new variable assignment
        modified_lines.append(f'let BluetoothPWD = "{ble_psd}";\n')
      elif pattern2.match(line):
        # Replace the line with the new variable assignment
        modified_lines.append(f'let BleSTASSIDDwarf = "{ble_STA_ssid}";\n')
      elif pattern3.match(line):
        # Replace the line with the new variable assignment
        modified_lines.append(f'let BleSTAPWDDwarf = "{ble_STA_pwd}";\n')
      else:
        modified_lines.append(line)

    # Write the modified content back to the HTML file
    with open(html_file_path, 'w') as html_file:
      html_file.writelines(modified_lines)

    return True

def parse_ra_to_float(ra_string):
    # Split the RA string into hours, minutes, and seconds
    hours, minutes, seconds = map(float, ra_string.split(':'))

    # Convert to decimal degrees
    ra_decimal = hours + minutes / 60 + seconds / 3600

    return ra_decimal
    
def parse_dec_to_float(dec_string):
    # Split the Dec string into degrees, minutes, and seconds
    if dec_string[0] == '-':
        sign = -1
        dec_string = dec_string[1:]
    else:
        sign = 1
    print(dec_string)
    degrees, minutes, seconds = map(float, dec_string.split(':'))

    # Convert to decimal degrees
    dec_decimal = sign * degrees + minutes / 60 + seconds / 3600

    return dec_decimal

def perform_getstatus():

    # GET STATUS
    module_id = 1  # MODULE_TELEPHOTO
    type_id = 0; #REQUEST

    ReqGetSystemWorkingState_message = camera.ReqGetSystemWorkingState()

    command = 10039 #CMD_CAMERA_TELE_GET_SYSTEM_WORKING_STATE
    response = connect_socket(ReqGetSystemWorkingState_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Get Status success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def unset_HostMaster():

    # SET Host
    module_id = 4  # MODULE_SYSTEM
    type_id = 0; #REQUEST

    ReqSetHostSlaveMode_message = system.ReqSetHostSlaveMode()
    ReqSetHostSlaveMode_message.mode = 0
    
    command = 13004 #CMD_SYSTEM_SET_HOSTSLAVE_MODE
    response = connect_socket(ReqSetHostSlaveMode_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Unset Host SLAVE success")
          log.success("Need to disconnect to take effect")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_goto(ra, dec, target):

    # GOTO
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqGotoDSO_message = astro.ReqGotoDSO()
    ReqGotoDSO_message.ra = ra
    ReqGotoDSO_message.dec = dec
    ReqGotoDSO_message.target_name = target

    command = 11002 #CMD_ASTRO_START_GOTO_DSO
    response = connect_socket(ReqGotoDSO_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Goto success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_goto_stellar(target_id, target_name):

    if read_longitude() is None:
        print("Longitude is not defined! ")
        return

    if read_latitude() is None:
        print("Latitude is not defined! ")
        return

    # GOTO
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqGotoSolarSystem_message = astro.ReqGotoSolarSystem()
    ReqGotoSolarSystem_message.index = target_id
    ReqGotoSolarSystem_message.lon = read_longitude()
    ReqGotoSolarSystem_message.lat = read_latitude()
    ReqGotoSolarSystem_message.target_name = target_name

    command = 11003 #CMD_ASTRO_START_GOTO_SOLAR_SYSTEM
    response = connect_socket(ReqGotoSolarSystem_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Goto success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_open_camera():

    # OPEN TELE PHOTO
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    ReqPhoto_message = camera.ReqPhoto()

    command = 10000 #CMD_CAMERA_TELE_OPEN_CAMERA
    response = connect_socket(ReqPhoto_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("OPEN TELE PHOTO success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_takePhoto():

    # START TAKE TELE PHOTO
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    ReqPhoto_message = camera.ReqPhoto()

    command = 10002 #CMD_CAMERA_TELE_PHOTOGRAPH
    response = connect_socket(ReqPhoto_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("TAKE TELE PHOTO success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_open_widecamera():

    # OPEN WIDE PHOTO
    module_id = 2  # MODULE_CAMERA_WIDE
    type_id = 0; #REQUEST

    ReqPhoto_message = camera.ReqPhoto()

    command = 12000 #CMD_CAMERA_WIDE_OPEN_CAMERA
    response = connect_socket(ReqPhoto_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("OPEN WIDE PHOTO success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_takeWidePhoto():

    # START WIDE TELE PHOTO
    module_id = 2  # MODULE_CAMERA_WIDE
    type_id = 0; #REQUEST

    ReqPhoto_message = camera.ReqPhoto()

    command = 12022 #CMD_CAMERA_WIDE_PHOTOGRAPH
    response = connect_socket(ReqPhoto_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("TAKE WIDE PHOTO success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_waitEndAstroPhoto():

    # use special message to get end of shooting
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    response = connect_socket("ASTRO CAPTURE ENDING", None, type_id, module_id)

    if response is not False: 

        if response == 0:
            log.success("ASTRO CAPTURE ENDING success")
            return True
        else:
            log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False

def perform_waitEndAstroWidePhoto():

    # use special message to get end of shooting
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    response = connect_socket("ASTRO WIDE CAPTURE ENDING", None, type_id, module_id)

    if response is not False: 

        if response == 0:
            log.success("ASTRO WIDE CAPTURE ENDING success")
            return True
        else:
            log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False

def perform_takeAstroPhoto():

    # START CAPTURE RAW LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqCaptureRawLiveStacking_message = astro.ReqCaptureRawLiveStacking()

    command = 11005 #CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING
    response = connect_socket(ReqCaptureRawLiveStacking_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("START CAPTURE RAW LIVE STACKING success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_stopAstroPhoto():

    # STOP CAPTURE RAW LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStopCaptureRawLiveStacking_message = astro.ReqStopCaptureRawLiveStacking()

    command = 11006 #CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING
    response = connect_socket(ReqStopCaptureRawLiveStacking_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("STOP CAPTURE RAW LIVE STACKING success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_takeAstroWidePhoto():

    # START CAPTURE WIDE RAW WIDE LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqCaptureRawLiveStacking_message = astro.ReqCaptureRawLiveStacking()

    command = 11016 #CMD_ASTRO_START_CAPTURE_WIDE_RAW_LIVE_STACKING ?? Tob confirmed
    response = connect_socket(ReqCaptureRawLiveStacking_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("START CAPTURE WIDE RAW LIVE STACKING success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_stopAstroWidePhoto():

    # STOP CAPTURE RAW LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStopCaptureRawLiveStacking_message = astro.ReqStopCaptureRawLiveStacking()

    command = 11017 #CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING
    response = connect_socket(ReqStopCaptureRawLiveStacking_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("STOP CAPTURE RAW LIVE STACKING success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_GoLive():

    # CMD_ASTRO_GO_LIVE
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqGoLive_message = astro.ReqGoLive()

    command = 11010 #CMD_ASTRO_GO_LIVE
    response = connect_socket(ReqGoLive_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("GO LIVE success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_time():

    # SET TIME
    module_id = 4  # MODULE_SYSTEM
    type_id = 0; #REQUEST

    ReqSetTime_message = system.ReqSetTime()

    # Local Time
    now = datetime.now()

    # Format the time in the required OCAT time format: YYYYMMDDHHMMSS
    ocat_time = now.strftime('%Y%m%d%H%M%S')

    # Assign the formatted time to ReqSetTime_message.timestamp
    ReqSetTime_message.timestamp = int(ocat_time)
    
    # UTC
    ReqSetTime_message.timestamp = math.floor(time.time())

    command = 13000 #CMD_SYSTEM_SET_TIME
    response = connect_socket(ReqSetTime_message, command, type_id, module_id)
    #log.success(f"Get Result : {response}")

    if response is not False: 

      if response == 0:
          log.success("Set Time success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_timezone():

    # SET TIMEZONE
    module_id = 4  # MODULE_SYSTEM
    type_id = 0; #REQUEST

    ReqSetTimezone_message = system.ReqSetTimezone()
    ReqSetTimezone_message.timezone = read_timezone()

    command = 13001 #CMD_SYSTEM_SET_TIME_ZONE
    response = connect_socket(ReqSetTimezone_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Set TimeZone success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_calibration():

    # CALIBRATION
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStartCalibration_message = astro.ReqStartCalibration ()

    command = 11000 #CMD_ASTRO_START_CALIBRATION

    response = connect_socket(ReqStartCalibration_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Calibration success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_stop_calibration():

    # STOP CALIBRATION
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStoptCalibration_message = astro.ReqStopCalibration ()

    command = 11001 #CMD_ASTRO_STOP_CALIBRATION

    response = connect_socket(ReqStoptCalibration_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Stop Calibration success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_stop_goto():

    # STOP GOTO
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStopGoto_message = astro.ReqStopGoto ()

    command = 11004 #CMD_ASTRO_STOP_GOTO

    response = connect_socket(ReqStopGoto_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Stop Goto success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_start_autofocus(infinite = False):

    # AutoFocus
    module_id = 8  # MODULE_FOCUS
    type_id = 0; #REQUEST

    ReqAstroAutoFocus_message = focus.ReqAstroAutoFocus ()

    # Assign the value : infinite = False : 0  True 1
    ReqAstroAutoFocus_message.mode = int(infinite)

    command = 15004 #CMD_FOCUS_START_ASTRO_AUTO_FOCUS

    response = connect_socket(ReqAstroAutoFocus_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Autofocus success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_stop_autofocus():

    # AutoFocus
    module_id = 8  # MODULE_FOCUS
    type_id = 0; #REQUEST

    ReqStopAstroAutoFocus_message = focus.ReqStopAstroAutoFocus ()

    command = 15005 #CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS

    response = connect_socket(ReqStopAstroAutoFocus_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Autofocus Stop success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_decoding_test(show_test, show_test1, show_test2):

    fct_show_test(show_test, show_test1, show_test2)


def perform_decode_wireshark(user_frame, masked, user_maskedcode):

    fct_decode_wireshark(user_frame, masked, user_maskedcode)

def format_double(value_str):
    try:
        value = float(value_str)
        if value <= 0:
            return value_str
        elif 0 < value < 1:
            # Représenter sous la forme "1/x"
            denominator = int(1 / value)
            return f"1/{denominator}"
        else:
            # Conserver la représentation en virgule flottante pour d'autres cas
            return value_str
    except ValueError:
        # La chaîne n'est pas un nombre valide
        return value_str

def perform_get_all_camera_setting():

  module_id = 1  # MODULE_TELE_CAMERA
  type_id = 0; #REQUEST

  ReqGetAllParams_message = camera.ReqGetAllParams ()

  command = 10036; #CMD_CAMERA_TELE_GET_ALL_PARAMS

  response = connect_socket(ReqGetAllParams_message, command, type_id, module_id)
  
  return response

def perform_get_all_feature_camera_setting():

  module_id = 1  # MODULE_TELE_CAMERA
  type_id = 0; #REQUEST

  ReqGetAllFeatureParams_message = camera.ReqGetAllFeatureParams ()

  command = 10038; #CMD_CAMERA_TELE_GET_ALL_FEATURE_PARAMS

  response = connect_socket(ReqGetAllFeatureParams_message, command, type_id, module_id)

  return response

def perform_get_all_camera_wide_setting():

  module_id = 2  # MODULE_WIDE_CAMERA
  type_id = 0; #REQUEST

  ReqGetAllParams_message = camera.ReqGetAllParams ()

  command = 12027; #CMD_CAMERA_WIDE_GET_ALL_PARAMS

  response = connect_socket(ReqGetAllParams_message, command, type_id, module_id)
  
  return response

def perform_get_camera_setting( type):

  Test = False
  if Test:
    # brightness
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetBrightness_message = camera.ReqGetBrightness ()

    command = 10016; #CMD_CAMERA_TELE_GET_BRIGHTNESS

    response = connect_socket(ReqGetBrightness_message, command, type_id, module_id)

    ReqGetContrast_message = camera.ReqGetContrast ()

    command = 10018; #CMD_CAMERA_TELE_GET_CONTRAST

    response = connect_socket(ReqGetContrast_message, command, type_id, module_id)

  if (type == "exposure"):
    # exposure
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetExp_message = camera.ReqGetExp ()

    command = 10010; #CMD_CAMERA_TELE_GET_EXP

    response = connect_socket(ReqGetExp_message, command, type_id, module_id)

    return format_double(response)

  elif (type == "gain"):
    # gain
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetGain_message = camera.ReqGetGain ()

    command = 10014; #CMD_CAMERA_TELE_GET_GAIN

    response = connect_socket(ReqGetGain_message, command, type_id, module_id)

    return response

  elif (type == "IR"):
    # IR
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetIrCut_message = camera.ReqGetIrCut ()

    command = 10032; #CMD_CAMERA_TELE_GET_IRCUT

    response = connect_socket(ReqGetIrCut_message, command, type_id, module_id)

    return response

  elif (type == "binning"):
    # binning
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
    ReqSetFeatureParams_message.param.hasAuto = False;
    ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
    ReqSetFeatureParams_message.param.id = 0; # "Astro binning"
    ReqSetFeatureParams_message.param.mode_index = 0;
    ReqSetFeatureParams_message.param.index = int(value);
    ReqSetFeatureParams_message.param.continue_value = 0;

    command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM

    response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

  elif (type == "fileFormat"):
    # fileFormat
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
    ReqSetFeatureParams_message.param.hasAuto = False;
    ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
    ReqSetFeatureParams_message.param.id = 2; # "Astro format"
    ReqSetFeatureParams_message.param.mode_index = 0;
    ReqSetFeatureParams_message.param.index = int(value);
    ReqSetFeatureParams_message.param.continue_value = 0;

    command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM

    response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

  elif (type == "count"):
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
    ReqSetFeatureParams_message.param.hasAuto = False;
    ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
    ReqSetFeatureParams_message.param.id = 1; # "Astro img_to_take"
    ReqSetFeatureParams_message.param.mode_index = 1;
    ReqSetFeatureParams_message.param.index = 0;
    ReqSetFeatureParams_message.param.continue_value = int(value);

    command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM
    cmd = Dwarfii_Api.DwarfCMD.CMD_CAMERA_TELE_SET_FEATURE_PARAM;

    response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

  elif (type == "wide_exposure"):
    # exposure
    module_id = 2  # MODULE_WIDE_CAMERA
    type_id = 0; #REQUEST

    ReqGetExp_message = camera.ReqGetExp ()

    command = 12005; #CMD_CAMERA_WIDE_GET_EXP

    response = connect_socket(ReqGetExp_message, command, type_id, module_id)

    return format_double(response)

  elif (type == "wide_gain"):
    # gain
    module_id = 2  # MODULE_WIDE_CAMERA
    type_id = 0; #REQUEST

    ReqGetGain_message = camera.ReqGetGain ()

    command = 12007; #CMD_CAMERA_WIDE_GET_GAIN

    response = connect_socket(ReqGetGain_message, command, type_id, module_id)

    return response

  return response

def perform_update_camera_setting( type, value, dwarf_id = "2"):

  if (type == "exposure"):
    # exposure_mode
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetExpMode_message = camera.ReqSetExpMode ()
    ReqSetExpMode_message.mode = 1

    command = 10007; #CMD_CAMERA_TELE_SET_EXP_MODE

    response = connect_socket(ReqSetExpMode_message, command, type_id, module_id)

    # exposure
    ReqSetExp_message = camera.ReqSetExp ()
    ReqSetExp_message.index = get_exposure_index_by_name(str(value), str(dwarf_id))

    command = 10009; #CMD_CAMERA_TELE_SET_EXP

    response = connect_socket(ReqSetExp_message, command, type_id, module_id)


  elif (type == "gain"):
    # gain 
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetGain_message = camera.ReqSetGain ()
    ReqSetGain_message.index = get_gain_index_by_name(str(value),str(dwarf_id))

    command = 10013; #CMD_CAMERA_TELE_SET_GAIN

    response = connect_socket(ReqSetGain_message, command, type_id, module_id)

  elif (type == "IR"):
    # gain
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetIrCut_message = camera.ReqSetIrCut ()
    ReqSetIrCut_message.value = int(value)

    command = 10031; #CMD_CAMERA_TELE_SET_IRCUT

    response = connect_socket(ReqSetIrCut_message, command, type_id, module_id)

  elif (type == "binning"):
    # binning
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
    ReqSetFeatureParams_message.param.hasAuto = False;
    ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
    ReqSetFeatureParams_message.param.id = 0; # "Astro binning"
    ReqSetFeatureParams_message.param.mode_index = 0;
    ReqSetFeatureParams_message.param.index = int(value);
    ReqSetFeatureParams_message.param.continue_value = 0;

    command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM

    response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

  elif (type == "fileFormat"):
    # fileFormat
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
    ReqSetFeatureParams_message.param.hasAuto = False;
    ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
    ReqSetFeatureParams_message.param.id = 2; # "Astro format"
    ReqSetFeatureParams_message.param.mode_index = 0;
    ReqSetFeatureParams_message.param.index = int(value);
    ReqSetFeatureParams_message.param.continue_value = 0;

    command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM

    response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

  elif (type == "count"):
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetFeatureParams_message = camera.ReqSetFeatureParams ()
    ReqSetFeatureParams_message.param.hasAuto = False;
    ReqSetFeatureParams_message.param.auto_mode = 1; # Manual
    ReqSetFeatureParams_message.param.id = 1; # "Astro img_to_take"
    ReqSetFeatureParams_message.param.mode_index = 1;
    ReqSetFeatureParams_message.param.index = 0;
    ReqSetFeatureParams_message.param.continue_value = int(value);

    command = 10037; #CMD_CAMERA_TELE_SET_FEATURE_PARAM

    response = connect_socket(ReqSetFeatureParams_message, command, type_id, module_id)

  elif (type == "wide_exposure"):
    # exposure_mode
    module_id = 2  # MODULE_WIDE_CAMERA
    type_id = 0; #REQUEST

    ReqSetExpMode_message = camera.ReqSetExpMode ()
    ReqSetExpMode_message.mode = 1

    command = 12002; #CMD_CAMERA_WIDE_SET_EXP_MODE

    response = connect_socket(ReqSetExpMode_message, command, type_id, module_id)

    # exposure
    ReqSetExp_message = camera.ReqSetExp ()
    ReqSetExp_message.index = get_wide_exposure_index_by_name(str(value), str(dwarf_id))

    command = 12004; #CMD_CAMERA_WIDE_SET_EXP

    response = connect_socket(ReqSetExp_message, command, type_id, module_id)

  elif (type == "wide_gain"):
    # gain 
    module_id = 2  # MODULE_WIDE_CAMERA
    type_id = 0; #REQUEST

    ReqSetGain_message = camera.ReqSetGain ()
    ReqSetGain_message.index = get_wide_gain_index_by_name(str(value),str(dwarf_id))
    print (f"index wide Gain =  {ReqSetGain_message.index}")
    command = 12006; #CMD_CAMERA_WIDE_SET_GAIN

    response = connect_socket(ReqSetGain_message, command, type_id, module_id)

  if response is not False: 

      if response == 0:
          log.success("Update camera setting")
          return True
      else:
          log.error(f"Error code: {response}")
  else:
      log.error("Dwarf API: Dwarf Device not connected")

  return False

def motor_action( action ):

    module_id = 6  # MODULE_MOTOR
    type_id = 0; #REQUEST

    if (action == 5):
      ReqMotorReset_message = motor.ReqMotorReset ()
      ReqMotorReset_message.id= 1;
      ReqMotorReset_message.direction = 0;
      command = 14003; #CMD_STEP_MOTOR_RESET
      response = connect_socket(ReqMotorReset_message, command, type_id, module_id)

    if (action == 6):
      ReqMotorReset_message = motor.ReqMotorReset ()
      ReqMotorReset_message.id= 2;
      ReqMotorReset_message.direction = 1;
      command = 14003; #CMD_STEP_MOTOR_RESET
      response = connect_socket(ReqMotorReset_message, command, type_id, module_id)

    if (action == 1):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 2;
      ReqMotorRunTo_message.end_position = 317;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 2;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    if (action == 2):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 1;
      ReqMotorRunTo_message.end_position = 160;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 3;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    if (action == 3):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 2;
      ReqMotorRunTo_message.end_position = 146.5;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 3;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    if (action == 7):  # For D3
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 2;
      ReqMotorRunTo_message.end_position = 166.5;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 3;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    if (action == 4):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 1;
      ReqMotorRunTo_message.end_position = 69;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 3;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    if (action == 0):
      ReqMotorRun_message = motor.ReqMotorRun ()
      ReqMotorRun_message.id= 2;
      ReqMotorRun_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRun_message.direction = 0;
      ReqMotorRun_message.speed_ramping = 100;
      ReqMotorRun_message.resolution_level = 3;
      command = 14000; #CMD_STEP_MOTOR_RUN
      response = connect_socket(ReqMotorRun_message, command, type_id, module_id)

    if (action == 10):
      ReqMotorServiceJoystickFixedAngle_message = motor.ReqMotorServiceJoystickFixedAngle ()
      ReqMotorServiceJoystickFixedAngle_message.vector_length = 0.8; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorServiceJoystickFixedAngle_message.speed = 15;

      command = 14006; #CMD_STEP_MOTOR_SERVICE_JOYSTICK
      response = connect_socket(ReqMotorServiceJoystickFixedAngle_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Motor Action success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False
