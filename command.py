import Security
from response import Response
from Components import Address, Modifier, Route
import modifier_compiler


synonyms = {
    "keyword": ["key", "keywords"],
    "route": ["trip"],
    "best-time": ["best", "bt", "besttime"]
}


class Command:
    def __init__(self, source: str, confirmed: bool = False):
        self.source = source.lower().strip()
        self.type = "null"
        self.confirmed = confirmed


data_dir = "data"


class KeywordCommand(Command):
    def __init__(self, source: str, confirmed: bool = False):
        """Receives a string and attempts to parse information from it if it follows the following pattern.\n
            keyword(or synonym) (add, remove, set) (keyword_name) = (address)\n
            Object will store the following data:\n
            Type: The command type (always = "keyword")\n
            Operation: add, remove, or set\n
            Name: (keyword_name)\n
            Address: address to be assigned to keyword_name\n
            Valid: A Response object."""
        super().__init__(source, confirmed)
        self.type = "keyword"
        self.operation = ""
        self.name = ""
        self.address = ""
        self.valid = self.__validate()

    def __validate(self):
        """Verifies the command given while also parsing data from it.\n
        Returns Response(False) if the command does not start with Keyword\n
        Returns Response(False, message) if the command starts with keyword, but has invalid syntax\n
        Returns Response(True) if the command is correct."""
        valid = False
        current = ""
        stage = "0"

        operation = ""
        name = ""
        address = ""

        for char in self.source:
            if stage == "0":
                # stage 0 is used to determine if the current token is equal to keyword or any of its synonyms
                if char.isspace():
                    if is_synonym("keyword", current):
                        # goes to stage 2 because I don't want to shift all the stages
                        stage = "2"
                    else:
                        # IF IT FAILS AT STAGE ONE, THE RESPONSE MESSAGE SHOULD BE NONE
                        return Response(False)
                else:
                    current += char
            elif stage == "2":
                # this tolerates any amount of space after the first space. ("keyword " and "keyword     " are valid)
                if char.isspace():
                    pass
                else:
                    current = char
                    stage = "3"
            elif stage == "3":
                # this will accept add, set or remove commands.
                current += char
                if len(current) < 3:
                    pass
                # 3 = len of add (shortest), 6 = len of remove (longest)
                elif 3 <= len(current) <= 6:
                    if current == "add" or current == "set" or current == "remove":
                        operation = current
                        current = ""
                        stage = "4"
                else:
                    return Response(False, f"\"{current}\" is not a valid sub-command for {self.type}")
            elif stage == "4":
                # keyword needs to be followed by a space
                if char.isspace():
                    stage = "5"
                else:
                    return Response(False, f"{operation} was followed by \"{char}\", which is invalid")
            elif stage == "5":
                # this tolerates any amount of space after the first space. ("keyword " and "keyword     " are valid)
                if char.isspace():
                    pass
                else:
                    current = char
                    stage = "6"
            elif stage == "6":
                # we should receive a name at this stage
                if char == "=":
                    # if current is empty, then the name was not given.
                    if not current.strip():
                        return Response(False, "Name cannot be empty space.")
                    elif operation == "remove":
                        return Response(False, f"Name \"{current.strip()}\" does not need to be defined using \"=\"")
                    else:
                        name = current
                        current = ""
                        stage = "7"
                else:
                    current += char
            elif stage == "7":
                current += char
                valid = True

        if stage == "0":
            if is_synonym("keyword", current):
                # this allows the user to input "keyword" to get a list of keywords they have
                self.operation = "list"
                self.confirmed = True
                return Response(True)
            return Response(False)

        if operation == "remove" and stage == "6":
            name_response = Security.is_command_name(current)
            if name_response.value:
                name = current.strip()
            else:
                return name_response
            self.name = name
            self.operation = operation
            return Response(True)
        elif not operation:
            return Response(valid, f"No valid operation was given after \"{self.source}\".\n"
                                   f"Add, Remove, and Set are valid operations.")
        elif not name:
            if not current:
                return Response(valid, f"No name was given after \"{operation}\".")
            else:
                # 6/23/2023
                # determines if the to-be name was valid.
                name_valid_response = Security.is_command_name(current)
                if name_valid_response.value:
                    # the to-be name was valid
                    return Response(valid, f"Name \"{current}\" needs to be followed by an equal sign \"=\"")
                else:
                    # the to-be name was not valid.
                    return name_valid_response
        elif not address:
            if current:
                if Security.is_command_name(current):
                    address = current.strip()
                else:
                    return Response(valid, f"Address \"{current}\" is not a valid address")
            else:
                return Response(valid, f"No address was specified")

        self.operation = operation.strip()
        self.name = name.strip()

        # confirms address is a valid address
        addy = Address(address)
        if not addy.valid.value:
            return Response(False, f"Address \"{address}\" is invalid")
        self.address = address.strip()
        return Response(valid, "")


