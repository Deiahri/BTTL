from response import Response
import requests, json, Log, os, Keys

find_place_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
place_id_url = "https://maps.googleapis.com/maps/api/place/details/json"
geocoder_url = "https://maps.googleapis.com/maps/api/geocode/json"

data_dir = "data"

keyword_file_extension = "kw"


class Keyword:
    def __init__(self, key: str, value: str, source="", keyword_id="-1"):
        self.key = key.strip()
        self.value = value
        self.source = source

        if keyword_id == "-1":
            self.id = get_next_id("keyword")
        else:
            self.id = keyword_id

    def get_keyword(self):
        return self.key

    def get_value(self):
        return self.value

    def get_source(self):
        return self.source

    def delete(self):
        try:
            os.remove(f"{data_dir}/keyword/{str(self.id).zfill(12)}.{keyword_file_extension}")
            return True
        except Exception as e:
            print(e)
            print(f"Could not delete {str(self.id).zfill(12)}.{keyword_file_extension}")
            Log.message(f"Could not delete {str(self.id).zfill(12)}.{keyword_file_extension}")
            return False

    def save(self):
        keyword_dict = {
            "key": self.key,
            "value": self.value,
            "source": self.source
        }
        if self.id == "-1":
            id_str = get_next_id("keyword")
            self.id = get_next_id("keyword")
        else:
            id_str = f"{self.id}".zfill(12)
        with open(f"{data_dir}/keyword/{id_str}.kw", "w") as keyword_file:
            json.dump(keyword_dict, keyword_file, indent=4)
        return True


def load_keyword_w_id(keyword_id):
    id_str = f"{keyword_id}".zfill(12)
    keyword_file_names = os.listdir(f"{data_dir}/keyword")
    keyword_data = {}
    for keyword_file_name in keyword_file_names:
        if keyword_file_name == f"{id_str}.kw":
            try:
                # it will try to open and read json data from file.
                # Will fail if json data is not formatted correctly
                with open(f"{data_dir}/keyword/{keyword_file_name}") as keyword_file:
                    keyword_data = json.load(keyword_file)
                break
            except json.decoder.JSONDecodeError:
                Log.message(f"\"{data_dir}/keyword/{keyword_file_name}\" contains invalid json data")

    if not keyword_data:
        # keyword_id file does not exist
        return False

    # create new keyword object using keyword_data
    key_obj = Keyword(keyword_data.get("key"), keyword_data.get("value"), keyword_data.get("source"), id_str)
    return key_obj


def load_keyword_w_name(keyword_name):
    keyword_file_names = os.listdir(f"{data_dir}/keyword")
    for keyword_file_name in keyword_file_names:
        with open(f"{data_dir}/keyword/{keyword_file_name}") as current_keyword_file:
            keyword_data = json.load(current_keyword_file)
            if keyword_data.get("key") == keyword_name:
                k = Keyword(keyword_data.get("key"), keyword_data.get("value"), keyword_data.get("source"),
                            keyword_file_name[0:-3])
                return k
    return False


