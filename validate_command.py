from command import RouteCommand, KeywordCommand, ConfirmCommand, BestTimeCommand
from response import Response


def validate(command):
    # it will pass this command over to all the possible command types until one returns true or false partial
    # false partial is when it gets parts of the command right (keyword add) but gets others wrong
    # (keyword add = bruh) <-- wrong because there is no name

    k_c = KeywordCommand(command)
    if k_c.valid.value:
        return k_c
    elif k_c.valid.message:
        return k_c.valid

    r_c = RouteCommand(command)
    if r_c.valid.value:
        return r_c
    elif r_c.valid.message:
        return r_c.valid

    c_c = ConfirmCommand(command)
    if c_c.valid.value:
        return c_c
    elif c_c.valid.message:
        return c_c.valid

    b_c = BestTimeCommand(command)
    if b_c.valid.value:
        return b_c
    elif b_c.valid.message:
        return b_c.valid

    # if it makes it to this point, then the given command matches no data
    return Response(False)

