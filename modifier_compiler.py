from Components import Time, Modifier, validate_month_day_range, time_to_24hr, days_in_month
from response import Response
import math

supported = ["month", "day", "relative_day", "time", "through", "then", "ignorable", "num", "position", "time_period"]

date_patterns = [
    ['year', 'month', 'day', 'time'],           # 2022 march 23rd
    ['month', 'day', 'year', 'time'],           # march 5th 1999
    ['month', 'num', 'year', 'time'],
    ['num', 'month', 'year', 'time'],
    ['month', 'num', 'time'],
    ['month', 'year', 'time'],                 # march 1999
    ['week', 'month'],                 # 2nd week of march
    ['week', 'year'],                  # 2nd week of 2023
    ['time']                           # 5:30
]

# January 3rd through 22nd 2024 on Mondays
# This week monday from 3:30pm-7:20pm
# August September, October, and November in 2024 from at 5pm
# September, October, and January 2020 from 5pm-6:30pm, March-April on Mondays
# January 3rd, March 18, and June 22nd from 9pm to 10am
# 2nd of August, 3rd of May, and 10th though 20th of June from 10am to 9:33pm on Wednesdays
MODIFIER_KEY = "modifier"
TIME_KEY = "time"


def compile_modifiers(modifiers):
    data = __index([])
    max_index = 0
    last_type = ""
    for modifier in modifiers:
        if modifier.type != "time":
            data[max_index][MODIFIER_KEY].append(modifier.origin)
        else:
            current_time_data = {
                TIME_KEY: [],
                MODIFIER_KEY: []
            }  # the data that will be added to the array data[max_index][TIME_KEY]
            current_pattern = []  # contains the current pattern of values in the time object [MONTH, YEAR, etc.]

            # modifier.value is set to a time object within the modifier class if that modifier is a time modifier.
            time_obj = modifier.value
            for time_index in range(len(time_obj.data)):
                # some time data types are unsupported. It will tell the user that, though, for example, "year" is valid
                # it is not currently supported.
                current_data = time_obj.data[time_index]
                current_type = time_obj.data_types[time_index]
                if __unsupported(current_type):
                    return Response(False, f"Date modifier {current_data} ({current_type}) is currently unsupported")
                # appends the current data type to current_pattern, then detects if this is a valid pattern
                # if not a valid pattern, the current_time_data is appended, and a new current_time_data dict is created
                if current_type == "then":
                    if current_time_data:
                        data[max_index][TIME_KEY].append(current_time_data)
                    data = __index(data)
                    max_index += 1
                    current_time_data = {}
                    current_pattern = []
                elif current_type == "through":
                    if last_type == "month" or last_type == "day" or last_type == "day_of_week" or \
                            last_type == "relative_day" or last_type == "time" or last_type == "num" or \
                            last_type == "position" or last_type == "time_period":
                        if last_type == "position":
                            last_type = "num"
                        elif last_type == "time_period":
                            last_type = "time"
                        __append(current_time_data, "-", last_type)
                    else:
                        return Response(False, f"{current_data} does not make sense after a \"{last_type}\"")
                elif current_type == "ignorable":
                    pass
                elif current_type == "position":
                    pass
                elif current_type == "time_period":
                    # appends am or pm to the time that it corresponds to
                    # 5:30 pm
                    current_time_data["time"][len(current_time_data["time"])-1] += current_data
                else:
                    current_pattern.append(current_type)
                    if not __valid_pattern(current_pattern):
                        if current_time_data:
                            data[max_index][TIME_KEY].append(current_time_data)
                            current_time_data = __append({}, current_data, current_type)
                            current_pattern = []
                    else:
                        current_time_data = __append(current_time_data, current_data, current_type)
                last_type = current_type
            if current_time_data:
                data[max_index][TIME_KEY].append(current_time_data)
    return data


precision_minutes = {
    "high": 5,   # high precision
    "medium": 10,  # medium precision
    "low": 20,  # low precision
    "v_low": 30,  # very low precision
}


