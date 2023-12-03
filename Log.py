import datetime
path = "LOG_DATA/ERRORS"


def error(e: Exception):
    """Accepts any exception and throws the message of the exception into a text file stored in
        the folder for errors"""
    if type(e) is Exception:
        now = __get_now()
        with open(f"{path}/{now}.txt", "w") as file:
            file.write(f"Error: {e.__str__()}")
        __alert("error")
    else:
        print(f"Log.error received type: {type(e)} instead of type exception.")


def message(s: str):
    """Receives a string and throws it into a text file stored in the folder for errors."""
    if type(s) is str:
        now = __get_now()
        with open(f"{path}/{now}.txt", "w") as file:
            file.write(f"Message: {s}")
        __alert("message")
    else:
        print(f"Log.error received type: {type(s)} instead of type string.")


def __get_now():
    """Returns the time right now formatted in a way that is acceptable for a file name."""
    dt = datetime.datetime
    now = f"{dt.now()}".replace(".", "-").replace(" ", "_").replace(":", "-")
    return now


def __alert(alert_type: str):
    """Receives a string and prints out "string" logged"""
    print(f"{alert_type} logged.")


