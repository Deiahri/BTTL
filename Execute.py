from command import KeywordCommand, RouteCommand, ConfirmCommand, BestTimeCommand
import Components, user, session, essentials, validate_command
from response import Response


def execute(c, user_number):
    # determines if current user exists.
    current_user = user.load_user(user_number)
    if not current_user:
        # THIS IS PERHAPS A TERRIBLE IDEA - NEEDS TO RETURN Response(False, "This user does not have an account")
        # If a user doesn't exist, I will need to push them to create an account
        current_user = user.User(user_number, "none", [], [], 1515)
        current_user.save()

    command_type = c.type
    if command_type == "keyword":
        return __execute_keyword(c, current_user)
    elif command_type == "route":
        return __execute_route(c, current_user)
    elif command_type == "confirm":
        return __execute_confirm(c, current_user)
    elif command_type == "best-time":
        return __execute_best_time(c, current_user)
    else:
        print("I don't know what kinda command you just tried to get me to execute.")


def __execute_keyword(c: KeywordCommand, current_user: user.User):
    operation = c.operation
    user_number = current_user.phone_number
    # checking if user already has a keyword with the requested name
    user_keywords = current_user.keywords
    current_keyword_exists = False
    for keyword in user_keywords:
        current_keyword = Components.load_keyword_w_id(keyword)
        if current_keyword.key == c.name:
            current_keyword_exists = True

    if not c.confirmed:
        # throws this command into the user's session data
        requirements = {
            "type": "confirm",
            "command": c.source,
            "date": essentials.time(),

            # this follows essentials.compare_times() format
            # time allotted to confirm a command is 1 hour.
            "time_limit": {"year": 0, "day": 0, "hour": 1, "minute": 0, "second": 0}
        }
        session.set_requirement(user_number, requirements)
        if operation == "add":
            if current_keyword_exists:
                return Response(False, f"Cannot add keyword. Current user already has keyword {c.name} defined")
            else:
                return Response(True, f"Are you sure you want to add keyword... \n"
                                      f"{c.name}: {c.address} ?\n"
                                      f"You have 1 hour to respond (with \"yes\" or \"no\")")
        elif operation == "remove":
            if current_keyword_exists:
                current_keyword = Components.load_keyword_w_name(c.name)
                return Response(True, f"Are you sure you want to remove keyword... \n"
                                      f"{c.name}: {current_keyword.value} ?\n"
                                      f"You have an hour to confirm")
            else:
                return Response(False, "Cannot remove keyword. Current user does not have keyword "
                                       f"{c.name} defined")
        elif operation == "set":
            if current_keyword_exists:
                current_keyword = Components.load_keyword_w_name(c.name)
                return Response(True, f"Are you sure you want to set keyword... \n"
                                      f"{c.name} from \"{current_keyword.value}\" to \"{c.address}\" ?\n"
                                      f"You have 1 hour to respond (with \"yes\" or \"no\")")
            else:
                return Response(False, "Cannot set keyword. Current user does not have keyword "
                                       f"{c.name} defined")
    else:
        # pre-execution stuff
        if operation == "add":
            if current_keyword_exists:
                print(f"Cannot add keyword. Current user already has keyword {c.name} defined.")
            else:
                kw = Components.Keyword(c.name, c.address, c.source)
                kw.save()
                current_user.add_keyword(kw)
                current_user.save()
                return Response(True, f"Successfully added keyword\n"
                                      f"{kw.key}: {kw.value}")

        elif operation == "remove":
            if not current_keyword_exists:
                print(f"Cannot remove keyword. Current user does not have keyword {c.name} defined")
            else:
                # removes the keyword requested from user list and from directory
                key_id_removed = current_user.remove_keyword(c.name)
                current_user.save()
                Components.load_keyword_w_id(key_id_removed).delete()
                return Response(True, f"Successfully removed keyword \"{c.name}\"")

        elif operation == "set":
            if not current_keyword_exists:
                print(f"Cannot set keyword. Current user does not have keyword {c.name} defined")
            else:
                current_keyword = Components.load_keyword_w_name(c.name)
                current_keyword.value = c.address
                current_keyword.save()
                return Response(True, f"Successfully set keyword\n"
                                      f"{current_keyword.key}: {current_keyword.value}")
        elif operation == "list":
            keyword_list = ""
            for key_id in current_user.keywords:
                current_keyword = Components.load_keyword_w_id(key_id)
                if current_keyword:
                    keyword_list += f"{current_keyword.key}: {current_keyword.value}\n"
            if not keyword_list:
                return Response(True, "You have no defined keywords.\n"
                                      "Use \"Keyword add\" command to add keywords.")
            else:
                return Response(True, keyword_list.strip())
        else:
            # operation is likely blank
            pass