class Address:
    def __init__(self, address: str = ""):
        self.origin = address.strip()
        self.type = ""  # can be either exact or keyword
        self.keyword = ""  # defined if type is keyword
        self.lat = 0.0
        self.lng = 0.0
        try:
            self.valid = self.validate()
        except Exception as e:
            self.valid = Response(False, f"Something went wrong while trying to validate address {address}")
            Log.error(e)

    def validate(self):
        if not len(self.origin) == 0:
            if self.origin[0] == "!":
                if len(self.origin) == 1:
                    return Response(False, "! should only be used when using a keyword.")
                self.type = "keyword"
                self.keyword = self.origin[1:]
                return Response(True)
            elif self.origin[0] == "@":
                return Response(False, f"Mixing of existing routes is not supported in this version of BTTL "
                                       f"(\"{self.origin}\")")

            self.type = "exact"

            address = self.origin

            geocoder_json = {
                "address": address,
                "key": Keys.geocoder_key
            }
            geocoder_response = requests.get(geocoder_url, params=geocoder_json)
            geocoder_response.raise_for_status()
            # geocode_json = {
            #     "input": address,
            #     "inputtype": "textquery",
            #     "fields": "formatted_address",
            #     "key": Keys.geocoder_key
            # }
            # response = requests.get(f"{find_place_url}", params=geocode_json)
            # response.raise_for_status()
            # place_id_response = requests.get(place_id_url, params=place_id_json)
            # with open("temp2.txt", "w") as file:
            #     json.dump(response.json(), file, indent=4)
            geocoder_response_json = geocoder_response.json()
            if geocoder_response_json.get("status") == "ZERO_RESULTS":
                return Response(False, f"Address \"{address}\" is not a valid address. "
                                       f"Make sure the address is exact or else results may be incorrect")
            else:
                latlng = geocoder_response_json["results"][0]["geometry"]["location"]
                self.lat = latlng["lat"]
                self.lng = latlng["lng"]
                return Response(True)
        else:
            return Response(False)

    def to_json(self):
        return {
            "origin": self.origin,
            "type": self.type,
            "keyword": self.keyword,
            "lat": self.lat,
            "lng": self.lng
        }

    def equal(self, address_2):
        if self.x == address_2.x:
            if self.y == address_2.y:
                return True
        return False

    def __str__(self):
        if self.type == "exact":
            return f"Address: lat: {self.lat} | lng: {self.lng} | valid: ({self.valid})"
        elif self.type == "keyword":
            return f"Keyword: {self.keyword} | lat: {self.lat} | lng: {self.lng} | valid: ({self.valid})"

    @staticmethod
    def from_json(address_json: dict):
        address_obj = Address()
        address_obj.origin = address_json.get("origin")
        address_obj.type = address_json.get("type")
        address_obj.keyword = address_json.get("keyword")
        address_obj.lat = address_json.get("lat")
        address_obj.lng = address_json.get("lng")
        address_obj.valid = Response(True)
        return address_obj


route_file_extension = "rt"


class Route:
    def __init__(self, key: str, addresses: list[Address], compiled_modifiers: list, search_estimate: dict, source: str,
                 route_id: str = "-1"):
        self.key = key
        self.addresses = addresses
        self.compiled_modifiers = compiled_modifiers
        self.search_estimate = search_estimate
        self.source = source
        self.route_id = route_id

    def save(self):
        # convert modifiers into json objects.
        # after, have load convert those json objects back into modifiers.
        json_addresses = []
        for address in self.addresses:
            json_addresses.append(address.to_json())
        route_dict = {
            "key": self.key,
            "addresses": json_addresses,
            "compiled_modifiers": self.compiled_modifiers,
            "search_estimate": self.search_estimate,
            "source": self.source
        }
        if self.route_id == "-1":
            self.route_id = get_next_id("route")
        else:
            self.route_id = f"{self.route_id}".zfill(12)

        with open(f"{data_dir}/route/{self.route_id}.rt", "w") as route_file:
            json.dump(route_dict, route_file, indent=4)

    def delete(self):
        try:
            os.remove(f"{data_dir}/route/{str(self.route_id).zfill(12)}.{route_file_extension}")
            return True
        except Exception as e:
            print(f"Could not delete {str(self.route_id).zfill(12)}.{route_file_extension}")
            Log.message(f"Could not delete {str(self.route_id).zfill(12)}.{route_file_extension}")
            return False


def load_route_w_id(route_id):
    target_route_file_id = f"{route_id}".zfill(12)
    route_file_names = os.listdir(f"{data_dir}/route")

    route_data = {}
    for route_file_name in route_file_names:
        if route_file_name == f"{target_route_file_id}.rt":
            with open(f"{data_dir}/route/{route_file_name}") as route_file:
                route_data = json.load(route_file)
            break

    if not route_data:
        # given route_id does not have a corresponding file
        return False

    address_objs = []
    # converts the address json to an address object
    for address_data in route_data.get('addresses'):
        current_address = Address.from_json(address_data)
        address_objs.append(current_address)

    route_obj = Route(route_data.get("key"), address_objs, route_data.get("compiled_modifiers"),
                      route_data.get("search_estimate"), route_data.get("source"), target_route_file_id)
    return route_obj


