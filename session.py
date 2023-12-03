import json, Log, essentials
path = "data/session"


def set_requirement(user_number, data: dict):
    """user_number: the number the requirement data will be saved under\n
        data: the data to be stored.\n
        Note: data requires "time_limit" to be defined\n
        Typical requirement is\n
        requirements = {
            "type": "confirm",\n
            "command": c.source,\n
            "date": essentials.time(), # current time\n

            # this follows essentials.compare_times() format
            # time allotted to confirm a command is 1 hour.
            "time_limit": {"year": 0, "day": 0, "hour": 1, "minute": 0, "second": 0}
        }"""
    user_data = __get_user_data(user_number)
    user_data["requirement"] = data
    __write_dict_to_user(user_number, user_data)


def get_requirement(user_number):
    """Returns the current user's requirement data if the time limit has not been exceeded"""
    user_data = __get_user_data(user_number)
    if user_data.get("requirement"):
        requirement_date = user_data.get("requirement").get("date")
        time_diff = essentials.compare_times(essentials.time(), requirement_date)
        time_limit = user_data.get("requirement").get("time_limit")
        if essentials.exceeds_time_limit(time_diff, time_limit):
            set_requirement(user_number, {})
            return {}

        return user_data.get("requirement")
    else:
        return {}


def __get_user_data(user_number):
    """Gets the user data located in user_number. If user number file does not exist, returns False"""
    try:
        user_file = open(f"{path}/number/{user_number}.temp", "r")
        try:
            return json.load(user_file)
        except json.decoder.JSONDecodeError:
            pass
        except Exception as e:
            Log.error(e)
    except FileNotFoundError:
        pass
    return False


def __write_dict_to_user(user_number, data):
    """Receives data and writes it to the user_number given"""
    with open(f"{path}/number/{user_number}.temp", "w") as user_file:
        json.dump(data, user_file, indent=4)


__write_dict_to_user("!", 4)

