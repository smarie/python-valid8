from abc import abstractmethod
from typing import Callable, Union, Tuple, List, Type, Sequence

from mini_lambda.main import _LambdaExpression


class BasicFailure(ValueError):
    """
    A utility class to represent base validation functions failures. It is a subclass of ValueError for consistency with
    python best practices.

    It is however recommended that exceptions raised by base validation functions be specific subtypes instead of that
    generic one, in order to provide a unique exception identifier for each failure mode.

    For example

    ```python
    class ConditionWasNotMet(BasicFailure):
        pass

    def my_validator(x):
        if <condition>:
            return True
        else:
            raise ConditionWasNotMet("x={val} does not meet <condition>".format(val=x))
    ```

    Note: in order to get more consistent error messages as well as error contents, applications may wish to subclass
    the `Failure` type instead of `BasicFailure`. See `Failure` for details.
    """
    pass


class Failure(BasicFailure):
    """
    Represents a validation failure with details (as opposed to `BasicFailure` that is basically a blank exception
    type subclassing `ValueError`).

    Users may typically extend this class to define their
    """

    help_msg = 'No additional diagnostic information is available'
    """ This class attribute holds the default help message used when no `help_msg` attribute is set at instance level 
    (for example through the constructor). Subclasses may wish to override this class attribute, or to define a 
    different behaviour by overriding `get_diagnostics_msg` """

    def __init__(self, validation_function, validated_value, validation_outcome, help_msg: str = None):
        """
        Creates a Failure associated with validation of validated_value using `base_validation_func`.
        Additional details about the validation_outcome (result or exception) can be provided

        :param validation_function: the validation function that failed validation
        :param validated_value: the value that was validated
        :param validation_outcome: the result (either a caught exception or a variable different than `True` or `None`)
        :param help_msg: an optional help message specific to this failure. If not provided, the class attribute
        `help_msg` will be used. This behaviour may be redefined by subclasses by overriding `get_diagnostics_msg`
        """

        # store details in the object for future access if needed
        self.validation_function = validation_function
        self.validated_value = validated_value
        self.validation_outcome = validation_outcome

        # store this one ONLY if non-None, otherwise the class attribute should be left visible
        if help_msg is not None:
            self.help_msg = help_msg

        # create the exception main message according to the type of result
        if isinstance(validation_outcome, Exception):
            contents = self.get_msg_for_caught_exception(validation_function, validated_value, validation_outcome)
            # exception: also link the traceback
            self.__traceback__ = validation_outcome.__traceback__
        else:
            contents = self.get_msg_for_wrong_result(validation_function, validated_value, validation_outcome)

        # call super constructor with the message
        super(BasicFailure, self).__init__(contents)

    def get_msg_for_wrong_result(self, failing_validation_func, value, validation_outcome) -> str:
        """

        :param failing_validation_func:
        :param value:
        :param validation_outcome:
        :return:
        """
        contents = 'base validation function [{val}] failed validating [{value}] and returned [{res}]. {diag}' \
                   ''.format(val=get_validation_function_name(failing_validation_func), res=validation_outcome,
                             value=value, diag=self.get_diagnostics_msg())
        return contents

    def get_msg_for_caught_exception(self, failing_base_validation_func, value, validation_outcome) -> str:
        """

        :param failing_base_validation_func:
        :param value:
        :param validation_outcome:
        :return:
        """
        contents = 'base validation function [{val}] failed validating [{value}] and raised [{exc}: {det}].' \
                   ''.format(val=get_validation_function_name(failing_base_validation_func),
                             exc=type(validation_outcome).__name__, det=validation_outcome,
                             value=value, diag=self.get_diagnostics_msg())
        return contents

    def get_diagnostics_msg(self) -> str:
        """
        The method used to get the diagnostics message associated with a failure. By default it returns the 'help_msg'
        attribute, whether it is defined at the instance level (for example by passing help_msg to the constructor) or
        at the class level (default).

        Subclasses may wish to override this behaviour to provide more fine-grain diagnosis adapted to the validator
        function and the value that was validated and failed validation. All contextual information is available in
        `self`.
        :return: the diagnostics message, explaining for example why this failure happened, and/or recommendations to
        make sure that it does not happen again
        """
        return self.help_msg


