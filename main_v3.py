"""
main_v3.py
-----------
V3 adaptation of the interactive menu from dwarf_test_apiV2/main.py, on
the same skeleton (text menu, sub-menus, loop) but wired to the V3
functions verified in this repo (see MIGRATION_V3.md for details on each).

Focuses on the CAMERA part (the bulk of the work done so far) and the
general functions that are already solid (connection, motor joystick,
status). Full astro GOTO/stacking is not covered here yet (next step of
the project) - only entering astro/DSO mode and the associated settings
(stackCount, auto calibration) are available.

Notable differences from dwarf_test_apiV2/main.py:
- No Bluetooth connection through this menu: run connect_bluetooth_cmd.py
  (or the web mode) separately first, THEN this script.
- Reading parameters goes through the live HTTP API
  (perform_read_camera_params_http_v3), not the old V2 commands
  CMD_CAMERA_TELE_GET_ALL_PARAMS (confirmed unresponsive in V3) - allow a
  few seconds after connecting before the first call (see MIGRATION_V3.md,
  "warm-up period").
- Entering a mode (photo/astro/burst/video/timelapse) is explicit and
  required before using the corresponding functions - unlike V2 where
  opening the camera was enough for everything. Reminder: you need to
  switch the technique (tech) again every time you change the type of
  shot (photo/burst/video/timelapse), even within mode 1 "Normal".

Usage:
    python connect_bluetooth_cmd.py --ssid "..." --pwd "..."   # once
    python main_v3.py
"""

import json
import time
import configparser

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_utils import (
    set_HostMaster,
    perform_time,
    perform_timezone,
    perform_set_location,
    perform_get_device_state_info,
    perform_enter_photo_mode,
    perform_enter_astro_mode,
    perform_enter_shooting_mode,
    perform_set_exposure_by_name_v3,
    perform_set_gain_v3,
    perform_set_gain_by_camera_v3,
    perform_set_wb_v3,
    perform_set_wb_preset_by_name_v3,
    perform_set_brightness_v3,
    perform_set_contrast_v3,
    perform_set_saturation_v3,
    perform_set_hue_v3,
    perform_set_sharpness_v3,
    perform_set_ir_filter_v3,
    perform_set_burst_count_v3,
    perform_set_burst_interval_by_name_v3,
    perform_set_timelapse_interval_by_name_v3,
    perform_set_timelapse_duration_by_name_v3,
    perform_read_camera_params_http_v3,
    perform_set_astro_stack_count_v3,
    perform_set_astro_mosaic_count_v3,
    perform_set_astro_auto_calibration_v3,
    perform_takePhoto,
    perform_start_burst_v3,
    perform_stop_burst_v3,
    perform_start_record_v3,
    perform_stop_record_v3,
    perform_start_timelapse_v3,
    perform_stop_timelapse_v3,
    perform_auto_focus_v3,
    perform_motor_joystick_v3,
    perform_motor_joystick_stop_v3,
    motor_action,
    perform_disconnect,
    perform_reboot,
    perform_powerdown,
    perform_set_astro_exposure_by_name_v3,
    perform_set_astro_gain_v3,
    perform_read_astro_stacking_status_v3,
    perform_takeAstroPhoto,
    perform_stopAstroPhoto,
    perform_calibration,
    perform_stop_calibration,
    perform_start_autofocus,
    perform_stop_autofocus,
    start_polar_align,
    stop_polar_align,
    perform_goto,
    perform_goto_stellar,
    perform_stop_goto,
    perform_waitEndAstroPhoto,
    perform_GoLive,
    perform_decoding_test,
    perform_decode_wireshark,
    perform_takeWidePhoto,
    perform_takeAstroWidePhoto,
    perform_stopAstroWidePhoto,
    perform_waitEndAstroWidePhoto,
    perform_powerOpenRGB,
    perform_powerCloseRGB,
    perform_powerIndOn,
    perform_powerIndOff,
    read_camera_exposure,
    read_camera_gain,
    read_camera_IR,
    read_camera_count,
    read_camera_wide_exposure,
    read_camera_wide_gain,
    perform_get_all_feature_camera_setting,
    perform_update_camera_setting,
)
from dwarf_python_api.get_live_data_dwarf import get_live_data

from dwarf_python_api.lib.data_utils import (
    allowed_exposures,
    allowed_exposuresD3,
    allowed_exposuresMini,
)
from dwarf_python_api.lib.data_wide_utils import (
    allowed_wide_exposures,
    allowed_wide_exposuresD3,
    allowed_wide_exposuresMini,
)
import dwarf_python_api.get_config_data
from dwarf_python_api.lib.websockets_utils import get_client_status
from dwarf_python_api.lib.dwarf_utils import (
    read_bluetooth_ble_wifi_type,
    read_bluetooth_autoAP,
    read_bluetooth_country_list,
    read_bluetooth_country,
    read_bluetooth_ble_psd,
    read_bluetooth_autoSTA,
    read_bluetooth_ble_STA_ssid,
    read_bluetooth_ble_STA_pwd,
)
from dwarf_ble_connect.connect_bluetooth import connect_bluetooth
from dwarf_ble_connect.lib.connect_direct_bluetooth import connect_ble_direct_dwarf


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def display_menu():
    print("")
    print("----------------------------------")
    print("    Dwarf API V3 - Test Menu      ")
    print("  ( First use menu B with B1 or B2")
    print("    for bluetooth connection )    ")
    print("----------------------------------")
    print("1. Full connection (MASTER LOCK + time/timezone)")
    print("2. Diagnostic (GET_DEVICE_STATE_INFO)")
    print("B. Bluetooth Functions")
    print("C. Camera Functions")
    print("A. Astro Functions (GOTO, calibration, EQ, stacking)")
    print("M. Motor Functions (Polar Position, joystick)")
    print("L. Light Functions (RGB / power indicator)")
    print("I. Get Live Image Data Function")
    print("S. Show status (get_client_status)")
    print("D. Force Disconnection")
    print("P. Power Off The Dwarf")
    print("R. Reboot the Dwarf")
    print("T. Test Frames Decoding")
    print("0. Exit")


def display_menu_test():
    print("")
    print("------------------")
    print("T1. Decoding Test Frames 1")
    print("T2. Decoding Test Frames 2")
    print("T3. Decoding Test Frames 3")
    print("T4. Decoding All Test Frames")
    print("D. Decoding Unmasked Wireshark Frame")
    print("0. Return")


def get_user_choice():
    try:
        return input("Enter your choice (1,2,B,C,A,M,L,I,S,D,P,R) or 0 to exit: ")
    except KeyboardInterrupt:
        print("Operation interrupted by the user (CTRL+C).")
        return '0'


def get_user_choice_test():
    try:
        choice = input("Enter your choice (T1 to T4) or D or 0 to return to main menu: ")
    except KeyboardInterrupt:
        print("Operation interrupted by the user (CTRL+C).")
        choice = '0'
    return choice


def option_1():
    print("=== Full connection ===")
    if not set_HostMaster():
        log.warning("MASTER LOCK: no response (expected on V3, non-blocking).")
    perform_time()
    perform_timezone()
    perform_set_location()
    log.success("Connection complete. Wait a few seconds (firmware warm-up)"
                " before using Camera functions that read live state.")


def option_2():
    print("=== Diagnostic GET_DEVICE_STATE_INFO ===")
    print("(details - shooting_mode_and_techs, battery, focus, etc. -")
    print(" are printed in the logs, NOTICE/INFO level)")
    result = perform_get_device_state_info()
    print(f"Return code: {result}")