def __execute_route(c: RouteCommand, current_user: user.User):
    operation = c.operation

    # check addresses for keywords and confirms that the current user has them.
    if operation == "add" or operation == "set":
        for current_address in c.addresses:
            if current_address.type == "keyword":
                keyword = current_address.keyword
                if not current_user.contains_keyword_name(keyword):
                    return Response(False, f"You referred to keyword \"{keyword}\", but have no such keyword defined.")

    user_number = current_user.phone_number
    contains_route = current_user.contains_route_name(c.name)
    if c.confirmed:
        if operation == "add":
            if contains_route:
                return Response(False, f"Cannot add route \"{c.name}\" because it already exists!\n")
            else:
                r_obj = Components.Route(c.name, c.addresses, c.compiled_modifiers, c.credit_estimate, c.source)
                r_obj.save()
                current_user.add_route(r_obj)
                current_user.save()
                return Response (True, f"Route {c.name} was successfully added")
        elif operation == "remove":
            if not contains_route:
                return Response(False, f"Cannot remove route \"{c.name}\" because it does not exist!\n")
            else:
                r_obj = current_user.get_route_w_name(c.name)
                # removes the route from the user's route list
                current_user.remove_route(r_obj.route_id)
                current_user.save()

                # removes the route file
                r_obj.delete()

                return Response(True, f"Route {c.name} was successfully removed")
        elif operation == "set":
            if not contains_route:
                return Response(False, f"Cannot set route \"{c.name}\" because it does not exist!\n")
            else:
                # creates a new route object, but the id of the route object is equal to
                # an existing route object with the same name/key.
                r_obj = Components.Route(c.name, c.addresses, c.compiled_modifiers, c.credit_estimate, c.source,
                                         current_user.get_route_w_name(c.name).route_id)
                r_obj.save()
                return Response(True, f"Route {c.name} was successfully changed")
    else:
        requirements = {
            "type": "confirm",
            "command": c.source,
            "date": essentials.time(),

            # this follows essentials.compare_times() format
            # time allotted to confirm a command is 1 hour.
            "time_limit": {"year": 0, "day": 0, "hour": 1, "minute": 0, "second": 0}
        }
        if operation == "add":
            if not contains_route:
                session.set_requirement(user_number, requirements)
                return Response(True, "Are you sure you want to add route \""
                                      f"{c.source}\"?\n"
                                      f"You have 1 hour to respond (with \"yes\" or \"no\")")
            return Response(False, f"Cannot add route \"{c.name}\" because it already exists!\n")
        elif operation == "remove":
            if contains_route:
                session.set_requirement(user_number, requirements)
                return Response(True, "Are you sure you want to remove route \""
                                      f"{c.name}\"?\n"
                                      f"You have 1 hour to respond (with \"yes\" or \"no\")")
            return Response(False, f"Cannot remove route \"{c.name}\" because it does not exist!\n")
        elif operation == "set":
            if contains_route:
                session.set_requirement(user_number, requirements)
                return Response(True, "Are you sure you want to execute \""
                                      f"{c.source}\"?\n"
                                      f"You have 1 hour to respond (with \"yes\" or \"no\")")
            return Response(False, f"Cannot set route \"{c.name}\" because it does not exist!\n")


def __execute_confirm(c: ConfirmCommand, current_user: user.User):
    requirements = session.get_requirement(current_user.phone_number)
    if c.value:
        if requirements:
            if requirements.get("type") == "confirm":
                command = validate_command.validate(requirements.get("command"))
                command.confirmed = True
                session.set_requirement(current_user.phone_number, {})
                return execute(command, current_user.phone_number)

        return Response(False, f"Confirm command \"{c.source}\" was passed, but there is nothing to confirm!\n"
                               f"(Maybe your last request expired.)")
    else:
        session.set_requirement(current_user.phone_number, {})
        return Response(True, "Previous request cancelled.")


def __execute_best_time(c: BestTimeCommand, current_user: user.User):
    if c.confirmed:
        return Response(True, f"Executing best-time command {c.source}")
    else:
        # c.route is a string iff the user uses @route_name
        if type(c.route) is str:
            if not current_user.get_route_w_name(c.route):
                return Response(False, f"Route {c.route} does not exist")
        # it is a route otherwise.
        requirements = {
            "type": "confirm",
            "command": c.source,
            "date": essentials.time(),

            # this follows essentials.compare_times() format
            # time allotted to confirm a command is 1 hour.
            "time_limit": {"year": 0, "day": 0, "hour": 1, "minute": 0, "second": 0}
        }
        session.set_requirement(current_user.phone_number, requirements)
        return Response(True, "Are you sure you want to execute \""
                              f"{c.source}\"?\n"
                              f"You have 1 hour to respond (with \"yes\" or \"no\")")

# k = RouteCommand("route remove micro")
# k = ConfirmCommand("yes")
# print(k.valid)
# print(execute(k, "+13829249240"))
