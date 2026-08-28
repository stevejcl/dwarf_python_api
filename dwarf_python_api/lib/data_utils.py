class AllowedExposures:
    def __init__(self):
        self.default_value_index = 75
        self.values = [
            {"index": 0, "name": "1/10000"},
            {"index": 3, "name": "1/8000"},
            {"index": 6, "name": "1/6400"},
            {"index": 9, "name": "1/5000"},
            {"index": 12, "name": "1/4000"},
            {"index": 15, "name": "1/3200"},
            {"index": 18, "name": "1/2500"},
            {"index": 21, "name": "1/2000"},
            {"index": 24, "name": "1/1600"},
            {"index": 27, "name": "1/1250"},
            {"index": 30, "name": "1/1000"},
            {"index": 33, "name": "1/800"},
            {"index": 36, "name": "1/640"},
            {"index": 39, "name": "1/500"},
            {"index": 42, "name": "1/400"},
            {"index": 45, "name": "1/320"},
            {"index": 48, "name": "1/250"},
            {"index": 51, "name": "1/200"},
            {"index": 54, "name": "1/160"},
            {"index": 57, "name": "1/125"},
            {"index": 60, "name": "1/100"},
            {"index": 63, "name": "1/80"},
            {"index": 66, "name": "1/60"},
            {"index": 69, "name": "1/50"},
            {"index": 72, "name": "1/40"},
            {"index": 75, "name": "1/30"},
            {"index": 78, "name": "1/25"},
            {"index": 81, "name": "1/20"},
            {"index": 84, "name": "1/15"},
            {"index": 87, "name": "1/13"},
            {"index": 90, "name": "1/10"},
            {"index": 93, "name": "1/8"},
            {"index": 96, "name": "1/6"},
            {"index": 99, "name": "1/5"},
            {"index": 102, "name": "1/4"},
            {"index": 105, "name": "1/3"},
            {"index": 108, "name": "0.4"},
            {"index": 111, "name": "0.5"}, 
            {"index": 114, "name": "0.6"},
            {"index": 117, "name": "0.8"},
            {"index": 120, "name": "1"},
            {"index": 123, "name": "1.3"},
            {"index": 126, "name": "1.6"},
            {"index": 129, "name": "2"},
            {"index": 132, "name": "2.5"},
            {"index": 135, "name": "3.2"},
            {"index": 138, "name": "4"},
            {"index": 141, "name": "5"},
            {"index": 144, "name": "6"},
            {"index": 147, "name": "8"},
            {"index": 150, "name": "10"},
            {"index": 153, "name": "13"},
            {"index": 156, "name": "15"}
        ]

class AllowedExposuresD3:
    def __init__(self):
        self.default_value_index = 75
        self.values = [
            {"index": 0, "name": "1/10000"},
            {"index": 3, "name": "1/8000"},
            {"index": 6, "name": "1/6400"},
            {"index": 9, "name": "1/5000"},
            {"index": 12, "name": "1/4000"},
            {"index": 15, "name": "1/3200"},
            {"index": 18, "name": "1/2500"},
            {"index": 21, "name": "1/2000"},
            {"index": 24, "name": "1/1600"},
            {"index": 27, "name": "1/1250"},
            {"index": 30, "name": "1/1000"},
            {"index": 33, "name": "1/800"},
            {"index": 36, "name": "1/640"},
            {"index": 39, "name": "1/500"},
            {"index": 42, "name": "1/400"},
            {"index": 45, "name": "1/320"},
            {"index": 48, "name": "1/250"},
            {"index": 51, "name": "1/200"},
            {"index": 54, "name": "1/160"},
            {"index": 57, "name": "1/125"},
            {"index": 60, "name": "1/100"},
            {"index": 63, "name": "1/80"},
            {"index": 66, "name": "1/60"},
            {"index": 69, "name": "1/50"},
            {"index": 72, "name": "1/40"},
            {"index": 75, "name": "1/30"},
            {"index": 78, "name": "1/25"},
            {"index": 81, "name": "1/20"},
            {"index": 84, "name": "1/15"},
            {"index": 87, "name": "1/13"},
            {"index": 90, "name": "1/10"},
            {"index": 93, "name": "1/8"},
            {"index": 96, "name": "1/6"},
            {"index": 99, "name": "1/5"},
            {"index": 102, "name": "1/4"},
            {"index": 105, "name": "1/3"},
            {"index": 108, "name": "0.4"},
            {"index": 111, "name": "0.5"}, 
            {"index": 114, "name": "0.6"},
            {"index": 117, "name": "0.8"},
            {"index": 120, "name": "1"},
            {"index": 123, "name": "1.3"},
            {"index": 126, "name": "1.6"},
            {"index": 129, "name": "2"},
            {"index": 132, "name": "2.5"},
            {"index": 135, "name": "3.2"},
            {"index": 138, "name": "4"},
            {"index": 141, "name": "5"},
            {"index": 144, "name": "6"},
            {"index": 147, "name": "8"},
            {"index": 150, "name": "10"},
            {"index": 153, "name": "13"},
            {"index": 156, "name": "15"},
            {"index": 159, "name": "30"},
            {"index": 160, "name": "45"},
            {"index": 162, "name": "60"},
            {"index": 163, "name": "90"},
            {"index": 165, "name": "120"},
            {"index": 168, "name": "180"}
        ]

