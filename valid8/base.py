import sys

import re
from copy import copy

try:
    # noinspection PyUnresolvedReferences
    from typing import Callable, Iterable, Any, Dict, Union
    try:  # python 3.5.3-
        # noinspection PyUnresolvedReferences
        from typing import Type
    except ImportError:
        pass
    else:
        # 1. the lowest-level user or 3d party-provided validation functions
        ValidationCallable = Union[Callable[[Any], Any],                    # f(val)
                                   Callable[..., Any]]                      # f(*args) or f(*args, **ctx) or f(val, **ctx)
        try:
            # noinspection PyUnresolvedReferences
            from mini_lambda import y
            ValidationCallableOrLambda = Union[ValidationCallable, type(y)]
            """A base validation function is a callable with signature (val), returning `True` or `None` in case of 
            success. Mini-lambda expressions are supported too."""
        except ImportError:
            ValidationCallableOrLambda = ValidationCallable
            """A base validation function is a callable with signature (val), returning `True` or `None` in case of 
            success"""

except ImportError:
    pass

try:
    # mini lambda 2.1.0
    from mini_lambda import is_mini_lambda_expr as is_mini_lambda
except ImportError:
    try:
        # mini lambda <= 2.0.1 backwards compliance
        # noinspection PyProtectedMember,PyUnresolvedReferences
        from mini_lambda.main import _LambdaExpression

        def is_mini_lambda(f):
            return isinstance(f, _LambdaExpression)
    except ImportError:
        # no mini lambda
        def is_mini_lambda(f):
            return False

from valid8.utils.string_tools import end_with_dot
from valid8.utils.signature_tools import getfullargspec, IsBuiltInError


class RootException(Exception):
    """ All exceptions defined within valid8 inherit from this class """


if sys.version_info < (3, 0):
    from future.utils import raise_with_traceback

    def raise_(exc):
        try:
            cause = exc.__cause__
        except AttributeError:
            raise exc
        else:
            if cause is not None:
                raise_with_traceback(exc)
            else:
                raise exc
else:
    def raise_(exc):
        raise exc


def should_be_hidden_as_cause(exc):
    """ Used everywhere to decide if some exception type should be displayed or hidden as the casue of an error """
    # reduced traceback in case of HasWrongType (instance_of checks)
    from valid8.validation_lib.types import HasWrongType, IsWrongType
    return isinstance(exc, (HasWrongType, IsWrongType))


def get_callable_name(validation_callable  # type: ValidationCallable
                      ):
    # type: (...) -> str
    """
    Used internally to get the name to display concerning a validation function, in error messages for example.

    :param validation_callable: a callable
    :return:
    """
    return validation_callable.__name__ if hasattr(validation_callable, '__name__') else str(validation_callable)


def get_callable_names(validation_callables  # type: Iterable[ValidationCallable]
                       ):
    # type: (...) -> str
    return ', '.join([get_callable_name(val) for val in validation_callables])


SUCCESS_CONDITIONS = 'in {None, True}'  # was used in some error messages


try:
    import numpy as np
except ImportError:
    NP_TRUE = None  # not available - use None as it is already a success condition

    def result_is_success(validation_result  # type: Any
                          ):
        # type: (...) -> bool
        """
        Helper function to check if some results returned by a validation function mean success or failure.

        The result should be True or None for a validation to be considered valid. Note that this is
        quite different from the standard python truth value test (where None is equivalent to False), but it seems
        more adapted to an intuitive usage, where a function that returns silently without any output means a
        successful validation.

        :param validation_result:
        :return:
        """
        # WARNING: if you change this definition, do not forget to do a search on all occurences of `result_is_success`
        # in the code base, and replace all inlined versions accordingly
        return (validation_result is None) or (validation_result is True)
else:
    NP_TRUE = np.bool_(True)

    def result_is_success(validation_result  # type: Any
                          ):
        # type: (...) -> bool
        """
        Helper function to check if some results returned by a validation function mean success or failure.

        The result should be True or None for a validation to be considered valid. Note that this is
        quite different from the standard python truth value test (where None is equivalent to False), but it seems
        more adapted to an intuitive usage, where a function that returns silently without any output means a
        successful validation.

        :param validation_result:
        :return:
        """
        # WARNING: if you change this definition, do not forget to do a search on all occurences of `result_is_success`
        # in the code base, and replace all inlined versions accordingly
        return (validation_result is None) or (validation_result is True) or (validation_result is NP_TRUE)