def load_route_w_name(route_name):
    target_route_file_id = f"{route_name}".zfill(12)
    route_file_names = os.listdir(f"{data_dir}/route")

    for route_file_name in route_file_names:
        with open(f"{data_dir}/route/{route_file_name}") as route_file:
            route_data = json.load(route_file)
            if route_data.get("key") == route_name:
                route_obj = Route(route_data.get("key"), route_data.get("addresses"),
                                  route_data.get("compiled_modifiers"), route_data.get("search_estimate"),
                                  route_data.get("source"), target_route_file_id)
                return route_obj
    return False


def get_next_id(dir_name):
    dir_name = dir_name.lower()
    if dir_name == "keyword":
        file_extension = ".kw"
        current_dir = f"{data_dir}/keyword"
    elif dir_name == "route":
        file_extension = ".rt"
        current_dir = f"{data_dir}/route"
    else:
        print("unexpected dir_name")
        return False

    last_id = -1
    for keyword_file in os.listdir(current_dir):
        if keyword_file.__contains__(file_extension):
            number_part = keyword_file[0:keyword_file.index(file_extension)]
            if number_part.isnumeric():
                if int(number_part) > last_id:
                    last_id = int(number_part)
    return f"{last_id+1}".zfill(12)


class Modifier:
    modifier_dict = {
        "travelMode": ["DRIVE", "BICYCLE", "WALK", "TWO_WHEELER", "TRANSIT"],
        # routingPreference always on traffic_aware or traffic_aware_optimal (need to test which is better)
        "routeModifiers": ["avoidTolls", "avoidHighways", "avoidFerries", "avoidIndoor"],
        "requestedReferenceRoute": ["FUEL_EFFICIENT"],
        "time_zone": ["CST"]
        # I will consider departureTime differently
    }

    vehicle_prefixes = ["via", "on", "in", "with", "by", "avoid"]
    negative_prefixes = ["without", "no", "avoid", "don't", "not"]

    synonyms_dict = {
        "DRIVE": ["car"],
        "BICYCLE": ["bike", "tricycle", "unicycle", "on unicycle", "cycle", "velocipede"],
        "WALK": ["foot", "hike", "trek"],
        "TWO_WHEELER": ["motor bike", "motorbike", "motor cycle", "motorcycle", "chopper", "scooter", "moped",
                        "dirtbike", "dirt bike"],
        "TRANSIT": ["bus", "metro", "subway", "shuttle", "busses", "metros", "subways", "shuttles"],
        # TRANSIT IS TRICKY, AS THERE IS A WAY TO SPECIFY BUS, TRAIN, SUBWAY, ETC.

        "Tolls": ["tolls", "toll"],  # negative is avoidTolls
        "Highways": ["highway", "high way"],  # negative is avoidHighways
        "Ferries": ["ferry", "ferry boat", "ferrys"],  # negative is avoidFerries
        "Indoor": ["inside", "in door", "indoors", "in doors"],  # negative is avoidIndoors
        "FUEL_EFFICIENT": ["save fuel", "fuel efficient", "fuel efficient route"],
        # Time zone synonyms
        "CST": ["central"],
        "EST": ["eastern"],
    }

    def __init__(self, modifier: str):
        self.origin = modifier.strip().lower()
        self.type = ""  # type will be either travelMode, routeModifiers, or requestedReferenceRoute
        self.value = ""
        self.negative = False
        self.valid = self.__validate()

    def __validate(self):
        current_modifier_type = ""
        current_modifier_value = ""
        modifier = self.origin
        done = False
        for modifier_type in Modifier.modifier_dict:
            if done:
                break
            for modifier_subtype in Modifier.modifier_dict.get(modifier_type):
                if done:
                    break
                if modifier.__contains__(modifier_subtype.lower()):
                    current_modifier_type = modifier_type
                    current_modifier_value = modifier_subtype
                    done = True
                else:
                    # sees if equal to synonym of modifier_subtype
                    if modifier_subtype.__contains__("avoid"):
                        modifier_subtype = modifier_subtype.removeprefix("avoid")
                    for modifier_subtype_synonym in Modifier.synonyms_dict.get(modifier_subtype):
                        if modifier.__contains__(modifier_subtype_synonym):
                            current_modifier_type = modifier_type
                            current_modifier_value = modifier_subtype

        # checks first time to see if a modifier type and value was not determined yet
        # if so, it may, possibly, be a date modifier.
        if not current_modifier_type and not current_modifier_value:
            time_mod = Time(modifier)
            if time_mod.valid.value:
                self.type = "time"
                self.value = time_mod
                return Response(True)
            else:
                if time_mod.valid.message:
                    return time_mod.valid

        if not current_modifier_type:
            current_modifier_type = "None"
            return Response(False, f"modifier \"{modifier}\" is invalid")
        if not current_modifier_value:
            current_modifier_value = "None"
            return Response(False, f"modifier \"{modifier}\" is invalid")

        self.type = current_modifier_type
        self.negative = self.detect_negative()
        if current_modifier_value == "Tolls" or current_modifier_value == "Highways" or \
                current_modifier_value == "Ferries" or current_modifier_value == "Indoor":
            current_modifier_value = "avoid" + current_modifier_value
            self.negative = not self.detect_negative()
        self.value = current_modifier_value
        return Response(True)

    def detect_negative(self):
        modifier_split = self.origin.split(" ")
        if len(modifier_split) > 1:
            for negative_prefix in Modifier.negative_prefixes:
                if modifier_split[0] == negative_prefix:
                    return True
        return False

    def __str__(self):
        return f"type: {self.type} | value: {self.value} | negative: {self.negative} | valid: ({self.valid})"