class RouteCommand(Command):
    def __init__(self, source: str, confirmed: bool = False):
        super().__init__(source, confirmed)
        self.type = "route"
        self.operation = ""
        self.name = ""
        self.addresses = []
        self.modifiers = []

        self.compiled_modifiers = []
        self.credit_estimate = {}
        self.valid = self.__validate()

    def __validate(self):
        stage = "0"
        current = ""

        operation = ""
        name = ""
        addresses = []
        modifiers = []

        for char in self.source:
            if stage == "0":
                # sees if first word is route or a synonym of route
                if char.isspace():
                    if is_synonym("route", current):
                        current = ""
                        stage = "1"
                    else:
                        return Response(False)
                else:
                    current += char
            elif stage == "1":
                if char.isspace():
                    continue
                else:
                    current += char
                    stage = "2"
            elif stage == "2":
                # this will accept add, set or remove commands.
                current += char
                if len(current) < 3:
                    pass
                # 3 = len of add (shortest), 6 = len of remove (longest)
                elif 3 <= len(current) <= 6:
                    if current == "add" or current == "set" or current == "remove":
                        operation = current
                        current = ""
                        stage = "3"
                else:
                    return Response(False, f"\"{current}\" is not a valid sub-command for {self.type}")
            elif stage == "3":
                if char.isspace():
                    pass
                else:
                    current = char
                    stage = "4"
            elif stage == "4":
                if char == "=":
                    if operation == "remove":
                        return Response(False, f"\"{current}\" does not need to be followed by an equals sign \"=\"")

                    name_valid_response = Security.is_command_name(current)
                    if name_valid_response.value:
                        name = current
                        stage = "5"
                        current = ""
                    else:
                        return name_valid_response
                else:
                    current += char
            elif stage == "5":
                # reading addresses from the command
                if char == ">":
                    if current.strip():
                        addresses.append(current.strip())
                        current = ""
                        stage = "5a"
                    else:
                        return Response(False, "No address was given before the \">\" symbol")
                elif char == "|":
                    if current.strip():
                        addresses.append(current.strip())
                        current = ""
                        stage = "6"
                    else:
                        return Response(False, "The address before the \"|\" should not be blank.")
                else:
                    current += char
            elif stage == "5a":
                # command should not end in stage 5a, or else it ended with a ">" symbol
                current = char
                stage = "5"
            elif stage == "6":
                # reading modifiers from the command.
                if char == ",":
                    if current.strip():
                        # received a comma.
                        modifiers.append(current)
                        current = ""
                        stage = "6a"
                    else:
                        return Response(False, "A comma was received, but no modifier was given before it.")
                else:
                    current += char
            elif stage == "6a":
                # should not end in stage 6a, or else a comma was given, but no modifier followed
                current = char
                stage = "6"

        if stage == "0":
            return Response(False)

        if stage == "5a":
            return Response(False, "Command cannot have a \">\" without a address following it")
        elif stage == "6a":
            return Response(False, "Command cannot have a \",\" without a modifier following it")
        elif stage == "5":
            if current.strip():
                addresses.append(current)
            else:
                return Response(False, "Address cannot be blank spaces.")
        elif stage == "6":
            if current.strip():
                modifiers.append(current)
            else:
                return Response(False, "Modifiers cannot be blank spaces.")

        if not operation:
            return Response(False, "No operation was given.")
        elif not name:
            if not current:
                return Response(False, f"No name was given after \"{operation}\"")
            else:
                if operation == "remove":
                    name = current
                else:
                    return Response(False, f"Name \"{current}\" needs to be followed by an equals sign \"=\" for commands "
                                           f"add and set.")
        if not operation == "remove":
            if not addresses:
                return Response(False, f"No addresses were given")
            elif len(addresses) == 1:
                return Response(False, f"Two addresses are required for a route, but only one was given.")
        self.operation = operation.strip()

        # validate name
        name_valid_response = Security.is_command_name(name)
        if not name_valid_response.value:
            return name_valid_response

        self.name = name.strip()
        # validate modifiers
        # I chose to validate modifiers first because modifiers is validated without calling api
        # Address calls geocoder api, which can cost money
        # and won't matter if it is validated first and modifier (checked last) ends up being invalid
        modifier_objects = []
        for modifier in modifiers:
            mod = Modifier(modifier)
            if not mod.valid.value:
                return mod.valid
            modifier_objects.append(mod)

        compiled = modifier_compiler.compile_modifiers(modifier_objects)
        if type(compiled) is Response:
            return compiled
        self.compiled_modifiers = compiled

        time_estimate = modifier_compiler.estimate_credits(compiled)
        if type(time_estimate) is Response:
            return time_estimate
        self.credit_estimate = time_estimate
        self.modifiers = modifier_objects

        # validate addresses
        address_objects = []
        for address in addresses:
            addy = Address(address)
            if not addy.valid.value:
                return addy.valid
            address_objects.append(addy)
        self.addresses = address_objects
        return Response(True)

    def count_days(self):
        pass