def is_error_of_type(exc, ref_type):
    """
    Helper function to determine if some exception is of some type, by also looking at its declared __cause__

    :param exc:
    :param ref_type:
    :return:
    """
    if isinstance(exc, ref_type):
        return True
    elif hasattr(exc, '__cause__') and exc.__cause__ is not None:
        return is_error_of_type(exc.__cause__, ref_type)


class HelpMsgFormattingException(Exception):
    """
    Exception raised when the help message cannot be formatted with the available context dictionary.
    See `HelpMsgMixIn` for details.
    """
    def __init__(self,
                 help_msg,      # type: str
                 context,       # type: Dict[str, Any]
                 varname=None,  # type: str
                 caught=None,   # type: KeyError
                 ):
        """
        Constructor

        :param help_msg:
        :param caught:
        :param context:
        :param varname:
        """
        self.help_msg = help_msg
        if not ((varname is None) ^ (caught is None)):
            raise ValueError("Only one of `varname` or `caught` should be provided")
        if caught is not None:
            varname = caught.args[0]
            self.__cause__ = caught

        msg = "Error while formatting the help message, variable '%s' is used in the `help_msg` but was not found " \
              "in the available context. Help message template was '%s'. Variables available: %s" \
              "" % (varname, help_msg, context)
        super(HelpMsgFormattingException, self).__init__(msg)


class HelpMsgMixIn(object):
    """ A helper class providing the ability to store a help message in the class or in the instance, and to get a
    formatted help message """

    __max_str_length_displayed__ = 100
    """ objects with a string representation larger than this constant will not be printed in the error messages. 
    Note that you can override this either on the class or on a particular instance. See `get_variable_str()` """

    help_msg = ''
    """ This class attribute holds the default help message used when no `help_msg` attribute is set at instance level 
    (for example through the constructor). Subclasses may wish to override this class attribute, or to define a 
    different behaviour by overriding `get_help_msg` """

    def get_help_msg(self):
        # type: (...) -> str
        """
        The method used to get the formatted help message according to kwargs. By default it returns the 'help_msg'
        attribute, whether it is defined at the instance level or at the class level.

        The help message is formatted according to help_msg.format(**context),
        where `context = self.get_context_for_help_msgs()` so that subclasses may easily override the behaviour.

        :return: the formatted help message
        """
        if self.help_msg is None or len(self.help_msg) == 0:
            return ''
        else:
            # grab the help msg and context info
            help_msg = self.help_msg
            context = self.get_context_for_help_msgs()

            # first format if needed
            try:
                is_context_a_copy = False
                variables = re.findall("{\\S+}", help_msg)
                for var_name_ in set(variables):
                    # extract the variable name
                    var_name_ = var_name_[1:-1]

                    # if variable is used in the context
                    if var_name_ in context:
                        # if the variable string representation is too big, replace its use in the help message
                        # (so as to keep the original object available for debug)
                        var_to_str = str(context[var_name_])
                        if len(var_to_str) > self.__max_str_length_displayed__:
                            if not is_context_a_copy:
                                # create a copy because we will modify it
                                context = copy(context)
                                is_context_a_copy = True

                            new_name = '@@@@' + var_name_ + '@@@@'
                            help_msg = help_msg.replace('{' + var_name_ + '}', '{' + new_name + '}')
                            context[new_name] = "(too big for display)"
                    else:
                        # anticipate the formatting issue
                        raise HelpMsgFormattingException(self.help_msg, context=context, varname=var_name_)

                # finally format the help message
                help_msg = help_msg.format(**context)

            except KeyError as e:
                # no need to raise from e, __cause__ is set in the constructor
                raise HelpMsgFormattingException(self.help_msg, context=context, caught=e)

            return help_msg

    def get_context_for_help_msgs(self):
        """ Subclasses may wish to override this method to change the dictionary of contextual information before it is
        sent to the help message formatter """
        return self.__dict__


MISSING = object()


