from response import Response


def is_command_name(name=""):
    message = f"keyword name \"{name}\" cannot contain \""
    value = False
    if name.__contains__(">"):
        message += ">\""
    elif name.__contains__("<"):
        message += "<\""
    elif name.__contains__("="):
        message += "=\""
    elif name.__contains__("!"):
        message += "!\""
    else:
        value = True
    if value:
        message = ""
    return Response(value, message)


def is_command_address(address=""):
    message = ""
    value = False
    if address.__contains__(">"):
        message += ">\""
    elif address.__contains__("<"):
        message += "<\""
    elif address.__contains__("="):
        message += "=\""
    elif address.__contains__("!"):
        if len(address) > 1:
            if not address[1:].__contains__("!"):
                pass
            else:
                message += "!\" anywhere except the front (!something = valid | !somethi!ng = not valid)"
        else:
            message += "!\""
    elif address.__contains__("/"):
        message += "/\""
    elif address.__contains__("\\"):
        message += "\\\""
    elif address.__contains__("#"):
        message += "#\""
    elif address.__contains__("@"):
        message += "!\""

    if not message:
        value = True
    else:
        message = f"Address \"{address}\" cannot contain \"{message}"
    return Response(value, message)


