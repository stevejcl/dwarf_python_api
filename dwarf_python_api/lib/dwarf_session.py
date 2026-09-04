"""
DwarfSession / DwarfManager.

Today, websockets_utils.py holds three module-level globals that make
multi-device control impossible:

    client_instance    # the (single) WebSocketClient
    event_loop          # the (single) background asyncio loop
    event_loop_thread    # the thread running it

...plus a fourth one in get_client_status():

    previous_values    # notification-change-detection cache

DwarfSession moves all four into an object you can have one of per physical
Dwarf. DwarfManager is a small registry keyed by dwarf_uid (NOT dwarf_id -
see DwarfConfig for why dwarf_id is unsafe as a key).

This file is purely additive: nothing in websockets_utils.py or
dwarf_utils.py is modified. See dwarf_session_socket.py for the
session-scoped equivalents of connect_socket/send_socket_message/etc, and
MIGRATION_MULTI_V3.md for how to wire this into dwarf_utils.py's perform_*
functions incrementally.
"""
from __future__ import annotations

import threading
from typing import Dict, Iterator, List, Optional

from dwarf_python_api.lib.dwarf_config import DwarfConfig


class DwarfSession:
    """One DwarfSession == one physical Dwarf: one WebSocketClient, one
    background event loop/thread, one notification cache. Fully independent
    from any other DwarfSession - create one per device you want to control
    concurrently."""

    def __init__(self, config: DwarfConfig):
        self.config = config
        self.client_instance = None            # a websockets_utils.WebSocketClient once connected
        self.event_loop = None                  # this session's background asyncio loop
        self.event_loop_thread = None           # the thread running that loop
        self.previous_values: dict = {}         # per-session equivalent of the old global cache
        self.lock = threading.Lock()            # guards previous_values (get_client_status is polled)

    @property
    def dwarf_uid(self) -> str:
        return self.config.dwarf_uid

    @property
    def is_connected(self) -> bool:
        return bool(self.client_instance and self.client_instance.websocket)

    def __repr__(self) -> str:
        return (
            f"<DwarfSession uid={self.config.dwarf_uid!r} "
            f"ip={self.config.dwarf_ip!r} connected={self.is_connected}>"
        )


class DwarfManager:
    """Registry of DwarfSession, keyed by dwarf_uid."""

    def __init__(self):
        self._sessions: Dict[str, DwarfSession] = {}
        self._default_uid: Optional[str] = None

    def add(self, config: DwarfConfig, make_default: bool = False) -> DwarfSession:
        if not config.dwarf_uid:
            raise ValueError(
                "DwarfConfig.dwarf_uid is required to register a session "
                "(it is the only value guaranteed unique per physical device)."
            )
        session = DwarfSession(config)
        self._sessions[config.dwarf_uid] = session
        if make_default or self._default_uid is None:
            self._default_uid = config.dwarf_uid
        return session

    def get(self, dwarf_uid: str) -> DwarfSession:
        return self._sessions[dwarf_uid]

    def remove(self, dwarf_uid: str) -> None:
        self._sessions.pop(dwarf_uid, None)
        if self._default_uid == dwarf_uid:
            self._default_uid = next(iter(self._sessions), None)

    def reindex(self, session: DwarfSession, old_uid: Optional[str] = None) -> None:
        """Re-file `session` under its CURRENT config.dwarf_uid, removing any
        stale entry filed under `old_uid` first (if it's still that same
        session object there).

        Use this whenever a session's dwarf_uid becomes known/corrected
        after the session was already created or registered - e.g. once
        BLE discovery reports the real dwarf_uid for a device that was
        first registered with an incomplete or wrong config. Without this,
        DwarfManager.get(<correct_uid>) would keep raising KeyError because
        the dict entry would still live under the old key.
        """
        was_default = False
        if old_uid and self._sessions.get(old_uid) is session:
            del self._sessions[old_uid]
            was_default = self._default_uid == old_uid

        new_uid = session.config.dwarf_uid
        if not new_uid:
            raise ValueError("session.config.dwarf_uid must be set before reindexing")

        self._sessions[new_uid] = session
        if was_default or self._default_uid is None:
            self._default_uid = new_uid

    def default(self) -> Optional[DwarfSession]:
        return self._sessions.get(self._default_uid) if self._default_uid else None

    def set_default(self, dwarf_uid: str) -> None:
        if dwarf_uid not in self._sessions:
            raise KeyError(dwarf_uid)
        self._default_uid = dwarf_uid

    def all(self) -> List[DwarfSession]:
        return list(self._sessions.values())

    def __len__(self) -> int:
        return len(self._sessions)

    def __iter__(self) -> Iterator[DwarfSession]:
        return iter(self._sessions.values())


# ---------------------------------------------------------------------------
# Module-level manager + compat shim.
#
# During migration, dwarf_utils.py's perform_*() functions should accept an
# optional `session: DwarfSession = None` parameter and fall back to
# get_default_session() when it's not given. This means astro_dwarf_session
# and any other caller keep working unmodified (mono-dwarf, implicit
# session) until they're explicitly migrated to pass a session.
# ---------------------------------------------------------------------------
_manager = DwarfManager()


def get_manager() -> DwarfManager:
    return _manager


def get_default_session() -> Optional[DwarfSession]:
    return _manager.default()


def set_default_session(session: DwarfSession) -> None:
    _manager._sessions[session.dwarf_uid] = session
    _manager._default_uid = session.dwarf_uid
