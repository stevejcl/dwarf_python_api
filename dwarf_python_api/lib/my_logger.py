# import data for config.py
import logging
import types
import os
import sys
# import data for config.py
import dwarf_python_api.get_config_data

# Define logger instance and initial variables
logger = logging.getLogger('my_logger')
file_handler = None  # Initialize file_handler as None
log_file = None  # Initialize log_file as None

# Define custom NOTICE and SUCCESS logging level
NOTICE_LEVEL_NUM = 22
SUCCESS_LEVEL_NUM = 25

# Custom success logging method
def notice(self, message, *args, **kwargs):
    if self.isEnabledFor(NOTICE_LEVEL_NUM):
        # We must pass args explicitly as a tuple to avoid the missing argument error
        self._log(NOTICE_LEVEL_NUM, message, args, **kwargs)

logging.Logger.notice = notice  # Add notice method to logger class

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        # We must pass args explicitly as a tuple to avoid the missing argument error
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)

logging.Logger.success = success  # Add success method to logger class

# --- Shared-log thread exclusion (additive, multi-Dwarf support) -----------
# A caller (e.g. the UI) that has already given a specific thread its own
# dedicated, filtered log handler can register that thread here so the
# shared/global file_handler below stops ALSO capturing its output. This
# module stays UI-agnostic - it just tracks thread idents to skip, with no
# knowledge of what "scheduler" or "session" means.
_shared_log_excluded_threads = set()


def exclude_thread_from_shared_log(thread_ident):
    """Stop the shared/global log file (update_log_file()'s file_handler)
    from also capturing this thread's records - use once that thread has
    its own dedicated handler, to avoid duplicate/cross-contaminated
    entries when multiple threads log concurrently."""
    _shared_log_excluded_threads.add(thread_ident)


def include_thread_in_shared_log(thread_ident):
    """Undo exclude_thread_from_shared_log() once the thread's own
    dedicated handler is no longer in use (e.g. it has stopped)."""
    _shared_log_excluded_threads.discard(thread_ident)


class _SharedLogThreadFilter(logging.Filter):
    """Attached to the shared/global file_handler - drops records from any
    thread that has registered its own dedicated handler via
    exclude_thread_from_shared_log(), so the shared file doesn't also pick
    up a copy of output that's already fully captured elsewhere."""
    def filter(self, record):
        return record.thread not in _shared_log_excluded_threads


# --- Per-thread device tagging (additive, multi-Dwarf support) -------------
# Most low-level protocol log lines (receive_messages, ping/pong, frame
# decoding...) live deep inside WebSocketClient's async methods, which
# don't have a dwarf_uid string handy to embed in an f-string by hand -
# there are hundreds of call sites, so editing each one isn't practical.
# What they DO all share is the THREAD they run on: session.event_loop_
# thread, one persistent background thread per physical Dwarf (see
# dwarf_session_socket.py's init_socket()). Registering that thread's
# ident here tags every record it produces with the device label, so a
# SHARED log file can still be told apart per device with a simple grep/
# search - without needing separate log files (see
# exclude_thread_from_shared_log() above for that alternative).
_thread_device_labels: dict[int, str] = {}


def register_thread_device_label(thread_ident, label):
    """Tag every future log record from this thread with `label`
    (typically a dwarf_uid). Call this once you know which physical
    device a given thread belongs to - e.g. right after a session's
    event_loop_thread is created/confirmed alive."""
    _thread_device_labels[thread_ident] = label


def unregister_thread_device_label(thread_ident):
    """Undo register_thread_device_label() once that thread has stopped
    (e.g. after a disconnect) so a later, unrelated thread that happens
    to reuse the same ident doesn't inherit a stale label."""
    _thread_device_labels.pop(thread_ident, None)


class _DeviceLabelFilter(logging.Filter):
    """Attaches a `device` attribute to every record (used by the format
    strings below as %(device)s) - "[label] " for a thread registered via
    register_thread_device_label(), or "" otherwise. Always returns True:
    this filter only annotates records, it never drops any (that's
    _SharedLogThreadFilter's job, on the file handler specifically)."""
    def filter(self, record):
        label = _thread_device_labels.get(record.thread)
        record.device = f"[{label}] " if label else ""
        return True

# --- Previous logs kept on restart -----------------------------------------
# (user-reported Oct 2026: the app restarted twice in a night, the second
# start's rotation overwrote <log>.old - the session that went wrong was
# lost). Several generations: <log>.old the last run, <log>.old.2 the one
# before... up to LOG_BACKUPS.
LOG_BACKUPS = 5
# Once per launch (user-reported Oct 2026: at each start the first rotation
# made the .old, a second one replaced it with an empty log). The native
# window's process (multiprocessing, spawned: it re-imports this module and
# re-runs setup_logger()) rotated the file the main process had just opened -
# on Windows the rename of an open file fails and shutil.move falls back to a
# copy: the fresh, empty log copied over the .old. Only the first process
# rotates (the variable is inherited by its children); os.replace never copies.
_ROTATED_ENV = "DWARF_PYTHON_API_LOGS_ROTATED"