CallableAndFailureTuple = Tuple[Callable, Union[str, Type[BasicFailure]]]
""" Represents the allowed construct to define a failure raiser from a validation function: a tuple """

ValidationFunc = Union[Callable, CallableAndFailureTuple]
""" Represents the 'typing' type for a single validation function """

ValidationFuncs = Union[ValidationFunc, List['ValidationFuncs']]  # recursion is used here ('forward reference')
""" Represents the 'typing' type for 'validation_func' arguments in the various methods """

supported_syntax = 'a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of ' \
                   'several such elements. Nested lists are supported and indicate an implicit `and_` (such as the ' \
                   'main list). Tuples indicate an implicit `_failure_raiser`. ' \
                   '[mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of ' \
                   'callables, they will be transformed to functions automatically.'


def get_validation_function_name(validation_callable: Callable) -> str:
    """
    Used internally to get the name to display concerning a validation function, in error messages for example.

    :param validation_callable: a callable
    :return:
    """
    return validation_callable.__name__ if hasattr(validation_callable, '__name__') else str(validation_callable)


def get_validation_function_names(validation_callables: Sequence[Callable]) -> str:
    return ', '.join([get_validation_function_name(val) for val in validation_callables])


def _failure_raiser(validation_callable: Callable, failure_type_or_help_msg: Union[str, Type[Failure]] = None) \
        -> Callable:
    """
    Wraps the provided validation function so that in case of failure it raises the given failure_type or a Failure
    with the given help message.

    :param validation_callable:
    :param failure_type_or_help_msg: a subclass of `Failure` that should be raised in case of failure, or a string help
    message for the raised `Failure`. Optional (default = Failure with no help message).
    :return:
    """

    # convert mini-lambdas to functions if needed
    if isinstance(validation_callable, _LambdaExpression):
        validation_callable = validation_callable.as_function()

    # check failure type
    failure_type_or_help_msg = failure_type_or_help_msg or Failure
    if not issubclass(failure_type_or_help_msg, Failure) and not isinstance(failure_type_or_help_msg, str):
        raise ValueError('failure_type_or_help_msg should be a subclass of Failure or a text, found: {}'
                         ''.format(str(failure_type_or_help_msg)))

    # create wrapper
    # option (a) use the `decorate()` helper method to preserve name and signature of the inner object
    # ==> NO, we want to support also non-function callable objects

    # option (b) simply create a wrapper manually
    def raiser(x):
        """ Wraps validation_callable to raise a failure_type_or_help_msg in case of failure """

        try:
            # perform validation
            res = validation_callable(x)

        except Exception as e:
            # caught any exception: raise the provided failure type with that exception in the details
            if isinstance(failure_type_or_help_msg, str):
                exc = Failure(validation_function=validation_callable, validated_value=x,
                              validation_outcome=e, help_msg=failure_type_or_help_msg)
            else:
                exc = failure_type_or_help_msg(failing_base_validation_func=validation_callable, var_value=x,
                                               validation_outcome=e)
            raise exc.with_traceback(e.__traceback__)

        if not result_is_success(res):
            # failure without exception: raise the provided failure type
            if isinstance(failure_type_or_help_msg, str):
                exc = Failure(validation_function=validation_callable, validated_value=x,
                              validation_outcome=res, help_msg=failure_type_or_help_msg)
            else:
                exc = failure_type_or_help_msg(failing_base_validation_func=validation_callable, var_value=x,
                                               validation_outcome=res)
            raise exc

    # set a name so that the error messages are more user-friendly
    raiser.__name__ = get_validation_function_name(validation_callable)

    return raiser


def is_not_none(x) -> bool:
    """ This method is not actually used in the wrapper created by _none_rejecter (check_not_none), but it is used as a
    reference for raised failure messages, and may be used by users too """
    return x is not None


