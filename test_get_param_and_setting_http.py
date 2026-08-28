"""
test_get_param_and_setting_http.py
------------------------------------
Test of the HTTP API (port 8082, independent of the WebSocket protocol on
port 9900) identified from dwarfAlp's documentation:

    GET  http://<ip>:8082/getDefaultParamsConfig
    POST http://<ip>:8082/shootingMode/getParamAndSetting  {"modeId": N}

Per the workflow documented by dwarfAlp, the official app calls these
endpoints AFTER already establishing a WebSocket session (MASTER LOCK,
ENTER_CAMERA...) - this script therefore first does a minimal WS
connection before trying the HTTP calls, in case the firmware doesn't
respond "cold".

Tests both modeId=1 (Normal/photo) AND modeId=2 (DSO/astro), hoping to
confirm/complete the param_id we had so far only identified through
network capture (in particular brightness/contrast/saturation/hue/
sharpness/burst/timelapse for photo mode).

Usage:
    python test_get_param_and_setting_http.py
"""

import json

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_utils import (
    set_HostMaster,
    perform_enter_photo_mode,
    perform_enter_astro_mode,
    perform_get_default_params_config_http,
    perform_get_param_and_setting_http,
    perform_read_camera_params_http_v3,
    perform_disconnect,
)


def show(label, result):
    log.info(f"=== {label} ===")
    if result is False:
        log.error("Failed (see error message above).")
    else:
        log.success("Response received:")
        print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    log.info("=== MASTER LOCK ===")
    if not set_HostMaster():
        log.warning("MASTER LOCK: no response, continuing anyway.")

    log.info("=== GET /getDefaultParamsConfig (before any active mode) ===")
    show("getDefaultParamsConfig", perform_get_default_params_config_http())

    log.info("=== Entering simple photo mode (mode=1) ===")
    perform_enter_photo_mode()
    show("getParamAndSetting modeId=1 (Normal/photo) - raw",
         perform_get_param_and_setting_http(1))
    show("getParamAndSetting modeId=1 - readable summary",
         perform_read_camera_params_http_v3(1))

    log.info("=== Entering astro mode (mode=8, or test mode=2 for DSO) ===")
    perform_enter_astro_mode()
    show("getParamAndSetting modeId=2 (DSO/astro) - raw",
         perform_get_param_and_setting_http(2))
    show("getParamAndSetting modeId=2 - readable summary",
         perform_read_camera_params_http_v3(2))

    perform_disconnect()


if __name__ == "__main__":
    main()
