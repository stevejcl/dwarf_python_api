from .websockets_utils import connect_socket
from .websockets_utils import get_camera_param_v3
from .websockets_utils import get_client_status
from .websockets_utils import disconnect_socket
from .websockets_testV2 import fct_show_test
from .websockets_testV2 import fct_decode_wireshark

# Multi-Dwarf foundation (additive, see MIGRATION_MULTI_V3.md).
# `session` is optional everywhere it's threaded through below: omit it
# (or pass None) to keep today's implicit mono-dwarf behavior unchanged.
from .dwarf_session import get_default_session
from .dwarf_session_socket import connect_socket as connect_socket_session
from .dwarf_session_socket import disconnect_socket as disconnect_socket_session
from .dwarf_session_socket import get_camera_param_v3 as get_camera_param_v3_session
from .dwarf_session_socket import get_client_status as get_client_status_session

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

def perform_disconnect(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""
    active_session = _resolve_session(session)
    if active_session is not None:
        disconnect_socket_session(active_session)
    else:
        disconnect_socket()

def perform_reboot(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # Power Down
    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqPowerReboot_message = rgb_power.ReqReboot ()

    command = 13505; # CMD_RGB_POWER_REBOOT

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqPowerReboot_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqPowerReboot_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Reboot command success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

def perform_powerdown(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # Power Down
    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqPowerDown_message = rgb_power.ReqPowerDown ()

    command = 13502; # CMD_RGB_POWER_POWER_DOWN

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqPowerDown_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqPowerDown_message, command, type_id, module_id)

    if response is not False: 

      if response == 0:
          log.success("Shutdown command success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

def perform_powerOpenRGB(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""
    # Turn On RGB Lights
    type = "Turn On RGB Lights"

    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqOpenRgb_message = rgb_power.ReqOpenRgb ()

    command = 13500; # CMD_RGB_POWER_OPEN_RGB

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqOpenRgb_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqOpenRgb_message, command, type_id, module_id)

    return get_result_value(type, response)

def perform_powerCloseRGB(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""
    # Turn Off RGB Lights
    type = "Turn Off RGB Lights"

    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqCloseRgb_message = rgb_power.ReqCloseRgb ()

    command = 13501; # CMD_RGB_POWER_CLOSE_RGB

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqCloseRgb_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqCloseRgb_message, command, type_id, module_id)

    return get_result_value(type, response)

def perform_powerIndOn(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""
    # Turn On RGB Lights
    type = "Turn On Power Lights"

    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqOpenPowerInd_message = rgb_power.ReqOpenPowerInd ()

    command = 13503; # CMD_RGB_POWER_POWERIND_ON

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqOpenPowerInd_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqOpenPowerInd_message, command, type_id, module_id)

    return get_result_value(type, response)

def perform_powerIndOff(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""
    # Turn Off RGB Lights
    type = "Turn Off Power Lights"

    module_id = 5   # MODULE_RGB_POWER
    type_id = 0;    # REQUEST

    ReqClosePowerInd_message = rgb_power.ReqClosePowerInd ()

    command = 13504; # CMD_RGB_POWER_POWERIND_OFF

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqClosePowerInd_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqClosePowerInd_message, command, type_id, module_id)

    return get_result_value(type, response)

def read_longitude(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.longitude
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.longitude

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

def read_latitude(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.latitude
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.latitude

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

def read_timezone(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.timezone
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.timezone

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

def read_camera_exposure(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.exposure
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.exposure

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

def read_camera_gain(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.gain
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.gain

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

def read_camera_IR(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ircut
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ircut

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

def read_camera_binning(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.binning
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.binning

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

def read_camera_format(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.format
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.format

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

def read_camera_count(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.count
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.count

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

def read_camera_wide_exposure(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.wide_exposure
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.wide_exposure

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

def read_camera_wide_gain(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.wide_gain
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.wide_gain

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

def read_bluetooth_ble_wifi_type(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ble_wifi_type
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ble_wifi_type

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
 
def read_bluetooth_autoAP(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ble_auto_ap
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ble_auto_ap

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

def read_bluetooth_country_list(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ble_country_list
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ble_country_list

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
 
def read_bluetooth_country(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ble_country
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ble_country

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
 
def read_bluetooth_ble_psd(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ble_psd
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ble_psd

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
 
def read_bluetooth_autoSTA(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ble_auto_sta
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ble_auto_sta

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

def read_bluetooth_ble_STA_ssid(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ble_sta_ssid
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ble_sta_ssid

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
 
def read_bluetooth_ble_STA_pwd(session=None):
    """`session`: optional DwarfSession - if given, reads session.config.ble_sta_pwd
    directly instead of parsing config.ini (see perform_goto())."""
    active_session = _resolve_session(session)
    if active_session is not None:
        return active_session.config.ble_sta_pwd

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

# perform_getstatus() moved to dwarf_utilsV2.py (Aug 2026) - confirmed
# non-responsive on V3 hardware, never wired into any menu.

def unset_HostMaster(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # SET Host
    module_id = 4  # MODULE_SYSTEM
    type_id = 0; #REQUEST

    ReqsetMasterLock_message = system.ReqsetMasterLock()
    ReqsetMasterLock_message.lock = False
    
    command = 13004 #CMD_SYSTEM_SET_MASTERLOCK

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqsetMasterLock_message, command, type_id, module_id)
    else:
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

def set_HostMaster(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # SET Host
    module_id = 4  # MODULE_SYSTEM
    type_id = 0; #REQUEST

    ReqsetMasterLock_message = system.ReqsetMasterLock()
    ReqsetMasterLock_message.lock = True
    
    command = 13004 #CMD_SYSTEM_SET_MASTERLOCK

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqsetMasterLock_message, command, type_id, module_id)
    else:
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

# BUG FOUND (Aug 2026, field-confirmed): SHOOTING_MODE_ASTRO was set to 8,
# which is actually SUN/Solar mode, not general DSO/deep-sky astro. A real
# session that entered "astro mode" using this constant before a DSO GOTO
# (target: Bode's Galaxy) left the device in Solar mode according to the
# official app - confirmed by checking option_A13's own mode table below.
# Corrected to 2 (DSO). SHOOTING_MODE_SUN added as the properly-named
# constant for what this used to (incorrectly) represent.
SHOOTING_MODE_DSO = 2
SHOOTING_MODE_ASTRO = SHOOTING_MODE_DSO  # kept as an alias - "astro" in this
                                          # codebase (astro_dwarf_session,
                                          # perform_enter_astro_mode, etc.)
                                          # always means DSO, not Solar.
SHOOTING_MODE_SUN = 8
SHOOTING_MODE_MOON = 9
SHOOTING_MODE_PLANET = 10
SHOOTING_TECH_DEEP_SKY = 2

SHOOTING_MODE_PHOTO = 1
SHOOTING_TECH_PHOTO = 1


def perform_get_device_state_info(session=None):
    """CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO (16405) - full device state.
    Purely informational, useful at the start of a connection.

    `session`: optional DwarfSession - see perform_goto().
    """

    module_id = protocol.MODULE_DEVICE_CONFIG
    type_id = 0 #REQUEST

    ReqGetDeviceStateInfo_message = task_center.ReqGetDeviceStateInfo()

    command = protocol.CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqGetDeviceStateInfo_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqGetDeviceStateInfo_message, command, type_id, module_id)

    if response is not False:
        log.success(f"GET DEVICE STATE INFO code: {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_switch_shooting_mode(mode=SHOOTING_MODE_ASTRO, session=None):
    """CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_MODE (16402).
    mode=8 = astro mode. Returns the effective shooting_mode_id, or False.

    `session`: optional DwarfSession - see perform_goto().
    """

    module_id = protocol.MODULE_DEVICE_CONFIG
    type_id = 0 #REQUEST

    ReqSwitchShootingMode_message = task_center.ReqSwitchShootingMode()
    ReqSwitchShootingMode_message.mode = mode

    command = protocol.CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_MODE

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqSwitchShootingMode_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqSwitchShootingMode_message, command, type_id, module_id)

    if response is not False:
        log.success(f"SWITCH SHOOTING MODE -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_enter_camera(encode_type=1, session=None):
    """CMD_GLOBAL_TASK_MANAGER_ENTER_CAMERA (16404).
    This is the V3 command that corresponds to "initializing the camera":
    without it, subsequent ASTRO/CAMERA commands do not respond.

    `session`: optional DwarfSession - see perform_goto().
    """

    module_id = protocol.MODULE_DEVICE_CONFIG
    type_id = 0 #REQUEST

    ReqEnterCamera_message = task_center.ReqEnterCamera()
    ReqEnterCamera_message.client_param.encode_type = encode_type

    command = protocol.CMD_GLOBAL_TASK_MANAGER_ENTER_CAMERA

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqEnterCamera_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqEnterCamera_message, command, type_id, module_id)

    if response is not False:
        log.success(f"ENTER CAMERA -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_switch_shooting_tech(tech=SHOOTING_TECH_DEEP_SKY, session=None):
    """CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_TECH (16403).
    tech=2 = Deep Sky / stacking.

    `session`: optional DwarfSession - see perform_goto().
    """

    module_id = protocol.MODULE_DEVICE_CONFIG
    type_id = 0 #REQUEST

    ReqSwitchShootingTech_message = task_center.ReqSwitchShootingTech()
    ReqSwitchShootingTech_message.tech = tech

    command = protocol.CMD_GLOBAL_TASK_MANAGER_SWITCH_SHOOTING_TECH

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqSwitchShootingTech_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqSwitchShootingTech_message, command, type_id, module_id)

    if response is not False:
        log.success(f"SWITCH SHOOTING TECH -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_preview_quality(level=1, session=None):
    """CMD_CAMERA_TELE_SET_PREVIEW_QUALITY (10050).
    Sent by the official app right after entering astro mode.
    Best effort: should not block the sequence if the device doesn't
    respond as expected on this particular point (to be confirmed on the
    first real test).

    `session`: optional DwarfSession - see perform_goto().
    """

    module_id = protocol.MODULE_CAMERA_TELE
    type_id = 0 #REQUEST

    ReqSetPreviewQuality_message = camera.ReqSetPreviewQuality()
    ReqSetPreviewQuality_message.level = level

    command = protocol.CMD_CAMERA_TELE_SET_PREVIEW_QUALITY

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqSetPreviewQuality_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqSetPreviewQuality_message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET PREVIEW QUALITY -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_enter_astro_mode(session=None):
    """Full V3 connection sequence: equivalent, for astro mode, of the
    (resolve MASTER/SLAVE + open camera) pair from V2.

    Call right after set_HostMaster() and before any ASTRO command.

    1) perform_switch_shooting_mode(2)  -> DSO/deep-sky astro mode
    2) perform_enter_camera()           -> V3 camera "initialization"
    3) perform_switch_shooting_tech(2)  -> Deep Sky / stacking technique
    4) perform_set_preview_quality(1)   -> preview quality (best effort)

    Returns True if the first 3 steps succeed (the 4th is non-blocking),
    False otherwise.

    Confirmed working on real hardware (Dwarf Mini): SWITCH_SHOOTING_MODE
    does return the mode sent, ENTER_CAMERA returns the mode sent,
    SWITCH_SHOOTING_TECH returns 2.

    NOTE: mode=8 was previously (incorrectly) used here - that value is
    actually SUN/Solar mode, not DSO (see SHOOTING_MODE_SUN). A real
    session confirmed this left the device in Solar mode instead of DSO
    before a deep-sky GOTO, which is likely why a subsequent EQ Solving
    step failed. Use perform_enter_shooting_mode(SHOOTING_MODE_SUN, ...)
    explicitly for solar/lunar/planetary sessions instead.

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_enter_shooting_mode(SHOOTING_MODE_ASTRO, SHOOTING_TECH_DEEP_SKY, session=session)


def perform_enter_photo_mode(session=None):
    """Equivalent of perform_enter_astro_mode() for simple photo (no mount
    alignment, no GOTO, no stacking).

    mode=1 / tech=1, identified empirically via the shooting_mode_and_techs
    diagnostic (CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO) on a real Dwarf
    Mini: mode=1 (root, no parent) offers techniques [1, 3, 4, 5], likely
    corresponding to photo/burst/video/timelapse. NOT YET TESTED on real
    hardware at the time this was written - the strongest hypothesis we
    have, to be confirmed.

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_enter_shooting_mode(SHOOTING_MODE_PHOTO, SHOOTING_TECH_PHOTO, session=session)


def perform_enter_shooting_mode(mode, tech, session=None):
    """Generic function used by perform_enter_astro_mode() and
    perform_enter_photo_mode(): switches to the given (mode, tech) pair.

    `session`: optional DwarfSession - see perform_goto(). Threaded through
    to every step of the sequence so the whole handshake targets the same
    device.
    """

    mode_result = perform_switch_shooting_mode(mode, session=session)
    if mode_result is False:
        log.error(f"V3: SWITCH SHOOTING MODE({mode}) failed, aborting")
        return False

    enter_result = perform_enter_camera(session=session)
    if enter_result is False:
        log.error("V3: ENTER CAMERA failed, aborting")
        return False

    tech_result = perform_switch_shooting_tech(tech, session=session)
    if tech_result is False:
        log.error(f"V3: SWITCH SHOOTING TECH({tech}) failed, aborting")
        return False

    preview_result = perform_set_preview_quality(1, session=session)
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


def perform_set_exposure_v3(value, param_id=PARAM_ID_PHOTO_TELE_EXPOSURE, mode=1, session=None):
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

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetExposure()
    message.param_id = param_id
    message.mode = mode
    message.value = value

    command = protocol.CMD_PARAM_SET_EXPOSURE

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET EXPOSURE (V3) -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_exposure_by_name_v3(name, dwarf_id="2", camera="tele", param_id=None, mode=1, session=None):
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

    `session`: optional DwarfSession - see perform_goto().
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
    return perform_set_exposure_v3(index, param_id=param_id, mode=mode, session=session)


def perform_set_gain_v3(value, param_id=PARAM_ID_PHOTO_TELE_GAIN, mode=1, session=None):
    """CMD_PARAM_SET_GAIN (16701), MODULE_CAMERA_PARAMS module (15).

    Replaces, in V3, the old CMD_CAMERA_TELE_SET_GAIN_MODE +
    CMD_CAMERA_TELE_SET_GAIN pair (CAMERA_TELE module) - confirmed by
    network capture of the official app.

    IMPORTANT (different from exposure): 'value' here is the DISPLAYED
    gain value directly (e.g. 50 for "50"), NOT the index of the old
    AllowedGains/AllowedGainsD3 table (where "50" is at index 15).
    Confirmed by network capture: the user went from 60 to 50 in the app,
    and the value sent was indeed 50.

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetGain()
    message.param_id = param_id
    message.mode = mode
    message.value = value

    command = protocol.CMD_PARAM_SET_GAIN

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET GAIN (V3) -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_gain_by_camera_v3(value, dwarf_id="2", camera="tele", mode=1, session=None):
    """Convenience wrapper around perform_set_gain_v3() that picks the
    right param_id for photo mode based on camera ("tele"/"wide") and
    dwarf_id, instead of requiring the caller to know the raw constant.

    Wide param_id CONFIRMED by network capture (Dwarf 3 AND Dwarf Mini,
    Aug 2026): PARAM_ID_PHOTO_WIDE_GAIN. IMPORTANT: the Dwarf II uses a
    DIFFERENT, also-confirmed wide param_id (PARAM_ID_PHOTO_WIDE_GAIN_D2)
    - selected automatically here based on dwarf_id == "2".

    `session`: optional DwarfSession - see perform_goto().
    """
    if camera == "wide":
        param_id = PARAM_ID_PHOTO_WIDE_GAIN_D2 if str(dwarf_id) == "2" else PARAM_ID_PHOTO_WIDE_GAIN
    else:
        param_id = PARAM_ID_PHOTO_TELE_GAIN
    return perform_set_gain_v3(value, param_id=param_id, mode=mode, session=session)


def perform_set_astro_exposure_v3(value, camera="tele", mode=1, session=None):
    """CMD_PARAM_SET_EXPOSURE (16700) for astro/DSO mode, using
    PARAM_ID_ASTRO_EXPOSURE/PARAM_ID_ASTRO_WIDE_EXPOSURE (both confirmed
    by network capture - tele independently confirmed by dwarfAlp, wide
    confirmed on a Dwarf Mini, Aug 2026 - see MIGRATION_V3.md).

    Same index convention as perform_set_exposure_v3() (index into the
    AllowedExposures/AllowedExposuresD3/AllowedExposuresMini table, not
    raw seconds) - prefer perform_set_astro_exposure_by_name_v3() to set
    by name. This applies to both "tele" and "wide".

    `session`: optional DwarfSession - see perform_goto().
    """
    param_id = PARAM_ID_ASTRO_WIDE_EXPOSURE if camera == "wide" else PARAM_ID_ASTRO_EXPOSURE
    return perform_set_exposure_v3(value, param_id=param_id, mode=mode, session=session)


def perform_set_astro_exposure_by_name_v3(name, dwarf_id="2", camera="tele", mode=1, session=None):
    """Like perform_set_astro_exposure_v3(), but by readable name ("0.5",
    "1/1000", "180", ...) instead of the raw index.

    `session`: optional DwarfSession - see perform_goto().
    """
    if camera == "wide":
        index = get_wide_exposure_index_by_name(str(name), str(dwarf_id))
    else:
        index = get_exposure_index_by_name(str(name), str(dwarf_id))
    return perform_set_astro_exposure_v3(index, camera=camera, mode=mode, session=session)


def perform_set_astro_gain_v3(value, camera="tele", mode=1, session=None):
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

    `session`: optional DwarfSession - see perform_goto().
    """
    param_id = PARAM_ID_ASTRO_WIDE_GAIN if camera == "wide" else PARAM_ID_ASTRO_GAIN
    return perform_set_gain_v3(value, param_id=param_id, mode=mode, session=session)


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

def perform_read_exposure_v3(param_id=PARAM_ID_PHOTO_TELE_EXPOSURE, dwarf_id="2", session=None):
    """Reads the last known exposure (cache, see above).

    Returns a dict {"mode": int, "name": str, "index": int} or None if
    nothing has been received yet for this param_id.

    mode: 0 = auto (value reported by the device's algorithm),
          1 = manual (value explicitly set via perform_set_exposure_*).
    name: readable name ("0.5", "1/1000", ...) via the existing
          AllowedExposures/AllowedExposuresD3 table (data_utils.py),
          still valid in V3 (see MIGRATION_V3.md).

    `session`: optional DwarfSession - see perform_goto(). The cache read
    is per-session (each session's WebSocketClient has its own
    cameraParamsDwarf dict) - no cross-device leak risk either way.
    """
    active_session = _resolve_session(session)
    if active_session is not None:
        param_data = get_camera_param_v3_session(active_session, param_id)
    else:
        param_data = get_camera_param_v3(param_id)
    if param_data is None:
        return None
    index = param_data["value"]
    return {
        "mode": param_data["mode"],
        "name": get_exposure_name_by_index(index, str(dwarf_id)),
        "index": index,
    }


def perform_read_gain_v3(param_id=PARAM_ID_PHOTO_TELE_GAIN, session=None):
    """Reads the last known gain (cache, see above).

    Returns a dict {"mode": int, "value": int} or None if nothing has been
    received yet for this param_id.

    IMPORTANT (as with perform_set_gain_v3): 'value' is directly the
    displayed value (not a table index).

    `session`: optional DwarfSession - see perform_read_exposure_v3().
    """
    active_session = _resolve_session(session)
    if active_session is not None:
        param_data = get_camera_param_v3_session(active_session, param_id)
    else:
        param_data = get_camera_param_v3(param_id)
    if param_data is None:
        return None
    return {"mode": param_data["mode"], "value": param_data["value"]}


def perform_read_all_camera_params_v3(dwarf_id="2", session=None):
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

    `session`: optional DwarfSession - see perform_read_exposure_v3().
    """
    active_session = _resolve_session(session)
    if active_session is not None:
        get_param = lambda pid: get_camera_param_v3_session(active_session, pid)
    else:
        get_param = get_camera_param_v3
    return {
        "exposure": perform_read_exposure_v3(dwarf_id=dwarf_id, session=session),
        "gain": perform_read_gain_v3(session=session),
        "wb": get_param(PARAM_ID_PHOTO_TELE_WB),
        "brightness": get_param(PARAM_ID_PHOTO_TELE_BRIGHTNESS),
        "contrast": get_param(PARAM_ID_PHOTO_TELE_CONTRAST),
        "saturation": get_param(PARAM_ID_PHOTO_TELE_SATURATION),
        "hue": get_param(PARAM_ID_PHOTO_TELE_HUE),
        "sharpness": get_param(PARAM_ID_PHOTO_TELE_SHARPNESS),
        "burst_count": get_param(PARAM_ID_BURST_COUNT),
        "burst_interval": get_param(PARAM_ID_BURST_INTERVAL),
        "timelapse_interval": get_param(PARAM_ID_TIMELAPSE_INTERVAL),
        "timelapse_duration": get_param(PARAM_ID_TIMELAPSE_DURATION),
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
# API shootingMode/getParamAndSetting.
PARAM_ID_ASTRO_STACK_COUNT_TELE = 0x0202000000000010    # "stackCount", tele
PARAM_ID_ASTRO_MOSAIC_COUNT_TELE = 0x0202000000000024   # "mosaicCount", tele
# BUG FOUND AND FIXED (Aug 2026, field-confirmed by a failed wide stackCount
# write): this was 0x0202100000000000 - camera byte correctly flipped to
# 0x10 for wide, but the trailing sub-parameter byte (0x10, "stackCount")
# was dropped/zeroed in the process instead of being preserved, unlike
# the already-confirmed exposure/gain wide pattern where only the camera
# byte changes and the trailing byte stays identical.
# CONFIRMED by network capture (Dwarf Mini, Aug 2026): explicit
# CMD_PARAM_SET_GENERAL_INT_PARAM (16703) calls changing wide stackCount
# (values 1-8, 51, 64, 351 observed) all carry param_id
# 0x0202100000000010 - matches the pattern-based fix exactly.
PARAM_ID_ASTRO_STACK_COUNT_WIDE = 0x0202100000000010    # "stackCount", wide
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

# CONFIRMED by network capture (Dwarf Mini, Aug 2026, two independent
# captures agree exactly): CMD_PARAM_SET_GENERAL_INT_PARAM (16703) with
# param_id 0x0202f0000000000f, values 2 (FITS) and 3 (TIFF) observed.
# This supersedes the earlier "UNCONFIRMED" guess (144942020819943420 =
# 0x0202effffffffffc), which was sourced from the live HTTP API's
# unreliable "paramId" JSON field and turned out to be wrong.
PARAM_ID_ASTRO_STACK_FORMAT = 0x0202f0000000000f    # "stackFormat" (2=FITS, 3=TIFF)

# CONFIRMED by network capture (Dwarf 3, Aug 2026): two explicit
# CMD_PARAM_SET_GENERAL_INT_PARAM (16703) calls toggling displaySource
# between 0 and 1 both carry param_id 0x0202f00000000012 - different
# from the live HTTP API's unreliable "paramId" JSON field for this same
# setting (144942020819943460 = 0x0202f00000000024), confirming that
# field is not to be trusted here either.
PARAM_ID_ASTRO_DISPLAY_SOURCE = 0x0202f00000000012    # "displaySource" (0=Single, 1=?)

# CONFIRMED by network capture (Dwarf 3, Aug 2026): explicit
# CMD_PARAM_SET_GENERAL_INT_PARAM (16703) calls toggling stackBinning
# between 0 and 1. Note the control was reported missing from the
# official app's UI until DWARFLAB support pointed out where to find it
# (it moved/is not where it used to be) - the setting itself is not
# discontinued, just relocated in the UI. Unlike stackFormat/
# displaySource (0x0202f0... family), this uses the same leading bytes
# as tele exposure/gain (0x0201...), with its own sub-index (0x1e).
PARAM_ID_ASTRO_STACK_BINNING = 0x020100000000001e    # "stackBinning" (0=4k, 1=2k)

# CMD_PARAM_SET_GENERAL_BOOL_PARAMS - NOT CONFIRMED by direct network
# capture, inferred from the sequential position in param.proto
# (ReqSetExposure=16700, ReqSetGain=16701, ReqSetWb=16702 [confirmed],
# ReqSetGeneralIntParam=16703 [confirmed], ReqSetGeneralFloatParam=16704,
# ReqSetGeneralBoolParams=16705, ReqSetAutoParam=16706 [confirmed]) - same
# method that correctly identified CMD_PARAM_SET_WB=16702. To be confirmed
# by network capture if you test perform_set_astro_auto_calibration_v3().
CMD_PARAM_SET_GENERAL_BOOL_PARAMS = 16705


def perform_auto_focus_v3(session=None):
    """CMD_FOCUS_AUTO_FOCUS (15000), MODULE_FOCUS module (8).

    Triggers autofocus (normal/photo mode - ReqNormalAutoFocus, distinct
    from ReqAstroAutoFocus used for astro). The new focus position then
    arrives as a notification (CMD_NOTIFY_FOCUS_POSITION, already cached
    by the existing mechanism - see self.FocusValueDwarf /
    get_client_status()).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = protocol.MODULE_FOCUS
    type_id = 0  # REQUEST

    message = focus.ReqNormalAutoFocus()

    command = protocol.CMD_FOCUS_AUTO_FOCUS

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"AUTO FOCUS (V3) -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_wb_v3(value, mode=2, param_id=PARAM_ID_PHOTO_TELE_WB, session=None):
    """CMD_PARAM_SET_WB (16702), MODULE_CAMERA_PARAMS module (15).

    White balance setting. 'value' is the preset index (exact order not
    confirmed - value=2 with mode=2 was observed to correspond to
    "Fluorescent" in the app at the time of capture, to be confirmed for
    the other presets). 'mode' seems to distinguish auto (probably 0) from
    manual/preset (2, the observed value).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetWb()
    message.param_id = param_id
    message.mode = mode
    message.value = value

    command = CMD_PARAM_SET_WB

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET WB (V3) -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_wb_preset_by_name_v3(name, param_id=PARAM_ID_PHOTO_TELE_WB, session=None):
    """Like perform_set_wb_v3(), but by readable preset name - official
    AllowedWBPreset table (data_utils.py), confirmed by network capture:
    'Incandescent', 'Warm Fluorescent', 'Fluorescent', 'Sunlight',
    'Cloudy', 'Shadow', 'Twilight'.

    Automatically sets mode=2 (confirmed = "preset" mode, as opposed to
    the "manual Kelvin temperature" mode covered by perform_set_wb_v3()
    with a value from AllowedWBTemp).

    `session`: optional DwarfSession - see perform_goto().
    """
    index = get_wb_preset_index_by_name(name)
    return perform_set_wb_v3(index, mode=2, param_id=param_id, session=session)


def perform_set_image_param_v3(param_id, value, session=None):
    """CMD_PARAM_SET_GENERAL_INT_PARAM (16703), MODULE_CAMERA_PARAMS module (15).

    Generic function for the 5 image parameters confirmed by network
    capture (prefer the named wrappers below):
    brightness, contrast, saturation, hue, sharpness.

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetGeneralIntParam()
    message.param_id = param_id
    message.value = value

    command = protocol.CMD_PARAM_SET_GENERAL_INT_PARAM

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET IMAGE PARAM (V3) {hex(param_id)} -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_brightness_v3(value, param_id=PARAM_ID_PHOTO_TELE_BRIGHTNESS, session=None):
    """Brightness. Confirmed by network capture: value=58 matches
    "Brightness: 58" shown in the app at the time of capture.

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, value, session=session)


def perform_set_contrast_v3(value, param_id=PARAM_ID_PHOTO_TELE_CONTRAST, session=None):
    """Contrast. Confirmed: value=52 matches "Contrast: 52".

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, value, session=session)


def perform_set_saturation_v3(value, param_id=PARAM_ID_PHOTO_TELE_SATURATION, session=None):
    """Saturation. Confirmed: value=56 matches "Saturation: 56".

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, value, session=session)


def perform_set_hue_v3(value, param_id=PARAM_ID_PHOTO_TELE_HUE, session=None):
    """Hue. Confirmed: value=-88 matches "Hue: -88" (accepts negative
    values, int32 field).

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, value, session=session)


def perform_set_sharpness_v3(value, param_id=PARAM_ID_PHOTO_TELE_SHARPNESS, session=None):
    """Sharpness. Confirmed: value=68 matches
    "Sharpness: 68".

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, value, session=session)


def perform_set_burst_interval_v3(seconds, param_id=PARAM_ID_BURST_INTERVAL, session=None):
    """CMD_PARAM_SET_GENERAL_INT_PARAM with PARAM_ID_BURST_INTERVAL.

    CONFIRMED by a dedicated network capture ("burst 20s / 5 photos"
    session): value=20 sent for a 20-second interval - raw seconds, not
    the index of the AllowedBurstInterval table.

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, seconds, session=session)


def perform_set_burst_interval_by_name_v3(name, param_id=PARAM_ID_BURST_INTERVAL, session=None):
    """Like perform_set_burst_interval_v3(), but by readable name ('Off',
    '1 s', '2 s', ..., '60 s' - AllowedBurstInterval table, data_utils.py),
    with automatic conversion to raw seconds.

    `session`: optional DwarfSession - see perform_goto().
    """
    seconds = get_burst_interval_seconds_by_name(name)
    return perform_set_burst_interval_v3(seconds, param_id=param_id, session=session)


def perform_set_burst_count_v3(count, param_id=PARAM_ID_BURST_COUNT, session=None):
    """CMD_PARAM_SET_GENERAL_INT_PARAM with PARAM_ID_BURST_COUNT.

    CONFIRMED by a dedicated network capture ("burst 20s / 5 photos"
    session): value=5 sent for 5 photos - RAW photo count, not the index
    of the AllowedBurstCount table (where "5" is at index 3).

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, count, session=session)


def perform_set_timelapse_interval_v3(seconds, param_id=PARAM_ID_TIMELAPSE_INTERVAL, session=None):
    """Interval between two timelapse shots, in seconds.

    Confirmed by network capture: the last value sent before starting
    (value=4) matches exactly the 'interval' field of the
    CMD_NOTIFY_TIMELAPSE_OUT_TIME notifications received during execution.

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, seconds, session=session)


def perform_set_timelapse_interval_by_name_v3(name, param_id=PARAM_ID_TIMELAPSE_INTERVAL, session=None):
    """Like perform_set_timelapse_interval_v3(), by readable name ('0.5 s',
    '1 s', ..., '60 s' - AllowedTimelapseInterval table, data_utils.py).

    `session`: optional DwarfSession - see perform_goto().
    """
    seconds = get_timelapse_interval_seconds_by_name(name)
    return perform_set_timelapse_interval_v3(seconds, param_id=param_id, session=session)


def perform_set_timelapse_duration_v3(value, param_id=PARAM_ID_TIMELAPSE_DURATION, session=None):
    """Total timelapse duration, very likely in raw seconds
    (0 = unlimited?) - consistent with the values observed in the capture
    (2400 = 40 min, 120 = 2 min, official AllowedTimelapseTotalTime table).

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(param_id, value, session=session)


def perform_set_timelapse_duration_by_name_v3(name, param_id=PARAM_ID_TIMELAPSE_DURATION, session=None):
    """Like perform_set_timelapse_duration_v3(), by readable name ('2 min',
    '5 min', ..., '\u221e' for unlimited - AllowedTimelapseTotalTime table,
    data_utils.py).

    `session`: optional DwarfSession - see perform_goto().
    """
    seconds = get_timelapse_totaltime_seconds_by_name(name)
    return perform_set_timelapse_duration_v3(seconds, param_id=param_id, session=session)


def perform_set_ir_filter_v3(name_or_index, session=None):
    """IR/Astro filter: 'VIS Filter' (0, normal), 'Astro Filter' (1),
    'Duo-Band Filter' (2) - official AllowedIRFilter table (data_utils.py).

    Accepts either a readable name ("Astro Filter") or a raw index (0/1/2,
    as an int or a numeric string like "1" - BUG FIXED Aug 2026: a plain
    isinstance(str) check treated numeric strings like "1" as a NAME to
    look up in the table, silently failing to match and falling back to
    the table's default index (0) every time - so callers passing a
    stringified config value (e.g. str(program['setup_camera']['ircut']))
    always got index 0 regardless of the actual configured value. Now
    only genuinely non-numeric strings go through the name lookup.

    CMD_CAMERA_TELE_SET_IRCUT (10031, CAMERA_TELE module) - unchanged V2
    command in V3, confirmed working. Called directly here (Aug 2026) -
    used to go through perform_update_camera_setting("IR", ...), which is
    otherwise unused in V3 now that exposure/gain/count have their own
    confirmed V3 functions; see dwarf_utilsV2.py for that legacy code.

    `session`: optional DwarfSession - see perform_goto().
    """
    if isinstance(name_or_index, str) and not name_or_index.strip().lstrip('-').isdigit():
        index = get_ir_filter_index_by_name(name_or_index)
    else:
        index = int(name_or_index)

    module_id = 1  # MODULE_TELE_CAMERA
    type_id = 0  # REQUEST

    ReqSetIrCut_message = camera.ReqSetIrCut()
    ReqSetIrCut_message.value = index

    command = 10031  # CMD_CAMERA_TELE_SET_IRCUT

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqSetIrCut_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqSetIrCut_message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET IR FILTER -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


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

def perform_motor_joystick_v3(vector_angle, vector_length, session=None):
    """CMD_STEP_MOTOR_SERVICE_JOYSTICK (14006), MODULE_MOTOR module (6).

    vector_angle: angle in degrees (0-360).
    vector_length: movement amplitude, observed between 0.01 and roughly 1
    in the capture (proportional to how far the virtual joystick is from
    its center).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = protocol.MODULE_MOTOR
    type_id = 0  # REQUEST

    message = motor.ReqMotorServiceJoystick()
    message.vector_angle = vector_angle
    message.vector_length = vector_length

    command = protocol.CMD_STEP_MOTOR_SERVICE_JOYSTICK

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_motor_joystick_stop_v3(session=None):
    """CMD_STEP_MOTOR_SERVICE_JOYSTICK_STOP (14008), MODULE_MOTOR module (6).
    Stops the current movement (empty message, confirmed by network capture).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = protocol.MODULE_MOTOR
    type_id = 0  # REQUEST

    message = motor.ReqMotorServiceJoystickStop()

    command = protocol.CMD_STEP_MOTOR_SERVICE_JOYSTICK_STOP

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def _resolve_session(session):
    """Resolve an explicit session, falling back to the mono-dwarf default
    (DwarfManager's default DwarfSession) when none is given. Returns None
    if no session is available at all (neither passed nor registered)."""
    return session or get_default_session()


def perform_goto(ra, dec, target, goto_only=False, rotation=None, session=None):
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

    `session`: optional DwarfSession (see dwarf_session.py). When given,
    the command is sent on that specific device's connection instead of
    the mono-dwarf default - required for multi-Dwarf control.
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

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqGotoDSO_message, command, type_id, module_id)
    else:
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

def perform_goto_stellar(target_id, target_name, force_start=False, session=None):
    """CMD_ASTRO_START_GOTO_SOLAR_SYSTEM (11003).

    V3: ReqGotoSolarSystem gained 1 new field compared to V2 (which only
    had index/lon/lat/target_name):
      - force_start (bool): likely forces the GOTO to proceed despite a
        recoverable warning (e.g. target near/below horizon) - mirrors the
        same force_start pattern seen on ReqCaptureRawLiveStacking. NOT YET
        CONFIRMED by network capture.
    Defaults to False (same behavior as before) if not specified.

    `session`: optional DwarfSession - see perform_goto(). Now properly
    per-session: read_longitude()/read_latitude() are session-aware since
    the read_* migration (see MIGRATION_MULTI_V3.md), so each device can
    have its own latitude/longitude.
    """

    if read_longitude(session=session) is None:
        log.error("Longitude is not defined! ")
        return

    if read_latitude(session=session) is None:
        log.error("Latitude is not defined! ")
        return

    # GOTO
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqGotoSolarSystem_message = astro.ReqGotoSolarSystem()
    ReqGotoSolarSystem_message.index = target_id
    ReqGotoSolarSystem_message.lon = read_longitude(session=session)
    ReqGotoSolarSystem_message.lat = read_latitude(session=session)
    ReqGotoSolarSystem_message.target_name = target_name
    ReqGotoSolarSystem_message.force_start = force_start

    command = 11003 #CMD_ASTRO_START_GOTO_SOLAR_SYSTEM

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqGotoSolarSystem_message, command, type_id, module_id)
    else:
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

def perform_open_camera(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # OPEN TELE PHOTO
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    ReqPhoto_message = camera.ReqPhoto()

    command = 10000 #CMD_CAMERA_TELE_OPEN_CAMERA

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqPhoto_message, command, type_id, module_id)
    else:
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

def perform_takePhoto(session=None):
    """CMD_CAMERA_TELE_PHOTOGRAPH (10002).

    `session`: optional DwarfSession - see perform_goto().
    """

    # START TAKE TELE PHOTO
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    ReqPhoto_message = camera.ReqPhoto()

    command = 10002 #CMD_CAMERA_TELE_PHOTOGRAPH

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqPhoto_message, command, type_id, module_id)
    else:
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

def perform_open_widecamera(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # OPEN WIDE PHOTO
    module_id = 2  # MODULE_CAMERA_WIDE
    type_id = 0; #REQUEST

    ReqPhoto_message = camera.ReqPhoto()

    command = 12000 #CMD_CAMERA_WIDE_OPEN_CAMERA

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqPhoto_message, command, type_id, module_id)
    else:
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

def perform_takeWidePhoto(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # START WIDE TELE PHOTO
    module_id = 2  # MODULE_CAMERA_WIDE
    type_id = 0; #REQUEST

    ReqPhoto_message = camera.ReqPhoto()

    command = 12022 #CMD_CAMERA_WIDE_PHOTOGRAPH

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqPhoto_message, command, type_id, module_id)
    else:
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

def perform_waitEndAstroPhoto(retry = False, session=None):
    """`session`: optional DwarfSession - see perform_goto(). Note this call
    blocks (synchronously) until the device reports completion or the
    connection layer's timeout is hit, so when running several DwarfSessions
    concurrently, call this from a dedicated thread per session rather than
    sequentially from the same thread."""

    # use special message to get end of shooting
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    message = "ASTRO CAPTURE ENDING" if not retry else "ASTRO CAPTURE ENDING RESTART"

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, None, type_id, module_id)
    else:
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

def perform_waitRetryEndAstroPhoto(session=None):
    return perform_waitEndAstroPhoto(True, session=session)

def perform_waitEndAstroWidePhoto(retry = False, session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # use special message to get end of shooting
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0; #REQUEST

    message = "ASTRO WIDE CAPTURE ENDING" if not retry else "ASTRO WIDE CAPTURE ENDING RESTART"

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, None, type_id, module_id)
    else:
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

def perform_waitRetryEndAstroWidePhoto(session=None):
    return perform_waitEndAstroWidePhoto(True, session=session)

def perform_takeAstroPhoto(ir_index=1, force_start=False, session=None):
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

    `session`: optional DwarfSession - see perform_goto().
    """

    # START CAPTURE RAW LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqCaptureRawLiveStacking_message = astro.ReqCaptureRawLiveStacking()
    ReqCaptureRawLiveStacking_message.ir_index = ir_index
    ReqCaptureRawLiveStacking_message.force_start = force_start

    command = 11005 #CMD_ASTRO_START_CAPTURE_RAW_LIVE_STACKING

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqCaptureRawLiveStacking_message, command, type_id, module_id)
    else:
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

def perform_start_mosaic_v3(horizontal_scale=2, vertical_scale=2, rotation=0, ir_index=1, force_start=False, session=None):
    """CMD_ASTRO_START_TELE_MOSAIC (11031, tele only - no wide mosaic
    command exists). NOT independently confirmed by network capture -
    the command constant was entirely missing from protocol.proto until
    now (Aug 2026), confirmed only via the dwarfAlp registry (present in
    the official app, request message ReqStartMosaic already existed in
    astro.proto with no way to reference the command number).

    IMPORTANT - how a mosaic is linked to its target: ReqStartMosaic
    carries NO target/coordinates field at all (only horizontal_scale,
    vertical_scale, rotation, ir_index, force_start). Exactly like
    perform_takeAstroPhoto() for a single-target session, the mosaic is
    centered on wherever the telescope is CURRENTLY POINTED - i.e. you
    must perform_goto() to the target first (the mosaic's center), then
    call this function; the device handles the internal grid of small
    pointing offsets around that center itself.

    horizontal_scale/vertical_scale: NOT confirmed - presumed to be the
    mosaic grid dimensions (e.g. 2=2x2, 3=3x3) by analogy with similar
    apps, but this is a guess, not verified by capture. Test with
    caution and report back what a captured "2" vs "3" etc. actually
    produces before relying on this.
    rotation: field-name only, meaning/units not confirmed.
    ir_index/force_start: same semantics as perform_takeAstroPhoto().

    See also perform_set_astro_mosaic_count_v3() (PARAM_ID_ASTRO_MOSAIC_COUNT_TELE)
    for the total number of subframes to stack per panel - a separate
    setting from the grid dimensions here, same relationship as
    stackCount is to a normal single-target session.

    `session`: optional DwarfSession - see perform_goto().
    """

    module_id = 3  # MODULE_ASTRO
    type_id = 0  # REQUEST

    ReqStartMosaic_message = astro.ReqStartMosaic()
    ReqStartMosaic_message.horizontal_scale = horizontal_scale
    ReqStartMosaic_message.vertical_scale = vertical_scale
    ReqStartMosaic_message.rotation = rotation
    ReqStartMosaic_message.ir_index = ir_index
    ReqStartMosaic_message.force_start = force_start

    command = protocol.CMD_ASTRO_START_TELE_MOSAIC

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStartMosaic_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqStartMosaic_message, command, type_id, module_id)

    if response is not False:

      if response == 0:
          log.success("START MOSAIC success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False

def perform_stopAstroPhoto(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # STOP CAPTURE RAW LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStopCaptureRawLiveStacking_message = astro.ReqStopCaptureRawLiveStacking()

    command = 11006 #CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStopCaptureRawLiveStacking_message, command, type_id, module_id)
    else:
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

def perform_takeAstroWidePhoto(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # START CAPTURE WIDE RAW WIDE LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqCaptureRawLiveStacking_message = astro.ReqCaptureRawLiveStacking()

    command = 11016 #CMD_ASTRO_START_CAPTURE_WIDE_RAW_LIVE_STACKING ?? Tob confirmed

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqCaptureRawLiveStacking_message, command, type_id, module_id)
    else:
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

def perform_stopAstroWidePhoto(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # STOP CAPTURE RAW LIVE STACKING
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStopCaptureRawLiveStacking_message = astro.ReqStopCaptureRawLiveStacking()

    command = 11017 #CMD_ASTRO_STOP_CAPTURE_RAW_LIVE_STACKING

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStopCaptureRawLiveStacking_message, command, type_id, module_id)
    else:
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

def perform_GoLive(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # CMD_ASTRO_GO_LIVE
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqGoLive_message = astro.ReqGoLive()

    command = 11010 #CMD_ASTRO_GO_LIVE

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqGoLive_message, command, type_id, module_id)
    else:
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

def perform_time(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

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

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqSetTime_message, command, type_id, module_id)
    else:
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

def perform_timezone(session=None):
    """`session`: optional DwarfSession - see perform_goto(). When given,
    prefers session.config.timezone over the mono-dwarf config.ini read."""

    # SET TIMEZONE
    module_id = 4  # MODULE_SYSTEM
    type_id = 0; #REQUEST

    timezone_value = session.config.timezone if session is not None else read_timezone()
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

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqSetTimezone_message, command, type_id, module_id)
    else:
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

def perform_set_location(session=None):
    """CMD_SYSTEM_SET_LOCATION (13010), MODULE_SYSTEM module (4).

    Confirmed via network capture of the official app (Aug 2026): sent at
    connection init, right after SET_TIME/SET_TIME_ZONE. country_region/
    province/city/district are display-only strings shown in the app,
    not used for any astro computation - left empty here since we don't
    have a reliable local source for them; only latitude/longitude/
    altitude matter for calibration/GOTO/EQ solving accuracy.

    Reads LATITUDE/LONGITUDE from config.ini (read_latitude/
    read_longitude) - returns False without sending anything if either
    is missing, same pattern as perform_timezone().

    `session`: optional DwarfSession - see perform_goto(). When given,
    prefers session.config.latitude/longitude over the mono-dwarf
    config.ini read.
    """
    module_id = 4  # MODULE_SYSTEM
    type_id = 0  # REQUEST

    if session is not None:
        latitude = session.config.latitude
        longitude = session.config.longitude
    else:
        latitude = read_latitude()
        longitude = read_longitude()
    if latitude is None or longitude is None:
        log.warning(
            "LATITUDE/LONGITUDE missing from config.ini: CMD_SYSTEM_SET_LOCATION not"
            " sent (an invalid value would crash the message construction)."
            " Set LATITUDE/LONGITUDE in config.ini if needed."
        )
        return False

    ReqSetLocation_message = system.ReqSetLocation()
    ReqSetLocation_message.latitude = latitude
    ReqSetLocation_message.longitude = longitude
    ReqSetLocation_message.altitude = 0
    log.notice(f"Location is : lat={latitude}, long={longitude}")

    command = 13010  # CMD_SYSTEM_SET_LOCATION

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqSetLocation_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqSetLocation_message, command, type_id, module_id)

    if response is not False:

      if response == 0:
          log.success("Set Location success")
          return True
      else:
          log.error(f"Error code: {response}")
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False
# NOTE: perform_get_device_state_info() already exists above (near
# perform_switch_shooting_mode) - confirmed via network capture of the
# official app (Aug 2026) to also be sent early at connection init,
# right after SET_TIME/SET_TIME_ZONE and before SET_LOCATION. Calling it
# early mirrors the official app's own startup sequence.

def perform_calibration(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # CALIBRATION
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStartCalibration_message = astro.ReqStartCalibration ()

    command = 11000 #CMD_ASTRO_START_CALIBRATION

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStartCalibration_message, command, type_id, module_id)
    else:
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

def perform_stop_calibration(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # STOP CALIBRATION
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStoptCalibration_message = astro.ReqStopCalibration ()

    command = 11001 #CMD_ASTRO_STOP_CALIBRATION

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStoptCalibration_message, command, type_id, module_id)
    else:
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

def perform_stop_goto(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # STOP GOTO
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStopGoto_message = astro.ReqStopGoto ()

    command = 11004 #CMD_ASTRO_STOP_GOTO

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStopGoto_message, command, type_id, module_id)
    else:
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

def perform_start_autofocus(infinite = False, session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # AutoFocus
    module_id = 8  # MODULE_FOCUS
    type_id = 0; #REQUEST

    ReqAstroAutoFocus_message = focus.ReqAstroAutoFocus ()

    # Assign the value : infinite = False : 0  True 1
    ReqAstroAutoFocus_message.mode = int(infinite)

    command = 15004 #CMD_FOCUS_START_ASTRO_AUTO_FOCUS

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqAstroAutoFocus_message, command, type_id, module_id)
    else:
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

def perform_stop_autofocus(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # AutoFocus
    module_id = 8  # MODULE_FOCUS
    type_id = 0; #REQUEST

    ReqStopAstroAutoFocus_message = focus.ReqStopAstroAutoFocus ()

    command = 15005 #CMD_FOCUS_STOP_ASTRO_AUTO_FOCUS

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStopAstroAutoFocus_message, command, type_id, module_id)
    else:
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

def get_result_value(type, result_cnx, is_double=False):
    """Restored (Aug 2026) from the pre-V3 (main branch) dwarf_utils.py -
    was missing entirely from this V3 branch's dwarf_utils.py even
    though 4 confirmed-working V3 functions here (perform_powerOpenRGB,
    perform_powerCloseRGB, perform_powerIndOn, perform_powerIndOff) call
    it directly - a pre-existing bug (NameError at call time, not
    caught by import/compile checks) unrelated to the dwarf_utilsV2.py
    migration. Also imported by dwarf_utilsV2.py for its own legacy
    functions - this is the canonical definition, not a copy."""

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
        log.error("Unknown Error ")

    return False

# perform_get_all_camera_setting(), perform_get_all_feature_camera_setting(),
# perform_get_all_camera_wide_setting(), perform_update_all_camera_setting(),
# perform_get_camera_setting(), and perform_update_camera_setting() all moved
# to dwarf_utilsV2.py (Aug 2026) - the three GET_ALL_*_SETTING functions are
# confirmed non-responsive on V3 hardware, and perform_update_camera_setting()
# is superseded by confirmed V3 functions for every branch that was actually
# exercised (see MIGRATION_V3.md).

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

def start_polar_align(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # start Polar Align
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStartEqSolving_message = astro.ReqStartEqSolving ()
    ReqStartEqSolving_message.lon = read_longitude(session=session);
    ReqStartEqSolving_message.lat = read_latitude(session=session);
    command = 11018; #CMD_ASTRO_START_EQ_SOLVING

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStartEqSolving_message, command, type_id, module_id)
    else:
        response = connect_socket(ReqStartEqSolving_message, command, type_id, module_id)

    return get_result_polar_value(response)

def stop_polar_align(session=None):
    """`session`: optional DwarfSession - see perform_goto()."""

    # stop Polar Align
    module_id = 3  # MODULE_ASTRO
    type_id = 0; #REQUEST

    ReqStopEqSolving_message = astro.ReqStopEqSolving ()
    command = 11019; #CMD_ASTRO_STOP_EQ_SOLVING

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, ReqStopEqSolving_message, command, type_id, module_id)
    else:
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

def motor_action( action, correction = 0, session=None ):
    """`session`: optional DwarfSession - see perform_goto()."""

    module_id = 6  # MODULE_MOTOR
    type_id = 0; #REQUEST

    # Rotation Motor Resetting
    if (action == 5):
      ReqMotorReset_message = motor.ReqMotorReset ()
      ReqMotorReset_message.id= 1;
      ReqMotorReset_message.direction = 0;
      command = 14003; #CMD_STEP_MOTOR_RESET
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorReset_message, command, type_id, module_id)
      else:
          response = connect_socket(ReqMotorReset_message, command, type_id, module_id)

    # Pitch Motor Resetting
    if (action == 6):
      ReqMotorReset_message = motor.ReqMotorReset ()
      ReqMotorReset_message.id= 2;
      ReqMotorReset_message.direction = 1;
      command = 14003; #CMD_STEP_MOTOR_RESET
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorReset_message, command, type_id, module_id)
      else:
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
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorRunTo_message, command, type_id, module_id)
      else:
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
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorRunTo_message, command, type_id, module_id)
      else:
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
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorRunTo_message, command, type_id, module_id)
      else:
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
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorRunTo_message, command, type_id, module_id)
      else:
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
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorRunTo_message, command, type_id, module_id)
      else:
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
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorRunTo_message, command, type_id, module_id)
      else:
          response = connect_socket(ReqMotorRunTo_message, command, type_id, module_id)

    if (action == 0):
      ReqMotorRun_message = motor.ReqMotorRun ()
      ReqMotorRun_message.id= 2;
      ReqMotorRun_message.speed = 10; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorRun_message.direction = 0;
      ReqMotorRun_message.speed_ramping = 100;
      ReqMotorRun_message.resolution_level = 3;
      command = 14000; #CMD_STEP_MOTOR_RUN
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorRun_message, command, type_id, module_id)
      else:
          response = connect_socket(ReqMotorRun_message, command, type_id, module_id)

    if (action == 8):
      ReqMotorGetPosition_message = motor.ReqMotorGetPosition ()
      ReqMotorGetPosition_message.id= 1;
      command = 14011; #CMD_STEP_MOTOR_GET_POSITION
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorGetPosition_message, command, type_id, module_id)
      else:
          response = connect_socket(ReqMotorGetPosition_message, command, type_id, module_id)

      ReqMotorGetPosition_message.id= 2;
      command = 14011; #CMD_STEP_MOTOR_GET_POSITION
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorGetPosition_message, command, type_id, module_id)
      else:
          response = connect_socket(ReqMotorGetPosition_message, command, type_id, module_id)

    if (action == 10):
      ReqMotorServiceJoystickFixedAngle_message = motor.ReqMotorServiceJoystickFixedAngle ()
      ReqMotorServiceJoystickFixedAngle_message.vector_length = 0.8; # 5 gears: 0.1, 1, 5, 10, 30 degrees/s
      ReqMotorServiceJoystickFixedAngle_message.speed = 15;

      command = 14006; #CMD_STEP_MOTOR_SERVICE_JOYSTICK
      active_session = _resolve_session(session)
      if active_session is not None:
          response = connect_socket_session(active_session, ReqMotorServiceJoystickFixedAngle_message, command, type_id, module_id)
      else:
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


def perform_get_default_params_config_http(session=None, port=8082, timeout=5):
    """GET /getDefaultParamsConfig (port 8082) - static default catalog.
    Based on your own tests, doesn't give much useful info anymore in V3
    (maybe just a generic catalog not tied to active param_id).

    `session`: optional DwarfSession - if given, targets that device's IP;
    otherwise falls back to the mono-dwarf config (_get_dwarf_ip()).
    """
    ip = session.config.dwarf_ip if session is not None else _get_dwarf_ip()
    if not ip:
        log.error("Dwarf API: unknown IP - run the BLE/web connection first.")
        return False
    url = f"http://{ip}:{port}/getDefaultParamsConfig"
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log.error(f"Error GET {url}: {e}")
        return False


def perform_get_param_and_setting_http(mode_id, session=None, port=8082, timeout=5):
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

    `session`: optional DwarfSession - see perform_get_default_params_config_http().
    """
    ip = session.config.dwarf_ip if session is not None else _get_dwarf_ip()
    if not ip:
        log.error("Dwarf API: unknown IP - run the BLE/web connection first.")
        return False
    url = f"http://{ip}:{port}/shootingMode/getParamAndSetting"
    try:
        response = requests.post(url, json={"modeId": int(mode_id)}, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        log.error(f"Error POST {url}: {e}")
        return False


DEVICE_INFO_HTTP_MODEL_MAP = {
    1: "Dwarf II",
    2: "Dwarf 3",
    3: "Dwarf 3 Pro (reserved, unreleased)",
    4: "Dwarf Mini",
}
"""Confirmed mapping for /deviceInfo's deviceId field, verified on a real
Dwarf 3 and Dwarf Mini.

Relationship to config.py's DWARF_ID (now resolved): config.py's DWARF_ID,
as written by connect_direct_bluetooth.py's BLE flow (dwarf_lib_ble.py,
detected by GATT service UUID), is the SAME raw value as /deviceInfo's
deviceId - NO offset. Confirmed twice on real hardware: Dwarf 3
(deviceId=2, DWARF_ID=2) and Dwarf Mini (deviceId=4, DWARF_ID=4).

config_to_dwarf_id_str()/config_to_dwarf_id_int() (get_config_data.py) is
a SEPARATE, intentional +1 transform used throughout astro_dwarf_session
and main_v3.py to get a "logical model number" for display and
model-specific branching (2=Dwarf II, 3=Dwarf 3, 5=Dwarf Mini - see e.g.
astro_dwarf_session_UI.py's DWARF_NAME_MAP, or dwarf_session.py's
model-specific IR filter branches). That logical number is NOT the same
scale as /deviceInfo's deviceId and should not be compared to it directly -
compare dwarf_model_id (raw) to deviceId (raw) instead, see
verify_device_identity() below.
"""


def perform_get_device_info_http(session=None, port=8082, timeout=5):
    """POST /deviceInfo (port 8082). Returns the device's own identity block:
    deviceName, sn, deviceId, mac/macAddress, staIpAddress, apIpAddress,
    sdCardInfo, wifiConnectedMode... - confirmed on a real Dwarf Mini AND a
    real Dwarf 3 (POST, not GET - GET returns 404, confirmed by testing).

    NOTE on deviceId: this field is a DIFFERENT numbering scheme from
    config.py's DWARF_ID - see DEVICE_INFO_HTTP_MODEL_MAP above for the
    confirmed conversion (config.py's DWARF_ID == this deviceId + 1).

    Useful to verify which physical device is actually reachable at a
    given IP, independent of BLE and of whatever config.py/config.ini
    happens to say - this is the only reliable identity check available
    when connecting directly (Dwarf already on + STA, no BLE (re)pairing
    done this run) - see verify_device_identity() below.

    SECURITY NOTE (confirmed on real hardware, unauthenticated plain
    HTTP): this endpoint also returns devicePwd and staWifiPwd in clear
    text. This function does NOT log the raw response for that reason -
    only pass along specific fields you need, and avoid logging/printing
    the full dict elsewhere.

    `session`: optional DwarfSession - if given, targets that device's IP;
    otherwise falls back to the mono-dwarf config (_get_dwarf_ip()).

    Returns the "data" dict on success, or False on error/unreachable.
    """
    ip = session.config.dwarf_ip if session is not None else _get_dwarf_ip()
    if not ip:
        log.error("Dwarf API: unknown IP - run the BLE/web connection first.")
        return False

    url = f"http://{ip}:{port}/deviceInfo"
    try:
        response = requests.post(url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        return payload.get("data") if isinstance(payload, dict) else payload
    except requests.RequestException as e:
        log.error(f"Error POST {url}: {e}")
        return False


def verify_device_identity(session, raise_on_mismatch=False):
    """Cross-checks the physical device actually reachable at
    session.config.dwarf_ip against session.config.dwarf_uid, using the
    live /deviceInfo HTTP endpoint (deviceName field - the same string BLE
    discovery uses as dwarf_uid, see dwarf_lib_ble.py's
    connection_state["device_dwarf_uid"] = dwarf_device.name).

    This is the safeguard for the "device already on + STA, connecting
    directly via WS/HTTP without BLE" path: apply_ble_discovery() (see
    dwarf_ble_session.py) only protects sessions during an actual BLE
    (re)pairing - it can't catch a config.py/config.ini whose (uid, ip)
    pairing was already wrong before this run started, since no BLE step
    ever ran to trigger it. Call this right after connecting, before
    sending any capture/goto command, whenever the session's identity
    wasn't just freshly confirmed by BLE.

    Returns:
        True  - confirmed match
        False - confirmed MISMATCH (wrong physical device at this IP)
        None  - could not verify (endpoint unreachable) - NOT a confirmed
                match, treat with the same caution as an unverified session

    If raise_on_mismatch=True, raises RuntimeError on a confirmed
    mismatch instead of returning False - use this to hard-abort before
    any command reaches what might be the wrong physical Dwarf.
    """
    info = perform_get_device_info_http(session=session)
    if not info:
        log.warning(
            f"[{session.dwarf_uid}] Could not reach /deviceInfo to verify identity "
            "- proceeding WITHOUT identity confirmation."
        )
        return None

    actual_name = info.get("deviceName")
    expected_name = session.config.dwarf_uid

    if actual_name != expected_name:
        message = (
            f"IDENTITY MISMATCH at {session.config.dwarf_ip}: config says dwarf_uid={expected_name!r}, "
            f"but the device actually there reports deviceName={actual_name!r} (sn={info.get('sn')!r}). "
            "This is very likely the wrong physical Dwarf - aborting rather than risk sending "
            "commands to it."
        )
        log.error(message)
        if raise_on_mismatch:
            raise RuntimeError(message)
        return False

    # Secondary, independent signal: config.py's DWARF_ID (dwarf_model_id)
    # should equal /deviceInfo's deviceId DIRECTLY - both use the same raw
    # 1=Dwarf II/2=Dwarf 3/4=Dwarf Mini scheme (confirmed on real Dwarf 3
    # and Dwarf Mini hardware - see DEVICE_INFO_HTTP_MODEL_MAP above for
    # why this is NOT the same as the +1 "logical model number" produced
    # by config_to_dwarf_id_str()/_int()). deviceName matching is still the
    # authoritative check above (this doesn't override it either way) -
    # this just catches a config file with a self-inconsistent
    # dwarf_uid/dwarf_model_id pair even when dwarf_uid happens to be right.
    raw_device_id = info.get("deviceId")
    if raw_device_id is not None and session.config.dwarf_model_id:
        try:
            expected_model_id = int(session.config.dwarf_model_id)
            actual_model_id = int(raw_device_id)
            if expected_model_id != actual_model_id:
                model_name = DEVICE_INFO_HTTP_MODEL_MAP.get(actual_model_id, "unknown model")
                log.warning(
                    f"[{session.dwarf_uid}] deviceName matches, but dwarf_model_id in config "
                    f"({expected_model_id}) doesn't match the device's actual deviceId "
                    f"({actual_model_id}, i.e. {model_name}) - config.py may have a stale/incorrect "
                    "DWARF_ID even though DWARF_UID is right."
                )
        except (TypeError, ValueError):
            pass

    log.success(f"[{session.dwarf_uid}] Identity verified via /deviceInfo (sn={info.get('sn')!r}).")
    return True


def resolve_dwarf_ip(session, raise_on_failure=False):
    """Try session.config.dwarf_ip (primary, from config.py) first via
    /deviceInfo; if that doesn't confirm the right dwarf_uid (wrong device,
    or unreachable), try session.config.alternate_dwarf_ip (the candidate
    that was discarded at load time - typically config.ini's dwarf_ip,
    which BLE never updates and so can legitimately drift from config.py's)
    as a fallback. Whichever candidate confirms the right uid becomes the
    session's dwarf_ip (any already-open stale connection to the other
    address is disconnected first). If NEITHER confirms - including the
    case where an address answers but with the WRONG device (e.g. two
    Dwarf physically swapped IPs) - this returns False: stop rather than
    guess further.

    This does not involve BLE at all - it only tries addresses already
    known from config.py/config.ini. For a genuinely NEW/unknown IP (the
    device moved to an address neither file mentions), use
    ensure_device_reachable() instead, which can fall back to a BLE scan.

    Returns True (resolved, session.config.dwarf_ip updated if needed),
    False (a candidate answered but with the WRONG device - a confirmed
    mismatch, not just unreachable), None (neither candidate could be
    reached at all - unconfirmed, not the same as a confirmed mismatch),
    or raises if raise_on_failure=True and nothing confirms.
    """
    primary_ip = session.config.dwarf_ip
    result = verify_device_identity(session)
    if result is True:
        return True

    alternate_ip = session.config.alternate_dwarf_ip
    if not alternate_ip or alternate_ip == primary_ip:
        log.warning(f"[{session.dwarf_uid}] No alternate IP candidate to fall back to.")
        if raise_on_failure:
            raise RuntimeError(f"Could not resolve dwarf_ip for {session.dwarf_uid} (tried {primary_ip!r} only)")
        return result  # False (confirmed wrong device) or None (unreachable) - preserve the distinction

    log.notice(
        f"[{session.dwarf_uid}] {primary_ip!r} didn't confirm - trying alternate candidate {alternate_ip!r} "
        "(from config.ini) before giving up."
    )
    if session.client_instance is not None:
        disconnect_socket_session(session)
    session.config.dwarf_ip = alternate_ip

    result2 = verify_device_identity(session)
    if result2 is True:
        log.success(f"[{session.dwarf_uid}] Alternate candidate {alternate_ip!r} confirmed - adopting it.")
        return True

    # Neither candidate panned out - restore the primary as the "recorded"
    # value rather than leave the session pointed at an unconfirmed
    # alternate, and stop. Distinguish a CONFIRMED wrong-device match
    # (False on either candidate) from both simply being unreachable
    # (None, None) - the latter is a connectivity/staleness question, not
    # proof the wrong device is out there.
    session.config.dwarf_ip = primary_ip
    confirmed_mismatch = (result is False) or (result2 is False)
    if confirmed_mismatch:
        log.error(
            f"[{session.dwarf_uid}] A candidate answered but with the WRONG device - stopping "
            f"(tried {primary_ip!r} and {alternate_ip!r})."
        )
    else:
        log.warning(
            f"[{session.dwarf_uid}] Neither {primary_ip!r} nor {alternate_ip!r} was reachable - "
            "identity unconfirmed (not a confirmed mismatch)."
        )
    if raise_on_failure:
        raise RuntimeError(f"Could not resolve dwarf_ip for {session.dwarf_uid} (tried {primary_ip!r} and {alternate_ip!r})")
    return False if confirmed_mismatch else None


def ensure_device_reachable(session, ble_ssid=None, ble_pwd=None, ble_psd=None, raise_on_failure=False):
    """Best-effort recovery for a session whose configured dwarf_ip may be
    stale - e.g. the device got a new IP (DHCP renewal, reconnected via
    the official phone app, moved to a different network) without a
    session-aware BLE reconnect in THIS process to catch it via
    apply_ble_discovery(). Verifying against a known-stale IP that nothing
    answers at is pointless - the right fix is to refresh the IP first,
    THEN verify against the new one, not endlessly retry the old dead one.

    Strategy:
      1. verify_device_identity(session) against the currently configured IP.
      2. If that's not a confirmed match (False: wrong device answered, or
         None: unreachable - most likely because the configured IP is
         stale), and BLE credentials were given, attempt a BLE reconnect
         targeted at THIS session's dwarf_uid (auto_select=session.dwarf_uid,
         so it's picked automatically even if several Dwarf are visible).
         This goes through connect_ble_direct_dwarf(..., session=session),
         so a successful reconnect updates session.config.dwarf_ip via
         apply_ble_discovery() and disconnects any stale open connection.
      3. Re-verify identity - this time against the freshly discovered IP.

    Without ble_ssid/ble_pwd, this behaves exactly like a plain
    verify_device_identity() call (no recovery attempted).

    Returns True only once a match is confirmed (possibly after
    recovery). False/None otherwise, matching verify_device_identity()'s
    return convention - see its docstring.
    """
    result = verify_device_identity(session)
    if result is True:
        return True

    if not (ble_ssid and ble_pwd):
        log.warning(
            f"[{session.dwarf_uid}] Not confirmed at {session.config.dwarf_ip} and no BLE credentials "
            "given to attempt recovery - giving up. Pass ble_ssid/ble_pwd to auto-recover from a stale IP."
        )
        if raise_on_failure:
            raise RuntimeError(f"Could not verify/reach {session.dwarf_uid} at {session.config.dwarf_ip}")
        return result

    log.notice(
        f"[{session.dwarf_uid}] Not reachable/confirmed at {session.config.dwarf_ip} - attempting a BLE "
        "reconnect to refresh its IP before giving up."
    )
    from dwarf_ble_connect.lib.connect_direct_bluetooth import connect_ble_direct_dwarf

    ble_ok = connect_ble_direct_dwarf(
        ble_psd or "DWARF_12345678", ble_ssid, ble_pwd, auto_select=session.dwarf_uid, session=session,
    )
    if not ble_ok:
        log.error(f"[{session.dwarf_uid}] BLE reconnect failed - giving up.")
        if raise_on_failure:
            raise RuntimeError(f"BLE reconnect failed for {session.dwarf_uid}")
        return False

    # session.config.dwarf_ip has just been refreshed in place by
    # apply_ble_discovery() (called inside connect_ble_direct_dwarf above) -
    # verify again, this time against the NEW ip, not the stale one.
    log.info(f"[{session.dwarf_uid}] BLE reconnect done - IP refreshed to {session.config.dwarf_ip!r}, re-verifying.")
    return verify_device_identity(session, raise_on_mismatch=raise_on_failure) is True


# ---------------------------------------------------------------------------
# V3: astro/DSO-specific settings (subframe count, mosaic,
# auto calibration) - discovered via the live HTTP API
# shootingMode/getParamAndSetting (modeId=2)
# ---------------------------------------------------------------------------

def perform_set_astro_stack_count_v3(count, camera="tele", session=None):
    """Total number of subframes to stack for an astro session.
    camera: "tele" or "wide". Confirmed by the live HTTP API
    (shootingMode/getParamAndSetting, modeId=2): range 1-999 for both
    cameras, value observed 390 (tele) / 100 (wide) at the time of capture.

    `session`: optional DwarfSession - see perform_goto().
    """
    param_id = PARAM_ID_ASTRO_STACK_COUNT_WIDE if camera == "wide" else PARAM_ID_ASTRO_STACK_COUNT_TELE
    return perform_set_image_param_v3(param_id, count, session=session)


def perform_set_astro_mosaic_count_v3(count, session=None):
    """Number of panels for an astro mosaic (tele camera only, no wide
    equivalent observed). Range 1-249 (default 45).

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(PARAM_ID_ASTRO_MOSAIC_COUNT_TELE, count, session=session)


def perform_set_astro_stack_format_v3(value, session=None):
    """Image format for astro stacking sessions - shared setting, not
    per-camera (tele/wide). Confirmed by network capture (Dwarf Mini,
    Aug 2026): 2 = FITS, 3 = TIFF.

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(PARAM_ID_ASTRO_STACK_FORMAT, value, session=session)


def perform_set_astro_display_source_v3(value, session=None):
    """Preview display source for astro stacking sessions - shared
    setting, not per-camera (tele/wide). Confirmed by network capture
    (Dwarf 3, Aug 2026): values 0 and 1 both accepted. 0 = Single
    (field-confirmed); the meaning of 1 is not yet confirmed (likely
    "Stacked"/live-stack preview, based on the setting's name, but not
    independently verified).

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(PARAM_ID_ASTRO_DISPLAY_SOURCE, value, session=session)


def perform_set_astro_stack_binning_v3(value, session=None):
    """Binning for astro stacking sessions - shared setting, not
    per-camera (tele/wide). Confirmed by network capture (Dwarf 3, Aug
    2026): 0 = 4k, 1 = 2k. The control was reported missing from the
    official app's UI at one point (relocated, not discontinued - see
    PARAM_ID_ASTRO_STACK_BINNING).

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_image_param_v3(PARAM_ID_ASTRO_STACK_BINNING, value, session=session)


def perform_set_bool_param_v3(param_id, value, session=None):
    """CMD_PARAM_SET_GENERAL_BOOL_PARAMS (16705, NOT CONFIRMED by network
    capture - inferred from sequential position, see comment above).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = protocol.MODULE_CAMERA_PARAMS
    type_id = 0  # REQUEST

    message = param.ReqSetGeneralBoolParams()
    message.param_id = param_id
    message.value = bool(value)

    command = CMD_PARAM_SET_GENERAL_BOOL_PARAMS

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"SET BOOL PARAM (V3) {hex(param_id)} -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")

    return False


def perform_set_astro_auto_calibration_v3(enabled, session=None):
    """Enables/disables automatic calibration before GOTO in astro/DSO
    mode. NOT CONFIRMED by network capture (see perform_set_bool_param_v3).
    Per the live HTTP API, defaultValue=true but currentValue=false at the
    time of capture (the user had disabled it).

    `session`: optional DwarfSession - see perform_goto().
    """
    return perform_set_bool_param_v3(PARAM_ID_ASTRO_AUTO_CALIBRATION, enabled, session=session)


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

def perform_read_camera_params_http_v3(mode_id, session=None):
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
    raw = perform_get_param_and_setting_http(mode_id, session=session)
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

def perform_start_burst_v3(session=None):
    """CMD_CAMERA_TELE_BURST (10003) - triggers a burst (count/interval
    set beforehand via perform_set_burst_count_v3()/
    perform_set_burst_interval_by_name_v3()).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = 1  # MODULE_CAMERA_TELE
    type_id = 0  # REQUEST

    message = camera.ReqBurstPhoto()

    command = 10003  # CMD_CAMERA_TELE_BURST

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"BURST -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_stop_burst_v3(session=None):
    """CMD_CAMERA_TELE_STOP_BURST (10004).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = 1
    type_id = 0

    message = camera.ReqStopBurstPhoto()

    command = 10004  # CMD_CAMERA_TELE_STOP_BURST

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"STOP BURST -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_start_record_v3(session=None):
    """CMD_CAMERA_TELE_START_RECORD (10005) - starts video recording.

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = 1
    type_id = 0

    message = camera.ReqStartRecord()

    command = 10005  # CMD_CAMERA_TELE_START_RECORD

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"START RECORD -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_stop_record_v3(session=None):
    """CMD_CAMERA_TELE_STOP_RECORD (10006).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = 1
    type_id = 0

    message = camera.ReqStopRecord()

    command = 10006  # CMD_CAMERA_TELE_STOP_RECORD

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"STOP RECORD -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_start_timelapse_v3(session=None):
    """CMD_CAMERA_TELE_START_TIMELAPSE_PHOTO (10033) - starts the timelapse
    (interval/duration set beforehand via perform_set_timelapse_*).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = 1
    type_id = 0

    message = camera.ReqStartTimeLapse()

    command = 10033  # CMD_CAMERA_TELE_START_TIMELAPSE_PHOTO

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
        response = connect_socket(message, command, type_id, module_id)

    if response is not False:
        log.success(f"START TIMELAPSE -> {response}")
        return response
    else:
        log.error("Dwarf API: Dwarf Device not connected")
    return False


def perform_stop_timelapse_v3(session=None):
    """CMD_CAMERA_TELE_STOP_TIMELAPSE_PHOTO (10034).

    `session`: optional DwarfSession - see perform_goto().
    """
    module_id = 1
    type_id = 0

    message = camera.ReqStopTimeLapse()

    command = 10034  # CMD_CAMERA_TELE_STOP_TIMELAPSE_PHOTO

    active_session = _resolve_session(session)
    if active_session is not None:
        response = connect_socket_session(active_session, message, command, type_id, module_id)
    else:
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

def perform_read_astro_stacking_status_v3(session=None):
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

    `session`: optional DwarfSession - see perform_goto().
    """
    active_session = _resolve_session(session)
    if active_session is not None:
        status = get_client_status_session(active_session)
    else:
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