def estimate_credits(data):
    """Receives data produced from compile_modifiers
        Note: credit allowance for users is about 1900"""
    for chunk in data:
        # this part verifies that every month, day, year, and time is valid.
        for time_chunk in chunk.get("time"):
            res = validate_month_day_range(time_chunk)
            if not res.value:
                return res
    data_minutes = []
    for chunk in data:
        data_minutes.append(
            {
                # gets the number of minutes calculated
                "minutes": __count_minutes(chunk),

                # gets the number of days calculated
                "days": __count_days(chunk)
            }
        )
    estimates = {
        "high": 0,
        "medium": 0,
        "low": 0,
        "v_low": 0
    }
    for chunk in data_minutes:
        current_minutes = chunk.get("minutes")
        current_days = chunk.get("days")
        for minute_index in range(len(current_minutes)):
            this_minutes = __sum(current_minutes[minute_index])
            this_day = current_days[minute_index]
            estimates["high"] += math.ceil(this_minutes / precision_minutes["high"]) * this_day
            estimates["medium"] += math.ceil(this_minutes / precision_minutes["medium"]) * this_day
            estimates["low"] += math.ceil(this_minutes / precision_minutes["low"]) * this_day
            estimates["v_low"] += math.ceil(this_minutes / precision_minutes["v_low"]) * this_day

    # adjusts for the searching between lowest points
    if not estimates.get("high") == 0:
        estimates["high"] += (precision_minutes["high"] - 1)
        estimates["medium"] += (precision_minutes["medium"]-1)
        estimates["low"] += (precision_minutes["low"]-1)
        estimates["v_low"] += (precision_minutes["v_low"]-1)
    return estimates


def __count_minutes(data_chunk):
    time_data = data_chunk.get("time")
    minutes = []
    if time_data:
        for time_chunk in time_data:
            time_array = time_chunk.get("time")
            if time_array:
                through = False
                last_time = ""
                time_set = []
                for time in time_array:
                    if time == "-":
                        through = True
                    elif through:
                        time_one = time_to_24hr(last_time)
                        time_two = time_to_24hr(time)
                        time_set[len(minutes)-1] = ((time_two[0]-time_one[0])*60+(time_two[1]-time_one[1]))
                        through = False
                    else:
                        time_set.append(1)
                        last_time = time
                minutes.append(time_set)
            else:
                minutes.append([24*60])
        return minutes
    else:
        return minutes


def __count_days(data_chunk):
    time_data = data_chunk.get("time")
    days = []
    if time_data:
        for time_chunk in time_data:
            time_chunk_days = time_chunk.get("num")
            time_chunk_months = time_chunk.get("month")
            if time_chunk_days:
                total_days = 0
                month_multiplier = 1
                if time_chunk_months:
                    month_multiplier = len(time_chunk_months)
                through = False
                last_day = 0
                for current_day in time_chunk_days:
                    if current_day == "-":
                        through = True
                    elif through:
                        total_days += (current_day-last_day) * month_multiplier
                        through = False
                    else:
                        last_day = current_day
                        total_days += 1*month_multiplier
                days.append(total_days)
            elif time_chunk_months:
                total_days = 0
                for current_month in time_chunk_months:
                    total_days += days_in_month(current_month)
                days.append(total_days)
            else:
                days.append(0)
        return days
    else:
        return days


def __append(time_data, data, data_type):
    if time_data.get(data_type):
        if type(time_data) is list:
            for array_data in data:
                time_data.get(data_type).append(array_data)
        else:
            time_data.get(data_type).append(data)
    else:
        if type(time_data) is list:
            time_data[data_type] = data
        else:
            time_data[data_type] = [data]
    return time_data


def __unsupported(dpc_value):
    for supported_key in supported:
        if dpc_value == supported_key:
            return False
    return True


def __valid_pattern(pattern):
    """Receives a pattern produced (usually) by compile_modifiers (current_pattern).\n
        The pattern is simplified, and then compared to patterns in date_patterns.\n
        If the simplified version of the given pattern matches any pattern in date_patterns, returns True."""
    simplified_pattern = []
    for index, item in enumerate(pattern):
        if len(simplified_pattern) == 0:
            simplified_pattern.append(item)
        else:
            if simplified_pattern[len(simplified_pattern)-1] == item:
                pass
            else:
                simplified_pattern.append(item)
    valid_patterns = date_patterns.copy()
    matching_valid_patterns = []
    for pattern_index, pattern in enumerate(valid_patterns):
        if len(pattern) >= len(simplified_pattern):
            valid = True
            for simplified_index in range(len(simplified_pattern)):
                if not pattern[simplified_index].lower() == simplified_pattern[simplified_index].lower():
                    valid = False
            if valid:
                matching_valid_patterns.append(pattern)
        else:
            valid_patterns.pop(pattern_index)

    if not matching_valid_patterns:
        return False
    return True


def __sum(arr: list):
    """receives a list, returns the sum of the items in the list"""
    total = 0
    try:
        for item in arr:
            total += item
        return total
    except:
        return -1


def __index(data):
    """Adds a new item to the data array being generated in compile_modifiers"""
    data.append(
        {
            TIME_KEY: [],       # will contain date modifiers in dictionaries { month: ["march"], day: [4]... etc. }
            MODIFIER_KEY: []    # will contain modifiers like EZTAG, CAR, etc.
        }
    )
    return data