def _none_accepter(validation_callable: Callable) -> Callable:
    """
    Wraps the given validation callable to accept None values silently. When a None value is received by the wrapper,
    it is not passed to the validation_callable and instead this function will return True. When any other value is
    received the validation_callable is called as usual.

    Note: the created wrapper has the same same than the validation callable for more user-friendly error messages

    :param validation_callable:
    :return:
    """
    # option (a) use the `decorate()` helper method to preserve name and signature of the inner object
    # ==> NO, we want to support also non-function callable objects

    # option (b) simply create a wrapper manually
    def accept_none(x):
        if x is not None:
            # proceed with validation as usual
            return validation_callable(x)
        else:
            # value is None: skip validation
            return True

    # set a name so that the error messages are more user-friendly
    accept_none.__name__ = 'skip_on_none({})'.format(get_validation_function_name(validation_callable))

    return accept_none


def _none_rejecter(validation_callable: Callable) -> Callable:
    """
    Wraps the given validation callable to reject None values. When a None value is received by the wrapper,
    it is not passed to the validation_callable and instead this function will raise a Failure. When any other value is
    received the validation_callable is called as usual.

    :param validation_callable:
    :return:
    """
    # option (a) use the `decorate()` helper method to preserve name and signature of the inner object
    # ==> NO, we want to support also non-function callable objects

    # option (b) simply create a wrapper manually
    def reject_none(x):
        if x is not None:
            return validation_callable(x)
        else:
            raise Failure(is_not_none, x, False)

    # set a name so that the error messages are more user-friendly ==> NO ! here we want to see the checker
    reject_none.__name__ = 'reject_none({})'.format(get_validation_function_name(validation_callable))

    return reject_none


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
     valid8.BasicFailure. In which case the tuple will be replaced with a _failure_raiser(callable, failure_type)

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
            final_list.append(_failure_raiser(*v))

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


class NonePolicy:
    """ This enumeration describes the various validation policies concerning `None` values that may be used with all
    validation entry points """

    __slots__ = []

    SKIP = 1
    """ If this policy is selected, None values will aways be valid (validation routines will not be executed) """
    FAIL = 2
    """ If this policy is selected, None values will aways be invalid (validation routines will not be executed) """
    VALIDATE = 3
    """ If this policy is selected, None values will be treated exactly like other values and follow the same 
    validation process."""


def get_none_policy_text(none_policy: NonePolicy):
    """
    Returns a user-friendly description of a NonePolicy

    :param none_policy:
    :return:
    """
    if none_policy is NonePolicy.SKIP:
        return "accept None without performing validation"
    elif none_policy is NonePolicy.FAIL:
        return "fail on None without performing validation"
    elif none_policy is NonePolicy.VALIDATE:
        return "validate None as any other values"
    else:
        raise ValueError('Invalid none_policy ' + str(none_policy))


def _create_main_validation_function(validation_func: ValidationFuncs, none_policy: NonePolicy) -> Callable:
    """
    Creates the main validation function from base validation function(s) and a None handling policy.

     - validation_func is first transformed into a single callable using `_process_validation_function_s` -
     replacing any tuple found by a `_failure_raiser` callable, replacing any list with `and_`, and transforming any
     mini_lambda expression to a function.
     - Finally if the selected policy for None is SKIP or FAIL, the `and_` is further wrapped by a none
     accepter/rejecter accordingly

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param allow_not_none: True to allow 'not_none' to be present in the list of validators
    :return:
    """
    validation_func = _process_validation_function_s(validation_func)

    if none_policy is NonePolicy.SKIP:
        # accept all None values
        return _none_accepter(validation_func)

    elif none_policy is NonePolicy.FAIL:
        # reject all None values
        return _none_rejecter(validation_func)

    elif none_policy is NonePolicy.VALIDATE:
        # do not handle None specifically
        return validation_func

    else:
        # invalid none_policy
        raise ValueError('Invalid none_policy : ' + str(none_policy))


