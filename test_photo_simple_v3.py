"""
test_photo_simple_v3.py
------------------------
Manual test for "simple photo on the table" mode (no mount alignment, no
GOTO, no stacking) on V3.

Built from a real network capture of the official app (Dwarf Mini, "normal
photo" session: connection, photo mode, exposure/gain settings, taking a
photo). That capture confirmed/revealed:

    - mode=1, tech=1 = simple photo (already tested and confirmed OK)
    - The official app does NOT call CMD_CAMERA_TELE_OPEN_CAMERA (10000,
      the old V2 "open camera"): ENTER_CAMERA (16404) is enough.
      This script therefore no longer calls it.
    - Exposure/gain go through the NEW CAMERA_PARAMS module (15):
      CMD_PARAM_SET_EXPOSURE (16700) / CMD_PARAM_SET_GAIN (16701), not the
      old V2 commands of the CAMERA_TELE module. See
      perform_set_exposure_v3() / perform_set_gain_v3() in dwarf_utils.py
      and MIGRATION_V3.md for details on the observed param_id encoding.
    - Taking the photo itself (CMD_CAMERA_TELE_PHOTOGRAPH, 10002) is
      unchanged from V2 (perform_takePhoto()).

This script therefore faithfully follows the sequence observed in the
capture rather than retrying the old V2 path (perform_open_camera /
perform_update_camera_setting), which we no longer have evidence is still
used by the official app in V3.

Usage:
    python test_photo_simple_v3.py
"""

import time

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_utils import (
    set_HostMaster,
    perform_time,
    perform_timezone,
    perform_get_device_state_info,
    perform_enter_photo_mode,
    perform_set_exposure_by_name_v3,
    perform_set_gain_v3,
    perform_read_exposure_v3,
    perform_read_gain_v3,
    perform_read_all_camera_params_v3,
    perform_takePhoto,
    perform_disconnect,
)


def main():
    log.info("=== Step 0: MASTER LOCK + diagnostic ===")
    # V3: see test_connect_v3.py - MASTER LOCK seems vestigial on V3
    # devices, we continue even if it times out.
    if not set_HostMaster():
        log.warning(
            "MASTER LOCK: no response (timeout or failure). Continuing"
            " anyway (probably vestigial on V3)."
        )

    # V3: confirmed by network capture of the official app - without this,
    # the Dwarf's internal clock can stay on an incorrect value (observed:
    # photo date in 2038). perform_timezone() doesn't crash if TIMEZONE is
    # missing from config.ini, it just logs a warning.
    log.info("Synchronizing time/timezone")
    perform_time()
    perform_timezone()

    # shooting_mode_and_techs details are printed directly in the logs
    # (NOTICE level) by the dispatcher.
    perform_get_device_state_info()
    time.sleep(1)

    log.info("=== Step A: entering simple photo mode (mode=1, tech=1) ===")
    if not perform_enter_photo_mode():
        log.error("perform_enter_photo_mode() failed. Continuing anyway"
                   " (see MIGRATION_V3.md).")

    time.sleep(1)
    log.info("Reading current parameters (pushed by the firmware on mode entry)")
    log.info(f"Current exposure: {perform_read_exposure_v3()}")
    log.info(f"Current gain: {perform_read_gain_v3()}")

    log.info("=== Step B: exposure/gain settings (V3 CAMERA_PARAMS module) ===")
    # Exposure by name (reuses the existing AllowedExposures table,
    # confirmed still valid in V3); gain by direct displayed value.
    perform_set_exposure_by_name_v3("0.5")
    time.sleep(0.5)
    perform_set_gain_v3(50)
    time.sleep(0.5)

    log.info("Checking parameters after the settings")
    log.info(f"Exposure re-read: {perform_read_exposure_v3()}")
    log.info(f"Gain re-read: {perform_read_gain_v3()}")
    log.info(f"All known parameters: {perform_read_all_camera_params_v3()}")

    log.info("=== Step C: taking the photo (CMD_CAMERA_TELE_PHOTOGRAPH, unchanged) ===")
    if perform_takePhoto():
        log.success("Simple photo V3: full sequence succeeded.")
    else:
        log.error("perform_takePhoto() failed.")

    perform_disconnect()


if __name__ == "__main__":
    main()