def _main_process():
    try:
        import multiprocessing
        return multiprocessing.parent_process() is None
    except Exception:
        return True


def _rotate(path, backups=None):
    """Moves `path` to <path>.old, after shifting the earlier backups
    (<path>.old -> <path>.old.2 ... the oldest dropped). Once per file and
    per launch, in the main process only (see _ROTATED_ENV)."""
    backups = LOG_BACKUPS if backups is None else backups
    key = os.path.abspath(path)
    done = [p for p in os.environ.get(_ROTATED_ENV, "").split(os.pathsep) if p]
    if key in done or not _main_process():
        return
    os.environ[_ROTATED_ENV] = os.pathsep.join(done + [key])
    if not os.path.exists(path):
        return

    def name(n):
        return f"{path}.old" if n == 1 else f"{path}.old.{n}"

    try:
        if os.path.exists(name(backups)):
            os.remove(name(backups))
        for n in range(backups - 1, 0, -1):
            if os.path.exists(name(n)):
                os.replace(name(n), name(n + 1))
        os.replace(path, name(1))
    except Exception as e:
        print(f"Error moving log file {path}: {e}")


# --- Separate file for unmatched/untreated notification frames -------------
# (user-requested Sep 2026, after tracing a misleading "bad UTF-8" warning
# to websockets_utils.py's fallback branch for frames whose cmd matched no
# known handler: "on risque d'en avoir beaucoup, notification non traite
# par exemple" - these can fire often, on perfectly normal traffic, and
# aren't actionable day-to-day, so they'd otherwise drown out the real
# signal in the main log). Lazily created on first use, in its own child
# logger with propagate=False so it never ALSO lands in the shared log
# file or console - only this dedicated file.
_unmatched_frame_logger = None


def log_unmatched_frame(message: str) -> None:
    """Logs to <main log file's basename>.err (or "unmatched_frames.err"
    if no main log file is configured at the time of the FIRST call -
    this only reads log_file once, lazily; it does not track later
    update_log_file() renames, which is an acceptable simplification for
    a low-stakes diagnostic file). Callers: websockets_utils.py's
    fallback handling for notification/response frames whose cmd matched
    nothing else in that if/elif chain.

    Rotated to <path>.old on restart (user-requested Sep 2026: "les logs
    vont etre enorme sinon" - unlike the main log, EVERY unmatched frame
    lands here, on perfectly normal traffic, so this file can grow much
    faster across repeated sessions) - same one-generation backup as
    update_log_file()'s own log_file + '.old' handling, not a rotating
    series of many backups - several since Oct 2026, see _rotate())."""
    global _unmatched_frame_logger
    if _unmatched_frame_logger is None:
        base = log_file if log_file else "unmatched_frames"
        err_path = os.path.splitext(base)[0] + ".err"
        _rotate(err_path)
        _unmatched_frame_logger = logging.getLogger("my_logger.unmatched_frames")
        _unmatched_frame_logger.setLevel(logging.DEBUG)
        _unmatched_frame_logger.propagate = False
        handler = logging.FileHandler(err_path)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(device)s%(message)s"))
        handler.addFilter(_SharedLogThreadFilter())
        handler.addFilter(_DeviceLabelFilter())
        _unmatched_frame_logger.addHandler(handler)
    _unmatched_frame_logger.debug(message)