def is_synonym(synonym_of, possible_synonym):
    """Given a synonym and what it is a synonym of, it will compare possible_synonym
    to the array of words in synonyms\n
    Uses valid_synonym_of() to validate the given \"synonym_of\" is a valid synonym"""
    synonym_of = synonym_of.lower()
    possible_synonym = possible_synonym.lower()
    if not valid_synonym_of(synonym_of):
        return False
    else:
        if possible_synonym == synonym_of:
            return True
        for synonym in synonyms[synonym_of]:
            if possible_synonym == synonym:
                return True
        return False


def valid_synonym_of(synonym_of):
    """Receives synonym_of as a parameter. Returns true of synonym_of is a key in the synonyms dictionary"""
    valid = False
    for synonym_base in synonyms:
        if synonym_base == synonym_of:
            valid = True
            break
    return valid


def longest_synonym_length(synonym_of):
    """Receives synonym_of which should be a key in the synonym dictionary\n
    Returns the length of the longest synonym related to synonym_of"""
    if valid_synonym_of(synonym_of):
        max_len = len(synonym_of)
        for synonym in synonyms[synonym_of]:
            if len(synonym) > max_len:
                max_len = len(synonym)
        return max_len
    else:
        print(f"Invalid synonym of ({synonym_of})")
        return -1


def shortest_synonym_length(synonym_of):
    """Receives synonym_of which should be a key in the synonym dictionary\n
    Returns the length of the longest synonym related to synonym_of"""
    if valid_synonym_of(synonym_of):
        min_len = len(synonym_of)
        for synonym in synonyms[synonym_of]:
            if len(synonym) < min_len:
                min_len = len(synonym)
        return min_len
    else:
        print(f"Invalid synonym of ({synonym_of})")
        return -1


class ConfirmCommand(Command):
    """Receives text, will try to match it with "Yes" or "No"""
    def __init__(self, source: str):
        super().__init__(source, False)
        self.type = "confirm"
        self.value = None
        self.additional_data = []
        self.valid = self.__validate()

    def __validate(self):
        yes_no = ""
        additional_data = []

        stage = "0"
        current = ""
        valid = False
        invalid_char = ""
        for char in self.source:
            if stage == "0":
                if char.isalpha():
                    stage = "1"
                    current += char
                else:
                    break
            elif stage == "1":
                if char == " ":
                    if current == "yes" or current == "no":
                        yes_no = current
                        current = ""
                        valid = True
                        stage = "2"
                    else:
                        break
                elif self.is_allowed_character(char):
                    current += char
                else:
                    invalid_char = char
                    break
            elif stage == "2":
                if char.isalpha() or char.isdigit():
                    current += char
                    stage = "3"
                elif char.isspace():
                    pass
                else:
                    invalid_char = char
                    break
            elif stage == "3":
                if self.is_allowed_character(char):
                    current += char
                elif char == ",":
                    additional_data.append(current.strip())
                    current = ""
                    stage = "4"
                    valid = False
                else:
                    invalid_char = char
                    break
            elif stage == "4":
                if char.isalpha() or char.isdigit():
                    current += char
                    stage = "3"
                    valid = True
                elif char.isspace():
                    pass
                else:
                    invalid_char = char
                    break

        if current:
            if not yes_no:
                if current == "yes" or current == "no":
                    yes_no = current
                    valid = True
                else:
                    valid = False
            else:
                additional_data.append(current)

        if not valid:
            if invalid_char:
                return Response(False, f"\"{char}\" is an invalid character.")
            elif stage == "4":
                return Response(False, f"{self.source} has a comma which is not followed by anything.")
            elif yes_no:
                return Response(False, f"\"{self.source}\" is an invalid confirmation.")
            else:
                return Response(False)
        else:
            self.additional_data = additional_data
            if yes_no == "yes":
                self.value = True
            else:
                self.value = False
            return Response(True)

    @staticmethod
    def is_allowed_character(s: str):
        allowed_chars = ["-"]
        for char in s:
            allowed = False
            if char.isspace():
                allowed = True
            elif char.isalpha():
                allowed = True
            elif char.isdigit():
                allowed = True
            else:
                for allowed_char in allowed_chars:
                    if char == allowed_char:
                        allowed = True
                        break

            if not allowed:
                return False

        return True

    def __str__(self):
        return f"{self.value} | {self.additional_data}"


