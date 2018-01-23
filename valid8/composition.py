from abc import abstractmethod
from collections import OrderedDict

from typing import Callable, Union, List, Tuple  # do not import Type for compatibility with earlier python 3.5

from valid8.base import Failure, result_is_success, get_callable_names, get_callable_name, _failure_raiser, \
    WrappingFailure, _none_accepter, _none_rejecter, _LambdaExpression


CallableAndFailureTuple = Tuple[Union[Callable, _LambdaExpression], Union[str, 'Type[Failure]']]
""" Represents the allowed construct to define a failure raiser from a validation function: a tuple """

ValidationFunc = Union[Callable, _LambdaExpression, CallableAndFailureTuple]
""" Represents the 'typing' type for a single validation function """

ValidationFuncs = Union[ValidationFunc, List['ValidationFuncs']]  # recursion is used here ('forward reference')
""" Represents the 'typing' type for 'validation_func' arguments in the various methods """

supported_syntax = 'a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of ' \
                   'several such elements. Nested lists are supported and indicate an implicit `and_` (such as the ' \
                   'main list). Tuples indicate an implicit `_failure_raiser`. ' \
                   '[mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of ' \
                   'callables, they will be transformed to functions automatically.'


def _process_validation_function_s(validation_func: ValidationFuncs, auto_and_wrapper: bool = True) \
        -> Union[Callable, List[Callable]]:
    """
    This function handles the various ways that users may enter 'validation functions', so as to output a single
    callable method. Setting "auto_and_wrapper" to False allows callers to get a list of callables instead.

    valid8 supports the following expressions for 'validation functions'
     * <ValidationFunc>
     * List[<ValidationFunc>(s)]. The list must not be empty.

    <ValidationFunc> may either be
     * a callable or a mini-lambda expression (instance of _LambdaExpression - in which case it is automatically
     'closed').
     * a Tuple[callable or mini-lambda expression ; failure_type]. Where failure type should be a subclass of
     valid8.Failure. In which case the tuple will be replaced with a _failure_raiser(callable, failure_type)

    When the contents provided does not match the above, this function raises a ValueError. Otherwise it produces a
    list of callables, that will typically be turned into a `and_` in the nominal case except if this is called inside
    `or_` or `xor_`.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_`. Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param auto_and_wrapper: if True (default), this function returns a single callable that is a and_() of all
    functions. Otherwise a list is returned.
    :return:
    """

    # handle the case where validation_func is not yet a list or is empty or none
    if validation_func is None:
        raise ValueError('mandatory validation_func is None')

    elif not isinstance(validation_func, list):
        # so not use list() because we do not want to convert tuples here.
        validation_func = [validation_func]

    elif len(validation_func) == 0:
        raise ValueError('provided validation_func list is empty')

    # now validation_func is a non-empty list
    final_list = []
    for v in validation_func:
        if isinstance(v, _LambdaExpression):
            # special case of a _LambdaExpression: automatically convert to a function
            # note: we have to do it before anything else (such as .index) otherwise we may get failures
            final_list.append(v.as_function())

        elif isinstance(v, tuple):
            # convert all the tuples to failure raisers
            if len(v) == 2:
                if isinstance(v[1], str):
                    final_list.append(_failure_raiser(v[0], help_msg=v[1]))
                elif isinstance(v[1], type) and issubclass(v[1], WrappingFailure):
                    final_list.append(_failure_raiser(v[0], failure_type=v[1]))
                else:
                    raise TypeError('base validation function(s) not compliant with the allowed syntax. Base validation'
                                    ' function(s) can be {}. Found [{}].'.format(supported_syntax, str(v)))
            else:
                raise TypeError('base validation function(s) not compliant with the allowed syntax. Base validation'
                                ' function(s) can be {}. Found [{}].'.format(supported_syntax, str(v)))

        elif callable(v):
            # use the validator directly
            final_list.append(v)

        elif isinstance(v, list):
            # a list is an implicit and_, make it explicit
            final_list.append(and_(*v))

        else:
            raise TypeError('base validation function(s) not compliant with the allowed syntax. Base validation'
                            ' function(s) can be {}. Found [{}].'.format(supported_syntax, str(v)))

    # return what is required:
    if auto_and_wrapper:
        # a single callable doing the 'and'
        return and_(*final_list)
    else:
        # or the list (typically for use inside or_(), xor_()...)
        return final_list