# Function to update or create the log file handler
def update_log_file(default_name: str = "app.log"):
    """
    Dynamically update or create the log file handler.

    `default_name`: this is a GENERIC library, reused by several
    standalone tools (main_v3.py, get_live_data_dwarf.py, ...) besides
    astro_dwarf_ui - it has no business hardcoding any ONE application's
    own naming convention. "app.log" is a neutral library-level default,
    used only when no config.py value is present at all AND the caller
    hasn't specified its own preference. An APPLICATION that wants a
    specific name (e.g. astro_dwarf_ui wanting "astro_session.log")
    should pass its own default_name explicitly - see astro_dwarf_ui.py's
    own startup call - rather than this library assuming any one app's
    convention for everyone (user-corrected Sep 2026: an earlier version
    of this fix hardcoded "astro_session.log" directly in here, which
    is exactly the kind of app-specific detail a generic library
    shouldn't own).
    """
    global log_file  # To update the global variable
    global file_handler  # To reference the existing file handler

    # Reload configuration data
    data_config = dwarf_python_api.get_config_data.get_config_data()

    # Determine the new log file
    # BUG FIX (user-reported Sep 2026): when no config.py is found at
    # all, get_config_data() falls back to log_file=None (a genuinely
    # MISSING value), not "" (an empty-but-present value) - the ""
    # check below correctly defaults THAT case to a real filename, but
    # None fell through to the final else, silently setting
    # new_log_file to None too, which the later `if log_file is not
    # None:` guard reads as "logging explicitly disabled" (the SAME as
    # data_config['log_file'] == "False") - conflating "no config file
    # present at all" with "user explicitly turned logging off" and
    # skipping file creation entirely, with no error/warning to explain
    # why. Both "" and None (not just "") now fall back to default_name.
    #
    # Follow-up (Sep 2026, user-reported): this whole function is
    # process-wide, not per-device - get_config_data() with no
    # explicit path looks for a single root-level config.py, which
    # doesn't exist in the multi-device layout (each device has its
    # own config_<slug>.py/.ini instead - see pages/pairing.py). That's
    # not a bug to fix here though: pages/logs.py's own module
    # docstring confirms the INTENDED design is one shared log file for
    # the whole process (every line already tagged with a "[dwarf_uid]"
    # prefix), not one file per device - so this function correctly has
    # no device-specific config to read, regardless of how many devices
    # are paired. What name that ONE shared file gets, absent a config.py
    # override, is the CALLER's choice (default_name), not this
    # library's to assume - see this function's own docstring.
    if data_config['log_file'] == "False":
        new_log_file = None
    elif not data_config['log_file']:  # "" or None
        new_log_file = default_name
    else:
        new_log_file = data_config['log_file']

    # Check if the log file has changed
    if new_log_file != log_file:
        log_file = new_log_file

        # Remove the existing file handler if it exists
        if file_handler and file_handler in logger.handlers:
            logger.removeHandler(file_handler)
            file_handler.close()  # Close the old file handler

        # Add the new file handler if log_file is not None
        if log_file is not None:
            try:
                # Backup old log files if they exist (.old, .old.2 ...)
                _rotate(log_file)

                # Determine file log level based on 'debug' in data_config
                file_log_level = logging.DEBUG if data_config.get('debug') else logging.INFO
                print(f"file_log_level: {file_log_level}")

                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(file_log_level)
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(device)s%(message)s'))
                file_handler.addFilter(_SharedLogThreadFilter())
                logger.addHandler(file_handler)
                logger.notice(f"Log file updated to: {log_file}")
            except Exception as e:
                logger.error(f"Failed to update log file: {e}")
        else:
            logger.info("Log file disabled.")

# Initial logger setup
def setup_logger():
    """
    Initialize the logger and configure handlers.
    """
    global logger

    # Set logger level to NOTSET, allowing handlers to filter logs
    logging.getLogger().setLevel(logging.NOTSET)  # Allow handlers to manage levels independently

    # Reload configuration data
    data_config = dwarf_python_api.get_config_data.get_config_data()

    # Set root logger level
    root_level = logging.DEBUG if data_config.get('debug') else logging.INFO
    logger.setLevel(root_level)
    print(f"root_level: {root_level}")

    # Add console logging handler separately
    console_handler = logging.StreamHandler()
    console_handle_level = logging.INFO if data_config.get('trace') else NOTICE_LEVEL_NUM
    if data_config['log_file'] == "False":
        console_handle_level = logging.DEBUG if data_config.get('debug') else logging.INFO

    console_handler.setLevel(console_handle_level)
    console_handler.setFormatter(logging.Formatter('%(device)s%(message)s'))
    logger.addHandler(console_handler)

    # Add custom log levels
    logging.addLevelName(NOTICE_LEVEL_NUM, 'NOTICE')
    logging.addLevelName(SUCCESS_LEVEL_NUM, 'SUCCESS')

    # Bind custom log methods to the logger
    logger.notice = types.MethodType(notice, logger)
    logger.success = types.MethodType(success, logger)

    # Tags every record with its device label (see
    # register_thread_device_label() above) before ANY handler sees it -
    # added once, here, rather than per-handler, so console and file
    # output both benefit without duplicating the filter.
    logger.addFilter(_DeviceLabelFilter())

    # Configure the log file handler using `update_log_file`
    update_log_file()

# Call the setup_logger function when the module is imported
setup_logger()

def debug(*messages):
    for message in messages:
        logger.debug(message) 

def error(*messages):
    for message in messages:
        logger.error(message) 

def warning(*messages):
    for message in messages:
        logger.warning(message) 

def info(*messages):
    for message in messages:
        logger.info(message) 

def notice(*messages):
    for message in messages:
        logger.notice(message)

def success(*messages):
    for message in messages:
        logger.success(message)