def option_D():
    print("=== Force Disconnection ===")
    perform_disconnect()


def option_P():
    confirm = input("Confirm powering off the Dwarf? (y/N): ")
    if confirm.lower() == 'y':
        perform_powerdown()


def option_R():
    confirm = input("Confirm rebooting the Dwarf? (y/N): ")
    if confirm.lower() == 'y':
        perform_reboot()


def option_S():
    print("=== Status (get_client_status) ===")
    status = get_client_status()
    print(json.dumps(status, indent=4))


def option_T():
    print("You selected Option T: Do Tests..")
    choice_test()
    # Add your Option T functionality here


def option_20():
    print("You selected Option T1: Decoding Test Frames 1")
    print("")
    # Add your Option T1 functionality here
    perform_decoding_test(True, False, False)


def option_21():
    print("You selected Option T2: Decoding Test Frames 2")
    print("")
    # Add your Option T2 functionality here
    perform_decoding_test(False, True, False)


def option_22():
    print("You selected Option T3: Decoding Test Frames 3")
    print("")
    # Add your Option T3 functionality here
    perform_decoding_test(False, False, True)


def option_23():
    print("You selected Option T4: Decoding Test All Frames")
    print("")
    # Add your Option T4 functionality here
    perform_decoding_test(True, True, True)


def option_24():
    print("You selected Option D. Decoding Unmasked Wireshark Frame")
    print("")
    # Add your Option D1 functionality here
    return input_frame(False)


# ---------------------------------------------------------------------------
# Input validation helpers - avoid silently sending a wrong/garbage value
# ---------------------------------------------------------------------------
# IMPORTANT for exposure: get_exposure_index_by_name()/
# get_wide_exposure_index_by_name() silently fall back to the table's
# default index if the name isn't found - so a typo currently resets
# exposure to its default value with NO warning at all. Validate here
# first so a bad name is caught and reported instead.

def _exposure_table_for(dwarf_id, camera):
    """Returns the AllowedExposures* table matching (dwarf_id, camera)."""
    if camera == "wide":
        if str(dwarf_id) == "5":
            return allowed_wide_exposuresMini
        elif str(dwarf_id) == "3":
            return allowed_wide_exposuresD3
        else:
            return allowed_wide_exposures
    else:
        if str(dwarf_id) == "5":
            return allowed_exposuresMini
        elif str(dwarf_id) == "3":
            return allowed_exposuresD3
        else:
            return allowed_exposures


def validate_exposure_name(name, dwarf_id, camera):
    """Checks that `name` is one of the valid exposure names for this
    device/camera. Returns True if valid, otherwise prints the list of
    valid names and returns False (caller should not proceed)."""
    table = _exposure_table_for(dwarf_id, camera)
    valid_names = [v["name"] for v in table.values]
    if name in valid_names:
        return True
    print(f"Invalid exposure name '{name}' for dwarf_id={dwarf_id}, camera={camera}.")
    print(f"Valid values: {', '.join(valid_names)}")
    return False


def validate_gain_value(value, mode, dwarf_id, camera):
    """Sanity range check for a gain value before sending it (V3 gain is
    a direct value, not a table index, so there is no discrete list to
    check against - only known min/max bounds, per device/mode/camera,
    read from the official app's own UI limits.

    Confirmed ranges (Aug 2026):
    - D3 tele:  normal 0-240   / astro 40-240
    - D3 wide:  normal 0-240   / astro 0-240    (no 40 floor on wide)
    - Mini tele: normal 0-240  / astro 40-240   (same as D3 tele)
    - Mini wide: normal 40-2500 (!) / astro 40-240
      The 2500 ceiling in Mini wide normal mode is confirmed (not a typo)
      - a full order of magnitude above every other range here, possibly
      a different gain scale/unit for that specific sensor/mode.
    - Dwarf II: not confirmed - falls back to the same bounds as tele/D3.
    """
    if camera == "wide" and dwarf_id == "3":
        min_v, max_v = (0, 240)
    elif camera == "wide" and dwarf_id == "5":
        if mode == 2:
            min_v, max_v = (40, 240)
        else:
            min_v, max_v = (40, 2500)
    elif mode == 2:
        min_v, max_v = (40, 240)
    else:
        min_v, max_v = (0, 240)
    if min_v <= value <= max_v:
        return True
    print(f"Invalid gain value {value}: expected between {min_v} and {max_v} for mode={mode}, dwarf_id={dwarf_id}, camera={camera}.")
    return False


