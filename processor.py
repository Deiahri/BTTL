import validate_command, Execute
from response import Response


# what data is, has not been determined yet
def process(data, direct: str):
    sent_from_phone = True
    sent_from_computer = False
    user = ""  # some phone number
    # get user data at this point (options: via website or via messages)
    if sent_from_computer:
        # check session ip data to see if user is logged in.
        # otherwise, check if they are trying to log in
        # otherwise, tell them to log in.
        pass
    elif sent_from_phone:
        # get the phone number from the data sent
        user = "+13829249240"
    else:
        # sent through some other method. I am not sure what other methods there are.
        return Response(False, "Unrecognized device.")

    # THIS IS EQUAL TO DIRECT ONLY FOR TESTING
    command_data = direct  # this command data will be extracted from the data sent

    # pass the command received over to validate_command.validate
    validate_response = validate_command.validate(command_data)
    if type(validate_response) is Response:
        # validate_command.validate() returns a response if no command matches.
        # Prepare response that is appropriate for either phone or computer
        reason = ""
        if validate_response.message:
            reason = f"\nReason: {validate_response.message}"
        else:
            reason = "\nCommand did not start with \"keyword\", \"route\", \"best-time\" or any synonym."
        return Response(False, f"\"{command_data}\" could not be understood{reason}")
    else:
        execute_response = Execute.execute(validate_response, user)
        return execute_response


# print(process("", "route add mister = asd > asd"))
# print(process("", "no"))

