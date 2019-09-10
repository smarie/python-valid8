from abc import abstractmethod
from collections import OrderedDict
from sys import version_info

from makefun import with_signature

from valid8.base import Failure, WrappingFailure, result_is_success, get_callable_names, get_callable_name, \
    _failure_raiser, _none_accepter, _none_rejecter
from valid8.checkers_syntax import _make_checker_callables


try:  # python 3.5+
    from typing import Callable, Union, List, Tuple, Iterable, Mapping, Any
    try:  # python 3.5.3-
        from typing import Type
    except ImportError:
        use_typing = False
    else:
        from valid8.checkers_syntax import ValidationFuncs
        use_typing = version_info > (3, 0)

except TypeError:
    # this happens with python 3.5.2: typing has an issue.
    use_typing = False

except ImportError:
    use_typing = False


class CompositionFailure(Failure):
    """ Root failure of all composition operators """

    def __init__(self,
                 validators,
                 value,
                 cause=None  # type: Exception
                 ):
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
            value_str = ' for value <%s>' % repr(self.wrong_value)
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
    def get_what(self):
        # type: (...) -> str
        pass


class AtLeastOneFailed(CompositionFailure):
    """ Raised by the and_ operator when at least one of the inner validators failed validation """

    def get_what(self):
        # type: (...) -> str
        return 'At least one validation function failed validation'


def and_(*validation_func  # type: ValidationFuncs
         ):
    # type: (...) -> Callable
    """
    An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a
    `AtLeastOneFailed` failure on the first `False` received or `Exception` caught.

    Note that an implicit `and_` is performed if you provide a list of validators to any of the entry points
    (`validator`/`validation`, `@validate_arg`, `@validate_field` ...). For `validate` you need to use an explicit
    one in `custom=<f>`.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements.
        Tuples indicate an implicit `_failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :return:
    """
    validation_funcs = _make_checker_callables(*validation_func)

    if len(validation_funcs) == 1:
        return validation_funcs[0]  # simplification for single validator case: no wrapper
    else:
        def and_v_(x):
            for validator in validation_funcs:
                try:
                    res = validator(x)
                except Exception as e:
                    # one validator was unhappy > raise
                    raise AtLeastOneFailed(validation_funcs, x, cause=e)
                if not result_is_success(res):
                    # one validator was unhappy > raise
                    raise AtLeastOneFailed(validation_funcs, x)

            return True

        and_v_.__name__ = 'and({})'.format(get_callable_names(validation_funcs))
        return and_v_


class DidNotFail(WrappingFailure):
    """ Raised by the not_ operator when the inner validation function did not fail."""
    help_msg = '{wrapped_func} validated value {wrong_value} with success, therefore the not() is a failure'