def update_config(longitude, latitude, timezone):
    """Saves the observer's longitude/latitude/timezone to config.ini -
    required by perform_goto_stellar() (solar system targets) before it
    can compute the target's position. Ported from the original
    dwarf_test_apiV2/main.py (unchanged - plain config.ini write, no V3
    protocol involved)."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    if 'CONFIG' not in config:
        config['CONFIG'] = {}
    config['CONFIG']['LONGITUDE'] = longitude
    config['CONFIG']['LATITUDE'] = latitude
    config['CONFIG']['TIMEZONE'] = timezone
    with open('config.ini', 'w') as config_file:
        config.write(config_file)


def input_test():
    user_longitude = input("Enter your Longitude: ")
    print("You entered:", user_longitude)
    user_latitude = input("Enter your Latitude: ")
    print("You entered:", user_latitude)
    user_timezone = input("Enter your TimeZone: ")
    print("You entered:", user_timezone)
    print("")
    update_config(user_longitude, user_latitude, user_timezone)


def input_manual_target():
    target_name = input("Enter a name for the target: ")
    print("You entered:", target_name)
    manual_RA = input("Enter the Right Ascension (hr:mm:ss.s) or decimal: ")
    print("You entered:", manual_RA)
    try:
        decimal_RA = float(manual_RA)
    except ValueError:
        decimal_RA = parse_ra_to_float(manual_RA)
    print("Converted to:", decimal_RA)
    manual_declination = input("Enter the Declination (<sign>deg:mm:ss.s) or decimal: ")
    print("You entered:", manual_declination)
    try:
        decimal_Dec = float(manual_declination)
    except ValueError:
        decimal_Dec = parse_ra_to_float(manual_declination)
    print("Converted to:", decimal_Dec)
    print("")
    go_goto = input("Press Enter to continue or 0 to exit: ")
    if (go_goto !="0"):
        # Convert to decimal value if not enterered
        perform_goto(decimal_RA, decimal_Dec, target_name)
    else:
        exit


def input_frame(masked):
    user_frame = input("Enter the wireshark capture frame payload data (option copy as C String) or 0 to return to previous menu: ")
    user_maskedcode = ""
    if (user_frame == "0"):
      return '0'
    else:
      print("You entered:", user_frame)
      if (masked):
          user_maskedcode = input("Enter the masked code: ")
          print("You entered:", user_maskedcode)
      perform_decode_wireshark(user_frame, masked, user_maskedcode)
      input_frame(masked)
      return ''


# ---------------------------------------------------------------------------
# Bluetooth sub-menu
# ---------------------------------------------------------------------------

def display_menu_bluetooth():
    print("")
    print("------------------ BLUETOOTH ------------------")
    print("B1. Connect via Bluetooth (direct/command-line mode)")
    print("B2. Connect via Bluetooth (web browser mode)")
    print("B3. Show saved Bluetooth configuration")
    print("B4. Edit WiFi SSID / password / Bluetooth password")
    print("0.  Return")


def get_user_choice_bluetooth():
    try:
        return input("Enter your choice (B1 to B4) or 0 to return: ")
    except KeyboardInterrupt:
        print("Operation interrupted by the user (CTRL+C).")
        return '0'


def _after_bluetooth_connect(success):
    """V3 sequence to run right after a successful Bluetooth connection
    (same logic as connect_bluetooth_cmd.py): MASTER LOCK + time/timezone.
    """
    if not success:
        log.error("Bluetooth -> WiFi connection failed.")
        return
    log.success("Bluetooth -> WiFi connection succeeded. IP saved in config.ini")
    option_1()


def option_B1():
    print("=== Direct Bluetooth connection (command line) ===")
    ble_psd = read_bluetooth_ble_psd() or "DWARF_12345678"
    ble_STA_ssid = read_bluetooth_ble_STA_ssid() or input("Target WiFi network SSID: ").strip()
    ble_STA_pwd = read_bluetooth_ble_STA_pwd() or input("Target WiFi network password: ").strip()
    select = input("Exact device name if several are detected (empty = auto): ").strip()

    result = connect_ble_direct_dwarf(ble_psd, ble_STA_ssid, ble_STA_pwd, select)
    _after_bluetooth_connect(result)


def option_B2():
    print("=== Bluetooth connection via web browser ===")
    print("(opens a local server + web page for BLE pairing from the browser)")
    result = connect_bluetooth()
    _after_bluetooth_connect(result)


def option_B3():
    print("=== Saved Bluetooth configuration (config.ini) ===")
    if (v := read_bluetooth_ble_wifi_type()) is not None:
        print(f"AP WiFi type: {'5G' if v == '0' else '2.4G'}")
    if (v := read_bluetooth_autoAP()) is not None:
        print(f"AP auto-start: {'no' if v == '0' else 'yes'}")
    if (v := read_bluetooth_country_list()) is not None:
        print(f"Country configuration: {'no' if v == '0' else 'yes'}")
    if (v := read_bluetooth_country()):
        print(f"Country: {v}")
    if (v := read_bluetooth_ble_psd()):
        print(f"Bluetooth password: {v}")
    if (v := read_bluetooth_autoSTA()) is not None:
        print(f"STA auto-start: {'no' if v == '0' else 'yes'}")
    if (v := read_bluetooth_ble_STA_ssid()):
        print(f"WiFi SSID (STA): {v}")
    if (v := read_bluetooth_ble_STA_pwd()):
        print(f"WiFi password (STA): {v}")


def option_B4():
    print("=== Edit WiFi SSID / password / Bluetooth password ===")
    print("(leave blank to leave a field unchanged)")
    ssid = input(f"New WiFi SSID [{read_bluetooth_ble_STA_ssid() or ''}]: ").strip()
    pwd = input("New WiFi password: ").strip()
    ble_psd = input(f"New Bluetooth password [{read_bluetooth_ble_psd() or 'DWARF_12345678'}]: ").strip()

    config = configparser.ConfigParser()
    config.read('config.ini')
    if 'CONFIG' not in config:
        config['CONFIG'] = {}
    if ssid:
        config['CONFIG']['BLE_STA_SSID'] = ssid
    if pwd:
        config['CONFIG']['BLE_STA_PWD'] = pwd
    if ble_psd:
        config['CONFIG']['BLE_PSD'] = ble_psd
    if ssid or pwd or ble_psd:
        with open('config.ini', 'w') as f:
            config.write(f)
        log.success("Bluetooth configuration updated in config.ini")
    else:
        print("No changes made.")


def choice_bluetooth():
    while True:
        display_menu_bluetooth()
        choice = get_user_choice_bluetooth().upper()
        actions = {'B1': option_B1, 'B2': option_B2, 'B3': option_B3, 'B4': option_B4}
        if choice == '0':
            print("Return to the main menu")
            break
        elif choice in actions:
            actions[choice]()
        else:
            print("Invalid choice. Please enter a correct value.")


# ---------------------------------------------------------------------------
# Camera sub-menu
# ---------------------------------------------------------------------------

def display_menu_camera():
    print("")
    print("------------------ CAMERA ------------------")
    print("C1.  Enter Simple Photo mode (mode=1, tech=1)")
    print("C2.  Enter astro mode (mode=8, Sun - see Astro submenu A13/A14 for DSO/Moon/Planet)")
    print("C3.  Read all current parameters (live HTTP API)")
    print("C4.  Set exposure (by name, e.g. 0.5, 1/1000) - tele or wide")
    print("C5.  Set gain (raw displayed value) - tele or wide")
    print("C6.  Set white balance - Kelvin temperature (2800-7500)")
    print("C7.  Set white balance - preset (Incandescent, Fluorescent, ...)")
    print("C8.  Set brightness/contrast/saturation/hue/sharpness")
    print("C9.  Set IR filter (VIS Filter / Astro Filter / Duo-Band Filter)")
    print("C10. Set burst settings (photo count + interval)")
    print("C11. Set timelapse settings (interval + total duration)")
    print("C12. Take one photo only")
    print("C13. Start/Stop a burst")
    print("C14. Start/Stop a video recording")
    print("C15. Start/Stop a timelapse")
    print("C16. Autofocus (normal/photo mode)")
    print("C17. Astro: set stackCount/mosaicCount")
    print("C18. Astro: enable/disable auto calibration")
    print("C19. Read saved config camera data (config.ini)")
    print("C20. Input camera data into config.ini")
    print("C21. Read current Dwarf camera data (live, tele+wide)")
    print("C22. Import saved config camera data into the Dwarf")
    print("0.   Return")


def get_user_choice_camera():
    try:
        return input("Enter your choice (C1 to C22) or 0 to return: ")
    except KeyboardInterrupt:
        print("Operation interrupted by the user (CTRL+C).")
        return '0'


def option_C1():
    print("=== Entering Simple Photo mode ===")
    perform_enter_photo_mode()


def option_C2():
    print("=== Entering astro mode (mode=8, Sun) ===")
    print("NOTE: this is hardcoded to mode=8 (confirmed = Sun, not generic")
    print("DSO). For DSO/Moon/Planet/etc., use the Astro submenu instead")
    print("(A13 for DSO, A14 for Sun/Moon/Planet).")
    perform_enter_astro_mode()


def option_C3():
    print("=== Reading current parameters (live HTTP API) ===")
    mode_id = input("modeId to query (1=Normal, 2=DSO, default 1): ").strip() or "1"
    result = perform_read_camera_params_http_v3(int(mode_id))
    if result is False:
        print("Read failed (see logs for HTTP details).")
    else:
        print(json.dumps(result, indent=2, default=str))


def option_C4():
    print("=== Setting exposure ===")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    dwarf_id = dwarf_python_api.get_config_data.get_config_data().get('dwarf_id')
    dwarf_id_str = dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id) or "2"
    name = input("Exposure name (e.g. 0.5, 1/1000, 1/30): ").strip()
    if name and validate_exposure_name(name, dwarf_id_str, camera_choice):
        perform_set_exposure_by_name_v3(name, dwarf_id=dwarf_id_str, camera=camera_choice)


def option_C5():
    print("=== Setting gain ===")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    dwarf_id = dwarf_python_api.get_config_data.get_config_data().get('dwarf_id')
    dwarf_id_str = dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id) or "2"
    value = input("Gain value (displayed number, e.g. 50): ").strip()
    if value and value.lstrip('-').isdigit() and validate_gain_value(int(value), mode=1, dwarf_id=dwarf_id_str, camera=camera_choice):
        perform_set_gain_by_camera_v3(int(value), dwarf_id=dwarf_id_str, camera=camera_choice)
    elif value:
        print(f"Invalid gain value '{value}': must be a whole number.")


def option_C6():
    print("=== White balance - Kelvin temperature ===")
    value = input("Temperature in Kelvin (2800-7500): ").strip()
    if value:
        perform_set_wb_v3(int(value), mode=0)


def option_C7():
    print("=== White balance - preset ===")
    print("Options: Incandescent, Warm Fluorescent, Fluorescent, Sunlight, Cloudy, Shadow, Twilight")
    name = input("Preset name: ").strip()
    if name:
        perform_set_wb_preset_by_name_v3(name)


def option_C8():
    print("=== Brightness/contrast/saturation/hue/sharpness ===")
    print("(leave blank to leave a field unchanged, range -100 to 100"
          " except hue -180/180 and sharpness 0/100)")
    b = input("Brightness: ").strip()
    c = input("Contrast: ").strip()
    s = input("Saturation: ").strip()
    h = input("Hue: ").strip()
    sh = input("Sharpness: ").strip()
    if b: perform_set_brightness_v3(int(b))
    if c: perform_set_contrast_v3(int(c))
    if s: perform_set_saturation_v3(int(s))
    if h: perform_set_hue_v3(int(h))
    if sh: perform_set_sharpness_v3(int(sh))


def option_C9():
    print("=== IR filter ===")
    print("Options: VIS Filter, Astro Filter, Duo-Band Filter")
    name = input("Filter name: ").strip()
    if name:
        perform_set_ir_filter_v3(name)


def option_C10():
    print("=== Burst settings ===")
    count = input("Number of photos (e.g. 5): ").strip()
    interval = input("Interval (name, e.g. 2 s, Off): ").strip()
    if count:
        perform_set_burst_count_v3(int(count))
    if interval:
        perform_set_burst_interval_by_name_v3(interval)
    print("Remember to switch to tech=3 (perform_enter_shooting_mode(1, 3))"
          " before triggering the burst (option C13).")


def option_C11():
    print("=== Timelapse settings ===")
    interval = input("Interval (name, e.g. 4 s): ").strip()
    duration = input("Total duration (name, e.g. 2 min, leave blank for unlimited): ").strip()
    if interval:
        perform_set_timelapse_interval_by_name_v3(interval)
    if duration:
        perform_set_timelapse_duration_by_name_v3(duration)
    print("Remember to switch to tech=5 (perform_enter_shooting_mode(1, 5))"
          " before triggering the timelapse (option C15).")


def option_C12():
    print("=== Simple photo ===")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    action = perform_takeWidePhoto if camera_choice == "wide" else perform_takePhoto
    if action():
        log.success("Photo taken successfully.")
    else:
        log.error("Failed to take the photo.")


def option_C13():
    print("=== Burst ===")
    choice = input("S(tart) / T(op, i.e. stop)? ").strip().upper()
    if choice == 'S':
        perform_start_burst_v3()
    elif choice == 'T':
        perform_stop_burst_v3()


def option_C14():
    print("=== Video recording ===")
    choice = input("S(tart) / T(op, i.e. stop)? ").strip().upper()
    if choice == 'S':
        perform_start_record_v3()
    elif choice == 'T':
        perform_stop_record_v3()


def option_C15():
    print("=== Timelapse ===")
    choice = input("S(tart) / T(op, i.e. stop)? ").strip().upper()
    if choice == 'S':
        perform_start_timelapse_v3()
    elif choice == 'T':
        perform_stop_timelapse_v3()


def option_C16():
    print("=== Autofocus (normal/photo mode) ===")
    perform_auto_focus_v3()


def option_C17():
    print("=== Astro: stackCount / mosaicCount ===")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    stack = input("Number of subframes to stack (1-999, blank = skip): ").strip()
    mosaic = input("Number of mosaic panels (1-249, blank = skip, tele only): ").strip()
    if stack:
        perform_set_astro_stack_count_v3(int(stack), camera=camera_choice)
    if mosaic:
        perform_set_astro_mosaic_count_v3(int(mosaic))


def option_C18():
    print("=== Astro: auto calibration ===")
    print("NOT CONFIRMED by direct network capture (see MIGRATION_V3.md)")
    choice = input("Enable (y) / Disable (n)? ").strip().lower()
    if choice == 'y':
        perform_set_astro_auto_calibration_v3(True)
    elif choice == 'n':
        perform_set_astro_auto_calibration_v3(False)


# ---------------------------------------------------------------------------
# Config file (config.ini) camera data - ported from the original V2 test
# app (dwarf_test_apiV2/main.py, options C1/C2/C3/C4). C1 and C2 are
# unchanged (pure config.ini read/write, no protocol dependency). C3/C4
# are adapted for V3: reading now uses the live HTTP API instead of the
# non-responsive V2 GET_ALL_PARAMS commands, and writing uses the
# confirmed V3 exposure/gain/IR functions where available.
# ---------------------------------------------------------------------------

def validate_input(input_str, min_val, max_val):
    """Accepts a plain number or a fraction like '1/10' and checks it
    falls within [min_val, max_val]."""
    try:
        if '/' in input_str:
            numerator, denominator = input_str.split("/")
            numerator = int(numerator)
            denominator = int(denominator)
            if denominator == 0:
                print("Invalid input. Denominator cannot be zero.")
                return False
            value = numerator / denominator
        else:
            value = float(input_str)
        return min_val <= value <= max_val
    except ValueError:
        print("Invalid input. Please provide a valid integer or fraction.")
        return False


def update_cameraconfig(camera_exposure, camera_gain, camera_IR, camera_binning,
                         camera_format, camera_count, camera_wide_exposure, camera_wide_gain):
    config = configparser.ConfigParser()
    config.read('config.ini')
    if camera_exposure:
        config['CONFIG']['EXPOSURE'] = camera_exposure
    if camera_gain:
        config['CONFIG']['GAIN'] = camera_gain
    if camera_IR:
        config['CONFIG']['IRCUT'] = camera_IR
    if camera_binning:
        config['CONFIG']['BINNING'] = camera_binning
    if camera_format:
        config['CONFIG']['FORMAT'] = camera_format
    if camera_count:
        config['CONFIG']['COUNT'] = camera_count
    if camera_wide_exposure:
        config['CONFIG']['WIDE_EXPOSURE'] = camera_wide_exposure
    if camera_wide_gain:
        config['CONFIG']['WIDE_GAIN'] = camera_wide_gain
    with open('config.ini', 'w') as config_file:
        config.write(config_file)


def option_C19():
    """Read Saved Config Camera Data (unchanged from V2) - displays the
    camera settings currently stored in config.ini, without touching the
    device."""
    print("=== Read saved config camera data ===")
    data_config = dwarf_python_api.get_config_data.get_config_data()
    dwarf_id = data_config['dwarf_id']
    print("The values in the Config File are : ")
    print("-----------------------------------")
    if (camera_exposure := read_camera_exposure()):
        print("the exposure is:", camera_exposure)
    if (camera_gain := read_camera_gain()):
        print("the gain is:", camera_gain)
    if (camera_IR := read_camera_IR()):
        if dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id) == "2":
            print("the IR value is:", "IRCut" if camera_IR == "0" else "IRPass")
        elif dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id) == "5":
            print("the IR value is:", "DARK" if camera_IR == "0" else "ASTRO" if camera_IR == "1" else "DUAL-BAND")
        else:
            print("the IR value is:", {"0": "VIS", "1": "ASTRO"}.get(camera_IR, "DUAL-BAND"))
    if (camera_count := read_camera_count()):
        print("the number of images for the session is:", camera_count)
    if (camera_wide_exposure := read_camera_wide_exposure()):
        print("the wide exposure is:", camera_wide_exposure)
    if (camera_wide_gain := read_camera_wide_gain()):
        print("the wide gain is:", camera_wide_gain)


def option_C20():
    """Input Camera Data to Config (unchanged from V2) - prompts for each
    value, validates it, and saves to config.ini. Does not touch the
    device - use C22 afterwards to push these values to the Dwarf."""
    print("=== Input camera data into config.ini ===")
    data_config = dwarf_python_api.get_config_data.get_config_data()
    dwarf_id = data_config['dwarf_id']
    dwarf_id_str = dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id)
    print(f"Connected to Dwarf {dwarf_python_api.get_config_data.config_to_dwarf_id_int(dwarf_id)}")

    max_exp = 15 if dwarf_id_str == "2" else 60
    camera_exposure_init = read_camera_exposure()
    prompt = f"Exposure in seconds (0 = auto - {max_exp}), fraction ok (e.g. 1/10)"
    camera_exposure = input(f"{prompt} [{camera_exposure_init or 1}]: ").strip()
    if not camera_exposure:
        camera_exposure = camera_exposure_init or "1"
    elif not validate_input(camera_exposure, 0, max_exp):
        print("Input Data Error:", camera_exposure, "- using default 1")
        camera_exposure = "1"

    camera_gain_init = read_camera_gain()
    camera_gain = input(f"Gain (0-240) [{camera_gain_init or 80}]: ").strip()
    if not camera_gain:
        camera_gain = camera_gain_init or "80"
    elif not (0 <= int(camera_gain) <= 240):
        print("Input Data Error:", camera_gain, "- using default 80")
        camera_gain = "80"

    camera_IR_init = read_camera_IR()
    if dwarf_id_str == "2":
        prompt = "IR value: 0=IRCut, 1=IRPass"
        valid_ir = ("0", "1")
    else:
        prompt = "IR value: 0=VIS, 1=Astro, 2=Duo-Band"
        valid_ir = ("0", "1", "2")
    camera_IR = input(f"{prompt} [{camera_IR_init or 0}]: ").strip()
    if not camera_IR:
        camera_IR = camera_IR_init or "0"
    elif camera_IR not in valid_ir:
        print("Input Data Error:", camera_IR, "- using default 0")
        camera_IR = "0"

    camera_binning = None
    camera_format = None

    camera_count_init = read_camera_count()
    camera_count = input(f"Number of images (1-999) [{camera_count_init or 999}]: ").strip()
    if not camera_count:
        camera_count = camera_count_init or "999"
    elif not (1 <= int(camera_count) <= 999):
        print("Input Data Error:", camera_count, "- using default 999")
        camera_count = "999"

    max_wide_exp = 60 if dwarf_id_str == "3" else 1
    camera_wide_exposure_init = read_camera_wide_exposure()
    camera_wide_exposure = input(f"Wide exposure in seconds (0 = auto - {max_wide_exp}), fraction ok [{camera_wide_exposure_init or 1}]: ").strip()
    if not camera_wide_exposure:
        camera_wide_exposure = camera_wide_exposure_init or "1"
    elif not validate_input(camera_wide_exposure, 0, max_wide_exp):
        print("Input Data Error:", camera_wide_exposure, "- using default 1")
        camera_wide_exposure = "1"

    if dwarf_id_str == "3":
        wg_min, wg_max, wg_default = 0, 240, "0"
    else:
        wg_min, wg_max, wg_default = 60, 160, "60"
    camera_wide_gain_init = read_camera_wide_gain()
    camera_wide_gain = input(f"Wide gain ({wg_min}-{wg_max}) [{camera_wide_gain_init or wg_default}]: ").strip()
    if not camera_wide_gain:
        camera_wide_gain = camera_wide_gain_init or wg_default
    elif not (wg_min <= int(camera_wide_gain) <= wg_max):
        print("Input Data Error:", camera_wide_gain, "- using default", wg_default)
        camera_wide_gain = wg_default

    update_cameraconfig(camera_exposure, camera_gain, camera_IR, camera_binning,
                         camera_format, camera_count, camera_wide_exposure, camera_wide_gain)
    print("Saved to config.ini.")


def option_C21():
    """Read Current Dwarf Camera Data (live) - V3: uses the live HTTP API
    (confirmed reliable for exposure/gain/IR filter) instead of the V2
    GET_ALL_PARAMS commands, which don't respond on V3 hardware."""
    mode_id = input("modeId to query (1=Normal, 2=DSO, default 1): ").strip() or "1"
    print("=== Read current Dwarf camera data (live) ===")
    data_config = dwarf_python_api.get_config_data.get_config_data()
    dwarf_id = data_config['dwarf_id']
    dwarf_id_str = dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id)
    print(f"Connected to Dwarf {dwarf_python_api.get_config_data.config_to_dwarf_id_int(dwarf_id)}")
    print("------------------")

    http_result = perform_read_camera_params_http_v3(int(mode_id))
    if isinstance(http_result, dict) and http_result.get("cameras", {}).get(0):
        tele_cam = http_result["cameras"][0]
        exposure_info = tele_cam.get("exposure")
        if exposure_info:
            auto_mode = exposure_info.get("mode")
            print(f"The exposure mode is: {'Manual' if auto_mode else 'Auto'}")
            print("the exposure is:", exposure_info.get("name") or exposure_info.get("value"))
        else:
            print("the exposure has not been found")

        gain_info = tele_cam.get("gain")
        if gain_info:
            print("the gain is:", gain_info.get("value"))
        else:
            print("the gain has not been found")

        if "filterType" in tele_cam:
            camera_IR = str(tele_cam["filterType"])
            if dwarf_id_str == "2":
                print("the IR value is:", "IRCut" if camera_IR == "0" else "IRPass")
            elif dwarf_id_str == "5":
                print("the IR value is:", "DARK" if camera_IR == "0" else "ASTRO" if camera_IR == "1" else "DUAL-BAND")
            else:
                print("the IR value is:", {"0": "VIS", "1": "ASTRO"}.get(camera_IR, "DUAL-BAND"))
        else:
            print("the IRfilter has not been found")
    else:
        print("the exposure has not been found")
        print("the gain has not been found")
        print("the IRfilter has not been found")

    # stackFormat/displaySource/stackBinning live under the virtual "15"
    # tech_settings entry - astro-mode specific, so this will typically
    # print nothing here (mode_id=1, Normal/Photo). Field-confirmed
    # mapping (Aug 2026): stackFormat 2=FITS/3=TIFF, displaySource
    # 0=Single (1 not yet observed). stackBinning mapping (0=4k/1=2k) is
    # an assumption by analogy with the old tele/wide binning values -
    # not yet confirmed.
    if isinstance(http_result, dict):
        stack_settings = http_result.get("tech_settings", {}).get(15)
        if stack_settings:
            if "stackFormat" in stack_settings:
                format_map = {2: "FITS", 3: "TIFF"}
                value = stack_settings["stackFormat"]
                print("the image format value is:", format_map.get(value, value))
            if "displaySource" in stack_settings:
                display_map = {0: "Single"}  # 1 not yet observed
                value = stack_settings["displaySource"]
                print("the display source value is:", display_map.get(value, value))
            if "stackBinning" in stack_settings:
                binning_map = {0: "4k"}  # 1=2k assumed, not yet confirmed
                value = stack_settings["stackBinning"]
                print("the Binning value is:", binning_map.get(value, value))
        count_tele_settings = http_result.get("tech_settings", {}).get(0)
        if count_tele_settings:
            if "stackCount" in count_tele_settings:
                value = count_tele_settings["stackCount"]
                print("the tele stack count value is:", value)
            if "mosaicCount" in count_tele_settings:
                value = count_tele_settings["mosaicCount"]
                print("the mosaic stack count value is:", value)
    # Wide
    if isinstance(http_result, dict) and http_result.get("cameras", {}).get(1):
        wide_cam = http_result["cameras"][1]
        exposure_info = wide_cam.get("exposure")
        if exposure_info:
            print("the wide exposure is:", exposure_info.get("name") or exposure_info.get("value"))
        else:
            print("the wide exposure has not been found")

        gain_info = wide_cam.get("gain")
        if gain_info:
            print("the wide gain is:", gain_info.get("value"))
        else:
            print("the wide gain has not been found")
    else:
        print("the wide exposure has not been found")
        print("the wide gain has not been found")

    if isinstance(http_result, dict):
        count_wide_settings = http_result.get("tech_settings", {}).get(1)
        if count_wide_settings:
            if "stackCount" in count_wide_settings:
                value = count_wide_settings["stackCount"]
                print("the wide stack count value is:", value)

