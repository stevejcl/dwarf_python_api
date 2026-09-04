"""
DwarfConfig unifies config.py + config.ini into a single explicit object.

This is ADDITIVE: it does not remove or change config.py / config.ini or the
existing read_*()/get_config_data() functions. It reads the *same* files with
the *same* formats you already have - no migration of existing installs is
required. The goal is simply to stop re-reading these files scattered across
15+ functions in dwarf_utils.py, and to give each DwarfSession its own
config object instead of a single implicit global file path.

Usage:
    from dwarf_python_api.lib.dwarf_config import DwarfConfig

    cfg_mini = DwarfConfig.from_files("config_mini.py", "config_mini.ini")
    cfg_d3   = DwarfConfig.from_files("config_d3.py", "config_d3.ini")
"""
from __future__ import annotations

import configparser
from dataclasses import dataclass
from typing import Optional

import dwarf_python_api.get_config_data as get_config_data


def _parse_bool(value, default: Optional[bool] = False) -> Optional[bool]:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().strip('"').lower() in ("true", "1", "yes")


@dataclass
class DwarfConfig:
    # --- Identity -----------------------------------------------------
    # dwarf_uid is the ONLY value guaranteed unique per physical device.
    # dwarf_model_id (ex-DWARF_ID) is a MODEL/TYPE code shared by every unit
    # of the same model (Dwarf 2 / Mini / 3) - never use it as a registry key.
    dwarf_uid: str
    dwarf_ip: str
    alternate_dwarf_ip: Optional[str] = None
    """The OTHER candidate IP (usually config.ini's, when it disagrees with
    config.py's) - kept rather than silently discarded, so
    resolve_dwarf_ip() in dwarf_utils.py can try it as a fallback if the
    primary dwarf_ip turns out to be wrong/unreachable, instead of just
    giving up."""
    dwarf_model_id: str = ""
    dwarf_ui: str = ""
    client_id: str = ""
    update_client_id: str = ""

    # --- BLE / networking ----------------------------------------------
    ble_psd: str = ""
    ble_sta_ssid: str = ""
    ble_sta_pwd: str = ""
    ble_wifi_type: str = ""
    ble_auto_ap: Optional[bool] = None
    ble_auto_sta: Optional[bool] = None
    ble_country: str = ""
    ble_country_list: str = ""

    # --- Location --------------------------------------------------------
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = ""

    # --- Camera defaults -------------------------------------------------
    exposure: str = "30"
    gain: str = "60"
    ircut: str = "0"
    binning: str = "0"
    count: str = "20"
    wide_exposure: str = ""
    wide_gain: str = ""
    camera_type: str = ""
    device_type: str = ""

    # --- Stellarium --------------------------------------------------------
    stellarium_ip: str = ""
    stellarium_port: Optional[int] = None

    # --- Logging / behaviour ----------------------------------------------
    log_file: str = "app.log"
    debug: bool = False
    trace: bool = False
    timeout_cmd: Optional[int] = None
    calibration: Optional[bool] = None

    # --- Provenance (kept so save-back helpers know which files to touch) --
    config_py_path: str = "config.py"
    config_ini_path: str = "config.ini"

    @classmethod
    def from_files(cls, config_py_path: str = "config.py", config_ini_path: str = "config.ini") -> "DwarfConfig":
        """Build a DwarfConfig by reading an existing config.py + config.ini
        pair, using get_config_data.get_config_data() for the .py side (same
        parser you already use) and configparser for the .ini side."""

        py_values = get_config_data.get_config_data(config_file=config_py_path)

        ini = configparser.ConfigParser()
        ini.read(config_ini_path)
        section = ini["CONFIG"] if ini.has_section("CONFIG") else None

        def ini_get(key: str, default: str = "") -> str:
            return section.get(key, default) if section else default

        def ini_getfloat(key: str) -> Optional[float]:
            try:
                return section.getfloat(key) if section else None
            except (ValueError, AttributeError):
                return None

        def ini_getint(key: str) -> Optional[int]:
            try:
                return section.getint(key) if section else None
            except (ValueError, AttributeError):
                return None

        timeout_cmd_raw = py_values.get("timeout_cmd")
        timeout_cmd = int(timeout_cmd_raw) if timeout_cmd_raw not in (None, "") else None

        return cls(
            dwarf_uid=py_values.get("dwarf_uid") or "",
            dwarf_ip=py_values.get("ip") or ini_get("dwarf_ip") or "",
            alternate_dwarf_ip=(
                ini_get("dwarf_ip") if py_values.get("ip") and ini_get("dwarf_ip") != py_values.get("ip") else None
            ),
            dwarf_model_id=py_values.get("dwarf_id") or "",
            dwarf_ui=py_values.get("ui") or "",
            client_id=py_values.get("client_id") or "",
            update_client_id=py_values.get("update_client_id") or "",

            ble_psd=ini_get("ble_psd"),
            ble_sta_ssid=ini_get("ble_sta_ssid"),
            ble_sta_pwd=ini_get("ble_sta_pwd"),
            ble_wifi_type=ini_get("ble_wifi_type"),
            ble_auto_ap=_parse_bool(ini_get("ble_auto_ap", ""), default=None),
            ble_auto_sta=_parse_bool(ini_get("ble_auto_sta", ""), default=None),
            ble_country=ini_get("ble_country"),
            ble_country_list=ini_get("ble_country_list"),

            latitude=ini_getfloat("latitude"),
            longitude=ini_getfloat("longitude"),
            timezone=ini_get("timezone"),

            exposure=ini_get("exposure", "30"),
            gain=ini_get("gain", "60"),
            ircut=ini_get("ircut", "0"),
            binning=ini_get("binning", "0"),
            count=ini_get("count", "20"),
            wide_exposure=ini_get("wide_exposure"),
            wide_gain=ini_get("wide_gain"),
            camera_type=ini_get("camera_type"),
            device_type=ini_get("device_type"),

            stellarium_ip=ini_get("stellarium_ip"),
            stellarium_port=ini_getint("stellarium_port"),

            log_file=py_values.get("log_file") or "app.log",
            debug=bool(py_values.get("debug")),
            trace=bool(py_values.get("trace")),
            timeout_cmd=timeout_cmd,
            calibration=py_values.get("calibration"),

            config_py_path=config_py_path,
            config_ini_path=config_ini_path,
        )