def not_(validation_func,  # type: CheckerCallable
         catch_all=False   # type: bool
         ):
    # type: (...) -> CheckerCallable
    """
    Generates the inverse of the provided validation functions: when the validator returns `False` or raises a
    `Failure`, this function returns `True`. Otherwise it raises a `DidNotFail` failure.

    By default, exceptions of types other than `Failure` are not caught and therefore fail the validation
    (`catch_all=False`). To change this behaviour you can turn the `catch_all` parameter to `True`, in which case all
    exceptions will be caught instead of just `Failure`s.

    Note that the argument is a **single** callable. You may use `not_all(<validation_functions_list>)` as a shortcut for
    `not_(and_(<validation_functions_list>))` to support several validation functions in the 'not'.

    :param validation_func: the base validation function. A callable.
    :param catch_all: an optional boolean flag. By default, only `Failure` error types are silently caught and turned
        into a 'ok' result. Turning this flag to True will assume that all exceptions should be caught and turned to a
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

    def get_what(self):
        # type: (...) -> str
        return 'No validation function succeeded validation'


def or_(*validation_func  # type: ValidationFuncs
        ):
    # type: (...) -> Callable
    """
    An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `AllValidatorsFailed` failure will be raised, together with details
    about all validation results.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements.
        Tuples indicate an implicit `_failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :return:
    """

    validation_func = _make_checker_callables(*validation_func)

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

    def get_what(self):
        # type: (...) -> str
        return 'Too many validation functions (more than 1) succeeded validation'


def xor_(*validation_func  # type: ValidationFuncs
         ):
    # type: (...) -> Callable
    """
    A 'xor' validation function: returns `True` if exactly one of the provided validators returns `True`. All exceptions
    will be silently caught. In case of failure, a global `XorTooManySuccess` or `AllValidatorsFailed` will be raised,
    together with details about the various validation results.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements.
        Tuples indicate an implicit `_failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :return:
    """

    validation_func = _make_checker_callables(*validation_func)

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


# Python 3+: load the 'more explicit api'
if use_typing:
    new_sig = """(*validation_func: ValidationFuncs,
                  catch_all: bool = False) -> Callable"""
else:
    new_sig = None


@with_signature(new_sig)
def not_all(*validation_func,  # type: ValidationFuncs
            **kwargs
            ):
    # type: (...) -> Callable
    """
    An alias for not_(and_(validators)).

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements.
        Tuples indicate an implicit `_failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :param catch_all: an optional boolean flag. By default, only Failure are silently caught and turned into
        a 'ok' result. Turning this flag to True will assume that all exceptions should be caught and turned to a
        'ok' result
    :return:
    """
    catch_all = pop_kwargs(kwargs, [('catch_all', False)])

    # in case this is a list, create a 'and_' around it (otherwise and_ will return the validation function without
    # wrapping it)
    main_validator = and_(*validation_func)
    return not_(main_validator, catch_all=catch_all)


# Python 3+: load the 'more explicit api'
if use_typing:
    new_sig = """(*validation_func: ValidationFuncs,
                  failure_type: 'Type[WrappingFailure]' = None,
                  help_msg: str = None,
                  **kw_context_args
                  ) -> Callable"""
else:
    new_sig = None


@with_signature(new_sig)
def failure_raiser(*validation_func,   # type: ValidationFuncs
                   **kwargs
                   ):
    # type: (...) -> Callable
    """
    This function is automatically used if you provide a tuple `(<function>, <msg>_or_<Failure_type>)`, to any of the
    methods in this page or to one of the `valid8` decorators. It transforms the provided `<function>` into a failure
    raiser, raising a subclass of `Failure` in case of failure (either not returning `True` or raising an exception)

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements.
        Tuples indicate an implicit `_failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :param failure_type: a subclass of `WrappingFailure` that should be raised in case of failure
    :param help_msg: an optional string help message for the raised `WrappingFailure` or <failure_type>. If `None`
        (default) the default `help_msg` from the `WrappingFailure` or <failure_type> will be used.
    :param kw_context_args:
    :return:
    """
    failure_type, help_msg = pop_kwargs(kwargs, [('failure_type', None), ('help_msg', None)], allow_others=True)
    # the rest of keyword arguments is used as context.
    kw_context_args = kwargs

    # create a single validation function from the possibly several provided
    main_func = and_(*validation_func)

    # finally create the failure raiser
    return _failure_raiser(main_func, failure_type=failure_type,  help_msg=help_msg, **kw_context_args)


def skip_on_none(*validation_func  # type: ValidationFuncs
                 ):
    # type: (...) -> Callable
    """
    This function is automatically used if you use `none_policy=SKIP`, you will probably never need to use it
    explicitly. If wraps the provided function (or implicit `and_` between provided functions) so that `None` values
    are not validated and the code continues executing.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements.
        Tuples indicate an implicit `_failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :return:
    """
    validation_func = and_(*validation_func)
    return _none_accepter(validation_func)


def fail_on_none(*validation_func  # type: ValidationFuncs
                 ):
    # type: (...) -> Callable
    """
    This function is automatically used if you use `none_policy=FAIL`, you will probably never need to use it
    explicitly.  If wraps the provided function (or implicit `and_` between provided functions) so that `None` values
    are not validated and instead a `ValueIsNone` failure is raised.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements.
        Tuples indicate an implicit `_failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :return:
    """
    validation_func = and_(*validation_func)
    return _none_rejecter(validation_func)


def pop_kwargs(kwargs,
               names_with_defaults,  # type: List[Tuple[str, Any]]
               allow_others=False
               ):
    """
    Internal utility method to extract optional arguments from kwargs.

    :param kwargs:
    :param names_with_defaults:
    :param allow_others: if False (default) then an error will be raised if kwargs still contains something at the end.
    :return:
    """
    all_arguments = []
    for name, default_ in names_with_defaults:
        try:
            val = kwargs.pop(name)
        except KeyError:
            val = default_
        all_arguments.append(val)

    if not allow_others and len(kwargs) > 0:
        raise ValueError("Unsupported arguments: %s" % kwargs)

    if len(names_with_defaults) == 1:
        return all_arguments[0]
    else:
        return all_arguments
