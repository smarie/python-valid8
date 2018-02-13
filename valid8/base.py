from copy import copy
from typing import Callable, Sequence, Any  # do not import Type for compatibility with earlier python 3.5

from valid8.utils_string import end_with_dot_space

try:
    # if mini_lambda is here, use this class
    from mini_lambda.main import _LambdaExpression
except ImportError:
    # otherwise define a dummy class
    class _LambdaExpression:
        pass


class RootException(Exception):
    """ All exceptions defined within valid8 inherit from this class """


def should_be_hidden_as_cause(exc):
    """ Used everywhere to decide if some exception type should be displayed or hidden as the casue of an error """
    # reduced traceback in case of HasWrongType (instance_of checks)
    from valid8.validation_lib.types import HasWrongType
    return isinstance(exc, HasWrongType)


def get_callable_name(validation_callable: Callable) -> str:
    """
    Used internally to get the name to display concerning a validation function, in error messages for example.

    :param validation_callable: a callable
    :return:
    """
    return validation_callable.__name__ if hasattr(validation_callable, '__name__') else str(validation_callable)


def get_callable_names(validation_callables: Sequence[Callable]) -> str:
    return ', '.join([get_callable_name(val) for val in validation_callables])


SUCCESS_CONDITIONS = 'in {None, True}'  # was used in some error messages


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


def is_error_of_type(exc, ref_type):
    """
    Helper function to determine if some exception is of some type, by also looking at its declared __cause__

    :param exc:
    :param ref_type:
    :return:
    """
    if isinstance(exc, ref_type):
        return True
    elif exc.__cause__ is not None:
        return is_error_of_type(exc.__cause__, ref_type)


class HelpMsgFormattingException(Exception):
    def __init__(self, help_msg: str, caught: KeyError):
        self.help_msg = help_msg
        self.__cause__ = caught

        msg = "Error while formatting help msg, keyword [{kw}] was not found in the validation context. Help message to " \
              "format was '{msg}'" \
              "".format(msg=help_msg, kw=caught.args[0])
        super(HelpMsgFormattingException, self).__init__(msg)


class HelpMsgMixIn:
    """ A helper class providing the ability to store a help message in the class or in the instance, and to get a
    formatted help message """

    help_msg = ''
    """ This class attribute holds the default help message used when no `help_msg` attribute is set at instance level 
    (for example through the constructor). Subclasses may wish to override this class attribute, or to define a 
    different behaviour by overriding `get_help_msg` """

    def get_help_msg(self, dotspace_ending: bool = False, **kwargs) -> str:
        """
        The method used to get the formatted help message according to kwargs. By default it returns the 'help_msg'
        attribute, whether it is defined at the instance level or at the class level.

        The help message is formatted according to help_msg.format(**kwargs), and may be terminated with a dot
        and a space if dotspace_ending is set to True.

        :param dotspace_ending: True will append a dot and a space at the end of the message if it is not
        empty (default is False)
        :param kwargs: keyword arguments to format the help message
        :return: the formatted help message
        """
        context = self.get_context_for_help_msgs(kwargs)

        if self.help_msg is not None and len(self.help_msg) > 0:
            # first format if needed
            try:
                help_msg = self.help_msg.format(**context)
            except KeyError as e:
                # no need to raise from e, __cause__ is set in the constructor
                raise HelpMsgFormattingException(self.help_msg, e)

            # then add a trailing dot and space if needed
            if dotspace_ending:
                return end_with_dot_space(help_msg)
            else:
                return help_msg
        else:
            return ''

    def get_context_for_help_msgs(self, context_dict):
        """ Subclasses may wish to override this method to change the dictionary of contextual information before it is
        sent to the help message formatter """
        return context_dict


