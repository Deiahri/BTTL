from response import Response
import requests, json, Log

find_place_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
place_id_url = "https://maps.googleapis.com/maps/api/place/details/json"
geocoder_url = "https://maps.googleapis.com/maps/api/geocode/json"


class Address:
    def __init__(self, address: str):
        self.origin = address
        self.lat = 0.0
        self.lng = 0.0
        self.address_text = ""
        try:
            self.valid = self.validate()
        except Exception as e:
            self.valid = Response(False, f"Something went wrong while trying to validate address {address}")
            Log.error(e)

    def validate(self):
        # ambiguous will be for addresses such as "mcdonald's"
        # ambiguous should only be used when a relative address is given.
        address = self.origin

        geocoder_json = {
            "address": address,
            "key": "AIzaSyCr_g_kZtEwlHDpoMxBOPuk-7A7B_SGG2M"
        }
        geocoder_response = requests.get(geocoder_url, params=geocoder_json)
        geocoder_response.raise_for_status()
        # geocode_json = {
        #     "input": address,
        #     "inputtype": "textquery",
        #     "fields": "formatted_address",
        #     "key": "AIzaSyCr_g_kZtEwlHDpoMxBOPuk-7A7B_SGG2M"
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
            self.address_text = geocoder_response_json["results"][0]["formatted_address"]
            return Response(True)

    def equal(self, address_2):
        if self.x == address_2.x:
            if self.y == address_2.y:
                return True
        return False

    def __str__(self):
        return f"Address: {self.address_text} | lat: {self.lat} | lng: {self.lng} | valid: ({self.valid})"


