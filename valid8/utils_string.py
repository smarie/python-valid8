def end_with_dot(msg,                  # type: str
                 trailing_space=False  # type: bool
                 ):
    # type: (...) -> str
    """
    Utility method to make sure that the provided string ends with dot and possibly with a space.

    The string is first right-stripped before adding the dot or dot space. If a dot is already present, it is
    not duplicated.

    If the string is empty, no dot nor space is added and an empty string is returned.

    :param msg: the string message to edit
    :param trailing_space: a boolean indicating if a space should be added after the trailing dot.
    :return:
    """
    # right-strip help message and ensure dot
    msg = msg.rstrip()
    if len(msg) > 0:
        if msg[-1] != '.':
            msg = msg + ('. ' if trailing_space else '.')
        elif trailing_space:
            msg = msg + ' '

    return msg