class Failure(HelpMsgMixIn, RootException):
    """
    A utility class to represent base validation functions failures. It contains details about what was the value being
    validated. It allows users to provide a more friendly help message, that may get formatted using contextual
    information. `Failure` is a subclass of `ValueError` for consistency with python best practices.

    It is recommended that users create dedicated subtypes instead of using this generic one, in order to provide a
    unique exception identifier for each failure mode.

    An easy way to create such a class is to simply create a `help_msg` field:

    ```python
    class NotFriendly(Failure):
        help_msg = "The value should be friendly"

    def my_validator(x):
        if not_friendly(x):
            return True
        else:
            raise NotFriendly(wrong_value=x)
    ```

    If you wish that users get more informative help messages, you may insert formatting placeholders in the `help_msg`
    field as it will be automatically formatted using help_msg.format(wrong_value=wrong_value, **kw_context_args).
    Any number of contextual keyword arguments (**kw_context_args) may be provided in the constructor for this purpose:

    ```python
    class ConditionWasNotMet(Failure):
        help_msg = "x={wrong_value} does not meet {condition}"

    def my_validator(x):
        if <condition>:
            return True
        else:
            # the only mandatory argument is `wrong_value`, then any set of keyword arguments may be provided:
            raise ConditionWasNotMet(wrong_value=x, condition=condition)
    ```

    For more stronger constructor signature, your subclass may override the __init__ method. The class below has an
    equivalent behaviour than above, but with a stricter constructor:

    ```python
    class ConditionWasNotMet(Failure):
        def __init__(self, wrong_value, condition):
            help_msg = "x={wrong_value} does not meet {condition}"
            super(ConditionWasNotMet, self).__init__(wrong_value=wrong_value, condition=condition, help_msg=help_msg)
    ```

    Note: if users wish to wrap an *existing* function (such as a lambda or mini lambda) with a Failure raiser, then
    they should subclass `WrappingFailure` instead of `Failure`. See `WrappingFailure` for details.
    """

    def __init__(self, wrong_value: Any, help_msg: str = None, append_details: bool=True, **kw_context_args):
        """
        Creates a Failure associated with failed validation of `wrong_value`. Contextual information may be provided as
        keyword arguments, and will be stored as fields in the created exception instance. An optional help message can
        be provided as an argument, and will be formatted using the dictionary of contextual information provided + the
        `wrong_value` keyword. If `help_msg` is not provided, the `help_msg` class field will be used and formatted the
        same way.

        :param wrong_value: the value that was validated and failed validation
        :param help_msg: an optional help message specific to this failure. If not provided, the class attribute
        `help_msg` will be used. This behaviour may be redefined by subclasses by overriding `get_help_msg`
        :param append_details: a boolean indicating if a default message containing the value should be appended to the
        string representation. Default is True
        :param kw_context_args: optional context (results, other) to store in this failure and that will be also used
        for help message formatting
        """

        self.append_details = append_details

        # store everything in self
        self.wrong_value = wrong_value
        self.__dict__.update(kw_context_args)

        # store help_msg ONLY if non-None otherwise the (possibly user-overriden) class attribute should be left visible
        if help_msg is not None:
            self.help_msg = help_msg

        # call super constructor with nothing, since Exception does not accept keyword arguments and we are redefining
        # __str__ anyway
        super(Failure, self).__init__()

    def __str__(self):
        """ Overrides the default exception message by relying on HelpMsgMixIn """
        if self.append_details:
            return self.get_help_msg(dotspace_ending=True, **self.__dict__) + self.get_details()
        else:
            return self.get_help_msg(**self.__dict__)

    def __repr__(self):
        """ Overrides the default exception representation """
        fields = [name + '=' + str(val) for name, val in self.__dict__.items() if not name.startswith('_')]
        return type(self).__name__ + '(' + ','.join(fields) + ')'

    def get_details(self):
        """ The function called to get the details appended to the help message when self.append_details is True """
        return 'Wrong value: [{}]'.format(self.wrong_value)