def get_exposure_name_by_index(index, dwarf_type = "2"):
    if (dwarf_type == "3"):
        found_option = next((option for option in allowed_exposuresD3.values if option["index"] == index), None)
    else:
        found_option = next((option for option in allowed_exposures.values if option["index"] == index), None)
    return found_option["name"] if found_option else "Auto"

def get_exposure_value_by_index(index, dwarf_type = "2"):
    name = get_exposure_name_by_index(index, dwarf_type)
    return 1 if name == "Auto" else eval(name)

def get_exposure_index_by_name(name, dwarf_type = "2"):
    found_option = False
    if (dwarf_type == "3"):
        found_option = next((option for option in allowed_exposuresD3.values if option["name"] == name), None)
        default_value_index = allowed_exposuresD3.default_value_index
    else:
        found_option = next((option for option in allowed_exposures.values if option["name"] == name), None)
        default_value_index = allowed_exposures.default_value_index
    return found_option["index"] if found_option else default_value_index

class AllowedGains:
    def __init__(self):
        self.default_value_index = 0
        self.values = [
            {"index": 0, "name": "0"},
            {"index": 3, "name": "10"},
            {"index": 6, "name": "20"},
            {"index": 9, "name": "30"},
            {"index": 12, "name": "40"},
            {"index": 15, "name": "50"},
            {"index": 18, "name": "60"},
            {"index": 21, "name": "70"},
            {"index": 24, "name": "80"},
            {"index": 27, "name": "90"},
            {"index": 30, "name": "100"},
            {"index": 33, "name": "110"},
            {"index": 36, "name": "120"},
            {"index": 39, "name": "130"},
            {"index": 42, "name": "140"},
            {"index": 45, "name": "150"},
            {"index": 48, "name": "160"},
            {"index": 51, "name": "170"},
            {"index": 54, "name": "180"},
            {"index": 57, "name": "190"},
            {"index": 60, "name": "200"},
            {"index": 63, "name": "210"},
            {"index": 66, "name": "220"},
            {"index": 69, "name": "230"},
            {"index": 72, "name": "240"}
        ]

class AllowedGainsD3:
    def __init__(self):
        self.default_value_index = 0
        self.values = [
            {"index": 0, "name": "0"},
            {"index": 1, "name": "2"},
            {"index": 2, "name": "5"},
            {"index": 3, "name": "10"},
            {"index": 6, "name": "20"},
            {"index": 9, "name": "30"},
            {"index": 12, "name": "40"},
            {"index": 15, "name": "50"},
            {"index": 18, "name": "60"},
            {"index": 21, "name": "70"},
            {"index": 24, "name": "80"},
            {"index": 27, "name": "90"},
            {"index": 30, "name": "100"},
            {"index": 33, "name": "110"},
            {"index": 36, "name": "120"},
            {"index": 39, "name": "130"},
            {"index": 42, "name": "140"},
            {"index": 45, "name": "150"},
            {"index": 48, "name": "160"},
            {"index": 51, "name": "170"},
            {"index": 54, "name": "180"},
            {"index": 57, "name": "190"},
            {"index": 60, "name": "200"},
            {"index": 63, "name": "210"},
            {"index": 66, "name": "220"},
            {"index": 69, "name": "230"},
            {"index": 72, "name": "240"}
        ]

