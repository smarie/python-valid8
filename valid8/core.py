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
    Represents a validation failure with details about which validation function triggered it, what was the value being
    validated, and what was the outcome (as opposed to `BasicFailure` that is basically a blank exception
    type subclassing `ValueError`).

    It is recommended that Users extend this class to define their own failure types, so as to provide a unique failure
    type for each kind of failure (this eases the process of error handling at app-level). An easy way to do this while
    providing details about the failure is to override the 'help_msg' field:

    ```python
    class SurfaceNotInValidRange(Failure):
        help_msg = 'Surface should be a positive number less than 10000 (square meter)'
    ```
    """

    help_msg = ''
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
        contents = '{diag}Function [{val}] returned [{res}] for value [{value}].' \
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
        contents = '{diag}Function [{val}] raised [{exc}: {det}] for value [{value}].' \
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
        if self.help_msg is not None and len(self.help_msg) > 0:
            return self.help_msg + '. ' if self.help_msg[-1] != '.' else ' '
        else:
            return ''


CallableAndFailureTuple = Tuple[Union[Callable, _LambdaExpression], Union[str, Type[BasicFailure]]]
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


def get_validation_function_name(validation_callable: Callable) -> str:
    """
    Used internally to get the name to display concerning a validation function, in error messages for example.

    :param validation_callable: a callable
    :return:
    """
    return validation_callable.__name__ if hasattr(validation_callable, '__name__') else str(validation_callable)


def get_validation_function_names(validation_callables: Sequence[Callable]) -> str:
    return ', '.join([get_validation_function_name(val) for val in validation_callables])


def _failure_raiser(validation_callable: Callable, failure_type: Type[Failure] = None, help_msg: str = None) \
        -> Callable:
    """
    Wraps the provided validation function so that in case of failure it raises the given failure_type or a Failure
    with the given help message.

    :param validation_callable:
    :param failure_type: an optional subclass of `Failure` that should be raised in case of failure, instead of
    `Failure`.
    :param help_msg: an optional string help message for the raised `Failure` (if no failure_type is provided)
    :return:
    """

    # check failure type
    if failure_type is not None and help_msg is not None:
        raise ValueError('Only one of failure_type and help_msg can be set at the same time')

    # convert mini-lambdas to functions if needed
    if isinstance(validation_callable, _LambdaExpression):
        validation_callable = validation_callable.as_function()

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
            if help_msg:
                exc = Failure(validation_function=validation_callable, validated_value=x,
                              validation_outcome=e, help_msg=help_msg)
            else:
                typ = failure_type or Failure
                exc = typ(validation_function=validation_callable, validated_value=x, validation_outcome=e)
            raise exc.with_traceback(e.__traceback__)

        if not result_is_success(res):
            # failure without exception: raise the provided failure type
            if help_msg:
                exc = Failure(validation_function=validation_callable, validated_value=x,
                              validation_outcome=res, help_msg=help_msg)
            else:
                typ = failure_type or Failure
                exc = typ(validation_function=validation_callable, validated_value=x, validation_outcome=res)
            raise exc

    # set a name so that the error messages are more user-friendly
    if help_msg or failure_type:
        raiser.__name__ = 'failure_raiser({}, {})'.format(get_validation_function_name(validation_callable),
                                                          help_msg or failure_type.__name__)
    else:
        raiser.__name__ = 'failure_raiser({})'.format(get_validation_function_name(validation_callable))

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


def _process_validation_function_s(validation_func: ValidationFuncs, auto_and_wrapper: bool = True,
                                   failure_type: Type[Failure] = None, help_msg: str = None) \
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

    # failure type and/or help msg
    if (failure_type is not None or help_msg is not None) and not auto_and_wrapper:
        raise ValueError('failure_type and help_msg may only be used if auto_and_wrapper is set to True')

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
                elif isinstance(v[1], type) and issubclass(v[1], Failure):
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
        if failure_type or help_msg:
            # a _failure_raiser surrounding an and_
            return _failure_raiser(and_(*final_list), failure_type=failure_type, help_msg=help_msg)
        else:
            # a single callable doing the 'and'
            return and_(*final_list)
    else:
        # or the list (typically for use inside or_(), xor_()...)
        return final_list


# ----------- tools to manually create the same wrappers than created internally ----
def failure_raiser(*validation_func: ValidationFuncs, failure_type: Type[Failure] = None, help_msg: str = None) \
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
    return _process_validation_function_s(list(validation_func), failure_type=failure_type,  help_msg=help_msg)


def skip_on_none(*validation_func: ValidationFuncs) -> Callable:
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


def fail_on_none(*validation_func: ValidationFuncs) -> Callable:
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


# ----------- composition (we cant move these in another file since and_() is quite tied to the core)
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

        msg = '{what} validation for value [{val}]. Successes: {succ} / Failures: {fails}' \
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
