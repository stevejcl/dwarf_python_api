"""
connect_bluetooth_cmd.py
--------------------------
Establishes the Bluetooth -> WiFi connection with the Dwarf, on the same
model as `connect_bluetooth.py` from dwarf_test_apiV2 (`--cmd` mode,
without the Windows GUI).

This script scans for Dwarf devices over BLE, sends the WiFi credentials
(SSID/password of the network the Dwarf should connect to in STA mode),
then, once the WiFi connection is established on the Dwarf side, writes
the obtained IP as well as dwarf_id/dwarf_uid to config.ini via
`dwarf_python_api.get_config_data.update_config_data(...)`.

This is the config.ini file that `websockets_utils.py` (function that
builds the `ws://<ip>:9900` URL) and the V3 test scripts
(`test_connect_v3.py`, `test_photo_simple_v3.py`) then read: you must
therefore run THIS script first, once (or whenever the IP changes),
before the test scripts.

Nothing here depends on the new V3 proto: the BLE WiFi provisioning
protocol (`dwarf_python_api.proto.ble_pb2`) is unchanged between V2 and V3
(verified: every field used by this code exists identically in the new
ble.proto, which only adds fields/messages on top).

Prerequisite: the `tkinter` module must be installed (unconditional import
in `dwarf_ble_connect/lib/connect_direct_bluetooth.py`, even though this
script doesn't use it in `--cmd` mode). On Linux: `sudo apt install
python3-tk` (Debian/Ubuntu) or the equivalent for your distribution.

Usage:
    python connect_bluetooth_cmd.py --ssid "MyWifi" --pwd "mypassword"

    # Reuses the Bluetooth password and WiFi credentials already saved in
    # config.ini if you don't pass --psd/--ssid/--pwd:
    python connect_bluetooth_cmd.py

    # Automatic selection if several Dwarf devices are detected (exact
    # name shown on a first run without --select):
    python connect_bluetooth_cmd.py --ssid "MyWifi" --pwd "..." --select "Dwarf2-XXXXXX"

Options:
    --psd     Bluetooth password of the Dwarf (default: DWARF_12345678,
              or the value already saved in config.ini)
    --ssid    SSID of the WiFi network the Dwarf should connect to (STA)
    --pwd     Password for that WiFi network
    --select  Exact name of the device to pick if several are detected
              (avoids the interactive prompt)
"""

import argparse
import os
import sys

import dwarf_python_api.lib.my_logger as log
from dwarf_ble_connect.lib.connect_direct_bluetooth import connect_ble_direct_dwarf
from dwarf_python_api.lib.dwarf_utils import (
    read_bluetooth_ble_psd,
    read_bluetooth_ble_STA_ssid,
    read_bluetooth_ble_STA_pwd,
)
import dwarf_python_api.get_config_data


def main():
    parser = argparse.ArgumentParser(description="Bluetooth -> WiFi connection for the Dwarf (cmd mode)")
    parser.add_argument("--psd", default=None, help="Bluetooth password of the Dwarf")
    parser.add_argument("--ssid", default=None, help="SSID of the target WiFi network (STA mode)")
    parser.add_argument("--pwd", default=None, help="Password of the target WiFi network")
    parser.add_argument("--select", default="", help="Exact device name if several are detected")
    parser.add_argument(
        "--config-py", default=None,
        help="Path to a specific config.py to write to (multi-Dwarf setups: one file per device). "
             "Defaults to ./config.py if omitted, exactly like before.",
    )
    args = parser.parse_args()

    if args.config_py:
        # Redirect the disk write to the exact file requested - without
        # this, update_config_data() (called deep inside
        # connect_ble_direct_dwarf) always writes to the hardcoded default
        # ./config.py, REGARDLESS of --config-py, silently discarding this
        # option. tmp/lock files are derived per config-py path so two
        # devices connecting concurrently don't share a lock/tmp file.
        dwarf_python_api.get_config_data.set_config_data(
            config_file=args.config_py,
            config_file_tmp=args.config_py + ".tmp",
            lock_file=args.config_py + ".lock",
        )
        log.info(f"Writing to: {os.path.abspath(args.config_py)}")

    ble_psd = args.psd or read_bluetooth_ble_psd() or "DWARF_12345678"
    ble_STA_ssid = args.ssid or read_bluetooth_ble_STA_ssid() or ""
    ble_STA_pwd = args.pwd or read_bluetooth_ble_STA_pwd() or ""

    log.info("##############")
    log.info("Values used:")
    log.info(f"Bluetooth PSD: {ble_psd}")
    log.info(f"WiFi STA SSID: {ble_STA_ssid or '(empty)'}")
    log.info(f"WiFi STA PWD : {'*******' if ble_STA_pwd else '(empty)'}")
    log.info("##############")

    if not ble_STA_ssid or not ble_STA_pwd:
        log.warning(
            "No WiFi SSID/password provided (neither as an argument, nor"
            " in config.ini). If the Dwarf isn't already configured in STA"
            " mode, the connection is likely to fail. Use --ssid and --pwd."
        )

    result = connect_ble_direct_dwarf(ble_psd, ble_STA_ssid, ble_STA_pwd, args.select)
    log.info(f"Result: {result}")

    if result:
        # Read back what was actually written, from the SAME file we just
        # redirected writes to (args.config_py if given, else the default) -
        # so what's printed here is guaranteed to match what a later,
        # separate script run (e.g. test_multi_v3_photo.py --config-py
        # <same path>) will read.
        written = dwarf_python_api.get_config_data.get_config_data(config_file=args.config_py)
        log.success(
            f"Bluetooth -> WiFi connection succeeded. dwarf_uid={written.get('dwarf_uid')!r} "
            f"ip={written.get('ip')!r} saved to "
            f"{os.path.abspath(args.config_py) if args.config_py else os.path.abspath('config.py')}"
        )
        return 0
    else:
        log.error("Bluetooth -> WiFi connection failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