def get_gain_name_by_index(index, dwarf_type = "2"):
    if (dwarf_type == "3"):
        found_option = next((option for option in allowed_gainsD3.values if option["index"] == index), None)
    else:
        found_option = next((option for option in allowed_gains.values if option["index"] == index), None)
    return found_option["name"] if found_option else "Auto"

def get_gain_index_by_name(name, dwarf_type = "2"):
    found_option = False
    if (dwarf_type == "3"):
        found_option = next((option for option in allowed_gainsD3.values if option["name"] == name), None)
        default_value_index = allowed_gainsD3.default_value_index
    else:
        found_option = next((option for option in allowed_gains.values if option["name"] == name), None)
        default_value_index = allowed_gains.default_value_index
    return found_option["index"] if found_option else default_value_index

# Example usage:
allowed_exposures = AllowedExposures()
allowed_gains = AllowedGains()

allowed_exposuresD3 = AllowedExposuresD3()
allowed_gainsD3 = AllowedGainsD3()


# ---------------------------------------------------------------------------
# V3 : tables extraites du code source officiel (data_dwarf3_config.ts /
# data_utils.ts, fournis par l'utilisateur) - source d'autorite pour les
# noms et l'ordre des options, communes a Dwarf II/3/Mini sauf mention
# contraire. Voir MIGRATION_V3.md pour le detail de l'encodage V3 confirme
# ou suppose pour chacune (index de table vs valeur brute).


class AllowedGainsWide:
    """WIDE-ANGLE camera gain - table NEVER SEEN BEFORE, very different
    from the tele camera: range 0-2500 (vs 0-240 for tele), confirmed by
    the live HTTP API shootingMode/getParamAndSetting (modeId=1, cameraId=1)."""
    def __init__(self):
        self.default_value_index = 0
        self.values = [
            {"index": i, "name": str(v)} for i, v in enumerate([
                40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160,
                170, 180, 190, 200, 210, 220, 230, 240, 250, 300, 350, 400,
                450, 500, 550, 600, 650, 700, 1000, 1300, 1600, 1900, 2200, 2500,
            ])
        ]
        # Note: unlike the other tables in this file, "index" here is just
        # the position in the list (0,1,2,...), NOT a step of 3 or a
        # meaningful value for the protocol - the live API only provides a
        # flat "values" list for this field, with no separate index
        # concept (see MIGRATION_V3.md).

class AllowedWBTemp:
    """White balance, "manual Kelvin temperature" mode. The "preset" mode
    (Fluorescent/Incandescent/...) uses a different encoding, see
    AllowedWBPreset below and perform_set_wb_preset_by_name_v3()."""
    def __init__(self):
        self.default_value_index = 51
        self.values = [
            {"index": i * 3, "name": str(2800 + i * 100)} for i in range(47)
        ]

class AllowedWBPreset:
    """White balance, "preset" mode (mode=2 in ReqSetWb). Official table
    (data_dwarf3_config.ts, provided by the user), confirmed by network
    capture: the sequence of values sent while cycling through the first 4
    presets shown in the app (Incandescent, Fluorescent, Warm Fluorescent,
    Sunlight) gives exactly value=0,2,1,3 - consistent with this table
    ("index" below = raw value sent to the protocol, which does NOT follow
    the app's display order - see note further down)."""
    def __init__(self):
        self.default_value_index = 0
        self.values = [
            {"index": 0, "name": "Incandescent"},
            {"index": 1, "name": "Warm Fluorescent"},
            {"index": 2, "name": "Fluorescent"},
            {"index": 3, "name": "Sunlight"},
            {"index": 4, "name": "Cloudy"},
            {"index": 5, "name": "Shadow"},
            {"index": 6, "name": "Twilight"},
        ]