class Time:
    end_char = "┘"
    month_min = {
        "january": "jan",
        "february": "feb",
        "march": "mar",
        "april": "apr",
        "may": "may",
        "june": "jun",
        "july": "jul",
        "august": "aug",
        "september": "sep",
        "october": "oct",
        "november": "nov",
        "december": "dec"
    }
    day_of_week_min = {
        "monday": "mon",
        "tuesday": "tue",
        "wednesday": "wed",
        "thursday": "thu",
        "friday": "fri",
        "saturday": "sat",
        "sunday": "sun"
    }

    relative_day_min = {
        "yesterday": "yest",
        "today": "toda",
        "tomorrow": "tomo",
    }

    then = ["then"]
    negative = ["not"]
    ignorable = ["from", "and", "of", "at"]
    through_keywords = ['through', "to", "-"]
    time_periods = ["am", "pm"]
    all = ["all", "everything"]

    ENTRY_LEVEL_KEY = "time_entry_levels"
    ENTRY_LEVEL_YEAR = "4"
    ENTRY_LEVEL_MONTH = "3"
    ENTRY_LEVEL_WEEK = "2"
    ENTRY_LEVEL_DAY = "1"
    ENTRY_LEVEL_RELATIVE_DAY = "1R"
    ENTRY_LEVEL_DAY_OF_WEEK = "1W"
    ENTRY_LEVEL_TIME = "0"
    ENTRY_LEVEL_AMBIGUOUS = "-1"
    ENTRY_LEVEL_AMBIGUOUS_POSITION = "-1p"
    ENTRY_LEVEL_AMBIGUOUS_NUMBER = "-1n"

    def __init__(self, time_str: str):
        self.source = time_str.lower().strip()
        self.data = []
        self.data_types = []
        self.valid = self.__validate()

    def __validate(self):
        """Takes in a modifier string and determines if all parts of it are valid time modifiers while also
            separating those parts and storing the data and data types into a respective arrays."""
        response = Response(True)
        source = self.source+Time.end_char
        current = ""
        stage = "0"
        for char in source:
            if char == Time.end_char:
                # confirms and applies current upon reaching the end of the string
                if current:
                    valid_response = self.confirm_and_apply(current)
                    if not valid_response.value:
                        response = valid_response
                        break
            elif char == "-":
                # confirms and applies current, and afterwards confirms and applies "-"
                if current:
                    valid_response = self.confirm_and_apply(current)
                    if not valid_response.value:
                        response = valid_response
                        break
                self.confirm_and_apply(char)
                stage = "0"
                current = ""
            elif char.isspace():
                # confirms and applies current upon reaching a space
                if current:
                    valid_response = self.confirm_and_apply(current)
                    if not valid_response.value:
                        response = valid_response
                        break
                stage = "0"
                current = ""
            elif stage == "0":
                # determine if we are currently on a letter or number
                current += char
                if char.isalpha():
                    stage = "1"
                elif char.isdigit():
                    stage = "2"
                else:
                    response = Response(False, f"Did not expect \"{char}\" in \"{source}\"")
                    break
            elif stage == "1":
                # stage for when an alphabet letter is detected in stage 0
                if char.isalpha():
                    current += char
                    pass
                elif char.isdigit():
                    # detects a number. Submits whatever
                    valid_response = self.confirm_and_apply(current)
                    if not valid_response.value:
                        response = valid_response
                        break
                    current = char
                    stage = "2"
                else:
                    response = Response(False, f"Did not expect \"{char}\" in \"{current}\"")
                    break
            elif stage == "2":
                # stage for when a number was detected in stage 0
                if char.isdigit():
                    current += char
                    pass
                elif char == ":":
                    current += char
                    pass
                elif char.isalpha():
                    valid_response = self.confirm_and_apply(current)
                    if not valid_response.value:
                        response = valid_response
                        break
                    current = char
                    stage = "1"

        if len(self.data) == 0:
            response = Response(False)

        return response

    def confirm_and_apply(self, time_chunk):
        """Determines what type of data time_chunk is and puts it into the object's data array\n\n
            Types: Year, Num, Time, Literal(week, day, month, year), after, before, position, month(february), ignorable
            negative(not), then, time_period (am pm), through, day_of_week(wednesday), relative_day (tomorrow)"""
        try:
            int(time_chunk)
            if len(time_chunk) >= 4:
                self.apply(int(time_chunk), "year")
            else:
                self.apply(int(time_chunk), "num")
        except Exception:
            if is_time(time_chunk).value:
                self.apply(time_chunk, "time")
            elif is_time(time_chunk).message:
                # received a message from is_time. Only partially correct times will return a message (NN: NN:NNN etc)
                return is_time(time_chunk)
            elif time_chunk == "week":
                self.apply(time_chunk, "literal")
            elif time_chunk == "day":
                self.apply(time_chunk, "literal")
            elif time_chunk == "month":
                self.apply(time_chunk, "literal")
            elif time_chunk == "year":
                self.apply(time_chunk, "literal")
            elif time_chunk == "after":
                self.apply(time_chunk, "after")
            elif time_chunk == "before":
                self.apply(time_chunk, "before")
            elif is_position(time_chunk):
                self.apply(time_chunk, "position")
            elif self.is_month(time_chunk):
                self.apply(self.is_month(time_chunk), "month")
            elif self.is_ignorable(time_chunk):
                self.apply(time_chunk, "ignorable")
            elif self.is_negative(time_chunk):
                self.apply(time_chunk, "negative")
            elif self.is_then(time_chunk):
                self.apply(time_chunk, "then")
            elif self.is_time_period(time_chunk):
                self.apply(time_chunk, "time_period")
            elif self.is_through(time_chunk):
                self.apply(time_chunk, "through")
            elif self.is_day_of_week(time_chunk):
                self.apply(self.is_day_of_week(time_chunk), "day_of_week")
            elif self.is_relative_day(time_chunk):
                self.apply(self.is_relative_day(time_chunk), "relative_day")
            elif self.is_all(time_chunk):
                self.apply(self.is_all(time_chunk), "all")
            else:
                return Response(False, f"Did not understand \"{time_chunk}\" in \"{self.source}\"")

        return Response(True)

    def apply(self, data, data_type):
        """Takes in data and that data's type and stores it in respective arrays (One for data and one of data type)\n\n
            This is used by the Time_Compiler class when computing the command's time range."""
        self.data.append(data)
        self.data_types.append(data_type)

    def is_all(self, potential_all):
        for all_keyword in self.all:
            if potential_all == all_keyword:
                return "all"
        return False

    def is_then(self, potential_then):
        """Returns true if potential_then is a value in Time.them"""
        for then in self.then:
            if potential_then == then:
                return True
        return False

    def is_negative(self, potential_negative):
        """Returns true if potential_negative is equal to a value in Time.negative"""
        for negative in self.negative:
            if potential_negative == negative:
                return True
        return False

    def is_day_of_week(self, potential_dow):
        """If the first three letters are equal to a value in Time.day_of_week_min, returns the matching key"""
        first_three = potential_dow[:3]
        for dow in self.day_of_week_min:
            if first_three == self.day_of_week_min[dow]:
                return dow
        return False

    def is_relative_day(self, potential_relative_day):
        """if the first four letters is equal to a value in Time.relative_day_min, returns the matching key"""
        first_four = potential_relative_day[:4]
        for relative_day in self.relative_day_min:
            if first_four == self.relative_day_min[relative_day]:
                return relative_day
        return False

    def is_time_period(self, time_chunk):
        """Returns true if string is equal to a value in Time.time_periods"""
        for time_period in self.time_periods:
            if time_chunk == time_period:
                return True
        return False

    def is_through(self, potential_through):
        """Returns true if string is equal to a value in Time.through_keywords"""
        for through in self.through_keywords:
            if potential_through == through:
                return True
        return False

    def is_ignorable(self, potential_ignorable):
        """Returns true if value is a value in Time.ignorable.\n
        Returns false otherwise"""
        for ignorable in self.ignorable:
            if potential_ignorable == ignorable:
                return True
        return False

    def is_month(self, potential_month):
        """if the first three letters of potential month is equal to any value in month_min, returns the matching key\n
        Returns false otherwise"""
        first_three = potential_month[:3]
        for month in self.month_min:
            if first_three == self.month_min[month]:
                return month
        return False

    def __str__(self):
        str_arr = []
        for index in range(len(self.data)):
            str_arr.append(f"{self.data[index]}({self.data_types[index]})")
        return f"{str_arr}"