class WrappingFailure(Failure):
    """
    Represents a Failure associated with a wrapped validation function. It contains additional details about which
    validation function it was, and what was the outcome.

    This exception class is used when a validation function is wrapped by a `failure_raiser` so as to raise
    a `Failure` when is fails. There are two ways to use this class:

     * either use the syntax `(<wrapped_callable>, <help_msg>)` when defining validation functions, or explicitly call
     `failure_raiser(<wrapped_callable>, help_msg=<help_msg>)`. Both are equivalent and will create instances of
     `WrappingFailure` with the provided help message when the wrapped callable fails.

     * or subclass it explicitly (recommended) and then use the syntax `(<callable>, <subclass>)` or
     `failure_raiser(<wrapped_callable>, failure_type=<subclass>)`. Both are equivalent and will create instances of
     your subclass when the wrapped callable fails.

    It is recommended that Users extend this class to define their own failure types, so as to provide a unique failure
    type for each kind of failure (this eases the process of error handling at app-level). An easy way to do this while
    providing details about the failure is to override the 'help_msg' field:

    ```python
    class SurfaceNotInValidRange(WrappingFailure):
        help_msg = 'Surface should be a positive number less than 10000 (square meter)'
    ```

    Similar to `Failure`, the help message is automatically formatted using variables `wrong_value`, `wrapped_func`,
    `validation_outcome`, and `**kw_context_args`. See `Failure` for details.
    """

    def __init__(self, wrapped_func: Callable, wrong_value: Any, validation_outcome: Any=False, help_msg: str = None,
                 **kw_context_args):
        """
        Creates a WrappingFailure associated with failed validation of `wrong_value` by `wrapped_func`. Additional
        details about the validation outcome (result or exception) can be provided in validation_outcome.

        Contextual information may be provided as keyword arguments, and will be stored as fields in the created
        exception instance. An optional help message can be provided as an argument, and will be formatted using the
        dictionary of contextual information provided + the `wrapped_func`, `wrong_value` and `validation_outcome`
        keywords. If `help_msg` is not provided, the `help_msg` class field will be used and formatted the same way.

        If `validation_outcome` is an Exception, it will be set as the `__cause__` of the created exception, so that
        users of this class do not need to use `raise ... from ...`.

        :param wrapped_func: the validation function that failed validation.
        :param wrong_value: the value that was validated by `wrapped_func` and for which the validation failed
        :param validation_outcome: the caught result of `wrapped_func(wrong_value)`: either a caught exception or a
        variable different than `True` or `None`). Default is `False` for convenience.
        :param help_msg: an optional help message specific to this failure. If not provided, the class attribute
        `help_msg` will be used. This behaviour may be redefined by subclasses by overriding `get_help_msg`
        :param kw_context_args: optional contextual informations to store in the exception, and that may be also used
        to format the help message
        """

        # store details in the object for future access if needed
        self.wrapped_func = wrapped_func
        self.validation_outcome = validation_outcome

        # call super constructor
        super(WrappingFailure, self).__init__(wrong_value=wrong_value, help_msg=help_msg, **kw_context_args)

        # automatically set the exception as the cause, so that we can forget to "raise from"
        if isinstance(validation_outcome, Exception):
            self.__cause__ = validation_outcome

    def get_details(self):
        """ Overrides the method in Failure so as to add a few details about the wrapped function and outcome """

        if isinstance(self.validation_outcome, Exception):
            if isinstance(self.validation_outcome, Failure):
                # do not say again what was the value, it is already mentioned inside :)
                end_str = ''
            else:
                end_str = ' for value [{value}]'.format(value=self.wrong_value)

            contents = 'Function [{wrapped}] raised [{exception}: {details}]{end}.' \
                       ''.format(wrapped=get_callable_name(self.wrapped_func),
                                 exception=type(self.validation_outcome).__name__, details=self.validation_outcome,
                                 end=end_str)
        else:
            contents = 'Function [{wrapped}] returned [{result}] for value [{value}].' \
                       ''.format(wrapped=get_callable_name(self.wrapped_func), result=self.validation_outcome,
                                 value=self.wrong_value)

        return contents

    def get_context_for_help_msgs(self, context_dict):
        """ We override this method from HelpMsgMixIn to replace wrapped_func with its name """
        context_dict = copy(context_dict)
        context_dict['wrapped_func'] = get_callable_name(context_dict['wrapped_func'])
        return context_dict


def _failure_raiser(validation_callable: Callable, failure_type: 'Type[WrappingFailure]' = None, help_msg: str = None,
                    **kw_context_args) -> Callable:
    """
    Wraps the provided validation function so that in case of failure it raises the given failure_type or a WrappingFailure
    with the given help message.

    :param validation_callable:
    :param failure_type: an optional subclass of `WrappingFailure` that should be raised in case of failure, instead of
    `WrappingFailure`.
    :param help_msg: an optional string help message for the raised `WrappingFailure` (if no failure_type is provided)
    :param kw_context_args: optional context arguments for the custom failure message
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
            # no need to raise from e since the __cause__ is already set in the constructor: we can safely commonalize
            res = e

        if not result_is_success(res):
            typ = failure_type or WrappingFailure
            exc = typ(wrapped_func=validation_callable, wrong_value=x, validation_outcome=res,
                      help_msg=help_msg, **kw_context_args)
            raise exc

    # set a name so that the error messages are more user-friendly

    # NO, Do not include the callable type or error message in the name since it is only used in error messages where
    # they will appear anyway !
    # ---
    # if help_msg or failure_type:
    #     raiser.__name__ = 'failure_raiser({}, {})'.format(get_callable_name(validation_callable),
    #                                                       help_msg or failure_type.__name__)
    # else:
    # ---
    # raiser.__name__ = 'failure_raiser({})'.format(get_callable_name(validation_callable))
    raiser.__name__ = get_callable_name(validation_callable)
    # Note: obviously this can hold as long as we do not check the name of this object in any other context than
    # raising errors. If we want to support this, then creating a callable object with everything in the fields will be
    # probably more appropriate so that error messages will be able to display the inner name, while repr() will still
    # say that this is a failure raiser.
    # TODO consider transforming failure_raiser into a class (see comment above)

    return raiser


class ValueIsNone(Failure, TypeError):
    help_msg = "The value must be non-None"


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
    accept_none.__name__ = 'skip_on_none({})'.format(get_callable_name(validation_callable))

    return accept_none


def _none_rejecter(validation_callable: Callable) -> Callable:
    """
    Wraps the given validation callable to reject None values. When a None value is received by the wrapper,
    it is not passed to the validation_callable and instead this function will raise a WrappingFailure. When any other value is
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
            raise ValueIsNone(wrong_value=x)

    # set a name so that the error messages are more user-friendly ==> NO ! here we want to see the checker
    reject_none.__name__ = 'reject_none({})'.format(get_callable_name(validation_callable))

    return reject_none