# Note: the display order in the V3 app's UI (as observed by the user) is
# "Incandescent, Fluorescent, Warm Fluorescent, Sunlight, Cloudy, Twilight,
# Shadow" - DIFFERENT from the table order above (index 0 to 6). Only the
# index/raw value matters for the protocol; the app's display order does
# not need to be reproduced here.

class AllowedIRFilter:
    """IR/Astro filter. Confirmed by the official config file
    (camera.supportParams id=8), only 3 options, no intermediate step
    (index = position)."""
    def __init__(self):
        self.default_value_index = 0
        self.values = [
            {"index": 0, "name": "VIS Filter"},
            {"index": 1, "name": "Astro Filter"},
            {"index": 2, "name": "Duo-Band Filter"},
        ]

class AllowedBurstCount:
    """Number of photos in a burst (featureParams id=3). WARNING: the V3
    encoding (this table's index, or a raw value?) is NOT confirmed - see
    MIGRATION_V3.md, the V3 param_id corresponding to this table has not
    been identified with certainty (PARAM_ID_BURST_SETTING actually seems
    to correspond to the interval, not the count - see
    AllowedBurstInterval)."""
    def __init__(self):
        self.default_value_index = 0
        self.values = [
            {"index": 0, "name": "3"}, {"index": 3, "name": "5"},
            {"index": 6, "name": "10"}, {"index": 9, "name": "15"},
            {"index": 12, "name": "20"}, {"index": 15, "name": "30"},
            {"index": 18, "name": "40"}, {"index": 21, "name": "50"},
            {"index": 24, "name": "60"}, {"index": 27, "name": "70"},
            {"index": 30, "name": "80"}, {"index": 33, "name": "90"},
            {"index": 36, "name": "100"}, {"index": 39, "name": "120"},
            {"index": 42, "name": "150"}, {"index": 45, "name": "200"},
            {"index": 48, "name": "300"}, {"index": 51, "name": "400"},
            {"index": 54, "name": "500"}, {"index": 57, "name": "600"},
            {"index": 60, "name": "700"}, {"index": 63, "name": "900"},
            {"index": 66, "name": "1000"},
        ]

class AllowedBurstInterval:
    """Interval between two shots of a burst (featureParams id=9).
    Confirmed by network capture: the V3 value sent (PARAM_ID_BURST_SETTING)
    is the RAW number of seconds (not this table's index) - use
    get_burst_interval_seconds_by_name() to convert a name to seconds."""
    def __init__(self):
        self.default_value_index = 0
        self.values = [
            {"index": 0, "name": "Off"}, {"index": 1, "name": "1 s"},
            {"index": 3, "name": "2 s"}, {"index": 6, "name": "3 s"},
            {"index": 9, "name": "4 s"}, {"index": 12, "name": "5 s"},
            {"index": 15, "name": "8 s"}, {"index": 18, "name": "10 s"},
            {"index": 21, "name": "15 s"}, {"index": 24, "name": "20 s"},
            {"index": 27, "name": "25 s"}, {"index": 30, "name": "30 s"},
            {"index": 33, "name": "60 s"},
        ]

class AllowedTimelapseInterval:
    """Interval between two shots of a timelapse (featureParams id=4).
    Confirmed by network capture (V3 value = raw seconds, not the index):
    the last value sent (4) matches exactly the 'interval' field of the
    CMD_NOTIFY_TIMELAPSE_OUT_TIME notifications received during execution.
    Use get_timelapse_interval_seconds_by_name()."""
    def __init__(self):
        self.default_value_index = 0
        self.values = [
            {"index": 0, "name": "0.5 s"}, {"index": 1, "name": "1 s"},
            {"index": 3, "name": "2 s"}, {"index": 6, "name": "3 s"},
            {"index": 9, "name": "4 s"}, {"index": 12, "name": "5 s"},
            {"index": 15, "name": "8 s"}, {"index": 18, "name": "10 s"},
            {"index": 21, "name": "15 s"}, {"index": 24, "name": "20 s"},
            {"index": 27, "name": "25 s"}, {"index": 30, "name": "30 s"},
            {"index": 33, "name": "60 s"},
        ]

