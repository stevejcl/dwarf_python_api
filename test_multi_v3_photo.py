"""
test_multi_v3_photo.py
-----------------------
Smoke test for the multi-Dwarf session foundation (DwarfConfig/DwarfSession/
DwarfManager + the session-aware perform_enter_photo_mode/perform_takePhoto).

Runs the simplest possible real-hardware round trip:
    1) build a DwarfConfig from your existing config.py + config.ini
    2) register it as a DwarfSession in the DwarfManager
    3) perform_enter_photo_mode(session=...)
    4) perform_takePhoto(session=...)
    5) print get_client_status(session) so you can see battery/temperature/
       capture counters update
    6) disconnect cleanly

This does NOT touch your existing mono-dwarf flow (main_v3.py, connect via
connect_bluetooth_cmd.py, etc.) - it's a separate, additive smoke test.

Prerequisites (same as main_v3.py):
    - The Dwarf must already be connected to your WiFi and reachable at the
      IP in config.py (run connect_bluetooth_cmd.py first if it isn't).
    - config.py / config.ini at the repository root, as usual.

Usage:
    python test_multi_v3_photo.py
    python test_multi_v3_photo.py --config-py config_mini.py --config-ini config_mini.ini
"""
import argparse
import os
import time

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_config import DwarfConfig
from dwarf_python_api.lib.dwarf_session import DwarfManager
from dwarf_python_api.lib.dwarf_session_socket import disconnect_socket, get_client_status
from dwarf_python_api.lib.dwarf_utils import (
    perform_enter_photo_mode,
    perform_takePhoto,
    verify_device_identity,
    ensure_device_reachable,
    resolve_dwarf_ip,
)


def main():
    parser = argparse.ArgumentParser(description="Smoke test: enter photo mode + take a photo via a DwarfSession.")
    parser.add_argument("--config-py", default="config.py", help="Path to config.py (default: config.py)")
    parser.add_argument("--config-ini", default="config.ini", help="Path to config.ini (default: config.ini)")
    parser.add_argument(
        "--warmup", type=float, default=3.0,
        help="Seconds to wait after connecting before sending commands (default: 3s)",
    )
    parser.add_argument(
        "--skip-identity-check", action="store_true",
        help="Skip the /deviceInfo identity verification (not recommended for multi-Dwarf setups)",
    )
    parser.add_argument(
        "--ble-ssid", default=None,
        help="WiFi SSID - if given (with --ble-pwd), a BLE reconnect targeted at this device's dwarf_uid "
             "is attempted automatically when the configured IP turns out to be stale/unreachable, "
             "before giving up.",
    )
    parser.add_argument("--ble-pwd", default=None, help="WiFi password, used with --ble-ssid")
    parser.add_argument("--ble-psd", default="DWARF_12345678", help="Dwarf's own Bluetooth password")
    args = parser.parse_args()

    print("=== Multi-Dwarf smoke test: photo mode ===")

    config_py_abspath = os.path.abspath(args.config_py)
    config_ini_abspath = os.path.abspath(args.config_ini)
    print(f"Reading config.py  from: {config_py_abspath}")
    print(f"Reading config.ini from: {config_ini_abspath}")
    if os.path.exists(config_py_abspath):
        with open(config_py_abspath, "r") as f:
            for line in f:
                if line.strip().startswith("DWARF_IP"):
                    print(f"  -> raw DWARF_IP line in that file: {line.strip()!r}")
                    break
    else:
        log.error(f"File does not exist at this path: {config_py_abspath}")

    config = DwarfConfig.from_files(args.config_py, args.config_ini)
    print(f"Loaded config: dwarf_uid={config.dwarf_uid!r} dwarf_ip={config.dwarf_ip!r}")

    if not config.dwarf_uid or not config.dwarf_ip:
        log.error("Missing dwarf_uid or dwarf_ip in config.py - connect via Bluetooth first (connect_bluetooth_cmd.py).")
        return

    manager = DwarfManager()
    session = manager.add(config, make_default=True)
    print(f"Session created: {session}")

    if not args.skip_identity_check:
        print("\nResolving/verifying device identity via /deviceInfo (checks config.py's IP first, then "
              "config.ini's as a fallback candidate, before considering BLE)...")
        identity_ok = resolve_dwarf_ip(session)

        if not identity_ok and args.ble_ssid and args.ble_pwd:
            print("Neither known candidate IP confirmed this device - attempting a BLE reconnect...")
            identity_ok = ensure_device_reachable(
                session, ble_ssid=args.ble_ssid, ble_pwd=args.ble_pwd, ble_psd=args.ble_psd,
            )

        if identity_ok is True:
            print(f"Identity confirmed (dwarf_ip is now {session.config.dwarf_ip!r}).")
        elif args.ble_ssid and args.ble_pwd:
            log.error(
                "Identity still not confirmed after trying known candidates and a BLE reconnect - aborting. "
                "See the messages above for details (wrong device, or BLE reconnect itself failed)."
            )
            return
        elif identity_ok is False:
            log.error("Identity MISMATCH - aborting before sending any command. See the error above for details.")
            return
        else:
            print("Could not reach /deviceInfo on any known candidate to verify identity (device off, "
                  "wrong/stale IP, or HTTP API not up yet) - proceeding WITHOUT confirmation. Pass "
                  "--ble-ssid/--ble-pwd to auto-recover via a targeted BLE reconnect, or "
                  "auto-recover from a stale IP via a targeted BLE reconnect, or --skip-identity-check "
                  "to silence this check entirely.")

    try:
        print(f"Entering photo mode (waiting {args.warmup}s warm-up after first connect)...")
        ok_mode = perform_enter_photo_mode(session=session)
        print(f"perform_enter_photo_mode -> {ok_mode}")

        if not ok_mode:
            log.error("Entering photo mode failed - aborting before takePhoto.")
            return

        time.sleep(args.warmup)

        print("Taking a photo...")
        ok_photo = perform_takePhoto(session=session)
        print(f"perform_takePhoto -> {ok_photo}")

        print("\nCurrent client status for this session:")
        status = get_client_status(session)
        print(status)

    finally:
        print("\nDisconnecting...")
        disconnect_socket(session)
        print(f"Session after disconnect: {session}")


if __name__ == "__main__":
    main()