class BestTimeCommand(Command):
    def __init__(self, source: str):
        super().__init__(source)
        self.type = "best-time"
        self.route = ""
        self.valid = self.__validate()

    def __validate(self):
        source = self.source
        current = ""
        stage = "0"
        illegal_character = ''
        data_start_index = -1
        for index, char in enumerate(source):
            if stage == "0":
                # read until a space is encountered.
                if BestTimeCommand.is_illegal_character(char):
                    illegal_character = char
                    stage = "4"
                elif char.isspace():
                    if is_synonym("best-time", current.strip()):
                        stage = "1"
                        current = ""
                        data_start_index = index
                    else:
                        break
                else:
                    current += char
            elif stage == "1":
                # skip spaces, if @ is encountered, go to stage 3
                # otherwise, send command to route_command
                if char.isspace():
                    pass
                elif char == "@":
                    stage = "3"
                elif BestTimeCommand.is_illegal_character(char):
                    stage = "4"
                    illegal_character = char
                else:
                    stage = "2"
            elif stage == "2":
                # stop parsing command.
                break
            elif stage == "3":
                if BestTimeCommand.is_illegal_character(char):
                    stage = "4"
                    illegal_character = char
            elif stage == "4":
                break

        if stage == "0" or stage == "1":
            if is_synonym("best-time", current.strip()):
                return Response(False, f"expected a route following \"{current.strip()}\"")
            else:
                return Response(False)
        elif stage == "2":
            # send command to route command
            r_command_data = f"route add r = {source[data_start_index+1:]}"
            r_command = RouteCommand(r_command_data)
            if not r_command.valid.value:
                return r_command.valid
            key = r_command.name
            address = r_command.addresses
            compiled_modifiers = r_command.compiled_modifiers
            search_estimate = r_command.credit_estimate
            source = r_command.source
            self.route = Route(key, address, compiled_modifiers, search_estimate, source)
        elif stage == "3":
            # locate the route sent to the compiler.
            route_name = source[source.index("@")+1:]
            self.route = route_name
        elif stage == "4":
            return Response(False, f'The character \"{illegal_character}\" cannot be used in a best-time command.')
        return Response(True)

    # illegal characters
    illegal_chars = ['!', '?', '@', '>', '|']

    @staticmethod
    def is_illegal_character(char):
        for illegal_char in BestTimeCommand.illegal_chars:
            if char == illegal_char:
                return True
        return False


# s = RouteCommand("route add bruh = new jersey > san fransisco | no tolls, car, March 19th")
# Route(s.name, s.addresses, s.compiled_modifiers, s.credit_estimate, s.source).save()
# s = ConfirmCommand("nos")
# print(s.valid)
# print(f"value: {s.value}")

# s = RouteCommand("")
# print(s.valid)
# print(s.compiled_modifiers)
# print(s.credit_estimate)


# comp = modifier_compiler.compile_modifiers(s.modifiers)
# if type(comp) is Response:
#     print(comp)
# else:
#     for item_c in comp:
#         print(item_c)
# print(modifier_compiler.estimate_credits(comp))