def option_C22():
    """Import Saved Config Camera Data into Dwarf - V3: exposure/gain/IR
    (tele and wide) go through the confirmed V3 CAMERA_PARAMS functions.
    Binning and image format are omitted - binning is no longer
    accessible in V3 and image format isn't a useful setting here.
    Count still goes through the old perform_update_camera_setting()
    path (CAMERA_TELE module) - NOT confirmed to still be accepted on V3
    hardware, no V3-native replacement identified yet."""
    print("=== Import saved config camera data into the Dwarf ===")
    data_config = dwarf_python_api.get_config_data.get_config_data()
    dwarf_id = data_config['dwarf_id']
    dwarf_id_str = dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id)
    print(f"Connected to Dwarf {dwarf_python_api.get_config_data.config_to_dwarf_id_int(dwarf_id)}")

    if (camera_exposure := read_camera_exposure()):
        print("the exposure is:", camera_exposure)
        perform_set_exposure_by_name_v3(camera_exposure, dwarf_id=dwarf_id_str, camera="tele")

    if (camera_gain := read_camera_gain()):
        print("the gain is:", camera_gain)
        perform_set_gain_by_camera_v3(int(camera_gain), dwarf_id=dwarf_id_str, camera="tele")

    if (camera_IR := read_camera_IR()):
        print("the IR value is:", camera_IR)
        perform_set_ir_filter_v3(int(camera_IR))

    if (camera_count := read_camera_count()):
        print("the number of images for the session is:", camera_count)
        perform_update_camera_setting("count", camera_count)

    if (camera_wide_exposure := read_camera_wide_exposure()):
        print("the wide exposure is:", camera_wide_exposure)
        perform_set_exposure_by_name_v3(camera_wide_exposure, dwarf_id=dwarf_id_str, camera="wide")

    if (camera_wide_gain := read_camera_wide_gain()):
        print("the wide gain is:", camera_wide_gain)
        perform_set_gain_by_camera_v3(int(camera_wide_gain), dwarf_id=dwarf_id_str, camera="wide")