# ----------- tools to manually create the same wrappers than created internally ----
def failure_raiser(*validation_func: ValidationFunc, failure_type_or_help_msg: Union[str, Type[Failure]] = None) \
        -> Callable:
    """
    Utility method to create a failure raiser manually, surrounding the provided validation function(s).

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param failure_type_or_help_msg: a subclass of `Failure` that should be raised in case of failure, or a string help
    message for the raised `Failure`. Optional (default = Failure with no help message).
    :return:
    """
    validation_func = _process_validation_function_s(list(validation_func))
    return _failure_raiser(validation_func, failure_type_or_help_msg=failure_type_or_help_msg)


def skip_on_none(*validation_func: ValidationFunc) -> Callable:
    """
    Utility method to manually create a validation function ignoring none (None will be accepted without executing the
    inner validation functions)

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """
    validation_func = _process_validation_function_s(list(validation_func))
    return _none_accepter(validation_func)


def fail_on_none(*validation_func: ValidationFunc) -> Callable:
    """
    Utility method to manually create a validation function failing on none (validation will fail without even
    executing the inner validation functions)

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """
    validation_func = _process_validation_function_s(list(validation_func))
    return _none_rejecter(validation_func)


# ----------- negation
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


# ----------- composition (we cant move these in another file since and_() is quite tight to the core)
class CompositionFailure(BasicFailure):
    """ Root failure of all composition operators """

    def __init__(self, validators, value):
        """
        Constructor from a list of validators and a value.
        The constructor will replay the validation process in order to get all the results and attach them in
        the message

        :param validators:
        :param value:
        """
        successes = list()
        failures = dict()
        failures_for_print = dict()

        for validator in validators:
            name = get_validation_function_name(validator)
            try:
                res = validator(value)
                if result_is_success(res):
                    successes.append(name)
                else:
                    failures[validator] = res
                    failures_for_print[name] = str(res)

            except Exception as exc:
                failures[validator] = exc
                failures_for_print[name] = '[{exc_type}] {msg}'.format(exc_type=type(exc).__name__, msg=str(exc))

        msg = '{what} validation for value [{val}]. Successes: {succ} / Failures: {fails} ' \
              ''.format(what=self.get_what(), val=value, succ=successes, fails=failures_for_print)

        super(CompositionFailure, self).__init__(msg)

        # additional information
        self.validators = validators
        self.value = value
        self.success = successes
        self.failures = failures

    @abstractmethod
    def get_what(self) -> str:
        pass


class AtLeastOneFailed(CompositionFailure):
    """ Raised by the and_ operator when at least one of the inner validators failed validation """

    def get_what(self) -> str:
        return 'At least one validator failed'


def and_(*validation_func: ValidationFuncs) -> Callable:
    """
    An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a
    `ValidationException` on the first `False` received or `Exception` caught.

    Note that an implicit `and_` is performed if you provide a list of validators to any of the entry points
    (`@validate`, `@validate_arg`, `assert_valid`, `is_valid`, `Validator`)

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
                    raise AtLeastOneFailed(validation_func, x).with_traceback(e.__traceback__)
                if not result_is_success(res):
                    # one validator was unhappy > raise
                    raise AtLeastOneFailed(validation_func, x)

            return True

        and_v_.__name__ = 'and({})'.format(get_validation_function_names(validation_func))
        return and_v_


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
    :param catch_all: an optional boolean flag. By default, only ValidationError are silently catched and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be catched and turned to a
    'ok' result
    :return:
    """

    # in case this is a list, create a 'and_' around it (otherwise and_ will return the validator without wrapping it)
    main_validator = and_(*validation_func)
    return not_(main_validator, catch_all=catch_all)


SUCCESS_CONDITIONS = 'in {None, True}'  # used in some error messages


def result_is_success(validation_result) -> bool:
    """
    Helper function to check if some results returned by a validation function mean success or failure.

    The result should be True or None for a validation to be considered valid. Note that this is
    quite different from the standard python truth value test (where None is equivalent to False), but it seems
    more adapted to an intuitive usage, where a function that returns silently without any output means a
    successful validation.

    :param validation_result:
    :return:
    """
    return validation_result in {None, True}