class ValidationFailure(HelpMsgMixIn, RootException):
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
        help_msg = "x={wrong_value} does not meet {condition}"
        def __init__(self, wrong_value, condition, **kwargs):
            super(ConditionWasNotMet, self).__init__(wrong_value=wrong_value, condition=condition, **kwargs)
    ```

    Note: if users wish to wrap an *existing* function (such as a lambda or mini lambda) with a failure raiser, then
    they should subclass `Failure`. See `Failure` for details.
    """

    # We do not use slots otherwise `help_msg` cannot easily be overridden by a class attribute
    # __slots__ = 'wrong_value', validation_func', 'validation_outcome', 'append_details', 'context'

    def __init__(self,
                 wrong_value,                 # type: Any
                 help_msg=None,               # type: str
                 append_details=True,         # type: bool
                 validation_func=None,        # type: ValidationCallable
                 validation_outcome=MISSING,  # type: Any
                 **kw_context_args):
        """
        Creates a failure associated with failed validation of `wrong_value`. Contextual information may be provided as
        keyword arguments, and will be stored as fields in the created exception instance. An optional help message can
        be provided as an argument, and will be formatted using the dictionary of contextual information provided + the
        `wrong_value` keyword. If `help_msg` is not provided, the `help_msg` class field will be used and formatted the
        same way.

        :param wrong_value: the value that was validated and failed validation
        :param help_msg: an optional help message specific to this failure. If not provided, the class attribute
            `help_msg` will be used. This behaviour may be redefined by subclasses by overriding `get_help_msg`
        :param append_details: a boolean indicating if a default message containing the value should be appended to the
            string representation. Default is True
        :param validation_func: optional, the validation function that was used to perform the validation per se. If
            provided, a non-None validation_outcome should also be provided
        :param validation_outcome: optional, the outcome of the validation function used. If provided, a non-None
            validation_func should also be provided
        :param kw_context_args: optional context (results, other) to store in this failure and that will be also used
            for help message formatting
        """
        # store everything in self
        self.wrong_value = wrong_value
        self.append_details = append_details
        # context data
        self.__dict__.update(kw_context_args)
        self.has_context_data = len(kw_context_args) > 0

        # store help_msg ONLY if non-None otherwise the (possibly user-overridden) class attribute should stay visible
        if help_msg is not None:
            self.help_msg = help_msg

        # store details about validation function and outcome if provided
        if (validation_func is not None) ^ (validation_outcome is not MISSING):
            raise ValueError("If a non-none `validation_func` is provided a `validation_outcome` should be "
                             "provided and conversely.")
        if validation_func is not None:
            self.validation_func = validation_func
        if validation_outcome is not MISSING:
            self.validation_outcome = validation_outcome
            # automatically set the exception as the cause, so that we can forget to "raise from"
            if isinstance(validation_outcome, Exception):
                self.__cause__ = validation_outcome

        # call super constructor with nothing, since Exception does not accept keyword arguments and we are redefining
        # __str__ anyway
        super(ValidationFailure, self).__init__()

    def is_wrapped_failure(self):
        """If True this failure was caused by catching a non-True non-None result from a validation function.
        If False this was explicitly raised BY a validation function"""
        return hasattr(self, 'validation_func')

    def __repr__(self):
        """ Overrides the default exception representation """
        fields = ['%s=%s' % (name, val) for name, val in self.__dict__.items() if not name.startswith('_')]
        return type(self).__name__ + '(' + ','.join(fields) + ')'

    def get_str_for_errors(self):
        """The method called by `ValidationError` and self.get_details() in case of wrapped failure"""
        return self.to_str(with_type=True, compact_mode=False)

    def get_str_for_composition_errors(self):
        """The method called by `CompositionFailure`. We do not need to display as much information."""
        return self.to_str(with_type=True, compact_mode=True)

    def __str__(self):
        """ Overrides the default exception message by relying on `HelpMsgMixIn` """
        return self.to_str(with_type=False, compact_mode=False)

    def to_str(self, with_type=False, compact_mode=False):
        if with_type:
            prefix = "%s: " % type(self).__name__
        else:
            prefix = ''

        try:
            # right-strip help message and ensure dot
            help_msg = self.get_help_msg()
            if self.append_details:
                details = self.get_details(compact_mode=compact_mode)
                help_msg = end_with_dot(help_msg, trailing_space=len(details.rstrip()) > 0)
                return "%s%s%s" % (prefix, help_msg, details)
            else:
                return "%s%s" % (prefix, end_with_dot(help_msg))

        except HelpMsgFormattingException as f:
            return "%s%s" % (prefix, f)

        except Exception as e:
            return "%sError while formatting help message: %s" % (prefix, e)

    def get_context_for_help_msgs(self):
        """
        From `HelpMsgMixIn.get_help_msg(self)`
        We override it to use self.context and to replace validation_func with its name
        """
        context_dict = self.__dict__
        if 'validation_func' in context_dict:
            context_dict = copy(context_dict)
            context_dict['validation_func'] = get_callable_name(context_dict['validation_func'])
            return context_dict
        else:
            return context_dict

    def get_wrong_value_str(self):
        """Utility to get the wrong value string or a replacement text if its repr is too long"""
        wrong_val_str = repr(self.wrong_value)
        if len(wrong_val_str) > self.__max_str_length_displayed__:
            return '(Actual value is too big to be printed in this message)'
        else:
            return wrong_val_str

    def get_details(self, compact_mode=False):
        """
        The function called to get the details appended to the help message when self.append_details is True.
        It ends with a dot.
        :return:
        """
        if not self.is_wrapped_failure():
            # --- Basic details: display the wrong value
            if compact_mode:
                # the value is already displayed elsewhere.
                return ""
            else:
                return 'Wrong value: %s.' % self.get_wrong_value_str()
        else:
            # --- Wrapped failure: display more details concerning the validation function and caught exception
            outcome = self.validation_outcome

            if isinstance(outcome, ValidationFailure):
                if compact_mode:
                    # use the compact string
                    return outcome.to_str(with_type=True, compact_mode=True)
                else:
                    wrapped_func_name = get_callable_name(self.validation_func)
                    # do not say again what was the value, it is already mentioned inside :)
                    # do not put an ending dot, that's the responsibility of the failure implementor
                    return 'Function [%s] raised %s' % (wrapped_func_name, outcome.get_str_for_errors())

            elif isinstance(outcome, Exception):
                # other exception
                exc_type = type(outcome).__name__
                if compact_mode:
                    return "%s: %s" % (exc_type, outcome)
                else:
                    wrapped_func_name = get_callable_name(self.validation_func)
                    # do not put an ending dot, that's the responsibility of the failure implementor
                    return 'Function [%s] raised %s: %s' % (wrapped_func_name, exc_type, outcome)

            else:
                # outcome is a non-None non-True value
                outcome_str = str(outcome)
                if compact_mode:
                    return "Returned %s." % outcome_str
                else:
                    wrapped_func_name = get_callable_name(self.validation_func)
                    value_str = self.get_wrong_value_str()
                    return 'Function [%s] returned [%s] for value %s.' % (wrapped_func_name, outcome_str, value_str)


class Invalid(ValidationFailure):
    """ validation failures raised by `failure_raiser`"""
    def get_str_for_composition_errors(self):
        """The method called by `CompositionFailure`. We do not need to display as much information."""
        return self.to_str(with_type=self.is_customized(), compact_mode=True)


class InvalidValue(Invalid, ValueError):
    def is_customized(self):
        return (self.__class__ is not InvalidValue) or (self.help_msg != InvalidValue.help_msg) or self.has_context_data


class InvalidType(Invalid, TypeError):
    def is_customized(self):
        return (self.__class__ is not InvalidType) or (self.help_msg != InvalidValue.help_msg) or self.has_context_data


def failure_raiser(validation_callable,   # type: ValidationCallableOrLambda
                   help_msg=None,         # type: str
                   failure_type=None,     # type: Type[ValidationFailure]
                   **kw_context_args):
    # type: (...) -> ValidationCallable
    """
    Wraps the provided validation function so that in case of failure it raises the given `failure_type` or a
    `ValidationFailure` with the given help message.

    >>> import sys, pytest
    >>> if sys.version_info < (3, 0):
    ...     pytest.skip('doctest skipped in python 2 because exception namespace is different but details matter')

    >>> def is_big(x): return x > 10
    >>> is_big_with_details = failure_raiser(is_big, help_msg="x should be big")
    >>> is_big_with_details(11)
    >>> is_big_with_details(2)
    Traceback (most recent call last):
    ...
    valid8.base.InvalidValue: x should be big. Function [is_big] returned [False] for value 2.
    >>> class MyTooSmall(ValidationFailure):
    ...     help_msg = "x should be bigger than 10. Found {wrong_value}"
    >>> is_big_with_details = failure_raiser(is_big, failure_type=MyTooSmall)
    >>> is_big_with_details(11)
    >>> is_big_with_details(2)
    Traceback (most recent call last):
    ...
    valid8.base.MyTooSmall: x should be bigger than 10. Found 2. Function [is_big] returned [False] for value 2.

    mini-lambda functions are automatically transformed to functions:

    >>> from mini_lambda import x
    >>> is_small_with_details = failure_raiser(x < 3, help_msg="x should be smaller than 3")
    >>> is_small_with_details(2)
    >>> is_small_with_details(11)
    Traceback (most recent call last):
    ...
    valid8.base.InvalidValue: x should be smaller than 3. Function [x < 3] returned [False] for value 11.

    :param validation_callable:
    :param failure_type: an optional subclass of `ValidationFailure` that should be raised in case of failure, instead
        of `ValidationFailure`.
    :param help_msg: an optional string help message for the raised failure.
    :param kw_context_args: optional context arguments for the custom failure message
    :return:
    """
    # create wrapper
    # --option (a) use `makefun or functool @wraps()` helper method to preserve name and signature of the inner object
    # ==> NO, we want to support also non-function callable objects

    # --option (b) simply create a wrapper manually
    should_wrap_failures = (failure_type is not None) or (help_msg is not None) or (len(kw_context_args) > 0)
    typ = failure_type if failure_type is not None else InvalidValue

    is_mini = False
    if is_mini_lambda(validation_callable):
        is_mini = True
        validation_callable = validation_callable.as_function()

    # general case - adapt to the signature required (val, ctx), (*args) or (val, **ctx)
    call_it = make_callable(validation_callable, is_mini_lambda=is_mini)

    def raiser(x, **ctx):
        """ Wraps validation_callable to raise a failure_type_or_help_msg in case of failure """

        try:
            # perform validation
            res = call_it(x, **ctx)
            # if not result_is_success(res): <= DO NOT REMOVE THIS COMMENT
            success = (res is None) or (res is True) or (res is NP_TRUE)

        except ValidationFailure as f:
            # failures should be raised "as is"
            if not should_wrap_failures:
                raise
            else:
                res = f
                success = False

        except Exception as e:
            # no need to raise from e since the __cause__ is already set in the constructor: we can safely commonalize
            res = e
            if typ is InvalidValue and isinstance(e, TypeError) and not isinstance(e, ValueError):
                # special case: we want to raise a Failure that inherits from TypeError
                exc = InvalidType(wrong_value=x, validation_func=validation_callable, validation_outcome=res,
                                  help_msg=help_msg, **kw_context_args)
                raise exc
            success = False

        if not success:
            # nominal failure: raise the proper exception
            exc = typ(wrong_value=x, validation_func=validation_callable, validation_outcome=res,
                      help_msg=help_msg, **kw_context_args)
            raise exc

    # set a name so that the error messages are more user-friendly

    # NO, Do not include the callable type or error message in the name since it is only used in error messages where
    # they will appear anyway !
    # ---
    # if help_msg or failure_type:
    #     raiser.__name__ = 'failure_raiser(%s, %s)' % (get_callable_name(validation_callable),
    #                                                   help_msg or failure_type.__name__)
    # else:
    # ---
    # raiser.__name__ = 'failure_raiser(%s)' % get_callable_name(validation_callable)
    raiser.__name__ = get_callable_name(validation_callable)
    # Note: obviously this can hold as long as we do not check the name of this object in any other context than
    # raising errors. If we want to support this, then creating a callable object with everything in the fields will be
    # probably more appropriate so that error messages will be able to display the inner name, while repr() will still
    # say that this is a failure raiser.
    # TODO consider transforming failure_raiser into a class (see comment above)

    return raiser


def as_failure_raiser(failure_type=None,     # type: Type[ValidationFailure]
                      help_msg=None,         # type: str
                      **kw_context_args):
    """
    A decorator to define a failure raiser. Same functionality then `failure_raiser`:

    >>> import sys, pytest
    >>> if sys.version_info < (3, 0):
    ...     pytest.skip('doctest skipped in python 2 because exception namespace is different but details matter')

    >>> @as_failure_raiser(help_msg="x should be smaller than 4")
    ... def is_small_with_details(x):
    ...     return x < 4
    >>> is_small_with_details(2)
    >>> is_small_with_details(11)
    Traceback (most recent call last):
    ...
    valid8.base.InvalidValue: x should be smaller than 4. Function [is_small_with_details] returned [False] for
        value 11.

    :param failure_type:
    :param help_msg:
    :param kw_context_args:
    :return:
    """
    if failure_type is None and help_msg is None and len(kw_context_args) == 0:
        raise ValueError("at least one argument should be provided in @as_failure_raiser")

    def apply_decorator(f):
        return failure_raiser(f, failure_type=failure_type, help_msg=help_msg, **kw_context_args)
    return apply_decorator


class ValueIsNone(ValidationFailure, TypeError):
    help_msg = "The value must be non-None"


def _none_accepter(validation_callable  # type: ValidationCallable
                   ):
    # type: (...) -> ValidationCallable
    """
    Wraps the given validation callable to accept None values silently. When a None value is received by the wrapper,
    it is not passed to the validation_callable and instead this function will return True. When any other value is
    received the validation_callable is called as usual.

    Note: the created wrapper has the same same than the validation callable for more user-friendly error messages

    Important: mini-lambda expressions are NOT transformed into function. Indeed this function is internal only
    and is always called after `_make_validation_funcs`

    :param validation_callable:
    :return:
    """
    # option (a) use the `decorate()` helper method to preserve name and signature of the inner object
    # ==> NO, we want to support also non-function callable objects

    # option (b) simply create a wrapper manually
    def accept_none(x, **ctx):
        if x is not None:
            # proceed with validation as usual
            # new: the validation callable is always a failure raiser so no need to return output
            validation_callable(x, **ctx)
        # else:
        #     value is None: skip validation

    # set a name so that the error messages are more user-friendly
    accept_none.__name__ = 'skip_on_none(%s)' % get_callable_name(validation_callable)

    return accept_none


def _none_rejecter(validation_callable  # type: ValidationCallable
                   ):
    # type: (...) -> ValidationCallable
    """
    Wraps the given validation callable to reject None values. When a None value is received by the wrapper,
    it is not passed to the validation_callable and instead this function will raise a `Failure`. When any other
    value is received the validation_callable is called as usual.

    Important: mini-lambda expressions are NOT transformed into function. Indeed this function is internal only
    and is always called after `_make_validation_funcs`

    :param validation_callable:
    :return:
    """
    # option (a) use the `decorate()` helper method to preserve name and signature of the inner object
    # ==> NO, we want to support also non-function callable objects

    # option (b) simply create a wrapper manually
    def reject_none(x, **ctx):
        if x is not None:
            # proceed with validation as usual
            # new: the validation callable is always a failure raiser so no need to return output
            validation_callable(x, **ctx)
        else:
            raise ValueIsNone(wrong_value=x)

    # set a name so that the error messages are more user-friendly ==> NO ! here we want to see the checker
    reject_none.__name__ = 'reject_none(%s)' % get_callable_name(validation_callable)

    return reject_none


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


def make_callable(f, is_mini_lambda=False):
    # inspect the signature to determine if the **kw_context_args should be passed along
    # Here we do not want to use inspect.signature but getfullargspec to be faster, but the counterpart is that we have
    # a lot of portability-related code to handle.... :(

    if is_mini_lambda:
        nbargs = 1
        nbvarargs = 0
        nbkwargs = 0
        nbdefaults = 0
    else:
        try:
            args, varargs, varkwargs, defaults = getfullargspec(f, skip_bound_arg=True)[0:4]

            nbargs = len(args) if args is not None else 0
            nbvarargs = 1 if varargs is not None else 0
            nbkwargs = 1 if varkwargs is not None else 0
            nbdefaults = len(defaults) if defaults is not None else 0
        except IsBuiltInError:
            # built-ins: TypeError: <built-in function isinstance> is not a Python function
            # assume signature with a single positional argument
            nbargs = 1
            nbvarargs = 0
            nbkwargs = 0
            nbdefaults = 0

    if (nbargs == 1) or (nbvarargs >= 1) or (nbargs >= 2 and nbdefaults >= (nbargs - 1)):  # can it receive 1 positional argument ?
        if nbkwargs == 0:  # can it also receive var-keyword arguments ?
            # no: `f(x)`
            def call_it(x, **ctx):
                return f(x)
        else:
            # yes: `f(x, **kwctx)`
            def call_it(x, **ctx):
                return f(x, **ctx)
    else:
        raise ValueError("Validation callable '%s' has an invalid signature: it should be callable able to receive "
                         "either a single positional argument f(x) or two f(x, ctx), or a single positional and a "
                         "var-keyword f(x, **ctx). Callable: %s" % (get_callable_name(f), f))

    return call_it
