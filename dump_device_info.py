"""
dump_device_info.py
---------------------
Collects as much information as possible about a device (Mini, Dwarf 3,
Dwarf 2) and writes it to a JSON file, to make it easy to compare
param_id/ranges/capabilities across models.

This whole script was built and tested on a Dwarf Mini - the goal here is
precisely to see what differs (or not) on Dwarf 3 and Dwarf 2. In
particular, we do NOT know whether Dwarf 2 (older hardware) even supports
the V3 protocol at all - the script is therefore tolerant of failures:
each step is tried independently, an error on one does not prevent the
next ones, and everything (success or failure) is logged in the final
report.

Sequence:
  1) MASTER LOCK (non-blocking if no response - already known for the Mini)
  2) Time/timezone
  3) GET_DEVICE_STATE_INFO (WS) - just to check that the device actually
     speaks the V3 protocol (shooting_mode_and_techs visible only in the
     logs, this function doesn't yet return the full structure - see
     MIGRATION_V3.md)
  4) GET /getDefaultParamsConfig (HTTP, port 8082)
  5) For each candidate mode (1, 2, 3, 4, 5, 8, 9, 10 - table from
     firmware-astronomy-functions.md): try entering the mode, then
     POST /shootingMode/getParamAndSetting {"modeId": N} (live HTTP).
     Mode 1 uses tech=1 (photo), the others use tech=2 (present in every
     astro technique per the known table).

Usage:
    python dump_device_info.py --label mini
    python dump_device_info.py --label dwarf3
    python dump_device_info.py --label dwarf2
    python dump_device_info.py --label dwarf2 --modes 1,2   # subset

The report is written to device_report_<label>_<timestamp>.json at the
root of the repo.
"""

import argparse
import json
import time
import traceback
from datetime import datetime

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_utils import (
    set_HostMaster,
    perform_time,
    perform_timezone,
    perform_get_device_state_info,
    perform_enter_shooting_mode,
    perform_get_default_params_config_http,
    perform_read_camera_params_http_v3,
    perform_disconnect,
)

DEFAULT_MODES = [1, 2, 3, 4, 5, 8, 9, 10]


def safe_call(label, fn, *args, **kwargs):
    """Execute fn(*args, **kwargs), log the result or the exception, never
    re-raise the exception (so it doesn't interrupt the collection)."""
    log.info(f"--- {label} ---")
    try:
        result = fn(*args, **kwargs)
        if result is False:
            log.warning(f"{label}: failed (False)")
            return {"ok": False, "error": "returned False"}
        log.success(f"{label}: OK")
        return {"ok": True, "result": result}
    except Exception as e:
        log.error(f"{label}: exception {type(e).__name__}: {e}")
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()}


def main():
    parser = argparse.ArgumentParser(description="Device information collection (V3)")
    parser.add_argument("--label", required=True, help="Free-form identifier for the tested device (e.g. mini, dwarf3, dwarf2)")
    parser.add_argument("--modes", default=None, help="Comma-separated list of modeId (default: 1,2,3,4,5,8,9,10)")
    args = parser.parse_args()

    modes = DEFAULT_MODES
    if args.modes:
        modes = [int(m.strip()) for m in args.modes.split(",") if m.strip()]

    report = {
        "label": args.label,
        "timestamp": datetime.now().isoformat(),
        "steps": {},
        "modes": {},
    }

    log.info(f"=== Collecting information for '{args.label}' ===")

    report["steps"]["master_lock"] = safe_call("MASTER LOCK", set_HostMaster)
    report["steps"]["set_time"] = safe_call("SET TIME", perform_time)
    report["steps"]["set_timezone"] = safe_call("SET TIMEZONE", perform_timezone)
    report["steps"]["device_state_info"] = safe_call("GET_DEVICE_STATE_INFO (WS)", perform_get_device_state_info)
    report["steps"]["default_params_config"] = safe_call(
        "GET /getDefaultParamsConfig (HTTP)", perform_get_default_params_config_http
    )

    # "Warm-up" delay: observed on Dwarf 3 that the very first modes tested
    # right after connecting systematically fail against the HTTP API
    # (even after the per-mode delay/retry already added), while modes
    # tested later in the same run all succeed - suggests a firmware-side
    # stabilization period after connecting, not a per-mode issue. See
    # MIGRATION_V3.md.
    log.info("Initial warm-up delay (8s) before starting per-mode tests...")
    time.sleep(8)

    for mode_id in modes:
        log.info(f"=== Mode {mode_id} ===")
        tech = 1 if mode_id == 1 else 2
        entry = safe_call(f"Entering mode {mode_id} (tech={tech})",
                           perform_enter_shooting_mode, mode_id, tech)
        time.sleep(2)
        live = safe_call(f"getParamAndSetting modeId={mode_id} (HTTP live)",
                          perform_read_camera_params_http_v3, mode_id)
        if live.get("ok") is False:
            # Second attempt after a longer delay: on Dwarf 3, an
            # immediate HTTP "returned False" failure right after entering
            # a mode sometimes seems due to a lack of stabilization delay
            # (observed on several modes in a row - see MIGRATION_V3.md).
            log.warning(f"Mode {mode_id}: failed, retrying after an extra 3s")
            time.sleep(3)
            live = safe_call(f"getParamAndSetting modeId={mode_id} (HTTP live, 2nd attempt)",
                              perform_read_camera_params_http_v3, mode_id)
        report["modes"][mode_id] = {"enter_mode": entry, "live_params": live}

    # Final retry pass over the failed modes, at the end of the run: if the
    # problem really is a firmware-side warm-up/stabilization period
    # (hypothesis under verification, see MIGRATION_V3.md), these modes
    # should now succeed since several cycles have elapsed.
    failed_modes = [m for m in modes if not report["modes"][m]["live_params"].get("ok")]
    if failed_modes:
        log.info(f"=== Final retry pass on failed modes: {failed_modes} ===")
        for mode_id in failed_modes:
            tech = 1 if mode_id == 1 else 2
            entry2 = safe_call(f"[Retry] Entering mode {mode_id} (tech={tech})",
                                perform_enter_shooting_mode, mode_id, tech)
            time.sleep(2)
            live2 = safe_call(f"[Retry] getParamAndSetting modeId={mode_id}",
                               perform_read_camera_params_http_v3, mode_id)
            report["modes"][mode_id]["retry_at_end"] = {"enter_mode": entry2, "live_params": live2}

    perform_disconnect()

    filename = f"device_report_{args.label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    log.success(f"Report written: {filename}")
    print(f"\n>>> Report written: {filename}\n")


if __name__ == "__main__":
    main()
