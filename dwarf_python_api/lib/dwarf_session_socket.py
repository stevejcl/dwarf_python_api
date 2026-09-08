"""
Session-scoped mirrors of the connect/send/status functions in
websockets_utils.py.

websockets_utils.py is NOT modified by this file - every function here is a
faithful line-by-line port of its global-based counterpart, with
client_instance / event_loop / event_loop_thread / previous_values replaced
by attributes on a DwarfSession. The branching logic (DISCONNECTED / ERROR /
SLAVEMODE / TIMEOUT / WARNING handling) is copied as-is on purpose: this is
hardware-validated behaviour and should not be "cleaned up" without
re-testing on real devices.

Mapping to the existing global functions, for reference during migration:

    websockets_utils.connect_socket(msg, cmd, type_id, module_id)
        -> connect_socket(session, msg, cmd, type_id, module_id)

    websockets_utils.disconnect_socket()
        -> disconnect_socket(session)

    websockets_utils.get_client_status()
        -> get_client_status(session)

Once dwarf_utils.py's perform_*() functions accept a `session` parameter,
swap their calls to connect_socket()/get_client_status() for the versions
in this module.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
import contextlib
import threading
import time

import dwarf_python_api.lib.my_logger as log
from dwarf_python_api.lib.dwarf_session import DwarfSession
from dwarf_python_api.lib.websockets_utils import (
    Dwarf_Result,
    ERROR_INTERRUPTED,
    ERROR_SLAVEMODE,
    ERROR_TIMEOUT,
    WebSocketClient,
    _filter_benign_connection_reset,
    flush_queue_for_command_id,
    get_result_with_timeout,
    process_command,
    run_event_loop,
    gb_timeout,
    ws_uri,
)


async def _start_socket(session: DwarfSession, ping_interval_task: int = 10) -> bool:
    """Mirrors websockets_utils.start_socket(), scoped to `session`."""
    config = session.config
    uri = config.dwarf_ip
    client_id = config.client_id

    if not (uri and client_id):
        log.error(f"[{session.dwarf_uid}] Missing dwarf_ip or client_id in DwarfConfig.")
        return False

    websocket_uri = ws_uri(uri)
    log.info(f"[{session.dwarf_uid}] Try Connect to {websocket_uri} for {client_id}")

    try:
        session.client_instance = WebSocketClient(
            asyncio.get_event_loop(), websocket_uri, client_id, ping_interval_task
        )
        session.client_instance.initialize_once()
        log.debug(f"[{session.dwarf_uid}] WebSocket Client init Once.")

        session.client_instance.run()
        log.debug(f"[{session.dwarf_uid}] WebSocket Client run.")
        return True

    except asyncio.CancelledError:
        log.debug(f"[{session.dwarf_uid}] start_socket cancelled Error.")
    except Exception as e:
        log.error(f"[{session.dwarf_uid}] Unknown Error closing : {e}")

    return False


async def _send_message_init(session: DwarfSession) -> bool:
    """Mirrors websockets_utils.send_message_init(), scoped to `session`."""
    result = False
    try:
        if session.client_instance:
            log.debug(f"[{session.dwarf_uid}] WebSocket Client Message Init Start.")
            task_init = session.client_instance.message_init()
            await task_init
            log.debug(f"[{session.dwarf_uid}] WebSocket Client init Message Start.")
            return result
    except asyncio.CancelledError:
        log.debug(f"[{session.dwarf_uid}] start_socket cancelled Error.")
    except Exception as e:
        log.error(f"[{session.dwarf_uid}] Unknown Error closing : {e}")
    return False


async def _send_socket(session: DwarfSession, message, command, type_id, module_id) -> bool:
    """Mirrors websockets_utils.send_socket(), scoped to `session`."""
    result = False
    try:
        if session.client_instance:
            log.debug(f"[{session.dwarf_uid}] WebSocket Client Send Start.")
            await session.client_instance.send_message(message, command, type_id, module_id)
            result = True
        log.debug(f"[{session.dwarf_uid}] WebSocket Client Send End.")
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt received. Stopping gracefully 1.")
    return result


async def init_socket(session: DwarfSession):
    """Mirrors websockets_utils.init_socket(), scoped to `session`."""
    result = False

    try:
        if not session.client_instance:
            # asyncio.SelectorEventLoop(), NOT asyncio.new_event_loop():
            # on Windows, new_event_loop() returns a ProactorEventLoop by
            # default, whose _ProactorBasePipeTransport._call_connection_
            # lost can raise a bare ConnectionResetError ([WinError
            # 10054]) when the Dwarf resets the connection - and this
            # specific callback can fire during the loop's OWN close()
            # sequence, seemingly bypassing set_exception_handler()
            # entirely (confirmed: that handler is already attached
            # below and on the throwaway loop in connect_socket(), and
            # the noise still got reported in real testing). SelectorEventLoop
            # has no Proactor/IOCP transport machinery at all, so this
            # whole class of noise can't happen with it - a more
            # thorough fix than trying to filter the exception after
            # the fact. No behavioural difference for our use (plain
            # WebSocket/TCP I/O, no subprocess management on this loop).
            session.event_loop = asyncio.SelectorEventLoop()
            session.event_loop_thread = threading.Thread(
                target=run_event_loop, args=(session.event_loop,), daemon=True
            )
            session.event_loop_thread.start()

        if not session.client_instance or not session.client_instance.start_client:

            future = asyncio.run_coroutine_threadsafe(_start_socket(session), session.event_loop)
            future.result()

            log.debug(f"[{session.dwarf_uid}] client_instance {session.client_instance}")
            if session.client_instance:
                # Back to 30s (Sep 2026, was momentarily 5s as a
                # diagnostic experiment, then briefly 60s before that) -
                # the real ROOT CAUSE of the reported "second device
                # falsely shows not-connected" issue was found and fixed
                # separately: WebSocketClient.Init_Send_
                # TeleGetSystemWorkingState was a CLASS-level attribute
                # (shared across every connected device) instead of a
                # per-INSTANCE one, so the second device's own init
                # command (CMD_GLOBAL_TASK_GET_DEVICE_STATE_INFO) was
                # silently never sent at all once the first device had
                # already flipped that shared flag to False - explaining
                # why no timeout duration ever helped (the question was
                # never asked, so no answer could ever arrive) and why
                # things "just started working" right after a wait gave
                # up (an unrelated later call succeeded normally). Now
                # that every instance tracks this independently (see
                # send_message_init()/initialize_once() in websockets_
                # utils.py, all converted from WebSocketClient.X to
                # self.X), user-confirmed via a real two-device log:
                # zero timeouts/failures, both devices connect within
                # ~13s of each other with no false negatives. 30s here
                # is a comfortable, unhurried default for this one-time
                # connection step now that the actual bug is gone -
                # matching gb_timeout's own spirit of generous patience
                # for one-time/rare operations (150s) rather than the
                # tight budget appropriate for frequent in-session
                # commands.
                result_cnx = asyncio.run_coroutine_threadsafe(
                    get_result_with_timeout(session.client_instance.result_queue, 30), session.event_loop
                ).result()

                if isinstance(result_cnx, dict) and "code" in result_cnx:
                    if result_cnx["result"] == Dwarf_Result.DISCONNECTED:
                        log.error(f"[{session.dwarf_uid}] Error WebSocket Disconnected.")
                        stop_event_loop(session)
                        result = False
                    elif result_cnx["result"] == Dwarf_Result.ERROR:
                        log.error(f"[{session.dwarf_uid}] Error WebSocket Connection.")
                        stop_event_loop(session)
                        result = False
                    else:
                        result = result_cnx["code"]
                elif isinstance(result_cnx, int):
                    result = result_cnx

            if session.client_instance and (result is not False):
                future = asyncio.run_coroutine_threadsafe(_send_message_init(session), session.event_loop)
                future.result()

                # Same reasoning as the connection-step wait above - back
                # to 30s now that the actual root cause (shared class-
                # level init flag) is fixed.
                result_cnx = asyncio.run_coroutine_threadsafe(
                    get_result_with_timeout(session.client_instance.result_queue, 30), session.event_loop
                ).result()

                if isinstance(result_cnx, dict) and "code" in result_cnx:
                    if result_cnx["result"] == Dwarf_Result.DISCONNECTED:
                        log.error(f"[{session.dwarf_uid}] Error WebSocket Disconnected.")
                        stop_event_loop(session)
                        result = False
                    elif result_cnx["result"] == Dwarf_Result.ERROR:
                        log.error(f"[{session.dwarf_uid}] Error WebSocket Connection.")
                        stop_event_loop(session)
                        result = False
                    elif result_cnx["result"] == Dwarf_Result.WARNING and result_cnx["code"] == ERROR_SLAVEMODE:
                        log.error(f"[{session.dwarf_uid}] Can't send command, SLAVE MODE detected.")
                        result = False
                    elif result_cnx["result"] == Dwarf_Result.WARNING and result_cnx["code"] == ERROR_TIMEOUT:
                        log.error(f"[{session.dwarf_uid}] command TIMEOUT.")
                        result = False
                    elif result_cnx["result"] == Dwarf_Result.WARNING:
                        log.error(f"[{session.dwarf_uid}] command error: {result_cnx.get('message')}")
                        result = False
                    else:
                        result = result_cnx["code"]
                elif isinstance(result_cnx, int):
                    result = result_cnx

            log.info(f"[{session.dwarf_uid}] Result : {result}")

    except KeyboardInterrupt:
        log.debug(f"[{session.dwarf_uid}] KeyboardInterrupt received. Stopping gracefully 2.")
    return result


async def send_socket_message(session: DwarfSession, message, command, type_id, module_id):
    """Mirrors websockets_utils.send_socket_message(), scoped to `session`."""
    result = False
    client = session.client_instance

    try:
        if client:
            await flush_queue_for_command_id(client.result_queue, client.result_queue_locked, command)

            future = asyncio.run_coroutine_threadsafe(
                _send_socket(session, message, command, type_id, module_id), client.task.get_loop()
            )
            future.result()

            if client:
                notification_result = True
                while notification_result:
                    notification_result = False
                    future_cnx = asyncio.run_coroutine_threadsafe(
                        get_result_with_timeout(client.result_queue, gb_timeout), session.event_loop
                    )
                    while not future_cnx.done():
                        time.sleep(0.1)
                    result_cnx = future_cnx.result()

                    if isinstance(result_cnx, dict) and "code" in result_cnx:
                        if result_cnx["result"] == Dwarf_Result.DISCONNECTED:
                            log.error(f"[{session.dwarf_uid}] Error WebSocket Disconnected.")
                            stop_event_loop(session)
                            result = False
                        elif result_cnx["result"] == Dwarf_Result.WARNING and result_cnx["code"] == ERROR_SLAVEMODE:
                            log.error(f"[{session.dwarf_uid}] Can't send command, SLAVE MODE detected.")
                            result = False
                        elif result_cnx["result"] == Dwarf_Result.WARNING and result_cnx["code"] == ERROR_TIMEOUT:
                            log.error(f"[{session.dwarf_uid}] command TIMEOUT.")
                            result = False
                        elif result_cnx["result"] == Dwarf_Result.WARNING:
                            log.error(f"[{session.dwarf_uid}] command error: {result_cnx.get('message')}")
                            result = False
                        else:
                            result = result_cnx["code"]
                            if result == 0 and isinstance(result_cnx, dict) and "notification" in result_cnx:
                                log.debug(f"[{session.dwarf_uid}] Notification Received : continue loop.")
                                notification_result = result_cnx["notification"]
                            elif result == 0 and process_command(
                                result_cnx.get("cmd_send"), result_cnx.get("cmd_recv")
                            ) is None:
                                log.info(f"[{session.dwarf_uid}] Ignore Frame Received : continue loop.")
                                notification_result = True

                    elif isinstance(result_cnx, int):
                        result = result_cnx

                log.info(f"[{session.dwarf_uid}] Result : {result}")

            if session.client_instance:
                session.client_instance.command = None

    except KeyboardInterrupt:
        log.debug(f"[{session.dwarf_uid}] KeyboardInterrupt received. Stopping gracefully 3.")
        log.warning("Operation interrupted by the user (CTRL+C).")
        result = ERROR_INTERRUPTED

    return result


def connect_socket(session: DwarfSession, message, command, type_id, module_id):
    """Mirrors websockets_utils.connect_socket(), scoped to `session`.

    This is the synchronous entry point dwarf_utils.py's perform_*()
    functions should call - same one-shot throwaway-loop pattern as the
    original, so behaviour under repeated calls is unchanged."""
    result = True
    # asyncio.SelectorEventLoop(), not asyncio.new_event_loop() - see
    # init_socket()'s comment above for why (avoids Windows'
    # ProactorEventLoop-specific _call_connection_lost noise at the
    # source rather than trying to filter it after the fact).
    loop = asyncio.SelectorEventLoop()
    asyncio.set_event_loop(loop)
    # Same benign-noise filter as the persistent per-device loop (see
    # run_event_loop() in websockets_utils.py) - this THROWAWAY loop is
    # created fresh on every single command send (connect_socket() is
    # dwarf_utils.py's per-perform_* entry point), so it's actually the
    # MORE frequent source of the Windows ProactorEventLoop
    # ConnectionResetError noise, not the persistent loop.
    loop.set_exception_handler(_filter_benign_connection_reset)

    try:
        if not session.client_instance or not session.client_instance.start_client:
            result = loop.run_until_complete(init_socket(session))

        if session.client_instance and (result is not False):
            result = loop.run_until_complete(
                send_socket_message(session, message, command, type_id, module_id)
            )
    except KeyboardInterrupt:
        result = False
        log.debug(f"[{session.dwarf_uid}] KeyboardInterrupt received. Stopping gracefully 4.")
    finally:
        loop.close()

    return result


def disconnect_socket(session: DwarfSession):
    """Mirrors websockets_utils.disconnect_socket(), scoped to `session`."""
    if session.client_instance and hasattr(session.client_instance, "task"):
        future = asyncio.run_coroutine_threadsafe(
            session.client_instance.disconnect(), session.client_instance.task.get_loop()
        )
        log.notice(f"[{session.dwarf_uid}] Disconnect signal sent to the client instance.")
        try:
            future.result(timeout=5)
        except concurrent.futures.TimeoutError:
            log.warning(
                f"[{session.dwarf_uid}] Disconnect did not complete within 5s "
                "(device unreachable or slow WS close handshake) - forcing shutdown anyway."
            )
            future.cancel()
        except Exception as e:
            log.warning(f"[{session.dwarf_uid}] Disconnect raised an exception, forcing shutdown anyway: {e}")
        stop_event_loop(session)
    else:
        log.warning(f"[{session.dwarf_uid}] Client not started")


def stop_event_loop(session: DwarfSession):
    """Mirrors websockets_utils.stop_event_loop(), scoped to `session`.

    PROPOSED FIX (not yet hardware-validated - see the module docstring's
    warning about not "cleaning up" this branching logic without
    re-testing on real devices): previously this went straight to
    `loop.stop()` + `thread.join()`. If disconnect_socket()'s 5s timeout
    had already fired (slow/unresponsive device), `client.task` (the
    WebSocketClient.start() coroutine) could still be mid-unwind when
    the loop was yanked out from under it - it would then only get
    cleaned up later by the garbage collector, producing "Task was
    destroyed but it is pending!" and, since the loop was never
    explicitly closed either, "RuntimeError: Event loop is closed"
    inside that GC-time cleanup. Harmless in a short-lived script that
    exits right after (which is why this never showed up before), but
    noisy - and a real resource leak - in a long-running UI that
    connects/disconnects repeatedly.

    This version gives the pending task one short, bounded chance
    (2s) to actually finish cancelling on ITS OWN loop before stopping
    that loop, and closes the loop explicitly afterward instead of
    leaving that to __del__.
    """
    if session.event_loop:
        client = session.client_instance
        task = getattr(client, "task", None) if client is not None else None
        if task is not None and not task.done():
            async def _drain_task():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await task

            try:
                future = asyncio.run_coroutine_threadsafe(_drain_task(), session.event_loop)
                future.result(timeout=2)
            except Exception as e:
                log.warning(
                    f"[{session.dwarf_uid}] Could not drain pending task before "
                    f"shutdown (proceeding anyway): {e}"
                )

        session.event_loop.call_soon_threadsafe(session.event_loop.stop)
        if session.event_loop_thread:
            session.event_loop_thread.join()

        try:
            session.event_loop.close()
        except Exception as e:
            log.warning(f"[{session.dwarf_uid}] Error closing event loop: {e}")

        log.debug(f"[{session.dwarf_uid}] Event loop and thread stopped.")
        session.client_instance = None


def get_camera_param_v3(session: DwarfSession, param_id):
    """Session-scoped mirror of websockets_utils.get_camera_param_v3().

    The underlying cache (cameraParamsDwarf) is already a per-instance
    dict on WebSocketClient - not a real global - so this only needed to
    stop reading the module-level `client_instance` global and read
    `session.client_instance` instead. No cache restructuring required."""
    if session.client_instance is None:
        return None
    return session.client_instance.cameraParamsDwarf.get(param_id)


def get_client_status(session: DwarfSession):
    """Mirrors websockets_utils.get_client_status(), scoped to `session`.

    Uses session.previous_values / session.lock instead of the global
    previous_values dict, so two sessions polled concurrently never mix up
    each other's "what changed since last poll" state."""
    client = session.client_instance

    if client is None:
        return {"error": "Dwarf is not connected"}

    status = {
        "HostMode": client.InitHostReceived,
        "takePhotoStarted": client.takePhotoStarted,
        "takeWidePhotoStarted": client.takeWidePhotoStarted,
        "AstroCapture": client.AstroCapture,
        "AstroWideCapture": client.AstroWideCapture,
        "startEQSolving": client.startEQSolving,
        "takePhotoCount": client.takePhotoCount,
        "takePhotoStacked": client.takePhotoStacked,
        "takeWidePhotoCount": client.takeWidePhotoCount,
        "takeWidePhotoStacked": client.takeWidePhotoStacked,
        "ErrorConnection": client.ErrorConnection,
        "BatteryLevelDwarf": client.BatteryLevelDwarf,
        "availableSizeDwarf": client.availableSizeDwarf,
        "totalSizeDwarf": client.totalSizeDwarf,
        "TemperatureLevelDwarf": client.TemperatureLevelDwarf,
        "CmosTemperatureDwarf": client.CmosTemperatureDwarf,
        "StreamTypeDwarf": client.StreamTypeDwarf,
        "StreamTypeByCamera": client.StreamTypeByCamera,
        "needsContinueShooting": client.needsContinueShooting,
        "eqAziErr": client.eqAziErr,
        "eqAltErr": client.eqAltErr,
        "FocusValueDwarf": client.FocusValueDwarf,
        "PowerIndicatorDwarf": client.PowerIndStateDwarf,
        "RgbIndicatorDwarf": client.RgbIndStateDwarf,
        "CameraParamsDwarf": client.cameraParamsDwarf,
    }

    with session.lock:
        previous_values = session.previous_values
        new_values = {}
        has_new_values = False

        for key, value in status.items():
            if key not in previous_values or previous_values[key] != value:
                new_values[key] = value
                has_new_values = True

        session.previous_values = status.copy()

    return {"hasNewValues": has_new_values, "fullStatus": status, "newValues": new_values}