class AllowedTimelapseTotalTime:
    """Total duration of the timelapse (featureParams id=5). V3 value very
    likely in raw seconds (0=unlimited?) - consistent with the values
    observed in the capture (2400=40min, 120=2min). Use
    get_timelapse_totaltime_seconds_by_name()."""
    def __init__(self):
        self.default_value_index = 3
        self.values = [
            {"index": 3, "name": "\u221e"}, {"index": 4, "name": "2 min"},
            {"index": 6, "name": "5 min"}, {"index": 9, "name": "8 min"},
            {"index": 12, "name": "10 min"}, {"index": 15, "name": "20 min"},
            {"index": 18, "name": "30 min"}, {"index": 21, "name": "40 min"},
            {"index": 24, "name": "50 min"}, {"index": 27, "name": "60 min"},
            {"index": 30, "name": "120 min"}, {"index": 33, "name": "180 min"},
            {"index": 36, "name": "240 min"}, {"index": 39, "name": "300 min"},
        ]

allowed_wb_temp = AllowedWBTemp()
allowed_gains_wide = AllowedGainsWide()
allowed_wb_preset = AllowedWBPreset()
allowed_ir_filter = AllowedIRFilter()
allowed_burst_count = AllowedBurstCount()
allowed_burst_interval = AllowedBurstInterval()
allowed_timelapse_interval = AllowedTimelapseInterval()
allowed_timelapse_totaltime = AllowedTimelapseTotalTime()


def get_wide_gain_v3_index_by_name(name):
    """WIDE-ANGLE camera gain - returns the numeric value directly (not a
    table index in the sense of the other get_*_index_by_name functions
    in this file: see AllowedGainsWide)."""
    found = next((o for o in allowed_gains_wide.values if o["name"] == str(name)), None)
    return int(found["name"]) if found else 0


def get_wb_preset_index_by_name(name):
    found = next((o for o in allowed_wb_preset.values if o["name"] == name), None)
    return found["index"] if found else allowed_wb_preset.default_value_index


def get_ir_filter_index_by_name(name):
    found = next((o for o in allowed_ir_filter.values if o["name"] == name), None)
    return found["index"] if found else allowed_ir_filter.default_value_index


def _parse_seconds_from_name(name):
    """'4 s' -> 4 ; '0.5 s' -> 0.5 ; 'Off' -> 0."""
    if name is None:
        return 0
    text = str(name).strip()
    if text.lower() == "off":
        return 0
    text = text.replace("s", "").strip()
    try:
        value = float(text)
        return int(value) if value == int(value) else value
    except ValueError:
        return 0


def _parse_seconds_from_minutes_name(name):
    """'2 min' -> 120 ; '\u221e' (infinity) -> 0."""
    if name is None:
        return 0
    text = str(name).strip()
    if text in ("\u221e", "inf", "infinite", "unlimited"):
        return 0
    text = text.replace("min", "").strip()
    try:
        return int(float(text) * 60)
    except ValueError:
        return 0


def get_burst_interval_seconds_by_name(name):
    """Name from the AllowedBurstInterval table ('4 s', 'Off', ...) -> raw
    seconds expected by the V3 protocol (see PARAM_ID_BURST_SETTING)."""
    return _parse_seconds_from_name(name)


def get_timelapse_interval_seconds_by_name(name):
    """Name from the AllowedTimelapseInterval table -> raw seconds expected
    by the V3 protocol (see PARAM_ID_TIMELAPSE_INTERVAL)."""
    return _parse_seconds_from_name(name)


def get_timelapse_totaltime_seconds_by_name(name):
    """Name from the AllowedTimelapseTotalTime table ('2 min', '\u221e',
    ...) -> raw seconds expected by the V3 protocol (see
    PARAM_ID_TIMELAPSE_DURATION). '\u221e' (unlimited) -> 0."""
    return _parse_seconds_from_minutes_name(name)
