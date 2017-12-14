from typing import Callable

from valid8.core import ValidationFuncs, BasicFailure, _process_validation_function_s, result_is_success, \
    get_validation_function_names, get_validation_function_name, and_


class DidNotFail(BasicFailure):
    """ Raised by the not_ operator when the inner validator did not fail."""
    def __init__(self, validator, value):
        """
        Constructor from the inner validator name and the value that caused validation

        :param validator:
        :param value:
        """
        msg = '{validator} validated value {value} with success, therefore the not() is a failure' \
              ''.format(validator=get_validation_function_name(validator), value=value)
        super(DidNotFail, self).__init__(msg)


def not_(validation_func: ValidationFuncs, catch_all: bool = False) -> Callable:
    """
    Generates the inverse of the provided validator: when the validator returns `False` or raises a `ValidationError`,
    this validator returns `True`. Otherwise it returns `False`.

    By default, exceptions other than `ValidationError` are not caught and therefore fail the validation
    (`catch_all=False`). To change this behaviour you can turn the `catch_all` parameter to `True`, in which case all
    exceptions will be caught instead of just `ValidationError`s.

    Note that you may provide a list of validators to `not_()`. It will be interpreted as `not_(and_(<valiators_list>))`

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param catch_all: an optional boolean flag. By default, only ValidationError are silently catched and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be catched and turned to a
    'ok' result
    :return:
    """

    # in case this is a validation_func list, create a 'and_' around it (otherwise this returns the validation_func)
    # not any more, this is not very intuitive
    # validation_func = and_(validation_func)

    def not_v_(x):
        try:
            res = validation_func(x)
            if not result_is_success(res):  # inverse the result
                return True

        except BasicFailure:
            return True  # caught exception: return True

        except Exception as e:
            if not catch_all:
                raise e
            else:
                return True  # caught exception: return True

        # if we're here that's a failure
        raise DidNotFail(validation_func, x)

    not_v_.__name__ = 'not({})'.format(get_validation_function_name(validation_func))
    return not_v_


class AllValidatorsFailed(BasicFailure):
    """ Raised by the or_ and xor_ operator when all inner validators failed validation """

    def get_what(self) -> str:
        return 'No validator succeeded'


def or_(*validation_func: ValidationFuncs) -> Callable:
    """
    An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught
    exception's message if any.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """

    validation_func = _process_validation_function_s(list(validation_func), auto_and_wrapper=False)

    if len(validation_func) == 1:
        return validation_func[0]  # simplification for single validator case
    else:
        def or_v_(x):
            for validator in validation_func:
                try:
                    res = validator(x)
                    if result_is_success(res):
                        # we can return : one validator was happy
                        return True
                except Exception:
                    # catch all silently
                    pass

            # no validator accepted: gather details and raise
            raise AllValidatorsFailed(validation_func, x)

        or_v_.__name__ = 'or({})'.format(get_validation_function_names(validation_func))
        return or_v_


class XorTooManySuccess(BasicFailure):
    """ Raised by the xor_ operator when more than one validator succeeded """

    def get_what(self) -> str:
        return 'Too many validators (more than 1) succeeded'


def xor_(*validation_func: ValidationFuncs) -> Callable:
    """
    A 'xor' validator: returns `True` if exactly one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught
    exception's message if any.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """

    validation_func = _process_validation_function_s(list(validation_func), auto_and_wrapper=False)

    if len(validation_func) == 1:
        return validation_func[0]  # simplification for single validator case
    else:
        def xor_v_(x):
            ok_validators = []
            for validator in validation_func:
                try:
                    res = validator(x)
                    if result_is_success(res):
                        ok_validators.append(validator)
                except Exception:
                    pass

            # return if were happy or not
            if len(ok_validators) == 1:
                # one unique validator happy: success
                return True

            elif len(ok_validators) > 1:
                # several validation_func happy : fail
                raise XorTooManySuccess(validation_func, x)

            else:
                # no validator happy, fail
                raise AllValidatorsFailed(validation_func, x)

        xor_v_.__name__ = 'xor({})'.format(get_validation_function_names(validation_func))
        return xor_v_


def not_all(*validation_func: ValidationFuncs, catch_all: bool = False) -> Callable:
    """
    An alias for not_(and_(validators)).

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param catch_all: an optional boolean flag. By default, only ValidationError are silently caught and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be caught and turned to a
    'ok' result
    :return:
    """

    # in case this is a list, create a 'and_' around it (otherwise and_ will return the validator without wrapping it)
    main_validator = and_(*validation_func)
    return not_(main_validator, catch_all=catch_all)