# ----------- we cant move these in another file since and_() is very tied to the above function.
class CompositionFailure(Failure):
    """ Root failure of all composition operators """

    def __init__(self, validators, value, cause: Exception=None):
        """
        Constructor from a list of validators and a value.
        The constructor will replay the validation process in order to get all the results and attach them in
        the message

        :param validators:
        :param value:
        :param cause
        """
        successes, failures = self.play_all_validators(validators, value)

        # store information
        self.validators = validators
        self.value = value
        self.successes = successes
        self.failures = failures

        super(CompositionFailure, self).__init__(wrong_value=value)

        # automatically set the exception as the cause, so that we can forget to "raise from"
        if cause is not None:
            self.__cause__ = cause

    def get_details(self):
        """ Overrides the base method in order to give details on the various successes and failures """

        # transform the dictionary of failures into a printable form
        need_to_print_value = True
        failures_for_print = OrderedDict()
        for validator, failure in self.failures.items():
            name = get_callable_name(validator)
            if isinstance(failure, Exception):
                if isinstance(failure, WrappingFailure) or isinstance(failure, CompositionFailure):
                    need_to_print_value = False
                failures_for_print[name] = '{exc_type}: {msg}'.format(exc_type=type(failure).__name__, msg=str(failure))
            else:
                failures_for_print[name] = str(failure)

        if need_to_print_value:
            value_str = ' for value [{val}]'.format(val=self.wrong_value)
        else:
            value_str = ''

        # OrderedDict does not pretty print...
        key_values_str = [repr(key) + ': ' + repr(val) for key, val in failures_for_print.items()]
        failures_for_print_str = '{' + ', '.join(key_values_str) + '}'

        # Note: we do note cite the value in the message since it is most probably available in inner messages [{val}]
        msg = '{what}{possibly_value}. Successes: {success} / Failures: {fails}' \
              ''.format(what=self.get_what(), possibly_value=value_str,
                        success=self.successes, fails=failures_for_print_str)

        return msg

    def play_all_validators(self, validators, value):
        """
        Utility method to play all the provided validators on the provided value and output the

        :param validators:
        :param value:
        :return:
        """
        successes = list()
        failures = OrderedDict()
        for validator in validators:
            name = get_callable_name(validator)
            try:
                res = validator(value)
                if result_is_success(res):
                    successes.append(name)
                else:
                    failures[validator] = res

            except Exception as exc:
                failures[validator] = exc

        return successes, failures

    @abstractmethod
    def get_what(self) -> str:
        pass


class AtLeastOneFailed(CompositionFailure):
    """ Raised by the and_ operator when at least one of the inner validators failed validation """

    def get_what(self) -> str:
        return 'At least one validation function failed validation'


def and_(*validation_func: ValidationFuncs) -> Callable:
    """
    An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a
    `AtLeastOneFailed` failure on the first `False` received or `Exception` caught.

    Note that an implicit `and_` is performed if you provide a list of validators to any of the entry points
    (`validate`, `validation`/`validator`, `@validate_arg`, `@validate_out`, `@validate_field` ...)

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """

    validation_func = _process_validation_function_s(list(validation_func), auto_and_wrapper=False)

    if len(validation_func) == 1:
        return validation_func[0]  # simplification for single validator case: no wrapper
    else:
        def and_v_(x):
            for validator in validation_func:
                try:
                    res = validator(x)
                except Exception as e:
                    # one validator was unhappy > raise
                    raise AtLeastOneFailed(validation_func, x, cause=e)
                if not result_is_success(res):
                    # one validator was unhappy > raise
                    raise AtLeastOneFailed(validation_func, x)

            return True

        and_v_.__name__ = 'and({})'.format(get_callable_names(validation_func))
        return and_v_


class DidNotFail(WrappingFailure):
    """ Raised by the not_ operator when the inner validation function did not fail."""
    help_msg = '{wrapped_func} validated value {wrong_value} with success, therefore the not() is a failure'


def not_(validation_func: ValidationFuncs, catch_all: bool = False) -> Callable:
    """
    Generates the inverse of the provided validation functions: when the validator returns `False` or raises a
    `Failure`, this function returns `True`. Otherwise it raises a `DidNotFail` failure.

    By default, exceptions of types other than `Failure` are not caught and therefore fail the validation
    (`catch_all=False`). To change this behaviour you can turn the `catch_all` parameter to `True`, in which case all
    exceptions will be caught instead of just `Failure`s.

    Note that you may use `not_all(<validation_functions_list>)` as a shortcut for
    `not_(and_(<validation_functions_list>))`

    :param validation_func: the base validation function. A callable, a tuple(callable, help_msg_str),
    a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param catch_all: an optional boolean flag. By default, only Failure are silently caught and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be caught and turned to a
    'ok' result
    :return:
    """

    def not_v_(x):
        try:
            res = validation_func(x)
            if not result_is_success(res):  # inverse the result
                return True

        except Failure:
            return True  # caught failure: always return True

        except Exception as e:
            if not catch_all:
                raise e
            else:
                return True  # caught exception in 'catch_all' mode: return True

        # if we're here that's a failure
        raise DidNotFail(wrapped_func=validation_func, wrong_value=x, validation_outcome=res)

    not_v_.__name__ = 'not({})'.format(get_callable_name(validation_func))
    return not_v_


