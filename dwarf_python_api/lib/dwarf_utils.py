from .websockets_utils import connect_socket
from .websockets_utils import get_camera_param_v3
from .websockets_utils import get_client_status
from .websockets_utils import disconnect_socket
from .websockets_testV2 import fct_show_test
from .websockets_testV2 import fct_decode_wireshark

from .data_utils import get_exposure_index_by_name
from .data_utils import get_gain_index_by_name
from .data_utils import get_exposure_name_by_index
from .data_utils import get_ir_filter_index_by_name
from .data_utils import get_wb_preset_index_by_name
from .data_utils import get_burst_interval_seconds_by_name
from .data_utils import get_timelapse_interval_seconds_by_name
from .data_utils import get_timelapse_totaltime_seconds_by_name

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
import dwarf_python_api.proto.rgb_pb2 as rgb_power
import dwarf_python_api.proto.task_center_pb2 as task_center
import dwarf_python_api.proto.param_pb2 as param

import configparser
import time
from datetime import datetime
import math
import re
import requests
import dwarf_python_api.get_config_data

def perform_disconnect():
    disconnect_socket()

def perform_reboot():

    # Power Down
    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqPowerReboot_message = rgb_power.ReqReboot ()

    command = 13505; # CMD_RGB_POWER_REBOOT
    response = connect_socket(ReqPowerReboot_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Reboot command success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

def perform_powerdown():

    # Power Down
    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqPowerDown_message = rgb_power.ReqPowerDown ()

    command = 13502; # CMD_RGB_POWER_POWER_DOWN
    response = connect_socket(ReqPowerDown_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Shutdown command success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

def perform_powerOpenRGB():
    # Turn On RGB Lights
    type = "Turn On RGB Lights"

    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqOpenRgb_message = rgb_power.ReqOpenRgb ()

    command = 13500; # CMD_RGB_POWER_OPEN_RGB
    response = connect_socket(ReqOpenRgb_message, command, type_id, module_id)

    return get_result_value(type, response)

def perform_powerCloseRGB():
    # Turn Off RGB Lights
    type = "Turn Off RGB Lights"

    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqCloseRgb_message = rgb_power.ReqCloseRgb ()

    command = 13501; # CMD_RGB_POWER_CLOSE_RGB
    response = connect_socket(ReqCloseRgb_message, command, type_id, module_id)

    return get_result_value(type, response)

def perform_powerIndOn():
    # Turn On RGB Lights
    type = "Turn On Power Lights"

    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqOpenPowerInd_message = rgb_power.ReqOpenPowerInd ()

    command = 13503; # CMD_RGB_POWER_POWERIND_ON
    response = connect_socket(ReqOpenPowerInd_message, command, type_id, module_id)

    return get_result_value(type, response)

def perform_powerIndOff():
    # Turn Off RGB Lights
    type = "Turn Off Power Lights"

    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqClosePowerInd_message = rgb_power.ReqClosePowerInd ()

    command = 13504; # CMD_RGB_POWER_POWERIND_OFF
    response = connect_socket(ReqClosePowerInd_message, command, type_id, module_id)

    return get_result_value(type, response)

def read_longitude():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        longitude = config.getfloat('CONFIG', 'LONGITUDE')
        return longitude
    except configparser.NoOptionError:
        log.error("longitude not found in config file.")
        return None
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return None

def read_latitude():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        latitude = config.getfloat('CONFIG', 'LATITUDE')
        return latitude
    except configparser.NoOptionError:
        log.error("latitude not found in config file.")
        return None
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return None

def read_timezone():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        timezone = config.get('CONFIG', 'TIMEZONE')
        return timezone
    except configparser.NoOptionError:
        log.error("timezone not found in config file.")
        return None
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return None

def read_camera_exposure():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_exposure = config.get('CONFIG', 'EXPOSURE')
        return camera_exposure
    except configparser.NoOptionError:
        log.error("camera exposure not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_camera_gain():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_gain = config.get('CONFIG', 'GAIN')
        return camera_gain
    except configparser.NoOptionError:
        log.error("camera gain not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_camera_IR():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_IR = config.get('CONFIG', 'IRCUT')
        return camera_IR
    except configparser.NoOptionError:
        log.error("camera IRCUT value not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_camera_binning():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_binning = config.get('CONFIG', 'BINNING')
        return camera_binning
    except configparser.NoOptionError:
        log.error("camera binning not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_camera_format():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_format = config.get('CONFIG', 'FORMAT')
        return camera_format
    except configparser.NoOptionError:
        log.error("camera format of image not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_camera_count():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_count = config.get('CONFIG', 'COUNT')
        return camera_count
    except configparser.NoOptionError:
        log.error("Nb of images to take not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_camera_wide_exposure():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_wide_exposure = config.get('CONFIG', 'WIDE_EXPOSURE')
        return camera_wide_exposure
    except configparser.NoOptionError:
        log.error("camera wide exposure not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_camera_wide_gain():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        camera_wide_gain = config.get('CONFIG', 'WIDE_GAIN')
        return camera_wide_gain
    except configparser.NoOptionError:
        log.error("camera wide gain not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_bluetooth_ble_wifi_type():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_wifi_type = config.get('CONFIG', 'BLE_WIFI_TYPE')
        return ble_wifi_type
    except configparser.NoOptionError:
        log.error("ble wifi type value not found in config file")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False
 
def read_bluetooth_autoAP():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_autoAP = config.get('CONFIG', 'BLE_AUTO_AP')
        return ble_autoAP
    except configparser.NoOptionError:
        log.error("ble autostart AP value not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_bluetooth_country_list():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_country_list = config.get('CONFIG', 'BLE_COUNTRY_LIST')
        return ble_country_list
    except configparser.NoOptionError:
        log.error("ble country list set value not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False
 
def read_bluetooth_country():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_country = config.get('CONFIG', 'BLE_COUNTRY')
        return ble_country
    except configparser.NoOptionError:
        log.error("ble country value not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False
 
def read_bluetooth_ble_psd():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_psd = config.get('CONFIG', 'BLE_PSD')
        return ble_psd
    except configparser.NoOptionError:
        log.error("ble pwd value not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False
 
def read_bluetooth_autoSTA():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_autoSTA = config.get('CONFIG', 'BLE_AUTO_STA')
        return ble_autoSTA
    except configparser.NoOptionError:
        log.error("ble autostart STA value not found in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def read_bluetooth_ble_STA_ssid():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_STA_ssid = config.get('CONFIG', 'BLE_STA_SSID')
        return ble_STA_ssid
    except configparser.NoOptionError:
        log.error("STA ssid value not found in config file")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False
 
def read_bluetooth_ble_STA_pwd():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_STA_pwd = config.get('CONFIG', 'BLE_STA_PWD')
        return ble_STA_pwd
    except configparser.NoOptionError:
        log.error("STA pwd value not found in config file")
        return False
    except configparser.NoSectionError:
        log.error("Data not found in config file.")
        return False

def save_bluetooth_config_from_ini_file():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        ble_psd = config.get('CONFIG', 'BLE_PSD')
        ble_STA_pwd = config.get('CONFIG', 'BLE_STA_PWD')
        ble_STA_ssid = config.get('CONFIG', 'BLE_STA_SSID')
    except configparser.NoOptionError:
        log.error("Wifi infos value not defined in config file.")
        return False
    except configparser.NoSectionError:
        log.error("Wifi Data not found in config file.")
        return False
 
    # check value
    if ble_psd=="" or ble_STA_pwd=="" or ble_STA_ssid=="":
        log.error("Wifi infos empty value detected")
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

    ReqsetMasterLock_message = system.ReqsetMasterLock()
    ReqsetMasterLock_message.lock = False
    
    command = 13004 #CMD_SYSTEM_SET_MASTERLOCK
    response = connect_socket(ReqsetMasterLock_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Unset Host Device success")
          log.success("Need to disconnect to take effect")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def set_HostMaster():

    # SET Host
    module_id = 4  # MODULE_SYSTEM
    type_id = 0; #REQUEST

    ReqsetMasterLock_message = system.ReqsetMasterLock()
    ReqsetMasterLock_message.lock = True
    
    command = 13004 #CMD_SYSTEM_SET_MASTERLOCK
    response = connect_socket(ReqsetMasterLock_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("set Host Device success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

# ---------------------------------------------------------------------------
# V3: "entering astro mode" handshake (MODULE_DEVICE_CONFIG module, 14)
# ---------------------------------------------------------------------------
# In V3, after set_HostMaster(), the device must be explicitly switched to
# astro mode and "entered" into camera before ASTRO/CAMERA commands respond
# correctly. This sequence (rather than directly opening the tele/wide
# camera) is what replaces the historical blocking point from V2. Sequence
# and values (mode=8, tech=2) taken from the dwarfAlp reference
# implementation, verified on real hardware, AND confirmed by the
# shooting_mode_and_techs diagnostic (CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO)
# obtained on a real Dwarf Mini:
#
#   mode=1  parent=-1  techs=[1, 3, 4, 5]   <- SIMPLE PHOTO (1=photo, 3=burst,
#                                               4=video, 5=timelapse)
#   mode=8  parent=3   techs=[2, 3, 4, 5]   <- ASTRO (confirmed working)
#   mode=9  parent=3   techs=[2, 3, 4, 5]   <- astro variant (EQ?)
#   mode=10 parent=3   techs=[2, 3, 4, 5]   <- astro variant
#
# mode=1/tech=1 (simple photo) had not yet been tested on real hardware at
# the time this was written - to be confirmed, but it's the strongest
# hypothesis we have.

SHOOTING_MODE_ASTRO = 8
SHOOTING_TECH_DEEP_SKY = 2

SHOOTING_MODE_PHOTO = 1
SHOOTING_TECH_PHOTO = 1


def perform_get_device_state_info():
    """CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO (16405) - full device state.
    Purely informational, useful at the start of a connection."""

    module_id = protocol.MODULE_DEVICE_CONFIG
    type_id = 0 #REQUEST

    ReqGetDeviceStateInfo_message = task_center.ReqGetDeviceStateInfo()

    command = protocol.CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO
    response = connect_socket(ReqGetDeviceStateInfo_message, command, type_id, module_id)

    if response is not False:
        log.success(f"GET DEVICE STATE INFO code: {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_switch_shooting_mode(mode=SHOOTING_MODE_ASTRO):
    """CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_MODE (16402).
    mode=8 = astro mode. Returns the effective shooting_mode_id, or False."""

    module_id = protocol.MODULE_DEVICE_CONFIG
    type_id = 0 #REQUEST

    ReqSwitchShootingMode_message = task_center.ReqSwitchShootingMode()
    ReqSwitchShootingMode_message.mode = mode

    command = protocol.CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_MODE
    response = connect_socket(ReqSwitchShootingMode_message, command, type_id, module_id)

    if response is not False:
        log.success(f"SWITCH SHOOTING MODE -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_enter_camera(encode_type=1):
    """CMD_GLOBAL_TASK_MANAGER_ENTER_CAMERA (16404).
    This is the V3 command that corresponds to "initializing the camera":
    without it, subsequent ASTRO/CAMERA commands do not respond."""

    module_id = protocol.MODULE_DEVICE_CONFIG
    type_id = 0 #REQUEST

    ReqEnterCamera_message = task_center.ReqEnterCamera()
    ReqEnterCamera_message.client_param.encode_type = encode_type

    command = protocol.CMD_GLOBAL_TASK_MANAGER_ENTER_CAMERA
    response = connect_socket(ReqEnterCamera_message, command, type_id, module_id)

    if response is not False:
        log.success(f"ENTER CAMERA -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_switch_shooting_tech(tech=SHOOTING_TECH_DEEP_SKY):
    """CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_TECH (16403).
    tech=2 = Deep Sky / stacking."""

    module_id = protocol.MODULE_DEVICE_CONFIG
    type_id = 0 #REQUEST

    ReqSwitchShootingTech_message = task_center.ReqSwitchShootingTech()
    ReqSwitchShootingTech_message.tech = tech

    command = protocol.CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_TECH
    response = connect_socket(ReqSwitchShootingTech_message, command, type_id, module_id)

    if response is not False:
        log.success(f"SWITCH SHOOTING TECH -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_preview_quality(level=1):
    """CMD_CAMERA_TELE_SET_PREVIEW_QUALITY (10050).
    Sent by the official app right after entering astro mode.
    Best effort: should not block the sequence if the device doesn't
    respond as expected on this particular point (to be confirmed on the
    first real test)."""

    module_id = protocol.MODULE_CAMERA_TELE
    type_id = 0 #REQUEST

    ReqSetPreviewQuality_message = camera.ReqSetPreviewQuality()
    ReqSetPreviewQuality_message.level = level

    command = protocol.CMD_CAMERA_TELE_SET_PREVIEW_QUALITY
    response = connect_socket(ReqSetPreviewQuality_message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET PREVIEW QUALITY -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_enter_astro_mode():
    """Full V3 connection sequence: equivalent, for astro mode, of the
    (resolve MASTER/SLAVE + open camera) pair from V2.

    Call right after set_HostMaster() and before any ASTRO command.

    1) perform_switch_shooting_mode(8)  -> astro mode
    2) perform_enter_camera()           -> V3 camera "initialization"
    3) perform_switch_shooting_tech(2)  -> Deep Sky / stacking technique
    4) perform_set_preview_quality(1)   -> preview quality (best effort)

    Returns True if the first 3 steps succeed (the 4th is non-blocking),
    False otherwise.

    Confirmed working on real hardware (Dwarf Mini): SWITCH_SHOOTING_MODE
    does return 8, ENTER_CAMERA returns 8, SWITCH_SHOOTING_TECH returns 2.
    """
    return perform_enter_shooting_mode(SHOOTING_MODE_ASTRO, SHOOTING_TECH_DEEP_SKY)


def perform_enter_photo_mode():
    """Equivalent of perform_enter_astro_mode() for simple photo (no mount
    alignment, no GOTO, no stacking).

    mode=1 / tech=1, identified empirically via the shooting_mode_and_techs
    diagnostic (CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO) on a real Dwarf
    Mini: mode=1 (root, no parent) offers techniques [1, 3, 4, 5], likely
    corresponding to photo/burst/video/timelapse. NOT YET TESTED on real
    hardware at the time this was written - the strongest hypothesis we
    have, to be confirmed.
    """
    return perform_enter_shooting_mode(SHOOTING_MODE_PHOTO, SHOOTING_TECH_PHOTO)


def perform_enter_shooting_mode(mode, tech):
    """Generic function used by perform_enter_astro_mode() and
    perform_enter_photo_mode(): switches to the given (mode, tech) pair.
    """

    mode_result = perform_switch_shooting_mode(mode)
    if mode_result is False:
        log.error(f"V3: SWITCH SHOOTING MODE({mode}) failed, aborting")
        return False

    enter_result = perform_enter_camera()
    if enter_result is False:
        log.error("V3: ENTER CAMERA failed, aborting")
        return False

    tech_result = perform_switch_shooting_tech(tech)
    if tech_result is False:
        log.error(f"V3: SWITCH SHOOTING TECH({tech}) failed, aborting")
        return False

    preview_result = perform_set_preview_quality(1)
    if preview_result is False:
        log.warning("V3: SET PREVIEW QUALITY failed (non-blocking)")

    log.success(f"V3: entering mode (mode={mode}, tech={tech}) completed")
    return True


# ---------------------------------------------------------------------------
# V3: exposure/gain settings (MODULE_CAMERA_PARAMS module, 15)
# ---------------------------------------------------------------------------
# Confirmed by network capture of the official app (Dwarf Mini, "normal
# photo" session): the app does NOT use the old V2 commands
# (CMD_CAMERA_TELE_SET_EXP_MODE/SET_EXP/SET_GAIN_MODE/SET_GAIN, CAMERA_TELE
# module) but the new CAMERA_PARAMS module with a param_id encoded on 64
# bits:
#
#   Photo (tele) exposure: param_id = 0x0101000000000001, mode=1
#   Photo (tele) gain    : param_id = 0x0101000000000002, mode=1
#   Astro        exposure: param_id = 0x0201000000000001 (dwarfAlp)
#   Astro        gain    : param_id = 0x0201000000000002 (dwarfAlp)
#
# Pattern observed (2 confirmed data points + dwarfAlp): the high-order
# byte distinguishes the context (0x01=normal photo, 0x02=astro), the last
# byte the parameter type (0x01=exposure, 0x02=gain). Not yet confirmed
# for the wide camera (no data captured on this so far). "mode" (field 2)
# is 1 in both observed cases = probably "manual" (mirroring the old
# ReqSetExpMode.mode=1 in V2).
#
# The exact meaning of "value" is CONFIRMED by cross-checking with the
# settings shown in the app at the time of capture:
#   - Exposure: it's the same INDEX as the old AllowedExposures/
#     AllowedExposuresD3 table (data_utils.py) - NOT the value in seconds.
#     Confirmed: value=102 (index of "1/4") then value=111 (index of "0.5",
#     the user having set "0.5s" at that time). Use
#     perform_set_exposure_by_name_v3() to set by name rather than raw
#     index.
#   - Gain: it's the DISPLAYED value directly (e.g. 50 for "50"), NOT the
#     index of the old AllowedGains table (where "50" is at index 15).
#     Confirmed: the user went from 60 to 50 in the app, value sent = 50.

PARAM_ID_PHOTO_TELE_EXPOSURE = 0x0101000000000001
PARAM_ID_PHOTO_TELE_GAIN = 0x0101000000000002
PARAM_ID_ASTRO_EXPOSURE = 0x0201000000000001
PARAM_ID_ASTRO_GAIN = 0x0201000000000002

# Wide camera: byte "camera" 0x00 for tele, 0x10 for wide (seen in the
# CMD_NOTIFY_GENERAL_INT_PARAM notifications broadcast by the firmware).
# CONFIRMED by network capture (Dwarf 3 AND Dwarf Mini, Aug 2026):
# explicit CMD_PARAM_SET_EXPOSURE/GAIN on the wide camera in photo mode -
# identical value on both devices.
#
# NOT valid for Dwarf II: a network capture (Aug 2026) of the Dwarf II's
# wide camera in photo mode shows a DIFFERENT leading byte -
# 0x0a01100000000001/2 instead of 0x0101100000000001/2 - do not assume
# the D3/Mini constants below apply to the Dwarf II. Currently unused in
# astro_dwarf_session (it exposes no separate wide device_type for
# "Dwarf II"), so this has no active impact, but keep this in mind if
# Dwarf II wide support is ever added here or in another consumer.
PARAM_ID_PHOTO_WIDE_EXPOSURE = 0x0101100000000001
PARAM_ID_PHOTO_WIDE_GAIN = 0x0101100000000002
PARAM_ID_PHOTO_WIDE_EXPOSURE_D2 = 0x0a01100000000001  # confirmed, not yet used anywhere
PARAM_ID_PHOTO_WIDE_GAIN_D2 = 0x0a01100000000002      # confirmed, not yet used anywhere

# Astro/DSO mode, wide camera. CONFIRMED by network capture (Dwarf 3 AND
# Dwarf Mini, Aug 2026): explicit CMD_PARAM_SET_EXPOSURE/GAIN with the
# wide camera selected in astro mode - identical value on both devices.
# This supersedes the earlier "NON FIABLE" finding in MIGRATION_V3.md,
# which was based on the live HTTP API's paramId field - now shown (by
# this same capture) to be generally unreliable for exp/gain across all
# modes/devices, not just wide - the wire-level value here is a genuine
# CMD_PARAM_SET_EXPOSURE/GAIN payload, not the HTTP JSON's paramId.
#
# Dwarf II equivalent NOT confirmed and NOT assumed to follow the
# 0x0201... pattern, given the photo-mode divergence documented above -
# moot for now since astro_dwarf_session has no wide astro path for
# "Dwarf II" anyway.
PARAM_ID_ASTRO_WIDE_EXPOSURE = 0x0201100000000001
PARAM_ID_ASTRO_WIDE_GAIN = 0x0201100000000002


def perform_set_exposure_v3(value, param_id=PARAM_ID_PHOTO_TELE_EXPOSURE, mode=1):
    """CMD_PARAM_SET_EXPOSURE (16700), MODULE_CAMERA_PARAMS module (15).

    Replaces, in V3, the old CMD_CAMERA_TELE_SET_EXP_MODE +
    CMD_CAMERA_TELE_SET_EXP pair (CAMERA_TELE module) for exposure
    settings - confirmed by network capture of the official app.

    IMPORTANT: 'value' is the same INDEX as in the old AllowedExposures/
    AllowedExposuresD3 table from data_utils.py (confirmed by network
    capture: 102 == index of "1/4", 111 == index of "0.5", and the user
    had indeed set "0.5s" at the time of capture). This is NOT the raw
    exposure value (seconds) - use perform_set_exposure_by_name_v3()
    below to set by name ("0.5", "1/1000", ...) rather than by raw index.
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetExposure()
    message.param_id = param_id
    message.mode = mode
    message.value = value

    command = protocol.CMD_PARAM_SET_EXPOSURE
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET EXPOSURE (V3) -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_exposure_by_name_v3(name, dwarf_id="2", camera="tele", param_id=None, mode=1):
    """Like perform_set_exposure_v3(), but by readable name ("0.5",
    "1/1000", "1/30", ...) instead of the raw index - directly reuses the
    existing AllowedExposures/AllowedExposuresD3/AllowedExposuresMini
    table (data_utils.py), confirmed still valid in V3 (see
    MIGRATION_V3.md).

    dwarf_id: "3"/"5" to use the Dwarf 3/Mini table (more long exposure
    options), otherwise the default (Dwarf II) table.

    camera: "tele" (default) or "wide". Wide param_id CONFIRMED by
    network capture (Dwarf 3 AND Dwarf Mini, Aug 2026):
    PARAM_ID_PHOTO_WIDE_EXPOSURE. IMPORTANT: the Dwarf II uses a
    DIFFERENT, also-confirmed wide param_id
    (PARAM_ID_PHOTO_WIDE_EXPOSURE_D2) - selected automatically here based
    on dwarf_id == "2".

    param_id: explicit override, bypasses the camera/dwarf_id-based
    selection above if provided (for callers that already know the exact
    param_id they need).
    """
    if param_id is None:
        if camera == "wide":
            param_id = PARAM_ID_PHOTO_WIDE_EXPOSURE_D2 if str(dwarf_id) == "2" else PARAM_ID_PHOTO_WIDE_EXPOSURE
        else:
            param_id = PARAM_ID_PHOTO_TELE_EXPOSURE
    if camera == "wide":
        index = get_wide_exposure_index_by_name(str(name), str(dwarf_id))
    else:
        index = get_exposure_index_by_name(str(name), str(dwarf_id))
    return perform_set_exposure_v3(index, param_id=param_id, mode=mode)


def perform_set_gain_v3(value, param_id=PARAM_ID_PHOTO_TELE_GAIN, mode=1):
    """CMD_PARAM_SET_GAIN (16701), MODULE_CAMERA_PARAMS module (15).

    Replaces, in V3, the old CMD_CAMERA_TELE_SET_GAIN_MODE +
    CMD_CAMERA_TELE_SET_GAIN pair (CAMERA_TELE module) - confirmed by
    network capture of the official app.

    IMPORTANT (different from exposure): 'value' here is the DISPLAYED
    gain value directly (e.g. 50 for "50"), NOT the index of the old
    AllowedGains/AllowedGainsD3 table (where "50" is at index 15).
    Confirmed by network capture: the user went from 60 to 50 in the app,
    and the value sent was indeed 50.
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetGain()
    message.param_id = param_id
    message.mode = mode
    message.value = value

    command = protocol.CMD_PARAM_SET_GAIN
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET GAIN (V3) -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_gain_by_camera_v3(value, dwarf_id="2", camera="tele", mode=1):
    """Convenience wrapper around perform_set_gain_v3() that picks the
    right param_id for photo mode based on camera ("tele"/"wide") and
    dwarf_id, instead of requiring the caller to know the raw constant.

    Wide param_id CONFIRMED by network capture (Dwarf 3 AND Dwarf Mini,
    Aug 2026): PARAM_ID_PHOTO_WIDE_GAIN. IMPORTANT: the Dwarf II uses a
    DIFFERENT, also-confirmed wide param_id (PARAM_ID_PHOTO_WIDE_GAIN_D2)
    - selected automatically here based on dwarf_id == "2".
    """
    if camera == "wide":
        param_id = PARAM_ID_PHOTO_WIDE_GAIN_D2 if str(dwarf_id) == "2" else PARAM_ID_PHOTO_WIDE_GAIN
    else:
        param_id = PARAM_ID_PHOTO_TELE_GAIN
    return perform_set_gain_v3(value, param_id=param_id, mode=mode)


def perform_set_astro_exposure_v3(value, camera="tele", mode=1):
    """CMD_PARAM_SET_EXPOSURE (16700) for astro/DSO mode, using
    PARAM_ID_ASTRO_EXPOSURE/PARAM_ID_ASTRO_WIDE_EXPOSURE (both confirmed
    by network capture - tele independently confirmed by dwarfAlp, wide
    confirmed on a Dwarf Mini, Aug 2026 - see MIGRATION_V3.md).

    Same index convention as perform_set_exposure_v3() (index into the
    AllowedExposures/AllowedExposuresD3/AllowedExposuresMini table, not
    raw seconds) - prefer perform_set_astro_exposure_by_name_v3() to set
    by name. This applies to both "tele" and "wide".
    """
    param_id = PARAM_ID_ASTRO_WIDE_EXPOSURE if camera == "wide" else PARAM_ID_ASTRO_EXPOSURE
    return perform_set_exposure_v3(value, param_id=param_id, mode=mode)


def perform_set_astro_exposure_by_name_v3(name, dwarf_id="2", camera="tele", mode=1):
    """Like perform_set_astro_exposure_v3(), but by readable name ("0.5",
    "1/1000", "180", ...) instead of the raw index."""
    if camera == "wide":
        index = get_wide_exposure_index_by_name(str(name), str(dwarf_id))
    else:
        index = get_exposure_index_by_name(str(name), str(dwarf_id))
    return perform_set_astro_exposure_v3(index, camera=camera, mode=mode)


def perform_set_astro_gain_v3(value, camera="tele", mode=1):
    """CMD_PARAM_SET_GAIN (16701) for astro/DSO mode, using
    PARAM_ID_ASTRO_GAIN/PARAM_ID_ASTRO_WIDE_GAIN (both confirmed by
    network capture - tele independently confirmed by dwarfAlp, wide
    confirmed on a Dwarf Mini, Aug 2026 - see MIGRATION_V3.md).

    IMPORTANT: as with perform_set_gain_v3(), 'value' is the displayed
    gain value directly, not a table index. Applies to both "tele" and
    "wide".

    Range confirmed by the live HTTP API: 40-240 for tele in astro mode
    (note the minimum of 40, different from the 0 minimum in normal photo
    mode) - wide range not yet independently confirmed, use with the same
    caution as tele until cross-checked.
    """
    param_id = PARAM_ID_ASTRO_WIDE_GAIN if camera == "wide" else PARAM_ID_ASTRO_GAIN
    return perform_set_gain_v3(value, param_id=param_id, mode=mode)


# ---------------------------------------------------------------------------
# V3: reading exposure/gain parameters (MODULE_CAMERA_PARAMS module)
# ---------------------------------------------------------------------------
# IMPORTANT - different from the V2 model: there is NO "GET" command in
# this module in V3 (confirmed: param.proto only defines ReqSetXxx
# messages, no ReqGetXxx; and the official app never calls
# CMD_CAMERA_TELE_GET_ALL_PARAMS/10036 in the analyzed network capture).
#
# Instead, the firmware BROADCASTS the current value of each parameter via
# CMD_NOTIFY_GENERAL_INT_PARAM (15264) notifications, automatically:
#   - on entering a mode (right after ENTER_CAMERA/SWITCH_SHOOTING_TECH),
#   - every time a parameter is changed (the firmware then sends back the
#     current state of ALL parameters in the group, not just the one that
#     changed).
#
# websockets_utils.py caches these notifications as they arrive
# (client_instance.cameraParamsDwarf, key=param_id). The functions below
# read this cache - so these functions do NOT send any network request,
# unlike their V2 equivalents (perform_get_camera_setting()) which sent an
# explicit GET request.
#
# Practical consequence: the cache only contains a value if at least one
# mode change or setting change has already happened since connecting.
# Call perform_enter_photo_mode()/perform_enter_astro_mode() (which
# triggers this initial broadcast) before reading, or you'll get None.

def perform_read_exposure_v3(param_id=PARAM_ID_PHOTO_TELE_EXPOSURE, dwarf_id="2"):
    """Reads the last known exposure (cache, see above).

    Returns a dict {"mode": int, "name": str, "index": int} or None if
    nothing has been received yet for this param_id.

    mode: 0 = auto (value reported by the device's algorithm),
          1 = manual (value explicitly set via perform_set_exposure_*).
    name: readable name ("0.5", "1/1000", ...) via the existing
          AllowedExposures/AllowedExposuresD3 table (data_utils.py),
          still valid in V3 (see MIGRATION_V3.md).
    """
    param_data = get_camera_param_v3(param_id)
    if param_data is None:
        return None
    index = param_data["value"]
    return {
        "mode": param_data["mode"],
        "name": get_exposure_name_by_index(index, str(dwarf_id)),
        "index": index,
    }


def perform_read_gain_v3(param_id=PARAM_ID_PHOTO_TELE_GAIN):
    """Reads the last known gain (cache, see above).

    Returns a dict {"mode": int, "value": int} or None if nothing has been
    received yet for this param_id.

    IMPORTANT (as with perform_set_gain_v3): 'value' is directly the
    displayed value (not a table index).
    """
    param_data = get_camera_param_v3(param_id)
    if param_data is None:
        return None
    return {"mode": param_data["mode"], "value": param_data["value"]}


def perform_read_all_camera_params_v3(dwarf_id="2"):
    """Gathers all known camera parameters into a single readable dict,
    from the cache passively fed by CMD_NOTIFY_GENERAL_INT_PARAM (see
    perform_read_exposure_v3()/perform_read_gain_v3() for details on the
    mechanism). This is the closest V3 equivalent of the old V2
    perform_get_all_camera_setting() (active CMD_CAMERA_TELE_
    GET_ALL_PARAMS request) - BUT this is NOT an active request: each
    value is only present if it has already been received since
    connecting (on entering a mode and/or after an explicit setting). A
    field is None if nothing has been received yet for that parameter.

    Only covers the "photo tele" parameters confirmed so far (see
    MIGRATION_V3.md): not yet the wide equivalents, nor the astro
    parameters (PARAM_ID_ASTRO_EXPOSURE/GAIN, different structure).
    """
    return {
        "exposure": perform_read_exposure_v3(dwarf_id=dwarf_id),
        "gain": perform_read_gain_v3(),
        "wb": get_camera_param_v3(PARAM_ID_PHOTO_TELE_WB),
        "brightness": get_camera_param_v3(PARAM_ID_PHOTO_TELE_BRIGHTNESS),
        "contrast": get_camera_param_v3(PARAM_ID_PHOTO_TELE_CONTRAST),
        "saturation": get_camera_param_v3(PARAM_ID_PHOTO_TELE_SATURATION),
        "hue": get_camera_param_v3(PARAM_ID_PHOTO_TELE_HUE),
        "sharpness": get_camera_param_v3(PARAM_ID_PHOTO_TELE_SHARPNESS),
        "burst_count": get_camera_param_v3(PARAM_ID_BURST_COUNT),
        "burst_interval": get_camera_param_v3(PARAM_ID_BURST_INTERVAL),
        "timelapse_interval": get_camera_param_v3(PARAM_ID_TIMELAPSE_INTERVAL),
        "timelapse_duration": get_camera_param_v3(PARAM_ID_TIMELAPSE_DURATION),
    }


# ---------------------------------------------------------------------------
# V3: autofocus, image (brightness/contrast/saturation/hue/sharpness),
# white balance, burst, timelapse
# ---------------------------------------------------------------------------
# Identified via network capture of the official app (full session:
# autofocus, setting the 5 image parameters, photo, video, burst,
# timelapse). See MIGRATION_V3.md for details.

# CMD_PARAM_SET_WB (16702) - not named in the dwarfAlp proto (a gap in
# their reverse engineering), but its sequential position (right after
# CMD_PARAM_SET_GAIN=16701, right before
# CMD_PARAM_SET_GENERAL_INT_PARAM=16703) and its decoded structure
# (ReqSetWb{param_id, mode, value}) leave no doubt.
CMD_PARAM_SET_WB = 16702

# "Image" parameters (CAMERA_PARAMS module, same family as exposure/gain)
PARAM_ID_PHOTO_TELE_WB = 0x0101000000000003
PARAM_ID_PHOTO_TELE_BRIGHTNESS = 0x0101000000000004
PARAM_ID_PHOTO_TELE_CONTRAST = 0x0101000000000005
PARAM_ID_PHOTO_TELE_SATURATION = 0x0101000000000006
PARAM_ID_PHOTO_TELE_HUE = 0x0101000000000007
PARAM_ID_PHOTO_TELE_SHARPNESS = 0x0101000000000008

# Burst/timelapse parameters (different param_id family - "group" byte
# = 0x02 instead of 0x01 - semantics less firmly established, see
# docstrings). CONFIRMED by a dedicated network capture ("burst 20s / 5
# photos" session):
PARAM_ID_BURST_INTERVAL = 0x0102f00000000016  # confirmed: value=20 for "20 s"
PARAM_ID_BURST_COUNT = 0x0102f00000000015     # confirmed: value=5 for "5 photos"
# Alias kept for compatibility with existing/already tested code.
PARAM_ID_BURST_SETTING = PARAM_ID_BURST_INTERVAL
PARAM_ID_TIMELAPSE_INTERVAL = 0x0102f00000000019
PARAM_ID_TIMELAPSE_DURATION = 0x0102f0000000001a

# Device-level parameters (deviceParams), discovered via the live HTTP API
# shootingMode/getParamAndSetting - not yet tested for writing
# (perform_set_image_param_v3 can be reused if needed, CAMERA_PARAMS
# module to be confirmed - these param_id have a different scale from
# everything seen so far, be cautious before writing to them).
PARAM_ID_DEVICE_AUTO_SHUTDOWN = 1389782697508969
PARAM_ID_DEVICE_WIDE_MATCHING_FRAME_CALIBRATION = 1389782697508968
PARAM_ID_DEVICE_DISABLE_HOST_SLAVE = 1389782697508965

# Astro/DSO-specific parameters (modeId=2), discovered via the live HTTP
# API shootingMode/getParamAndSetting. Confirmed reliable (byte pattern
# consistent with the rest):
PARAM_ID_ASTRO_STACK_COUNT_TELE = 0x0202000000000010    # "stackCount", tele
PARAM_ID_ASTRO_MOSAIC_COUNT_TELE = 0x0202000000000024   # "mosaicCount", tele
PARAM_ID_ASTRO_STACK_COUNT_WIDE = 0x0202100000000000    # "stackCount", wide
PARAM_ID_ASTRO_AUTO_CALIBRATION = 0x0203f00000000064    # "autoCalibration" (bool)

# NOT RELIABLE: these param_id, reported by the HTTP API for the wide
# camera in astro mode, have a byte pattern inconsistent with everything
# else (e.g. 02 01 0f ff ff ff ff fc instead of the expected pattern
# 02 01 1x...) - most likely an app-side computation artifact (the same
# "reusing the group's last param_id" bug already spotted for brightness/
# contrast/etc., or an overflow in their formula for the wide camera). DO
# NOT use without confirmation via direct WebSocket protocol network
# capture.
# PARAM_ID_ASTRO_WIDE_EXPOSURE_UNCONFIRMED = 144414255238610940
# PARAM_ID_ASTRO_STACK_FORMAT_UNCONFIRMED = 144942020819943420

# CMD_PARAM_SET_GENERAL_BOOL_PARAMS - NOT CONFIRMED by direct network
# capture, inferred from the sequential position in param.proto
# (ReqSetExposure=16700, ReqSetGain=16701, ReqSetWb=16702 [confirmed],
# ReqSetGeneralIntParam=16703 [confirmed], ReqSetGeneralFloatParam=16704,
# ReqSetGeneralBoolParams=16705, ReqSetAutoParam=16706 [confirmed]) - same
# method that correctly identified CMD_PARAM_SET_WB=16702. To be confirmed
# by network capture if you test perform_set_astro_auto_calibration_v3().
CMD_PARAM_SET_GENERAL_BOOL_PARAMS = 16705


def perform_auto_focus_v3():
    """CMD_FOCUS_AUTO_FOCUS (15000), MODULE_FOCUS module (8).

    Triggers autofocus (normal/photo mode - ReqNormalAutoFocus, distinct
    from ReqAstroAutoFocus used for astro). The new focus position then
    arrives as a notification (CMD_NOTIFY_FOCUS_POSITION, already cached
    by the existing mechanism - see self.FocusValueDwarf /
    get_client_status()).
    """
    module_id = protocol.MODULE_FOCUS
    type_id = 0  # REQUEST

    message = focus.ReqNormalAutoFocus()

    command = protocol.CMD_FOCUS_AUTO_FOCUS
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"AUTO FOCUS (V3) -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_wb_v3(value, mode=2, param_id=PARAM_ID_PHOTO_TELE_WB):
    """CMD_PARAM_SET_WB (16702), MODULE_CAMERA_PARAMS module (15).

    White balance setting. 'value' is the preset index (exact order not
    confirmed - value=2 with mode=2 was observed to correspond to
    "Fluorescent" in the app at the time of capture, to be confirmed for
    the other presets). 'mode' seems to distinguish auto (probably 0) from
    manual/preset (2, the observed value).
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetWb()
    message.param_id = param_id
    message.mode = mode
    message.value = value

    command = CMD_PARAM_SET_WB
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET WB (V3) -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_wb_preset_by_name_v3(name, param_id=PARAM_ID_PHOTO_TELE_WB):
    """Like perform_set_wb_v3(), but by readable preset name - official
    AllowedWBPreset table (data_utils.py), confirmed by network capture:
    'Incandescent', 'Warm Fluorescent', 'Fluorescent', 'Sunlight',
    'Cloudy', 'Shadow', 'Twilight'.

    Automatically sets mode=2 (confirmed = "preset" mode, as opposed to
    the "manual Kelvin temperature" mode covered by perform_set_wb_v3()
    with a value from AllowedWBTemp)."""
    index = get_wb_preset_index_by_name(name)
    return perform_set_wb_v3(index, mode=2, param_id=param_id)


def perform_set_image_param_v3(param_id, value):
    """CMD_PARAM_SET_GENERAL_INT_PARAM (16703), MODULE_CAMERA_PARAMS module (15).

    Generic function for the 5 image parameters confirmed by network
    capture (prefer the named wrappers below):
    brightness, contrast, saturation, hue, sharpness.
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetGeneralIntParam()
    message.param_id = param_id
    message.value = value

    command = protocol.CMD_PARAM_SET_GENERAL_INT_PARAM
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET IMAGE PARAM (V3) {hex(param_id)} -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_brightness_v3(value, param_id=PARAM_ID_PHOTO_TELE_BRIGHTNESS):
    """Brightness. Confirmed by network capture: value=58 matches
    "Brightness: 58" shown in the app at the time of capture."""
    return perform_set_image_param_v3(param_id, value)


def perform_set_contrast_v3(value, param_id=PARAM_ID_PHOTO_TELE_CONTRAST):
    """Contrast. Confirmed: value=52 matches "Contrast: 52"."""
    return perform_set_image_param_v3(param_id, value)


def perform_set_saturation_v3(value, param_id=PARAM_ID_PHOTO_TELE_SATURATION):
    """Saturation. Confirmed: value=56 matches "Saturation: 56"."""
    return perform_set_image_param_v3(param_id, value)


def perform_set_hue_v3(value, param_id=PARAM_ID_PHOTO_TELE_HUE):
    """Hue. Confirmed: value=-88 matches "Hue: -88" (accepts negative
    values, int32 field)."""
    return perform_set_image_param_v3(param_id, value)


def perform_set_sharpness_v3(value, param_id=PARAM_ID_PHOTO_TELE_SHARPNESS):
    """Sharpness. Confirmed: value=68 matches
    "Sharpness: 68"."""
    return perform_set_image_param_v3(param_id, value)


def perform_set_burst_interval_v3(seconds, param_id=PARAM_ID_BURST_INTERVAL):
    """CMD_PARAM_SET_GENERAL_INT_PARAM with PARAM_ID_BURST_INTERVAL.

    CONFIRMED by a dedicated network capture ("burst 20s / 5 photos"
    session): value=20 sent for a 20-second interval - raw seconds, not
    the index of the AllowedBurstInterval table.
    """
    return perform_set_image_param_v3(param_id, seconds)


def perform_set_burst_interval_by_name_v3(name, param_id=PARAM_ID_BURST_INTERVAL):
    """Like perform_set_burst_interval_v3(), but by readable name ('Off',
    '1 s', '2 s', ..., '60 s' - AllowedBurstInterval table, data_utils.py),
    with automatic conversion to raw seconds."""
    seconds = get_burst_interval_seconds_by_name(name)
    return perform_set_burst_interval_v3(seconds, param_id=param_id)


def perform_set_burst_count_v3(count, param_id=PARAM_ID_BURST_COUNT):
    """CMD_PARAM_SET_GENERAL_INT_PARAM with PARAM_ID_BURST_COUNT.

    CONFIRMED by a dedicated network capture ("burst 20s / 5 photos"
    session): value=5 sent for 5 photos - RAW photo count, not the index
    of the AllowedBurstCount table (where "5" is at index 3).
    """
    return perform_set_image_param_v3(param_id, count)


def perform_set_timelapse_interval_v3(seconds, param_id=PARAM_ID_TIMELAPSE_INTERVAL):
    """Interval between two timelapse shots, in seconds.

    Confirmed by network capture: the last value sent before starting
    (value=4) matches exactly the 'interval' field of the
    CMD_NOTIFY_TIMELAPSE_OUT_TIME notifications received during execution.
    """
    return perform_set_image_param_v3(param_id, seconds)


def perform_set_timelapse_interval_by_name_v3(name, param_id=PARAM_ID_TIMELAPSE_INTERVAL):
    """Like perform_set_timelapse_interval_v3(), by readable name ('0.5 s',
    '1 s', ..., '60 s' - AllowedTimelapseInterval table, data_utils.py)."""
    seconds = get_timelapse_interval_seconds_by_name(name)
    return perform_set_timelapse_interval_v3(seconds, param_id=param_id)


def perform_set_timelapse_duration_v3(value, param_id=PARAM_ID_TIMELAPSE_DURATION):
    """Total timelapse duration, very likely in raw seconds
    (0 = unlimited?) - consistent with the values observed in the capture
    (2400 = 40 min, 120 = 2 min, official AllowedTimelapseTotalTime table)."""
    return perform_set_image_param_v3(param_id, value)


def perform_set_timelapse_duration_by_name_v3(name, param_id=PARAM_ID_TIMELAPSE_DURATION):
    """Like perform_set_timelapse_duration_v3(), by readable name ('2 min',
    '5 min', ..., '\u221e' for unlimited - AllowedTimelapseTotalTime table,
    data_utils.py)."""
    seconds = get_timelapse_totaltime_seconds_by_name(name)
    return perform_set_timelapse_duration_v3(seconds, param_id=param_id)


def perform_set_ir_filter_v3(name_or_index):
    """IR/Astro filter: 'VIS Filter' (0, normal), 'Astro Filter' (1),
    'Duo-Band Filter' (2) - official AllowedIRFilter table (data_utils.py).

    Reuses CMD_CAMERA_TELE_SET_IRCUT (10031, CAMERA_TELE module),
    unchanged V2 command in V3 (already handled by
    perform_update_camera_setting("IR", ...))."""
    if isinstance(name_or_index, str):
        index = get_ir_filter_index_by_name(name_or_index)
    else:
        index = name_or_index
    return perform_update_camera_setting("IR", index)


# ---------------------------------------------------------------------------
# V3: joystick motor control (MOTOR module, 6)
# ---------------------------------------------------------------------------
# Identified via network capture: when the user uses the directional pad
# in the app (drag, not the step-by-step arrows), it sends
# CMD_STEP_MOTOR_SERVICE_JOYSTICK (14006) in a BURST - up to several
# hundred messages for a single gesture, one per virtual joystick position
# update - then CMD_STEP_MOTOR_SERVICE_JOYSTICK_STOP (14008, empty
# message) on release.
#
# ARCHITECTURE WARNING: connect_socket() is synchronous (opens, sends,
# waits for the response, closes on every call) - this is NOT suited to
# real-time, high-frequency control like the official app does (hundreds
# of calls per second). These functions are fine for a one-off movement
# (bump/nudge), not for reproducing a continuous drag gesture - that would
# require a "fire-and-forget" sending mode without waiting for a response
# on every frame, not implemented here.

def perform_motor_joystick_v3(vector_angle, vector_length):
    """CMD_STEP_MOTOR_SERVICE_JOYSTICK (14006), MODULE_MOTOR module (6).

    vector_angle: angle in degrees (0-360).
    vector_length: movement amplitude, observed between 0.01 and roughly 1
    in the capture (proportional to how far the virtual joystick is from
    its center).
    """
    module_id = protocol.MODULE_MOTOR
    type_id = 0  # REQUEST

    message = motor.ReqMotorServiceJoystick()
    message.vector_angle = vector_angle
    message.vector_length = vector_length

    command = protocol.CMD_STEP_MOTOR_SERVICE_JOYSTICK
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_motor_joystick_stop_v3():
    """CMD_STEP_MOTOR_SERVICE_JOYSTICK_STOP (14008), MODULE_MOTOR module (6).
    Stops the current movement (empty message, confirmed by network capture)."""
    module_id = protocol.MODULE_MOTOR
    type_id = 0  # REQUEST

    message = motor.ReqMotorServiceJoystickStop()

    command = protocol.CMD_STEP_MOTOR_SERVICE_JOYSTICK_STOP
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

    return False

def perform_goto(ra, dec, target, goto_only=False, rotation=None):
    """CMD_ASTRO_START_GOTO_DSO (11002).

    V3: ReqGotoDSO gained 2 new fields compared to V2 (which only had
    ra/dec/target_name):
      - goto_only (bool): if True, only slews to the target without
        automatically starting stacking afterward - lets you separate
        "point at target" from "start capturing". NOT YET CONFIRMED by
        network capture, based on the proto field name/type.
      - rotation (optional int32): camera/frame rotation angle to apply
        during the GOTO, presumably in degrees. NOT YET CONFIRMED by
        network capture.
    Both default to the same behavior as before (goto_only=False,
    rotation unset) if not specified.
    """

    # GOTO
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqGotoDSO_message = astro.ReqGotoDSO()
    ReqGotoDSO_message.ra = ra
    ReqGotoDSO_message.dec = dec
    ReqGotoDSO_message.target_name = target
    ReqGotoDSO_message.goto_only = goto_only
    if rotation is not None:
        ReqGotoDSO_message.rotation = rotation

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

def perform_goto_stellar(target_id, target_name, force_start=False):
    """CMD_ASTRO_START_GOTO_SOLAR_SYSTEM (11003).

    V3: ReqGotoSolarSystem gained 1 new field compared to V2 (which only
    had index/lon/lat/target_name):
      - force_start (bool): likely forces the GOTO to proceed despite a
        recoverable warning (e.g. target near/below horizon) - mirrors the
        same force_start pattern seen on ReqCaptureRawLiveStacking. NOT YET
        CONFIRMED by network capture.
    Defaults to False (same behavior as before) if not specified.
    """

    if read_longitude() is None:
        log.error("Longitude is not defined! ")
        return

    if read_latitude() is None:
        log.error("Latitude is not defined! ")
        return

    # GOTO
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqGotoSolarSystem_message = astro.ReqGotoSolarSystem()
    ReqGotoSolarSystem_message.index = target_id
    ReqGotoSolarSystem_message.lon = read_longitude()
    ReqGotoSolarSystem_message.lat = read_latitude()
    ReqGotoSolarSystem_message.target_name = target_name
    ReqGotoSolarSystem_message.force_start = force_start

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

def perform_waitEndAstroPhoto(retry = False):

    # use special message to get end of shooting
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    message = "ASTRO CAPTURE ENDING" if not retry else "ASTRO CAPTURE ENDING RESTART"

    response = connect_socket(message, None, type_id, module_id)

    if response is not False: 

        if response == 0:
            log.success("{message} success")
            return True
        elif response == -1:
            log.warning("ASTRO CAPTURE NOT STARTED")
            return True
        else:
            log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False

def perform_waitRetryEndAstroPhoto():
    return perform_waitEndAstroPhoto(True)

def perform_waitEndAstroWidePhoto(noretry = False):

    # use special message to get end of shooting
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    message = "ASTRO WIDE CAPTURE ENDING" if not retry else "ASTRO WIDE CAPTURE ENDING RESTART"

    response = connect_socket(message, None, type_id, module_id)

    if response is not False: 

        if response == 0:
            log.success("{message} success")
            return True
        elif response == -1:
            log.warning("ASTRO WIDE CAPTURE NOT STARTED")
            return True
        else:
            log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False

def perform_waitRetryEndAstroWidePhoto():
    return perform_waitEndAstroWidePhoto(True)

def perform_takeAstroPhoto(ir_index=1, force_start=False):
    """CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING (11005).

    V3: ReqCaptureRawLiveStacking was completely EMPTY in V2, it gained 2
    new fields in V3:
      - ir_index (int32): IR/Astro filter to use for the capture, per
        dwarfAlp's documented workflow ("ReqCaptureRawLiveStacking(ir_index=1
        or 2)"). Matches the AllowedIRFilter table indices (1=Astro Filter,
        2=Duo-Band Filter - see perform_set_ir_filter_v3()). Defaults to 1
        (Astro), the standard choice for DSO capture with a normal
        telescope; use 2 for narrowband/nebula work with a Duo-Band filter.
      - force_start (bool): forces the capture to start despite a
        recoverable warning (e.g. no dark frame, or a dark frame taken at
        a different sensor temperature) - per dwarfAlp's documented
        workflow, CMD_ASTRO_CONTINUE_SHOOTING (11050) is the alternative
        mechanism to use AFTER a warning has already been raised, while
        force_start here skips the warning check upfront. Defaults to
        False (same behavior as before).
    """

    # START CAPTURE RAW LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqCaptureRawLiveStacking_message = astro.ReqCaptureRawLiveStacking()
    ReqCaptureRawLiveStacking_message.ir_index = ir_index
    ReqCaptureRawLiveStacking_message.force_start = force_start

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

    # Calculate timezone offset in hours
    local_time = datetime.now()
    utc_time = datetime.utcnow()
    timezone_offset = (local_time - utc_time).total_seconds() / 3600  # Offset in hours
    # Round to the nearest 0.25 (15 minutes)
    rounded_timezone_offset = round(timezone_offset * 4) / 4
    ReqSetTime_message.timezone_offset = rounded_timezone_offset
    log.notice(f"Timezone offset is : {timezone_offset} H")

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

    timezone_value = read_timezone()
    if timezone_value is None:
        log.warning(
            "TIMEZONE missing from config.ini: CMD_SYSTEM_SET_TIME_ZONE not"
            " sent (an invalid value would crash the message construction)."
            " Set TIMEZONE in config.ini if needed."
        )
        return False

    ReqSetTimezone_message = system.ReqSetTimezone()
    ReqSetTimezone_message.timezone = timezone_value
    log.notice(f"Timezone is : {timezone_value}")

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
            # Keep the floating point representation for other cases
            return value_str
    except ValueError:
        # The string is not a valid number
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

def perform_update_all_camera_setting( type, allValue, dwarf_id = "2"):

  type_id = 0; #REQUEST
  if (type == "wide"):
    module_id = 2  # MODULE_WIDE_CAMERA
  else:
    module_id = 1  # MODULE_TELE_CAMERA

  ReqSetAllParam_message = camera.ReqSetAllParams ()
  if (type == "wide"):
    if (allValue['camera_exposure']):
      ReqSetAllParam_message.exp_mode = 1
      ReqSetAllParam_message.exp_index = get_wide_exposure_index_by_name(str(allValue['camera_exposure']), str(dwarf_id))
    else:
      ReqSetAllParam_message.exp_mode = 0
      ReqSetAllParam_message.exp_index = 0
    if (allValue['camera_gain']):
      ReqSetAllParam_message.gain_mode = 1
      ReqSetAllParam_message.gain_index = get_wide_gain_index_by_name(str(allValue['camera_gain']),str(dwarf_id))
    else:
      ReqSetAllParam_message.gain_mode = 1
      ReqSetAllParam_message.gain_index = 0
  else:
    if (allValue['camera_exposure']):
      ReqSetAllParam_message.exp_mode = 1
      ReqSetAllParam_message.exp_index = get_exposure_index_by_name(str(allValue['camera_exposure']), str(dwarf_id))
    else:
      ReqSetAllParam_message.exp_mode = 0
      ReqSetAllParam_message.exp_index = 0
    if (allValue['camera_gain']):
      ReqSetAllParam_message.gain_mode = 1
      ReqSetAllParam_message.gain_index = get_gain_index_by_name(str(allValue['camera_gain']),str(dwarf_id))
    else:
      ReqSetAllParam_message.gain_mode = 1
      ReqSetAllParam_message.gain_index = 0

  ReqSetAllParam_message.ircut_value = 0;
  ReqSetAllParam_message.wb_mode = 0;
  ReqSetAllParam_message.wb_index_type = 2;
  ReqSetAllParam_message.wb_index = 0;
  ReqSetAllParam_message.brightness = 0;
  ReqSetAllParam_message.contrast = 0;
  ReqSetAllParam_message.hue = 0;
  ReqSetAllParam_message.saturation = 0;
  ReqSetAllParam_message.sharpness = 50;
  ReqSetAllParam_message.jpg_quality = 80;

  if (type == "wide"):
    command = 12028; #CMD_CAMERA_WIDE_SET_ALL_PARAMS
  else:
    command = 10035; #CMD_CAMERA_TELE_SET_ALL_PARAMS
  
  response = connect_socket(ReqSetAllParam_message, command, type_id, module_id)

  if response is not False: 

      if response == 0:
          log.success("Update camera setting")
          return True
      else:
          log.error(f"Error code: {response}")
  else:
      log.error("Dwarf API: Dwarf Device not connected")

  return False

def get_result_value ( type, result_cnx, is_double = False):

  if result_cnx is False: 
    log.error("Dwarf API: Dwarf Device not connected")

  elif isinstance(result_cnx, int):
    if result_cnx >= 0:
      log.success(f"{type} value: {result_cnx}")
      return result_cnx
    else: 
      log.error(f"Error code: {result_cnx}")

  elif isinstance(result_cnx, dict) and 'code' in result_cnx:
    if result_cnx["code"] == 0 and 'value' in result_cnx:
      log.success(f"{type} value: {result_cnx['value'] if not is_double else format_double(result_cnx['value'])}")
      return result_cnx["value"] if not is_double else format_double(result_cnx["value"])
    else: 
      if result_cnx["code"] == 0:
        log.success(f"{type} no value")
        return result_cnx["code"]
      else:
        log.error(f"Error code: {result_cnx['code']}")
  else: 
    log.error(f"Unknown Error ")

  return False

def perform_get_camera_setting( type):

  Test = False
  if Test:
    # brightness
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetBrightness_message = camera.ReqGetBrightness ()

    command = 10016; #CMD_CAMERA_TELE_GET_BRIGHTNESS

    response = connect_socket(ReqGetBrightness_message, command, type_id, module_id)

    if get_result_value(type, response) is not False:
      ReqGetContrast_message = camera.ReqGetContrast ()

      command = 10018; #CMD_CAMERA_TELE_GET_CONTRAST

      response = connect_socket(ReqGetContrast_message, command, type_id, module_id)

      return get_result_value(type, response)

  if (type == "exposure"):
    # exposure
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetExp_message = camera.ReqGetExp ()

    command = 10010; #CMD_CAMERA_TELE_GET_EXP

    response = connect_socket(ReqGetExp_message, command, type_id, module_id)

    return get_result_value(type, response, true)

  elif (type == "gain"):
    # gain
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetGain_message = camera.ReqGetGain ()

    command = 10014; #CMD_CAMERA_TELE_GET_GAIN

    response = connect_socket(ReqGetGain_message, command, type_id, module_id)

    return get_result_value(type, response, type)

  elif (type == "IR"):
    # IR
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqGetIrCut_message = camera.ReqGetIrCut ()

    command = 10032; #CMD_CAMERA_TELE_GET_IRCUT

    response = connect_socket(ReqGetIrCut_message, command, type_id, module_id)

    return get_result_value(type, response)

  elif (type == "wide_exposure"):
    # exposure
    module_id = 2  # MODULE_WIDE_CAMERA
    type_id = 0; #REQUEST

    ReqGetExp_message = camera.ReqGetExp ()

    command = 12005; #CMD_CAMERA_WIDE_GET_EXP

    response = connect_socket(ReqGetExp_message, command, type_id, module_id)

    return get_result_value(type, response, True)

  elif (type == "wide_gain"):
    # gain
    module_id = 2  # MODULE_WIDE_CAMERA
    type_id = 0; #REQUEST

    ReqGetGain_message = camera.ReqGetGain ()

    command = 12007; #CMD_CAMERA_WIDE_GET_GAIN

    response = connect_socket(ReqGetGain_message, command, type_id, module_id)

    return get_result_value(type, response)

  return False

def perform_update_camera_setting( type, value, dwarf_id = "2"):

  if (type == "exposure"):
    # exposure_mode
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetExpMode_message = camera.ReqSetExpMode ()
    ReqSetExpMode_message.mode = 1

    command = 10007; #CMD_CAMERA_TELE_SET_EXP_MODE

    response = connect_socket(ReqSetExpMode_message, command, type_id, module_id)

    if response == 0:
      # exposure
      ReqSetExp_message = camera.ReqSetExp ()
      ReqSetExp_message.index = get_exposure_index_by_name(str(value), str(dwarf_id))
      log.notice(f"Set Exp Index to:  {get_exposure_index_by_name(str(value), str(dwarf_id))}")

      command = 10009; #CMD_CAMERA_TELE_SET_EXP

      response = connect_socket(ReqSetExp_message, command, type_id, module_id)

  elif (type == "gain"):
    # gain 
    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0; #REQUEST

    ReqSetGain_message = camera.ReqSetGain ()
    ReqSetGain_message.index = get_gain_index_by_name(str(value),str(dwarf_id))
    log.notice(f"Set Gain Index to:  {get_gain_index_by_name(str(value), str(dwarf_id))}")

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

    if response == 0:
      # exposure
      ReqSetExp_message = camera.ReqSetExp ()
      ReqSetExp_message.index = get_wide_exposure_index_by_name(str(value), str(dwarf_id))
      log.notice(f"Set Wide Exp Index to:  {get_wide_exposure_index_by_name(str(value), str(dwarf_id))}")

      command = 12004; #CMD_CAMERA_WIDE_SET_EXP

      response = connect_socket(ReqSetExp_message, command, type_id, module_id)

  elif (type == "wide_gain"):
    # gain 
    module_id = 2  # MODULE_WIDE_CAMERA
    type_id = 0; #REQUEST

    ReqSetGain_message = camera.ReqSetGain ()
    ReqSetGain_message.index = get_wide_gain_index_by_name(str(value),str(dwarf_id))
    log.notice(f"Set Wide Gain Index to:  {get_wide_gain_index_by_name(str(value), str(dwarf_id))}")

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

def decimal_to_dms(decimal_degrees):
    degrees = int(decimal_degrees)
    minutes_full = abs((decimal_degrees - degrees) * 60)
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60

    return f"{degrees}° {minutes}' {seconds:.1f}\""

def get_result_polar_value ( result_cnx):

  if result_cnx is False: 
    log.error("Dwarf API: Dwarf Device not connected")

  elif isinstance(result_cnx, int):
    if result_cnx == 0:
      log.success("Start Polar Alignement")
      return result_cnx
    else:
      log.error(f"Error code: {result_cnx}")

  elif isinstance(result_cnx, dict) and 'code' in result_cnx:
    if result_cnx["code"] == 0 and 'azi_err' in result_cnx and 'alt_err' in result_cnx:
      log.success("Polar Alignement result")
      log.notice(f"Azimuth error value: {decimal_to_dms(result_cnx['azi_err'])}")
      log.notice(f"Altitude error value: {decimal_to_dms(result_cnx['alt_err'])}")
      return {'azi_err' : result_cnx['azi_err'], 'alt_err' : result_cnx['alt_err']}
    else:
      if result_cnx["code"] == 0:
        log.success(f"Polar Alignement no result value")
        return result_cnx["code"]
      else:
        log.error(f"Error code: {result_cnx['code']}")
  else: 
    log.error(f"Unknown Error ")

  return False

def start_polar_align():

    # start Polar Align
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStartEqSolving_message = astro.ReqStartEqSolving ()
    ReqStartEqSolving_message.lon = read_longitude();
    ReqStartEqSolving_message.lat = read_latitude();
    command = 11018; #CMD_ASTRO_START_EQ_SOLVING
    response = connect_socket(ReqStartEqSolving_message, command, type_id, module_id)

    return get_result_polar_value(response)

def stop_polar_align():

    # stop Polar Align
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStopEqSolving_message = astro.ReqStopEqSolving ()
    command = 11019; #CMD_ASTRO_STOP_EQ_SOLVING
    response = connect_socket(ReqStopEqSolving_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Stop Polar Alignement success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def motor_action( action, correction = 0 ):

    module_id = 6  # MODULE_MOTOR
    type_id = 0; #REQUEST

    # Rotation Motor Resetting
    if (action == 5):
      ReqMotorReset_message = motor.ReqMotorReset ()
      ReqMotorReset_message.id= 1;
      ReqMotorReset_message.direction = 0;
      command = 14003; #CMD_STEP_MOTOR_RESET
      response = connect_socket(ReqMotorReset_message, command, type_id, module_id)

    # Pitch Motor Resetting
    if (action == 6):
      ReqMotorReset_message = motor.ReqMotorReset ()
      ReqMotorReset_message.id= 2;
      ReqMotorReset_message.direction = 1;
      command = 14003; #CMD_STEP_MOTOR_RESET
      response = connect_socket(ReqMotorReset_message, command, type_id, module_id)

    #Closed Barrel Position
    if (action == 1):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 2;
      ReqMotorRunTo_message.end_position = 317 + correction;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 2;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    # Rotation Motor positioning...
    if (action == 2):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 1;
      ReqMotorRunTo_message.end_position = 158.6 + correction;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 3;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    # Rotation Motor positioning D3...
    if (action == 9):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 1;
      ReqMotorRunTo_message.end_position = 158 + correction;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 3;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    # Pitch Motor positioning...
    if (action == 3):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 2;
      ReqMotorRunTo_message.end_position = 150.5 + correction;
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 3;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    # Pitch Motor positioning D3...
    if (action == 7):  # For D3
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 2;
      ReqMotorRunTo_message.end_position = 169 + correction; 
      ReqMotorRunTo_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRunTo_message.speed_ramping = 100;
      ReqMotorRunTo_message.resolution_level = 3;
      command = 14001; #CMD_STEP_MOTOR_RUN_TO
      response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    # Turn 90° Rotation Motor
    if (action == 4):
      ReqMotorRunTo_message = motor.ReqMotorRunTo ()
      ReqMotorRunTo_message.id= 1;
      ReqMotorRunTo_message.end_position = 67.6 + correction;
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

    if (action == 8):
      ReqMotorGetPosition_message = motor.ReqMotorGetPosition ()
      ReqMotorGetPosition_message.id= 1;
      command = 14011; #CMD_STEP_MOTOR_GET_POSITION
      response = connect_socket(ReqMotorGetPosition_message, command, type_id, module_id)

      ReqMotorGetPosition_message.id= 2;
      command = 14011; #CMD_STEP_MOTOR_GET_POSITION
      response = connect_socket(ReqMotorGetPosition_message, command, type_id, module_id)

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


# ---------------------------------------------------------------------------
# V3: HTTP API (port 8082) - "live" parameter/param_id catalog
# ---------------------------------------------------------------------------
# Independent of the WebSocket protocol (port 9900) analyzed so far.
# Identified via dwarfAlp's documentation (official APK analysis + real
# tests):
#
#   GET  http://<ip>:8082/getDefaultParamsConfig
#       -> default (static) catalog; not very useful in V3 based on your
#          own tests - probably the equivalent of data_dwarf3_config.ts
#          but frozen, without the per-mode "live" values.
#
#   POST http://<ip>:8082/shootingMode/getParamAndSetting
#        body JSON: {"modeId": <id>}
#       -> LIVE catalog (exposure names/indices, gain values, param_id)
#          FOR THE REQUESTED MODE. This is probably the most reliable
#          mechanism to find ALL param_id (including those we haven't
#          identified yet via network capture) without guessing.
#
# Independently confirmed by dwarfAlp for modeId=2 (DSO/astro) on a Dwarf
# Mini: exposure param_id=144396663052566529 (=0x0201000000000001, exactly
# PARAM_ID_ASTRO_EXPOSURE already used in this file) and gain
# param_id=144396663052566530 (=0x0201000000000002 = PARAM_ID_ASTRO_GAIN).
#
# These functions use plain HTTP via `requests` (not the WebSocket/protobuf
# protocol) - they don't require an active WS connection, but per the
# workflow documented by dwarfAlp, the official app calls them AFTER
# establishing the WS session (MASTER LOCK, ENTER_CAMERA...) - to be
# tested whether a "cold" call (without an active WS session) returns
# nothing.

def _get_dwarf_ip():
    data_config = dwarf_python_api.get_config_data.get_config_data()
    return data_config.get('ip')


def perform_get_default_params_config_http(port=8082, timeout=5):
    """GET /getDefaultParamsConfig (port 8082) - static default catalog.
    Based on your own tests, doesn't give much useful info anymore in V3
    (maybe just a generic catalog not tied to active param_id).
    """
    ip = _get_dwarf_ip()
    if not ip:
        log.error("Dwarf API: unknown IP (config.ini) - run the BLE/web connection first.")
        return False
    url = f"http://{ip}:{port}/getDefaultParamsConfig"
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log.error(f"Error GET {url}: {e}")
        return False


def perform_get_param_and_setting_http(mode_id, port=8082, timeout=5):
    """POST /shootingMode/getParamAndSetting (port 8082), body {"modeId": mode_id}.

    LIVE catalog of the parameters for the requested mode (exposure
    names/indices, gain values, param_id) - confirmed working for
    modeId=2 (DSO/astro) by dwarfAlp on a Dwarf Mini. Also try modeId=1
    (Normal/photo) to try to confirm/complete the param_id for
    brightness/contrast/saturation/hue/sharpness/burst/timelapse that we
    had so far only identified via network capture.

    If the result is empty/unexpected, try first establishing a WS
    session (set_HostMaster + perform_enter_astro_mode()/
    perform_enter_photo_mode() depending on the mode tested) before this
    call - per the workflow documented by dwarfAlp, the official app calls
    this endpoint AFTER already having an active WS session, not cold.
    """
    ip = _get_dwarf_ip()
    if not ip:
        log.error("Dwarf API: unknown IP (config.ini) - run the BLE/web connection first.")
        return False
    url = f"http://{ip}:{port}/shootingMode/getParamAndSetting"
    try:
        response = requests.post(url, json={"modeId": int(mode_id)}, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log.error(f"Error POST {url}: {e}")
        return False


# ---------------------------------------------------------------------------
# V3: astro/DSO-specific settings (subframe count, mosaic,
# auto calibration) - discovered via the live HTTP API
# shootingMode/getParamAndSetting (modeId=2)
# ---------------------------------------------------------------------------

def perform_set_astro_stack_count_v3(count, camera="tele"):
    """Total number of subframes to stack for an astro session.
    camera: "tele" or "wide". Confirmed by the live HTTP API
    (shootingMode/getParamAndSetting, modeId=2): range 1-999 for both
    cameras, value observed 390 (tele) / 100 (wide) at the time of capture.
    """
    param_id = PARAM_ID_ASTRO_STACK_COUNT_WIDE if camera == "wide" else PARAM_ID_ASTRO_STACK_COUNT_TELE
    return perform_set_image_param_v3(param_id, count)


def perform_set_astro_mosaic_count_v3(count):
    """Number of panels for an astro mosaic (tele camera only, no wide
    equivalent observed). Range 1-249 (default 45)."""
    return perform_set_image_param_v3(PARAM_ID_ASTRO_MOSAIC_COUNT_TELE, count)


def perform_set_bool_param_v3(param_id, value):
    """CMD_PARAM_SET_GENERAL_BOOL_PARAMS (16705, NOT CONFIRMED by network
    capture - inferred from sequential position, see comment above).
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetGeneralBoolParams()
    message.param_id = param_id
    message.value = bool(value)

    command = CMD_PARAM_SET_GENERAL_BOOL_PARAMS
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET BOOL PARAM (V3) {hex(param_id)} -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_astro_auto_calibration_v3(enabled):
    """Enables/disables automatic calibration before GOTO in astro/DSO
    mode. NOT CONFIRMED by network capture (see perform_set_bool_param_v3).
    Per the live HTTP API, defaultValue=true but currentValue=false at the
    time of capture (the user had disabled it)."""
    return perform_set_bool_param_v3(PARAM_ID_ASTRO_AUTO_CALIBRATION, enabled)


# ---------------------------------------------------------------------------
# V3: GROUPED and RELIABLE reading of all parameters via the live HTTP API
# ---------------------------------------------------------------------------
# Much better source than the passive notification cache
# (perform_read_all_camera_params_v3(), based on CMD_NOTIFY_GENERAL_INT_PARAM):
# this is an ACTIVE request that always returns the actual CURRENT state
# (field "currentValue"), for MANY more parameters (filter, resolution,
# framerate, subframe count, auto calibration...), on BOTH cameras (tele
# and wide) - confirmed by two real captures (modeId=1 and modeId=2). See
# MIGRATION_V3.md for details on the exchanges that led to building this
# parser.

def perform_read_camera_params_http_v3(mode_id):
    """Queries POST /shootingMode/getParamAndSetting {"modeId": mode_id}
    and returns a clean, readable dict of the CURRENT values
    ("currentValue") for each camera (0=tele, 1=wide), rather than the
    raw JSON.

    Requires an active WS session beforehand (MASTER LOCK + entering the
    corresponding mode) - confirmed empirically to be required (see
    MIGRATION_V3.md, "live HTTP API").

    Returns False if the HTTP request fails. Returns a dict shaped like:

    {
        "mode_id": 1,
        "cameras": {
            0: {  # tele
                "brightness": 58, "contrast": 52, "saturation": 56,
                "hue": -88, "sharpness": 68,
                "filterType": 1, "resolutionType": 1, ...
                "exposure": {"mode": 1, "value": 111, "name": "0.5"},
                "gain": {"mode": 1, "value": 50},
                "wb": {"mode": 0, "value": 5542, "scene": 0},
            },
            1: { ... },  # wide, same keys
        },
        "device": {"autoShutdown": True, "disableHostSlave": False, ...},
        # Only present if the mode provides them (e.g. modeId=2/astro):
        "shooting_mode": {"autoCalibration": False, ...},
        "tech_settings": {15: {...}, 0: {"stackCount": 390, ...}, 1: {...}},
    }
    """
    raw = perform_get_param_and_setting_http(mode_id)
    if raw is False:
        return False

    try:
        data = raw["data"]
    except (KeyError, TypeError):
        log.error("Unexpected HTTP response (no 'data' key)")
        return False

    result = {"mode_id": data.get("modeId", mode_id), "cameras": {}}

    # IMPORTANT: `.get(key, default)` only returns `default` if the key is
    # ABSENT - if the JSON explicitly contains "cameraParams": null (seen
    # on Dwarf 2, modes 4 and 5, where this mode has no camera settings),
    # `.get` returns `None`, not `[]`, which crashed `for cam in None:`.
    # All the reads below therefore use `(... or default)` rather than
    # `.get(key, default)` alone, to cover both cases (key absent AND key
    # present with a null value).

    for cam in (data.get("cameraParams") or []):
        cam_id = cam.get("cameraId")
        cam_dict = {}

        for gp in (cam.get("generalParams") or []):
            cam_dict[gp["name"]] = gp.get("currentValue")

        special = cam.get("specialParams") or {}
        if "exp" in special:
            exp = special["exp"]
            index = exp.get("currentValue")
            cam_dict["exposure"] = {
                "mode": exp.get("currentMode"),
                "value": index,
                "name": next((v["name"] for v in (exp.get("values") or []) if v["value"] == index), None),
            }
        if "gain" in special:
            gain = special["gain"]
            cam_dict["gain"] = {"mode": gain.get("currentMode"), "value": gain.get("currentValue")}
        if "wb" in special:
            wb = special["wb"]
            cam_dict["wb"] = {
                "mode": wb.get("currentMode"),
                "value": wb.get("currentValue"),
                "scene": wb.get("sceneValue"),
            }

        result["cameras"][cam_id] = cam_dict

    device_params = (data.get("deviceParams") or {}).get("generalParams") or []
    if device_params:
        result["device"] = {p["name"]: p.get("currentValue") for p in device_params}

    shooting_mode_params = (data.get("shootingModeParams") or {}).get("generalParams") or []
    if shooting_mode_params:
        result["shooting_mode"] = {p["name"]: p.get("currentValue") for p in shooting_mode_params}

    tech_settings = data.get("shootingTechSettings") or []
    if tech_settings:
        result["tech_settings"] = {
            ts.get("cameraId"): {p["name"]: p.get("currentValue") for p in (ts.get("generalParams") or [])}
            for ts in tech_settings
        }

    return result


# ---------------------------------------------------------------------------
# V3: triggering burst / video / timelapse (CAMERA_TELE module, 1)
# ---------------------------------------------------------------------------
# Unchanged V2 commands, but completion is now tracked via the new
# CMD_NOTIFY_BURST_STATE/RECORD_STATE/TIMELAPSE_STATE notifications (see
# the fix already in place in websockets_utils.py, VALID_PAIRS).
# Use AFTER perform_enter_shooting_mode(mode, tech) with the corresponding
# tech (3=burst, 4=video, 5=timelapse) and perform_set_burst_*/
# perform_set_timelapse_* settings if needed.

def perform_start_burst_v3():
    """CMD_CAMERA_TELE_BURST (10003) - triggers a burst (count/interval
    set beforehand via perform_set_burst_count_v3()/
    perform_set_burst_interval_by_name_v3())."""
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0  # REQUEST

    message = camera.ReqBurstPhoto()

    command = 10003  # CMD_CAMERA_TELE_BURST
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"BURST -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_stop_burst_v3():
    """CMD_CAMERA_TELE_STOP_BURST (10004)."""
    module_id = 1
    type_id = 0

    message = camera.ReqStopBurstPhoto()

    command = 10004  # CMD_CAMERA_TELE_STOP_BURST
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"STOP BURST -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_start_record_v3():
    """CMD_CAMERA_TELE_START_RECORD (10005) - starts video recording."""
    module_id = 1
    type_id = 0

    message = camera.ReqStartRecord()

    command = 10005  # CMD_CAMERA_TELE_START_RECORD
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"START RECORD -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_stop_record_v3():
    """CMD_CAMERA_TELE_STOP_RECORD (10006)."""
    module_id = 1
    type_id = 0

    message = camera.ReqStopRecord()

    command = 10006  # CMD_CAMERA_TELE_STOP_RECORD
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"STOP RECORD -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_start_timelapse_v3():
    """CMD_CAMERA_TELE_START_TIMELAPSE_PHOTO (10033) - starts the timelapse
    (interval/duration set beforehand via perform_set_timelapse_*)."""
    module_id = 1
    type_id = 0

    message = camera.ReqStartTimeLapse()

    command = 10033  # CMD_CAMERA_TELE_START_TIMELAPSE_PHOTO
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"START TIMELAPSE -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_stop_timelapse_v3():
    """CMD_CAMERA_TELE_STOP_TIMELAPSE_PHOTO (10034)."""
    module_id = 1
    type_id = 0

    message = camera.ReqStopTimeLapse()

    command = 10034  # CMD_CAMERA_TELE_STOP_TIMELAPSE_PHOTO
    response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"STOP TIMELAPSE -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


# ---------------------------------------------------------------------------
# V3: astro stacking session monitoring (start/progress/stop)
# ---------------------------------------------------------------------------
# All the underlying plumbing for this already existed in the V2 code and
# uses commands/messages confirmed unchanged in V3
# (perform_start_astro_photo/perform_stopAstroPhoto trigger the session,
# and websockets_utils.py's dispatcher already tracks progress via
# CMD_NOTIFY_STATE_CAPTURE_RAW_LIVE_STACKING/CMD_NOTIFY_PROGRASS_CAPTURE_RAW_
# LIVE_STACKING into client_instance.AstroCapture/takePhotoCount/
# takePhotoStacked). This function is just a convenience wrapper around
# get_client_status() to read that state without digging through the raw
# JSON each time.

def perform_read_astro_stacking_status_v3():
    """Reads the current astro stacking session state from the client
    status cache (get_client_status()). Returns a dict:

    {
        "capturing": bool,       # AstroCapture - a session is active
        "current_count": int,    # number of subframes captured so far
        "stacked_count": int,    # number of subframes actually stacked
    }

    (wide-camera equivalents are in get_client_status() directly -
    AstroWideCapture/takeWidePhotoCount/takeWidePhotoStacked - not
    duplicated here since the wide astro path is not yet confirmed
    reliable, see MIGRATION_V3.md).

    Note: this reads the passively-updated cache (fed by notifications
    received while a stacking session is running) - it does not send any
    network request, and will not reflect anything before the first
    notification has arrived after perform_start_astro_photo().
    """
    status = get_client_status()
    if isinstance(status, str) or not isinstance(status, dict):
        # get_client_status() returns a JSON string when there is no
        # client_instance (not connected) instead of a dict.
        return None
    full_status = status.get("fullStatus", {})
    return {
        "capturing": full_status.get("AstroCapture"),
        "current_count": full_status.get("takePhotoCount"),
        "stacked_count": full_status.get("takePhotoStacked"),
    }
