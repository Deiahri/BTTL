import datetime


def time():
    """Returns the current time formatted in essential's time format: (n+)-(nn)-(nn) (nn):(nn)"""
    t = str(datetime.datetime.now())
    t = t[0:t.index(".")-3]
    return t


def compare_times(t1: str, t2: str):
    """Receives two strings formatted in essential's time format (returns false otherwise).\n
        Returns the time difference between the two"""
    if is_essentials_time_format(t1) and is_essentials_time_format(t2):
        t1_split = t1.split(" ")
        t2_split = t2.split(" ")

        t1_date_split = t1_split[0].split("-")
        t2_date_split = t2_split[0].split("-")
        t1_time_split = t1_split[1].split(":")
        t2_time_split = t2_split[1].split(":")
        return carry_time_math({
            "year": int(t1_date_split[0])-int(t2_date_split[0]),
            "month": int(t1_date_split[1])-int(t2_date_split[1]),
            "day": int(t1_date_split[2])-int(t2_date_split[2]),
            "hour": int(t1_time_split[0])-int(t2_time_split[0]),
            "minute": int(t1_time_split[1])-int(t2_time_split[1]),
        })
    else:
        return False


def carry_time_math(time_diff):
    """Receives a dictionary of numbers, that follows compare_times format, and normalizes them.\n
        Ex: [years: 0, months: 3, days: 5, hours: 12, minutes: -5] ->
        [years: 0, months: 3, days: 5, hours: 11, minutes: 55]"""
    all_positive = False
    conversions = {
        "year": 12,     # year = 12 months
        "month": 30,    # month = 30 days (appx)
        "day": 24,      # day = 24 hours
        "hour": 60,     # hour = 60 minutes
        "minute": 60,   # minute = 60 seconds
    }
    indexes = ["year", "month", "day", "hour", "minute"]
    while not all_positive:
        last_positive = ""
        last_negative = ""
        for key in time_diff:
            if time_diff.get(key) > 0:
                last_positive = key
            elif time_diff.get(key) < 0:
                if last_positive:
                    # only continues to next step if last positive was set
                    last_negative = key
                    break

        if not last_positive and not last_negative:
            break
        elif not last_negative:
            all_positive = True
        else:
            add_amount = conversions.get(last_positive)
            time_diff[last_positive] -= 1
            time_diff[indexes[indexes.index(last_positive)+1]] += add_amount

    return time_diff


def is_essentials_time_format(time_data: str):
    """Uses a DFA that checks time_data against the pattern n+-nn-nn nn:nn (essential's time format)"""
    stage = 0
    valid = False
    for char in time_data:
        if stage == 0:
            if char.isdigit():
                stage = 1
            else:
                break
        elif stage == 1:
            if char.isdigit():
                pass
            elif char == "-":
                stage = 2
            else:
                break
        elif stage == 2:
            if char.isdigit():
                stage = 3
            else:
                break
        elif stage == 3:
            if char.isdigit():
                stage = 4
            else:
                break
        elif stage == 4:
            if char == "-":
                stage = 5
            else:
                break
        elif stage == 5:
            if char.isdigit():
                stage = 6
            else:
                break
        elif stage == 6:
            if char.isdigit():
                stage = 7
            else:
                break
        elif stage == 7:
            if char.isspace():
                stage = 8
            else:
                break
        elif stage == 8:
            if char.isdigit():
                stage = 9
            else:
                break
        elif stage == 9:
            if char.isdigit():
                stage = 10
            else:
                break
        elif stage == 10:
            if char == ":":
                stage = 11
            else:
                break
        elif stage == 11:
            if char.isdigit():
                stage = 12
            else:
                break
        elif stage == 12:
            if char.isdigit():
                stage = 13
                valid = True
            else:
                break
        else:
            valid = False
    return valid


def exceeds_time_limit(time_diff: dict, time_limit: dict):
    """Returns whether time_diff exceeds time_limit\n
        Limit format: {"hour": 4, "minute" 12}
        time_diff will follow the format returned by compare_times"""
    indexes = ["year", "month", "day", "hour", "minute"]
    time_limit_diff = {}
    for index in indexes:
        time_diff_amt = time_diff.get(index)
        time_limit_amt = time_limit.get(index)
        if not time_diff_amt:
            time_diff_amt = 0
        if not time_limit_amt:
            time_limit_amt = 0
        time_limit_diff[index] = time_limit_amt - time_diff_amt

    time_limit_diff = carry_time_math(time_limit_diff)
    for diff in time_limit_diff.values():
        if diff < 0:
            return True
    return False

