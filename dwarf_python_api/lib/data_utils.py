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
            {"index": 87, "name": "1/1320"},
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
            {"index": 87, "name": "1/1320"},
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
            {"index": 162, "name": "60"}
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