def is_position(string):
    """Returns True if string is a position string (st, nd, rd, th), False otherwise"""
    if string == "st" or string == "nd" or string == "rd" or string == "th":
        return True
    return False


def is_time(string):
    """Given a string,\n
    return true RESPONSE if string is of format NN:NN or N:NN\n
    returns false RESPONSE with a message if of format N: NN: N:NNN... NN:NNN... etc\n
    and returns false Response without message if of any other format"""
    stage = "0"
    for char in string:
        if stage == "0":
            #
            if char.isdigit():
                stage = "1"
            else:
                break
        elif stage == "1":
            # N
            if char.isdigit():
                stage = "2"
            elif char == ":":
                stage = "3"
            else:
                break
        elif stage == "2":
            # NN
            if char == ":":
                stage = "3"
            else:
                break
        elif stage == "3":
            # NN: or N:
            if char.isdigit():
                stage = "4"
            else:
                break
        elif stage == "4":
            # NN:N or N:N
            if char.isdigit():
                stage = "5"
            else:
                break
        elif stage == "5":
            # NN:NN or N:NN (This is the only valid final state)
            stage = "6"
            break

    if stage == "5":
        # value given was either NN:NN or N:NN
        return Response(True)
    elif int(stage[0]) >= 3:
        # the value given was partially a valid time string, but was incorrect
        return Response(False, f"{string} is not a valid time (NN:NN or N:NN)")
    else:
        # the value given was not partially valid.
        return Response(False)


