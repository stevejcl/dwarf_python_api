"""
dwarf_ble_session.py

Bridges BLE discovery results directly onto a DwarfSession, instead of the
session having to rely on config.py having been rewritten on disk (see
MIGRATION_MULTI_V3.md, "BLE" section, for the field bug this fixes: a
session created before a BLE (re)provisioning happened would otherwise keep
talking to a now-stale IP - potentially some *other* physical Dwarf still
listening there - because nothing ever told it the address had changed).

This module does not touch connect_direct_bluetooth.py's connection logic
itself (BLE scanning/pairing/WiFi handoff) - it only consumes the
connection_state dict that flow already produces, and applies it to a
session:

    - if the session already had an open connection and the IP just
      discovered differs from what it's currently using, the stale
      connection is disconnected first (never silently keep talking to
      whatever answers at the old IP)
    - the session's DwarfConfig is updated in place (dwarf_ip,
      dwarf_model_id, dwarf_uid)
    - if dwarf_uid changed (e.g. it was wrong/empty in the config file the
      session was first built from, and BLE just discovered the real one),
      the DwarfManager entry is re-keyed via DwarfManager.reindex() so
      manager.get(<correct_uid>) keeps working
"""
from __future__ import annotations

from typing import Optional

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_session import DwarfManager, DwarfSession, get_manager
from dwarf_python_api.lib.dwarf_session_socket import disconnect_socket


def apply_ble_discovery(
    session: DwarfSession,
    ip_address: Optional[str] = None,
    dwarf_id: Optional[str] = None,
    dwarf_uid: Optional[str] = None,
    manager: Optional[DwarfManager] = None,
) -> DwarfSession:
    """Apply a BLE connection_state's discovered ip/dwarf_id/dwarf_uid onto
    `session`, guarding against stale-IP reuse and re-keying the manager
    entry if the uid changed. Returns `session` for convenience."""

    manager = manager or get_manager()
    old_uid = session.config.dwarf_uid

    ip_changed = bool(ip_address) and ip_address != session.config.dwarf_ip
    if ip_changed and session.client_instance is not None:
        log.warning(
            f"[{session.dwarf_uid or '<no uid yet>'}] BLE discovery reports a different IP "
            f"({session.config.dwarf_ip!r} -> {ip_address!r}) while a connection was open - "
            "disconnecting the stale socket rather than risk talking to the wrong physical device."
        )
        disconnect_socket(session)

    if ip_address:
        session.config.dwarf_ip = ip_address
    if dwarf_id:
        session.config.dwarf_model_id = dwarf_id

    if dwarf_uid and dwarf_uid != old_uid:
        session.config.dwarf_uid = dwarf_uid
        # reindex() only touches the manager's dict if old_uid genuinely
        # pointed to this same session object - safe to call unconditionally,
        # including the very first time (old_uid empty / not yet registered).
        manager.reindex(session, old_uid=old_uid)
        log.notice(f"Session dwarf_uid corrected/confirmed: {old_uid!r} -> {dwarf_uid!r}")

    return session