class Modifier:
    modifier_dict = {
        "travelMode": ["DRIVE", "BICYCLE", "WALK", "TWO_WHEELER", "TRANSIT"],
        # routingPreference always on traffic_aware or traffic_aware_optimal (need to test which is better)
        "routeModifiers": ["avoidTolls", "avoidHighways", "avoidFerries", "avoidIndoor"],
        "requestedReferenceRoute": ["FUEL_EFFICIENT"]
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

        "Tolls": ["tolls"],  # negative is avoidTolls
        "Highways": ["highway", "high way"],  # negative is avoidHighways
        "Ferries": ["ferry", "ferry boat", "ferrys"],  # negative is avoidFerries
        "Indoor": ["inside", "in door", "indoors", "in doors"],  # negative is avoidIndoors
        "FUEL_EFFICIENT": ["save fuel", "fuel efficient", "fuel efficient route"]
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
        self.time_str = time_str.lower().strip()
        self.time_dic = []
        self.level = 0
        self.temp_data = [{}]
        self.valid = self.__validate()
        if not self.temp_data[0]:
            self.valid = Response(False)
        self.simplify()

    def __validate(self):
        time_str = self.time_str.replace(",", "") + Time.end_char  # note: time_str should never contain commas
        current = ""
        stage = "0"
        for char in time_str:
            if char == self.end_char:
                apply_response = self.apply(current)
                if not apply_response.value:
                    return apply_response
            elif is_illegal_modifier_character(char):
                return Response(False, f"Modifier \"{self.time_str}\" contains illegal character \"{char}\"")
            elif char.isspace():
                if current:
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                    current = ""
                    stage = "0"
            elif char == "-":
                if current:
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                self.apply(char)
                current = ""
                stage = "0"

            elif stage == "0":
                if char.isdigit():
                    current += char
                    stage = "1"
                elif char.isalpha():
                    current += char
                    stage = "11"
            elif stage == "1":
                if char.isdigit():
                    current += char
                    stage = "4"
                elif char == ":":
                    current += char
                    stage = "5"
                elif char.isalpha():
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                    current = char
                    stage = "11"
                else:
                    return Response(False, f"Did not expect {char} at stage {stage}")
            elif stage == "4":
                if char.isdigit():
                    current += char
                    stage = "4"
                elif char.isalpha():
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                    current = char
                    stage = "11"
                elif char == ":":
                    current += char
                    stage = "5"
            elif stage == "5":
                # recieved 2 numbers followed by : (should be a time)
                if char.isdigit():
                    current += char
                    stage = "6"
                else:
                    return Response(False, f"Expected 2 more numbers after {current}. Received {char}")
            elif stage == "6":
                # recieved 2 numbers, : and a number. Expecting one more
                if char.isdigit():
                    current += char
                    stage = "7"
                else:
                    return Response(False, f"Expected 1 more number after {current}. Received {char}")
            elif stage == "7":
                if char.isdigit():
                    return Response(False, f"Got more numbers than expected after {current}. Received {char}")
                elif char.isalpha():
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                    current = char
                    stage = "11"
                else:
                    return Response(False, f"Did not expect to receive {char} after {current}")
            elif stage == "11":
                # one-letter word
                if char.isdigit():
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                    current = char
                    stage = "1"
                elif char.isalpha():
                    current += char
                    stage = "12"
                else:
                    return Response(False, f"Was not expecting {char} in stage {stage}")
            elif stage == "12":
                # two-letter word
                if char.isnumeric():
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                    current = char
                    stage = "1"
                elif char.isalpha():
                    current += char
                    stage = "13"
                else:
                    return Response(False, f"Was not expecting {char} in stage {stage}")
            elif stage == "13":
                # three-letter word
                if char.isalpha():
                    current += char
                    stage = "15"
                elif char.isalpha():
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                    current = char
                    stage = "11"
                elif char.isnumeric():
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                    current = char
                    stage = "1"
                else:
                    return Response(False, f"Was not expecting {char} in stage {stage}")
            elif stage == "15":
                # four-letter word
                if char.isalpha():
                    current += char
                    stage = "16"
                elif char.isnumeric():
                    apply_response = self.apply(current)
                    if not apply_response.value:
                        return apply_response
                else:
                    return Response(False, f"Was not expecting {char} in stage {stage}")
            elif stage == "16":
                # five-or-more-letter word
                if char.isalpha():
                    current += char

        return Response(True)

    def apply(self, value):
        # Entry levels: Year = 4, Month = 3, Week = 2, Day = 1, Time = 0
        # print(self.temp_data)
        # print(f"applying: {value}")
        value_type = self.determine_level(value)
        self.solve_conflicts_with_current_level(value_type)
        level = self.level
        has_entry_level = True

        print(f"apply = {level} : {value}")

        if type(value_type) is Response:
            return value_type
        elif value_type == Time.ENTRY_LEVEL_YEAR:
            self.insert_temp("year", value, level)
        elif value_type == Time.ENTRY_LEVEL_AMBIGUOUS_NUMBER:
            self.insert_temp("num", value, level)
        elif value_type == Time.ENTRY_LEVEL_TIME:
            self.insert_temp(f"time", value, level)
            self.insert_temp(f"time_type", "24hr", level)
        elif value_type == "am_pm":
            if self.temp_data[level].get("time_period"):
                return Response(False, f"Received {value} after {self.temp_data[level].get('time_period')}")
            if self.temp_data[level].get("num"):
                self.insert_temp("time", num_to_time(self.temp_data[level].pop("num")), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_TIME, number=True)
            self.insert_temp("time_period", value, level)
            self.insert_temp("time_type", "12hr", level)
        elif value_type == "position":
            if self.temp_data[level].get("num"):
                self.insert_temp("position", self.temp_data[level].pop("num"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_AMBIGUOUS_POSITION, number=True)
                has_entry_level = False
                # this version pops ONLY the last number and converts it into a position.
                # self.insert_temp("position", self.temp_data[level]["num"].pop(len(self.temp_data[level]["num"])-1)
                # , level)
            else:
                return Response(False, f"Received {value} without context")
        elif value_type == Time.ENTRY_LEVEL_RELATIVE_DAY:
            relative_days = self.temp_data[level].get("relative_day")
            if relative_days:
                if relative_days.__contains__(self.is_relative_day(value)):
                    return Response(False, f"Received {self.is_relative_day(value)} twice")
            self.insert_temp("relative_day", value, level)
        elif value_type == "month":
            value_type = Time.ENTRY_LEVEL_MONTH
            if self.temp_data[level].get("num"):
                self.insert_temp(f"month", self.temp_data[level].pop("num"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_MONTH)
            elif self.temp_data[level].get("position"):
                self.insert_temp(f"month", self.temp_data[level].pop("position"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_MONTH)
            else:
                has_entry_level = False
                insert_response = self.insert_temp("type", value, level)
                if not insert_response.value:
                    return insert_response
            has_entry_level = False
        elif value_type == Time.ENTRY_LEVEL_WEEK:
            if self.temp_data[level].get("num"):
                self.insert_temp("week", self.temp_data[level].pop("num"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_WEEK)
            elif self.temp_data[level].get("position"):
                self.insert_temp("week", self.temp_data[level].pop("position"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_WEEK)
            else:
                has_entry_level = False
                insert_response = self.insert_temp("type", value, level)
                if not insert_response.value:
                    return insert_response
            has_entry_level = False
        elif value_type == Time.ENTRY_LEVEL_DAY:
            if self.temp_data[level].get("num"):
                self.insert_temp("day", self.temp_data[level].pop("num"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_DAY)
            elif self.temp_data[level].get("position"):
                self.insert_temp("day", self.temp_data[level].pop("position"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_DAY)
            else:
                has_entry_level = False
                insert_response = self.insert_temp("type", value, level)
                if not insert_response.value:
                    return insert_response
            has_entry_level = False
        elif value_type == "next":
            if self.temp_data[level].get("next"):
                return Response(False, "Already receieved the word \"Next\".")
            self.insert_temp("next", True, level)
        elif value_type == Time.ENTRY_LEVEL_MONTH:
            # value == january, feb, marc, apr, etc.
            self.insert_temp("month", self.is_month(value), level)
        elif value_type == Time.ENTRY_LEVEL_DAY_OF_WEEK:
            # value == mon, tuesday, wedne, thursd, etc.
            self.insert_temp("day_of_week", self.is_day_of_week(value), level)
        elif value_type == Time.ENTRY_LEVEL_YEAR:
            if self.temp_data[level].get("num"):
                self.insert_temp(f"year", self.temp_data[level].pop("num"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_YEAR)
            elif self.temp_data[level].get("position"):
                self.insert_temp(f"year", self.temp_data[level].pop("position"), level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_YEAR)
            else:
                has_entry_level = False
                insert_response = self.insert_temp("type", value, level)
                if not insert_response.value:
                    return insert_response
            has_entry_level = False
        elif value_type == "ignorable":
            pass
        elif value_type == "through":
            if self.temp_data[level].get("through"):
                return Response(False, f"Through was mentioned twice in modifier \"{self.time_str}\"")
            self.temp_data[level]["through"] = True
            self.next_level()
        else:
            return Response(False, f"Modifier part \"{value}\" in \"{self.time_str}\" not understood.")

        if has_entry_level:
            # this part deals only with the entry_level array
            if not value_type == "ignorable" and not value_type == "through" and not value_type == "next" and\
                    not value_type == "am_pm":
                self.insert_temp(Time.ENTRY_LEVEL_KEY, value_type, level)

        return Response(True)

    def change_ambiguous_entry_levels(self, level, new_level, **kwargs):
        entry_level_ambiguous = ""
        if kwargs.get("position"):
            entry_level_ambiguous = Time.ENTRY_LEVEL_AMBIGUOUS_POSITION
        if kwargs.get("number"):
            if entry_level_ambiguous:
                entry_level_ambiguous = Time.ENTRY_LEVEL_AMBIGUOUS
            else:
                entry_level_ambiguous = Time.ENTRY_LEVEL_AMBIGUOUS_NUMBER
        if not entry_level_ambiguous:
            entry_level_ambiguous = Time.ENTRY_LEVEL_AMBIGUOUS

        entry_levels = self.temp_data[level][Time.ENTRY_LEVEL_KEY]
        for index in range(0, len(entry_levels)):
            # print(self.temp_data[level][Time.ENTRY_LEVEL_KEY][index])
            if entry_levels[index].__contains__(entry_level_ambiguous):
                self.temp_data[level][Time.ENTRY_LEVEL_KEY][index] = new_level

    def solve_conflicts_with_current_level(self, value_level):
        conflict = False
        need_to_check = True
        entry_levels = self.temp_data[self.level].get(Time.ENTRY_LEVEL_KEY)
        if not entry_levels or len(entry_levels) < 2:
            return
        direction = ""
        last_value = -5
        value_level_modified = ""  # some value levels can be -1a or -1p etc. value_level_modified will not have letter

        if value_level[0] == "-":
            if value_level[1].isdigit():
                value_level_modified = value_level[:2]
        elif value_level[0].isdigit():
            value_level_modified = value_level[0]
        else:
            need_to_check = False

        if value_level == entry_levels[len(entry_levels)-1]:
            need_to_check = False
        print(f"Entry levels: {self.temp_data[self.level][self.ENTRY_LEVEL_KEY]} | {need_to_check} | {value_level}")
        if need_to_check:
            for entry_index in range(len(entry_levels)):
                if direction:
                    break
                if last_value == -5:
                    last_value = parse_integer(entry_levels[len(entry_levels) - 1 - entry_index])
                else:
                    entry_level_dif = parse_integer(entry_levels[len(entry_levels) - 1 - entry_index]) - last_value
                    if entry_level_dif == 0:
                        # this will never happen, as this condition is handled just before this for-loop
                        last_value = parse_integer(entry_levels[len(entry_levels) - 1 - entry_index])
                    elif entry_level_dif > 0:
                        direction = "down"
                    else:
                        direction = "up"

            if direction == "down":
                if value_level < entry_levels[len(entry_levels)-1]:
                    # we are good
                    pass
                else:
                    conflict = True
            elif direction == "up":
                if value_level > entry_levels[len(entry_levels)-1]:
                    # we are good
                    pass
                else:
                    conflict = True
            else:
                print(f"I am not sure how this happened, but direction is == {direction}")

        if conflict:
            print("solved conflict")
            self.next_level()

    def determine_level(self, value):
        try:
            int(value)
            if len(value) >= 4:
                return Time.ENTRY_LEVEL_YEAR
            elif len(value) > 0:
                return Time.ENTRY_LEVEL_AMBIGUOUS_NUMBER
            else:
                return Response(False, f"Number \"{value}\" of modifier \"{self.time_str}\" is not valid")
        except:
            if is_time(value).value:
                return Time.ENTRY_LEVEL_TIME
            elif is_time(value).message:
                return is_time(value)
            elif value == "am" or value == "pm":
                return "am_pm"
            elif value == "st" or value == "nd" or value == "rd" or value == "th":
                return "position"
            elif self.is_relative_day(value):
                return Time.ENTRY_LEVEL_RELATIVE_DAY
            elif value == "month":
                return "month"
            elif value == "week":
                return Time.ENTRY_LEVEL_WEEK
            elif value == "day":
                return Time.ENTRY_LEVEL_DAY
            elif value == "next":
                return "next"
            elif self.is_month(value):
                return Time.ENTRY_LEVEL_MONTH
            elif self.is_day_of_week(value):
                return Time.ENTRY_LEVEL_DAY_OF_WEEK
            elif value == "year":
                return Time.ENTRY_LEVEL_YEAR
            elif value == "and" or value == "from" or value == "at" or value == "on" or value == "of" or value == "or":
                return "ignorable"
            elif value == "through" or value == "to" or value == "-":
                return "through"

    def insert_temp(self, key, value, level):
        if (len(self.temp_data) - 1) < level:
            self.temp_data.insert(level, {})
        if key == "type":
            # only one value for type can be specified in a modifier
            if self.temp_data[level].get("type"):
                return Response(False, f"Type \"{value}\" was given, but type was already specified ("
                                       f"{self.temp_data[level].get('type')})")
            self.temp_data[level]["type"] = value
        elif key == "next":
            self.temp_data[level]["next"] = value
        elif key == "time_type" or key == "time_period":
            self.temp_data[level][key] = value
        elif not self.temp_data[level].get(key):
            if type(value) is list:
                self.temp_data[level][key] = value
            else:
                self.temp_data[level][key] = [value]
        else:
            if type(value) is list:
                for v in value:
                    self.temp_data[level][key].append(v)
            else:
                self.temp_data[level][key].append(value)
        return Response(True)

    def simplify(self):
        # this will be used to simplify the temp_data if there are ambiguities such as position = 3rd
        # without further context
        level = self.level
        temp_data = self.temp_data

        if temp_data[level].get("position"):
            positions = temp_data[level].get("position")
            if temp_data[level].get("month"):
                self.insert_temp("day", positions, level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_DAY, position=True)
            else:
                return
            temp_data[level].pop("position")
        if temp_data[level].get("num"):
            nums = temp_data[level].get("num")
            if temp_data[level].get("month"):
                self.insert_temp(f"day", nums, level)
                self.change_ambiguous_entry_levels(level, Time.ENTRY_LEVEL_DAY, number=True)
            else:
                return
            temp_data[level].pop("num")

    def is_month(self, potential_month):
        first_three = potential_month[0:3]
        index = 1
        for month in self.month_min:
            if first_three == self.month_min[month]:
                return index
            index += 1
        return False

    def is_day_of_week(self, potential_day_of_week):
        # mon = 1, tue = 2, etc.
        first_three = potential_day_of_week[0:3]
        index = 1
        for day_of_week in self.day_of_week_min:
            if first_three == self.day_of_week_min[day_of_week]:
                return index
            index += 1
        return False

    def is_relative_day(self, potential_relative_day):
        first_four = potential_relative_day[:4]
        for relative_day in self.relative_day_min:
            if first_four == self.relative_day_min[relative_day]:
                return relative_day
        return False

    def next_level(self):
        # increments level
        self.simplify()
        self.level += 1
        self.temp_data.append({})


def is_illegal_modifier_character(char):
    illegal_character = ["/", "\\"]
    if len(char) == 1:
        for illegal_char in illegal_character:
            if char == illegal_char:
                return True
    return False


def is_time(potential_time):
    stage = 0
    valid = False
    for char in potential_time:
        if stage == 0:
            if char.isdigit():
                stage = 1
            else:
                break
        elif stage == 1:
            if char.isdigit():
                stage = 2
            elif char == ":":
                stage = 3
            else:
                break
        elif stage == 2:
            if char == ":":
                stage = 3
            else:
                break
        elif stage == 3:
            if char.isdigit():
                stage = 4
            else:
                break
        elif stage == 4:
            if char.isdigit():
                stage = 5
                valid = True
            else:
                break
        elif stage == 5:
            valid = False
            break

    if not valid:
        if stage >= 3:
            return Response(False, f"Time {potential_time} is not a valid time.")
        else:
            return Response(False)
    return Response(True)


def num_to_time(num):
    if type(num) is list:
        re = []
        for number in num:
            re.append(f"{number}:00")
        return re
    return f"{num}:00"


def parse_integer(val):
    t = ""
    if val[0] == "-":
        t = "-"
    for rt in val:
        if rt.isnumeric():
            t += rt
    return int(t)

#
# s = Time("eztag")
# print("--------------")
# for current_level in s.temp_data:
#     print(current_level)
# print("--------------")
# print(s.valid)

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