max_day = {
    "january": 31,
    "february": 28,
    "march": 31,
    "april": 30,
    "may": 31,
    "june": 30,
    "july": 31,
    "august": 31,
    "september": 30,
    "october": 31,
    "november": 30,
    "december": 31
}


def days_in_month(month, year=2000):
    leap = (year % 4 == 0)
    if month == "february":
        if leap:
            return 29

    month_days = max_day.get(month.lower())
    if month_days:
        return month_days
    else:
        Log.message(f"Component's days_in_month method received {month}, which is not a valid month.")
        return 30


def validate_month_day_range(data_chunk={}):
    """Confirms that the date range given is valid. It uses data_chunk,
        a subset of data from the data produced by modifier_compiler.compile()"""
    days = data_chunk.get('num')
    if days:
        for month in data_chunk.get("month"):
            for day in days:
                if day == "-":
                    continue
                elif max_day.get(month) < int(day):
                    return Response(False, f"{month} does not have {day} days")
                elif day < 1:
                    return Response(False, f"{month} does not contain a day less than 1. You put {day}")
    time_data = data_chunk.get("time")
    if time_data:
        last_time = None
        through = False
        for time_data_chunk in time_data:
            if last_time is None:
                last_time = time_data_chunk
            elif time_data_chunk == "-":
                through = True
            else:
                if through:
                    comparison_result = compare_time(last_time, time_data_chunk)
                    if comparison_result == -1:
                        # last time is greater than the current time.
                        return Response(False, f"Invalid time range: {last_time}-{time_data_chunk}. The first time "
                                               f"cannot be greater than the last time. (FIRST TIME-LAST TIME)")
                    elif comparison_result == 0:
                        return Response(False, f"{last_time}-{time_data_chunk} is redundant. Only {last_time} is "
                                               f"sufficient")
                    else:
                        through = False
    return Response(True)