class AllValidatorsFailed(CompositionFailure):
    """ Raised by the or_ and xor_ operator when all inner validators failed validation """

    def get_what(self) -> str:
        return 'No validation function succeeded validation'


def or_(*validation_func: ValidationFuncs) -> Callable:
    """
    An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `AllValidatorsFailed` failure will be raised, together with details
    about all validation results.

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
                # noinspection PyBroadException
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

        or_v_.__name__ = 'or({})'.format(get_callable_names(validation_func))
        return or_v_


class XorTooManySuccess(CompositionFailure):
    """ Raised by the xor_ operator when more than one validation function succeeded """

    def get_what(self) -> str:
        return 'Too many validation functions (more than 1) succeeded validation'


def xor_(*validation_func: ValidationFuncs) -> Callable:
    """
    A 'xor' validation function: returns `True` if exactly one of the provided validators returns `True`. All exceptions
    will be silently caught. In case of failure, a global `XorTooManySuccess` or `AllValidatorsFailed` will be raised,
    together with details about the various validation results.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """

    validation_func = _process_validation_function_s(list(validation_func), auto_and_wrapper=False)

    if len(validation_func) == 1:
        return validation_func[0]  # simplification for single validation function case
    else:
        def xor_v_(x):
            ok_validators = []
            for val_func in validation_func:
                # noinspection PyBroadException
                try:
                    res = val_func(x)
                    if result_is_success(res):
                        ok_validators.append(val_func)
                except Exception:
                    pass

            # return if were happy or not
            if len(ok_validators) == 1:
                # one unique validation function happy: success
                return True

            elif len(ok_validators) > 1:
                # several validation_func happy : fail
                raise XorTooManySuccess(validation_func, x)

            else:
                # no validation function happy, fail
                raise AllValidatorsFailed(validation_func, x)

        xor_v_.__name__ = 'xor({})'.format(get_callable_names(validation_func))
        return xor_v_


def not_all(*validation_func: ValidationFuncs, catch_all: bool = False) -> Callable:
    """
    An alias for not_(and_(validators)).

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param catch_all: an optional boolean flag. By default, only Failure are silently caught and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be caught and turned to a
    'ok' result
    :return:
    """

    # in case this is a list, create a 'and_' around it (otherwise and_ will return the validation function without
    # wrapping it)
    main_validator = and_(*validation_func)
    return not_(main_validator, catch_all=catch_all)


def failure_raiser(*validation_func: ValidationFuncs, failure_type: 'Type[WrappingFailure]' = None,
                   help_msg: str = None, **kw_context_args) -> Callable:
    """
    This function is automatically used if you provide a tuple `(<function>, <msg>_or_<Failure_type>)`, to any of the
    methods in this page or to one of the `valid8` decorators. It transforms the provided `<function>` into a failure
    raiser, raising a subclass of `Failure` in case of failure (either not returning `True` or raising an exception)

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param failure_type: a subclass of `WrappingFailure` that should be raised in case of failure
    :param help_msg: a string help message for the raised `WrappingFailure`. Optional (default = WrappingFailure with
    no help message).
    :return:
    """
    main_func = _process_validation_function_s(list(validation_func))
    return _failure_raiser(main_func, failure_type=failure_type,  help_msg=help_msg, **kw_context_args)


def skip_on_none(*validation_func: ValidationFuncs) -> Callable:
    """
    This function is automatically used if you use `none_policy=SKIP`, you will probably never need to use it
    explicitly. If wraps the provided function (or implicit `and_` between provided functions) so that `None` values
    are not validated and the code continues executing.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """
    validation_func = _process_validation_function_s(list(validation_func))
    return _none_accepter(validation_func)


def fail_on_none(*validation_func: ValidationFuncs) -> Callable:
    """
    This function is automatically used if you use `none_policy=FAIL`, you will probably never need to use it
    explicitly.  If wraps the provided function (or implicit `and_` between provided functions) so that `None` values
    are not validated and instead a `ValueIsNone` failure is raised.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """
    validation_func = _process_validation_function_s(list(validation_func))
    return _none_rejecter(validation_func)