def choice_camera():
    while True:
        display_menu_camera()
        choice = get_user_choice_camera().upper()
        actions = {
            'C1': option_C1, 'C2': option_C2, 'C3': option_C3, 'C4': option_C4,
            'C5': option_C5, 'C6': option_C6, 'C7': option_C7, 'C8': option_C8,
            'C9': option_C9, 'C10': option_C10, 'C11': option_C11, 'C12': option_C12,
            'C13': option_C13, 'C14': option_C14, 'C15': option_C15, 'C16': option_C16,
            'C17': option_C17, 'C18': option_C18,
            'C19': option_C19, 'C20': option_C20, 'C21': option_C21, 'C22': option_C22,
        }
        if choice == '0':
            print("Return to the main menu")
            break
        elif choice in actions:
            actions[choice]()
        else:
            print("Invalid choice. Please enter a correct value.")


# ---------------------------------------------------------------------------
# Astro sub-menu
# ---------------------------------------------------------------------------

def display_menu_astro():
    print("")
    print("------------------ ASTRO ------------------")
    print("A0.  Set observer location (longitude/latitude/timezone)")
    print("A1.  Set astro exposure (by name, e.g. 0.5, 180)")
    print("A2.  Set astro gain (raw displayed value, 40-240 for tele)")
    print("A3.  Set stackCount/mosaicCount (subframes to stack)")
    print("A4.  Start/Stop platform calibration")
    print("A5.  Start/Stop autofocus (normal or infinite)")
    print("A6.  Start/Stop EQ solving (polar alignment)")
    print("A7.  GOTO a target (RA/Dec or solar system object)")
    print("A8.  Stop GOTO")
    print("A9.  Start/Stop astro stacking session")
    print("A10. Read stacking status (progress)")
    print("A11. Wait until End of Imaging Session")
    print("A12. Finish/Finalize session (Go Live) - do this before starting a new one")
    print("A13. Enter astro shooting mode (DSO=2, Sun=8, Moon=9, Planet=10...)")
    print("A14. Enter Solar mode (Sun/Moon/Planet shortcut, default Sun)")
    print("0.   Return")


