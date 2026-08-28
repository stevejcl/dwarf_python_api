"""
test_get_all_params_v2.py
---------------------------
Dedicated test: does the V2 command CMD_CAMERA_TELE_GET_ALL_PARAMS (10036,
perform_get_all_camera_setting()) still get a response from the V3
firmware?

Context: we confirmed (by network capture) that the official app NEVER
sends this command in V3 - but we had never actually tried sending it
ourselves to see if the firmware would respond if we did. The protobuf
message is unchanged between V2 and V3 (ReqGetAllParams/ResGetAllParams),
and the dispatcher already knows how to decode the response (V2 legacy,
never removed) - so if it doesn't work, it will be firmware silence, not
a client-side decoding problem.

WARNING: if the firmware genuinely doesn't respond, this script will sit
at the usual timeout (up to ~30s depending on configuration) before
concluding failure - that's expected, not a bug.

The test is run in both possible scenarios, one after the other:
1) Right after MASTER LOCK, without entering any particular mode
   (the "as-is V2" hypothesis).
2) After perform_enter_photo_mode() (in case the firmware only accepts
   this command once a shooting mode is active).

Usage:
    python test_get_all_params_v2.py
"""

import time

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_utils import (
    set_HostMaster,
    perform_enter_photo_mode,
    perform_get_all_camera_setting,
    perform_disconnect,
)


def try_get_all_params(label):
    log.info(f"=== Sending CMD_CAMERA_TELE_GET_ALL_PARAMS ({label}) ===")
    log.info("If the firmware doesn't respond, this will wait for the"
              " usual timeout (~30s) before concluding failure.")
    result = perform_get_all_camera_setting()
    if result is False:
        log.error(f"[{label}] No response (timeout) or error.")
    else:
        log.success(f"[{label}] Response received: {result}")
    return result


def main():
    log.info("=== MASTER LOCK ===")
    if not set_HostMaster():
        log.warning("MASTER LOCK: no response, continuing anyway.")

    result1 = try_get_all_params("without active mode")

    log.info("=== Entering simple photo mode ===")
    perform_enter_photo_mode()
    time.sleep(1)

    result2 = try_get_all_params("after perform_enter_photo_mode()")

    log.info("=== Conclusion ===")
    if result1 is False and result2 is False:
        log.notice("CMD_CAMERA_TELE_GET_ALL_PARAMS gets no response from"
                    " the V3 firmware, in either scenario tested - confirmed"
                    " obsolete/not implemented on the firmware side.")
    elif result1 is not False or result2 is not False:
        log.notice("Response received in at least one scenario: the V2"
                    " command still works (at least partially) on this V3"
                    " firmware!")

    perform_disconnect()


if __name__ == "__main__":
    main()