def compare_time(time_1, time_2):
    """Returns -1 if time_1 is greater. Returns 1 if time_2 is greater. Returns 0 if equal"""
    time_1_abs = time_to_24hr(time_1)
    time_2_abs = time_to_24hr(time_2)

    if time_1_abs[0] > time_2_abs[0]:
        return -1
    elif time_2_abs[0] > time_1_abs[0]:
        return 1
    else:
        if time_1_abs[1] > time_2_abs[1]:
            return -1
        elif time_2_abs[1] > time_1_abs[1]:
            return 1
        else:
            return 0


def time_to_24hr(time_1):
    """Receives time as a string in the format HH:MM or H:MM, followed possibly by am or pm.
        Returns the time as an array [HH, MM] adjusted for am or pm (pm results in HH+12)"""
    time_1_abs = []

    colon_index1 = time_1.index(":")
    time_1_abs.append(int(time_1[0:colon_index1]))
    time_1_abs.append(int(time_1[colon_index1 + 1:colon_index1 + 3]))

    if time_1[-1] == "m":
        if time_1[-2:] == "pm":
            time_1_abs[0] += 12

    return time_1_abs


# s = Time("september 11th 1981 from 9:00pm - 8:00am Tuesday and Tomorrow after 2nd week and 36th year month day then "
#          "august before monday and after March 3rd")
# print(s.valid)
# for index in range(0, len(s.data)):
#     print(f"{s.data[index]}: {s.data_types[index]}")
#
# t = Time("4th and 5th week of may")
# print("--------------")
# for current_level in t.temp_data:
#     print(current_level)
# print("--------------")
# print(t.valid)
#
# u = Time("Tomorrow from 4:55pm to 3:00am")
# print("--------------")
# for current_level in u.temp_data:
#     print(current_level)
# print("--------------")
# print(u.valid)
