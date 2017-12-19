def end_with_dot_space(msg):
    """
    Utility method to end the provided string with dot and space
    :param msg:
    :return:
    """
    if msg[-2:] == '. ':
        return msg
    elif msg[-1] == '.':
        return msg + ' '
    else:
        return msg + '. '


def end_with_dot(msg):
    """
    Utility method to end a string with a dot if needed

    :param msg:
    :return:
    """
    if msg[-1] == '.':
        return msg
    else:
        return msg + '.'