def get_user_choice_astro():
    try:
        return input("Enter your choice (A0 to A14) or 0 to return: ")
    except KeyboardInterrupt:
        print("Operation interrupted by the user (CTRL+C).")
        return '0'


def option_A0():
    print("=== Set observer location ===")
    input_test()


def option_A1():
    print("=== Set astro exposure ===")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    dwarf_id = dwarf_python_api.get_config_data.get_config_data().get('dwarf_id')
    dwarf_id_str = dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id) or "2"
    name = input("Exposure name (e.g. 0.5, 180, 1/1000): ").strip()
    if name and validate_exposure_name(name, dwarf_id_str, camera_choice):
        perform_set_astro_exposure_by_name_v3(name, dwarf_id=dwarf_id_str, camera=camera_choice)


def option_A2():
    print("=== Set astro gain ===")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    dwarf_id = dwarf_python_api.get_config_data.get_config_data().get('dwarf_id')
    dwarf_id_str = dwarf_python_api.get_config_data.config_to_dwarf_id_str(dwarf_id) or "2"
    value = input("Gain value (displayed number, 40-240 for tele): ").strip()
    if value and value.lstrip('-').isdigit() and validate_gain_value(int(value), mode=2, dwarf_id=dwarf_id_str, camera=camera_choice):
        perform_set_astro_gain_v3(int(value), camera=camera_choice)
    elif value:
        print(f"Invalid gain value '{value}': must be a whole number.")


def option_A3():
    print("=== stackCount / mosaicCount ===")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    stack = input("Number of subframes to stack (1-999, blank = skip): ").strip()
    mosaic = input("Number of mosaic panels (1-249, blank = skip, tele only): ").strip()
    if stack:
        perform_set_astro_stack_count_v3(int(stack), camera=camera_choice)
    if mosaic:
        perform_set_astro_mosaic_count_v3(int(mosaic))


def option_A4():
    print("=== Platform calibration ===")
    choice = input("S(tart) / T(op, i.e. stop)? ").strip().upper()
    if choice == 'S':
        perform_calibration()
    elif choice == 'T':
        perform_stop_calibration()


def option_A5():
    print("=== Autofocus ===")
    choice = input("S(tart) / T(op, i.e. stop)? ").strip().upper()
    if choice == 'S':
        infinite = input("Infinite focus? (y/N): ").strip().lower() == 'y'
        perform_start_autofocus(infinite=infinite)
    elif choice == 'T':
        perform_stop_autofocus()


