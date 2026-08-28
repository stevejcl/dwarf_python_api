"""
test_connect_v3.py
-------------------
Manual script to validate the V3 connection sequence on a real Dwarf.
Run from the repo root (where the dwarf_python_api/ folder lives), on the
same network as the Dwarf (AP or STA depending on your usual setup).

Usage:
    python test_connect_v3.py

This script ONLY does the connection sequence (MASTER LOCK + entering
astro mode). It does not take a photo, does not GOTO: the goal is to
validate this specific point before going further.
"""

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_utils import (
    set_HostMaster,
    perform_time,
    perform_timezone,
    perform_get_device_state_info,
    perform_enter_astro_mode,
    perform_disconnect,
)


def main():
    log.info("=== Step 1/3: MASTER LOCK ===")
    # V3: this mechanism seems vestigial on V3 devices (Dwarf 3 / Mini).
    # dwarfAlp itself catches failure at this step without ever blocking the
    # rest of the connection (just logs a warning) - only an optional
    # informational call depends on it on their side. We do the same here:
    # we try, but a timeout/failure doesn't prevent continuing with the
    # rest of the sequence.
    if not set_HostMaster():
        log.warning(
            "MASTER LOCK: no response (timeout or failure). This mechanism"
            " seems vestigial on V3 devices - continuing anyway."
        )

    # V3: confirmed by network capture of the official app - it sends
    # SET_TIME + SET_TIME_ZONE right at the start of the session, before
    # GET_DEVICE_STATE_INFO. Without this, the Dwarf's internal clock can
    # stay on an incorrect default value (observed: photo date in 2038,
    # a classic sign of an unsynchronized clock / sentinel value close to
    # the Y2038 overflow). CMD_SYSTEM_SET_TIME (13000) and
    # CMD_SYSTEM_SET_TIME_ZONE (13001) are unchanged since V2.
    log.info("Synchronizing time/timezone")
    perform_time()
    perform_timezone()  # logs a warning and doesn't crash if TIMEZONE is
                         # missing from config.ini (see perform_timezone())

    # Diagnostic detail (shooting_mode_and_techs) is printed directly in
    # the logs (NOTICE level) by the dispatcher.
    log.info("=== Step 2/3: GET DEVICE STATE INFO (informational) ===")
    perform_get_device_state_info()

    log.info("=== Step 3/3: ENTER ASTRO MODE (mode + camera + tech) ===")
    if perform_enter_astro_mode():
        log.success("V3 connection sequence completed successfully.")
    else:
        log.error("The V3 connection sequence failed. See logs above to"
                   " find out at which step exactly (mode / camera / tech).")

    perform_disconnect()


if __name__ == "__main__":
    main()
