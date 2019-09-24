from valid8.base import ValidationFailure


class HasWrongType(ValidationFailure, TypeError):
    """ Custom ValidationFailure raised by instance_of """
    help_msg = "Value should be an instance of {ref_type}"

    def __init__(self,
                 wrong_value,
                 ref_type,
                 **kwargs
                 ):
        super(HasWrongType, self).__init__(wrong_value=wrong_value, ref_type=ref_type, **kwargs)


def instance_of(*args):
    """
    This type validation function can be used in two modes:

     * providing two arguments (x, ref_type), it returns `True` if isinstance(x, ref_type) and raises a HasWrongType
     error if not. If ref_type is a set of types, any match with one of the included types will do

     * providing a single argument (ref_type), this is a function generator. It returns a validation function to check
     that `instance_of(x, ref_type)`.

    :param args:
    :return:
    """
    if len(args) == 2:
        # Standard mode
        value, ref_type = args
        if not isinstance(ref_type, set):
            # ref_type is a single type
            if isinstance(value, ref_type):
                return True
            else:
                raise HasWrongType(wrong_value=value, ref_type=ref_type)

        else:
            # ref_type is a set
            match = False
            # test against each of the provided types
            for ref in ref_type:
                if isinstance(value, ref):
                    match = True
                    break
            if match:
                return True
            else:
                raise HasWrongType(wrong_value=value, ref_type=ref_type,
                                   help_msg='Value should be an instance of any of {ref_type}')

    elif len(args) == 1:
        # Function generator mode
        ref_type = args[0]
        if not isinstance(ref_type, set):
            # ref_type is a single type
            def instance_of_ref(x):
                # noinspection PyTypeHints
                if isinstance(x, ref_type):
                    return True
                else:
                    raise HasWrongType(wrong_value=x, ref_type=ref_type)
        else:
            # ref_type is a set
            def instance_of_ref(x):
                _match = False
                # test against each of the provided types
                for _ref in ref_type:
                    if isinstance(x, _ref):
                        _match = True
                        break
                if _match:
                    return True
                else:
                    raise HasWrongType(wrong_value=x, ref_type=ref_type,
                                       help_msg='Value should be an instance of any of {ref_type}')

        instance_of_ref.__name__ = 'instance_of_%s' % ref_type
        return instance_of_ref
    else:
        raise TypeError('instance_of expected 2 (normal) or 1 (function generator) arguments, got ' + str(len(args)))


class IsWrongType(ValidationFailure, TypeError):
    """ Custom ValidationFailure raised by subclass_of """
    help_msg = 'Value should be a type that is a subclass of {ref_type}'

    def __init__(self,
                 wrong_value,
                 ref_type,
                 **kwargs
                 ):
        super(IsWrongType, self).__init__(wrong_value=wrong_value, ref_type=ref_type, **kwargs)


def subclass_of(*args):
    """
    This type validation function can be used in two modes:
     * providing two arguments (c, ref_type), it returns `True` if issubclass(c, ref_type) and raises a IsWrongType
     error if not. If ref_type is a set of types, any match with one of the included types will do
     * providing a single argument (ref_type), this is a function generator. It returns a validation function to check
     that `subclass_of(c, ref_type)`.

    :param args:
    :return:
    """
    if len(args) == 2:
        # Standard mode
        typ, ref_type = args
        if not isinstance(ref_type, set):
            # ref_type is a single type
            if issubclass(typ, ref_type):
                return True
            else:
                raise IsWrongType(wrong_value=typ, ref_type=ref_type)
        else:
            # ref_type is a set
            match = False
            # test against each of the provided types
            for ref in ref_type:
                if issubclass(typ, ref):
                    match = True
                    break
            if match:
                return True
            else:
                raise IsWrongType(wrong_value=typ, ref_type=ref_type,
                                  help_msg='Value should be a subclass of any of {ref_type}')

    elif len(args) == 1:
        # Function generator mode
        ref_type = args[0]
        if not isinstance(ref_type, set):
            def subclass_of_ref(x):
                # noinspection PyTypeHints
                if issubclass(x, ref_type):
                    return True
                else:
                    raise IsWrongType(wrong_value=x, ref_type=ref_type)
        else:
            # ref_type is a set
            def subclass_of_ref(x):
                _match = False
                # test against each of the provided types
                for _ref in ref_type:
                    if issubclass(x, _ref):
                        _match = True
                        break
                if _match:
                    return True
                else:
                    raise IsWrongType(wrong_value=x, ref_type=ref_type,
                                      help_msg='Value should be a subclass of any of {ref_type}')

        subclass_of_ref.__name__ = 'subclass_of_%s' % ref_type
        return subclass_of_ref
    else:
        raise TypeError('subclass_of expected 2 (normal) or 1 (function generator) arguments, got ' + str(len(args)))