def option_A6():
    print("=== EQ solving (polar alignment) ===")
    choice = input("S(tart) / T(op, i.e. stop)? ").strip().upper()
    if choice == 'S':
        result = start_polar_align()
        print(f"Result: {result}")
    elif choice == 'T':
        stop_polar_align()


def option_A7():
    print("=== GOTO ===")
    print("1) RA/Dec target   2) Solar system object   3) Quick target (Polaris/Vega/M42/M31/Jupiter)")
    choice = input("Choice: ").strip()
    if choice == '1':
        ra = input("RA (decimal hours): ").strip()
        dec = input("Dec (decimal degrees): ").strip()
        target = input("Target name: ").strip()
        if ra and dec:
            perform_goto(float(ra), float(dec), target)
    elif choice == '2':
        target_name = input("Target (Sun/Moon/planet): ").strip()
        select_solar_target(target_name)
    elif choice == '3':
        perform_goto_quick_target()


# Fixed RA (decimal hours)/Dec (decimal degrees) for quick manual testing -
# ported from the original V2 test app (dwarf_test_apiV2/main.py).
QUICK_TARGETS = {
    "polaris": (2.5390302777777776, 89.26980527777778),
    "vega": (18.61522686111111, 38.784415833333334),
    "m42": (5.588475138888889, -5.3923),
    "m31": (0.7122101388888887, 41.271721388888885),
}


def perform_goto_quick_target():
    print("Quick targets: Polaris, Vega, M42, M31, Jupiter")
    name = input("Target: ").strip()
    key = name.lower()
    if key == "jupiter":
        select_solar_target("Jupiter")
        return
    if key in QUICK_TARGETS:
        ra, dec = QUICK_TARGETS[key]
        perform_goto(ra, dec, name)
        return
    print(f"Unknown quick target '{name}' - use option 1 (RA/Dec) or 2 (solar system) instead.")


def select_solar_target (target):
   
    target_name = target
    target_id = None
   
    if (target.lower() == "mercury"):
        target_id = 1

    if (target.lower() == "venus"):
        target_id = 2

    if (target.lower() == "mars"):
        target_id = 3

    if (target.lower() == "jupiter"):
        target_id = 4

    if (target.lower() == "saturn"):
        target_id = 5

    if (target.lower() == "uranus"):
        target_id = 6

    if (target.lower() == "neptune"):
        target_id = 7

    if (target.lower() == "moon"):
        target_id = 8

    if (target.lower() == "sun"):
        target_id = 9

    if target_id in (8, 9):
        # Confirmed on real hardware: for the Sun and Moon specifically,
        # CMD_ASTRO_START_GOTO_SOLAR_SYSTEM (11003) itself performs a
        # visual check against the camera feed - not just a mathematical
        # (ephemeris-based) pointing like the other solar system targets.
        # It fails with CODE_ASTRO_SUN_MOON_NOT_FOUND (-11531) if the lens
        # cap is on or the target isn't actually visible near the computed
        # position. See MIGRATION_V3.md.
        print("REMINDER: for Sun/Moon, remove the lens cap and make sure")
        print("the target is roughly visible/unobstructed - the GOTO itself")
        print("performs a visual check and will fail with")
        print("CODE_ASTRO_SUN_MOON_NOT_FOUND otherwise.")

    if target_id:
        perform_goto_stellar(target_id, target_name)
    else:
        print("Warning: Target not found!")

def option_A8():
    print("=== Stop GOTO ===")
    perform_stop_goto()


def option_A9():
    print("=== Astro stacking session ===")
    print("REMINDER: the firmware rejects this with CODE_ASTRO_NEED_GOTO")
    print("(-11513) unless a GOTO (A7) has actually been performed first -")
    print("confirmed on real hardware. Entering astro mode (A1-A3 settings)")
    print("alone is NOT enough, you need a real target set via GOTO.")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    choice = input("S(tart) / T(op, i.e. stop)? ").strip().upper()
    if choice == 'S':
        if camera_choice == "wide":
            perform_takeAstroWidePhoto()
        else:
            perform_takeAstroPhoto()
    elif choice == 'T':
        if camera_choice == "wide":
            perform_stopAstroWidePhoto()
        else:
            perform_stopAstroPhoto()
        print("")
        print("REMINDER: once a session is done/stopped, the official app")
        print("shows a 'Finish/Edit' screen - A12 (Go Live) is the API")
        print("equivalent of pressing 'Finish'. Skipping it and starting a")
        print("new session directly gets rejected with")
        print("CODE_ASTRO_FUNCTION_BUSY. Run A12 before starting a new one.")


def option_A10():
    print("=== Stacking status ===")
    status = perform_read_astro_stacking_status_v3()
    if status is None:
        print("Not connected.")
    else:
        print(json.dumps(status, indent=2, default=str))


def option_A11():
    print("=== Wait until End of Imaging Session ===")
    camera_choice = input("Camera: tele/wide (default tele): ").strip() or "tele"
    if camera_choice == "wide":
        perform_waitEndAstroWidePhoto()
    else:
        perform_waitEndAstroPhoto()

def option_A12():
    print("=== Finish/Finalize session (Go Live) ===")
    print("This is the API equivalent of pressing 'Finish' on the official")
    print("app's end-of-session screen (Finish/Edit). Confirmed necessary:")
    print("skipping this and starting a new stacking session directly")
    print("gets rejected with CODE_ASTRO_FUNCTION_BUSY.")
    perform_GoLive()


def option_A13():
    print("=== Enter astro shooting mode ===")
    print("Modes (from the firmware's shooting_mode_and_techs table):")
    print("  2  = DSO (Deep Sky Object) - galaxies, nebulae, clusters")
    print("  3  = Sun/Moon (parent mode)")
    print("  4  = Milky Way")
    print("  5  = Star Trail")
    print("  8  = Sun")
    print("  9  = Moon")
    print("  10 = Planet")
    print("NOTE: perform_enter_astro_mode() (used elsewhere, e.g. option C2)")
    print("is hardcoded to mode=8 (Sun) - use THIS option for DSO (mode=2)")
    print("or any other astro mode.")
    mode = input("Mode (default 2 for DSO): ").strip() or "2"
    tech = input("Tech (default 2, present in all astro modes): ").strip() or "2"
    perform_enter_shooting_mode(int(mode), int(tech))


def option_A14():
    print("=== Enter Solar mode (Sun/Moon/Planet) ===")
    print("Modes (from the firmware's shooting_mode_and_techs table):")
    print("  8  = Sun (confirmed working on real hardware)")
    print("  9  = Moon")
    print("  10 = Planet")
    print("  3  = Sun/Moon (parent mode)")
    mode = input("Mode (default 8 for Sun): ").strip() or "8"
    tech = input("Tech (default 2, present in all astro modes): ").strip() or "2"
    perform_enter_shooting_mode(int(mode), int(tech))


def choice_astro():
    while True:
        display_menu_astro()
        choice = get_user_choice_astro().upper()
        actions = {
            'A0': option_A0,
            'A1': option_A1, 'A2': option_A2, 'A3': option_A3, 'A4': option_A4,
            'A5': option_A5, 'A6': option_A6, 'A7': option_A7, 'A8': option_A8,
            'A9': option_A9, 'A10': option_A10, 'A11': option_A11, 'A12': option_A12,
            'A13': option_A13, 'A14': option_A14,
        }
        if choice == '0':
            print("Return to the main menu")
            break
        elif choice in actions:
            actions[choice]()
        else:
            print("Invalid choice. Please enter a correct value.")


# ---------------------------------------------------------------------------
# Motor (joystick) sub-menu
# ---------------------------------------------------------------------------

def display_menu_motor():
    print("")
    print("------------------ MOTOR ------------------")
    print("M1. One-off movement (angle + amplitude)")
    print("M2. Stop the movement")
    print("C. Closed Barrel Position")
    print("I. Init Horizontal Position")
    print("I3. Init Horizontal Position for D3")
    print("P. Polar Align Position")
    print("P3. Polar Align Position For D3")
    print("S. Turn 90° for Second Polar Align Position")
    print("S3. Turn 90° for Second Polar Align Position for D3")
    print("RR. Option RR. Reset Rotation Axis")
    print("RS. Option RS. Reset Pitch Axis")
    print("GP. Option GP. Read Position (D3 only)")
    print("PA. Option PA. Auto Polar align")
    print("PS. Option PS. Stop Polar align")
    print("0.  Return")


def get_user_choice_motor():
    try:
        return input("Enter your choice (M1,M2,C,I,P,P3,S or 0 to return to main menu: ")
        return input("Enter your choice (M1, M2) or 0 to return: ")
    except KeyboardInterrupt:
        print("Operation interrupted by the user (CTRL+C).")
        return '0'


def option_M1():
    print("=== One-off movement ===")
    print("(synchronous control - fine for a small adjustment, not for a")
    print(" continuous drag like in the app - see MIGRATION_V3.md)")
    angle = input("Angle in degrees (0-360): ").strip()
    length = input("Amplitude (roughly 0.01 to 1): ").strip()
    if angle and length:
        perform_motor_joystick_v3(float(angle), float(length))


def option_M2():
    print("=== Stop movement ===")
    perform_motor_joystick_stop_v3()

def option_MC():
    print("You selected Option C. Closed Barrel Position")
    print("")
    # Add your Option MC functionality here
    motor_action(1)

def option_MI():
    print("You selected Option I. Init Horizontal Position")
    print("")
    # Add your Option MI functionality here
    motor_action(2)

def option_MI3():
    print("You selected Option I. Init Horizontal Position for D3")
    print("")
    # Add your Option MI functionality here
    motor_action(9)

def option_MP():
    print("You selected Option P. Polar Align Position")
    print("")
    # Add your Option MP functionality here
    motor_action(3)

def option_MP3():
    print("You selected Option P. Polar Align Position for D3")
    print("")
    # Add your Option MP functionality here
    motor_action(7)

def option_MS():
    print("You selected Option S. Turn 90° for Second Polar Align Position")
    print("")
    # Add your Option MS functionality here
    motor_action(4)

def option_MS3():
    print("You selected Option S. Turn 90° for Second Polar Align Position for D3")
    print("")
    # Add your Option MS functionality here
    motor_action(4,0.5)

def option_RR():
    print("You selected Option RR. Reset Rotation Axis")
    print("")
    # Add your Option RR functionality here
    motor_action(5)

def option_RS():
    print("You selected Option RS.  Reset Pitch Axis")
    print("")
    # Add your Option RS functionality here
    motor_action(6)

def option_GP():
    print("You selected Option GP.  Read Position")
    print("")
    # Add your Option GP functionality here
    motor_action(8)

def option_PA():
    print("You selected Option PA.  Auto Polar align")
    print("")
    # Add your Option GP functionality here
    start_polar_align()

def option_PS():
    print("You selected Option PS.  Stop Polar align")
    print("")
    # Add your Option GP functionality here
    stop_polar_align()

def choice_test():
    while True:
        display_menu_test()
        user_choice = get_user_choice_test().upper()

        if user_choice == 'T1':
            option_20()

        elif user_choice == 'T2':
            option_21()

        elif user_choice == 'T3':
            option_22()

        elif user_choice == 'T4':
            option_23()

        elif user_choice == 'D':
            if (option_24() == '0'):
              break

        elif user_choice == '0':
            print("Return to the main menu")
            break

        else:
            print("Invalid choice. Please enter a correct value.")


# ---------------------------------------------------------------------------
# LED/RGB light sub-menu (MODULE_RGB_POWER, module 5)
# ---------------------------------------------------------------------------

def display_menu_lights():
    print("")
    print("------------------ LIGHTS ------------------")
    print("L1. Turn RGB lights ON")
    print("L2. Turn RGB lights OFF")
    print("L3. Turn power indicator light ON")
    print("L4. Turn power indicator light OFF")
    print("0.  Return")


def get_user_choice_lights():
    try:
        return input("Enter your choice (L1 to L4) or 0 to return: ")
    except KeyboardInterrupt:
        print("Operation interrupted by the user (CTRL+C).")
        return '0'


def option_L1():
    print("=== RGB lights ON ===")
    perform_powerOpenRGB()


def option_L2():
    print("=== RGB lights OFF ===")
    perform_powerCloseRGB()


def option_L3():
    print("=== Power indicator light ON ===")
    perform_powerIndOn()


def option_L4():
    print("=== Power indicator light OFF ===")
    perform_powerIndOff()


def choice_lights():
    while True:
        display_menu_lights()
        choice = get_user_choice_lights().upper()
        actions = {'L1': option_L1, 'L2': option_L2, 'L3': option_L3, 'L4': option_L4}
        if choice == '0':
            print("Return to the main menu")
            break
        elif choice in actions:
            actions[choice]()
        else:
            print("Invalid choice. Please enter a correct value.")


def choice_motor():
    while True:
        display_menu_motor()
        user_choice = get_user_choice_motor().upper()
        if user_choice == 'M1':
            option_M1()
        elif user_choice == 'M2':
            option_M2()

        elif user_choice == 'C':
            option_MC()

        elif user_choice == 'I':
            option_MI()

        elif user_choice == 'I3':
            option_MI3()

        elif user_choice == 'P':
            option_MP()

        elif user_choice == 'P3':
            option_MP3()

        elif user_choice == 'S':
            option_MS()

        elif user_choice == 'S3':
            option_MS3()

        elif user_choice == 'RR':
            option_RR()

        elif user_choice == 'RS':
            option_RS()

        elif user_choice == 'GP':
            option_GP()

        elif user_choice == 'PA':
            option_PA()

        elif user_choice == 'PS':
            option_PS()

        elif user_choice == '0':
            print("Return to the main menu")
            break

        else:
            print("Invalid choice. Please enter a correct value.")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    while True:
        display_menu()
        choice = get_user_choice().upper()

        if choice == '1':
            option_1()
        elif choice == '2':
            option_2()
        elif choice == 'B':
            choice_bluetooth()
        elif choice == 'C':
            choice_camera()
        elif choice == 'A':
            choice_astro()
        elif choice == 'M':
            choice_motor()
        elif choice == 'L':
            choice_lights()
        elif choice == 'I':
            perform_enter_photo_mode()
            get_live_data()
        elif choice == 'S':
            option_S()
        elif choice == 'D':
            option_D()
        elif choice == 'P':
            option_P()
        elif choice == 'R':
            option_R()
        elif choice == 'T':
            option_T()
        elif choice == '0':
            print("Goodbye.")
            # IMPORTANT: perform_disconnect() must be called before exiting,
            # otherwise the background event_loop_thread (non-daemon, see
            # websockets_utils.py) keeps running forever and the Python
            # process never actually terminates, even after this loop
            # returns - confirmed on real hardware (the process kept
            # running silently after a full GOTO+stacking session, with
            # nothing left to do and no further command sent). See
            # MIGRATION_V3.md.
            perform_disconnect()
            break
        else:
            print("Invalid choice. Please enter a correct value.")


if __name__ == "__main__":
    main()
