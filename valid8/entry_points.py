from copy import copy
from typing import Callable, Any, List, Union  # do not import Type for compatibility with earlier python 3.5

from valid8.utils_string import end_with_dot
from valid8.base import result_is_success, get_callable_name, _none_accepter, _none_rejecter, RootException, \
    HelpMsgMixIn, is_error_of_type, HelpMsgFormattingException, should_be_hidden_as_cause
from valid8.composition import ValidationFuncs, _process_validation_function_s


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


class NoneArgPolicy(NonePolicy):
    """ This enumeration extends `NonePolicy` to add policies specific to function input validation used in @validate... decorators """

    __slots__ = []

    SKIP_IF_NONABLE_ELSE_VALIDATE = 4
    """ If this policy is selected, if an input argument appears as optional (default value of None or PEP484 type hint
    Optional) then the policy for this argument is SKIP, otherwise the policy for this argument is VALIDATE """

    SKIP_IF_NONABLE_ELSE_FAIL = 5
    """ If this policy is selected, if an input argument appears as optional (default value of None or PEP484 type hint
    Optional) then the policy for this argument is SKIP, otherwise the policy for this argument is FAIL """


def get_none_policy_text(none_policy: int, verbose: bool=False):
    """
    Returns a user-friendly description of a NonePolicy taking into account NoneArgPolicy

    :param none_policy:
    :param verbose:
    :return:
    """
    if none_policy is NonePolicy.SKIP:
        return "accept None without performing validation" if verbose else 'SKIP'
    elif none_policy is NonePolicy.FAIL:
        return "fail on None without performing validation" if verbose else 'FAIL'
    elif none_policy is NonePolicy.VALIDATE:
        return "validate None as any other values" if verbose else 'VALIDATE'
    elif none_policy is NoneArgPolicy.SKIP_IF_NONABLE_ELSE_FAIL:
        return "accept None without validation if the argument is optional, otherwise fail on None" if verbose \
            else 'SKIP_IF_NONABLE_ELSE_FAIL'
    elif none_policy is NoneArgPolicy.SKIP_IF_NONABLE_ELSE_VALIDATE:
        return "accept None without validation if the argument is optional, otherwise validate None as any other " \
               "values" if verbose else 'SKIP_IF_NONABLE_ELSE_VALIDATE'
    else:
        raise ValueError('Invalid none_policy ' + str(none_policy))


def _add_none_handler(validation_callable: Callable, none_policy: int) -> Callable:
    """
    Adds a wrapper or nothing around the provided validation_callable, depending on the selected policy

    :param validation_callable:
    :param none_policy: an int representing the None policy, see NonePolicy
    :return:
    """
    if none_policy is NonePolicy.SKIP:
        return _none_accepter(validation_callable)  # accept all None values

    elif none_policy is NonePolicy.FAIL:
        return _none_rejecter(validation_callable)  # reject all None values

    elif none_policy is NonePolicy.VALIDATE:
        return validation_callable                  # do not handle None specifically, do not wrap

    else:
        raise ValueError('Invalid none_policy : ' + str(none_policy))  # invalid none_policy


class ValidationError(HelpMsgMixIn, RootException):
    """
    Represents a Validation error raised by a 'defensive mode' validation entry point such as `validate`, `validator`/`validation`, `assert_valid`,
    `@validate_io`, `@validate_arg`, or `<Validator>.assert_valid()`. It contains details about the `Validator`, the value
    that was being validated, and the outcome (a value or an exception). All these details are stored in the instance.

    There are two ways to use this class:

     * either use the syntax `assert_valid(..., help_msg=<help_msg>)` when performing validation, or create your
     `Validator` instances with argument help_msg=<help_msg>. Both are equivalent and will create instances of
     `ValidationError` with the provided help message when validation fails.

     * or subclass it explicitly (recommended) and then use the syntax `assert_valid(..., error_type=<subclass>)` or
     create your `Validator` instances with argument `error_type=<subclass>`. Both are equivalent and will create
     instances of your subclass when validation fails.

    This class looks very similar to `Failure` but is very different:
     - `Failure` is an *optional* base exception type for *base validation functions*. It does not know anything about
     the validation context or purpose. Besides, many base validation functions do not even raise it (they would raise
     other exceptions or return a non-True, non-None result). So consider it a goodie when writing validation functions.
     - `ValidationError` is the base exception type for validation. When validation fails, the exception raised will
     *always* be an instance of `ValidationError`. It knows the full context of validation: name of variable being
     validated, name of function and argument in case of InputValidation, and applicative intent through the help
     message or a user-created subclass. If a `ValidationError` was caused by a base validation function raising a
     `Failure`, then this `Failure` will be set as the `__cause__` of the error, and will also be available in the
     contents of `ValidationError` (in the `validation_outcome` field)

    It is recommended that Users extend this class to define their own validation errors, so as to provide a unique
    error type for each kind of applicative error (this eases the process of error handling at app-level). An easy way
    to do this while providing details about the validation error is to override the 'help_msg' field:

    ```python
    class SurfaceNotInValidRange(ValidationError):
        help_msg = 'Surface should be a positive number less than 10000 (square meter)'

    assert_valid(is_between(0, 10000), surface=surface, error_type=SurfaceNotInValidRange)
    ```

    If you wish that users get more informative help messages, you may insert formatting placeholders in the `help_msg`
    field as it will be automatically formatted using help_msg.format(var_value=var_value, **kw_context_args).
    Any number of contextual keyword arguments (**kw_context_args) may be provided in the constructor for this purpose:

    ```python
    class SurfaceNotInValidRange(ValidationError):
        help_msg = "x={var_value} does not meet {condition}"

    def my_validator(x):
        if <condition>:
            return True
        else:
            # the only mandatory argument is `var_value`, then any set of keyword arguments may be provided:
            raise ConditionWasNotMet(var_value=x, condition=condition)
    ```

    For more stronger constructor signature, your subclass may override the __init__ method. The class below has an
    equivalent behaviour than above, but with a stricter constructor:

    ```python
    class ConditionWasNotMet(Failure):
        def __init__(self, var_value, condition):
            help_msg = "x={var_value} does not meet {condition}"
            super(ConditionWasNotMet, self).__init__(var_value=var_value, condition=condition, help_msg=help_msg)
    ```

    Note: if users wish to wrap an *existing* function (such as a lambda or mini lambda) with a Failure raiser, then
    they should subclass `WrappingFailure` instead of `Failure`. See `WrappingFailure` for details.
    """

    def __init__(self, validator: 'Validator', var_value, var_name: str, validation_outcome: Any = None,
                 help_msg: str = None, append_details: bool = True, **kw_context_args):
        """
        Creates a ValidationError associated with validation of `var_value` using `validator`. Additional details
        about the `var_name` and `validation_outcome` (result or exception) can be provided. All of this
        information is stored in the exception object so as to be managed by a global error handler at application-level
        if needed (for example for internationalization purposes)

        :param validator: the Validator that raised this exception
        :param var_value: the value that was validated and failed validation
        :param var_name: the name associated to that value
        :param validation_outcome: the result of the validation process (either a non-True non-None value, or an
        exception)
        :param help_msg: an optional help message specific to this validation error. If not provided, the class
        attribute `help_msg` will be used. This behaviour may be redefined by subclasses by overriding `get_help_msg`
        :param append_details: a boolean indicating if a default message containing the value should be appended to the
        string representation. Default is True
        :param kw_context_args: optional context (results, other) to store in this failure and that will be also used
        for help message formatting
        """

        self.display_prefix_for_exc_outcomes = True

        self.append_details = append_details

        # store everything in self
        self.validator = validator
        self.var_value = var_value
        self.var_name = var_name
        self.validation_outcome = validation_outcome
        self.__dict__.update(kw_context_args)

        # store help_msg ONLY if non-None otherwise the possibly user-overridden class attribute should be left visible
        if help_msg is not None:
            self.help_msg = help_msg

        # call super constructor with nothing, since Exception does not accept keyword arguments and we are redefining
        # __str__ anyway
        super(ValidationError, self).__init__()

        # automatically set the exception as the cause, so that we can forget to "raise from" (except when from None)
        if isinstance(validation_outcome, Exception) and not should_be_hidden_as_cause(validation_outcome):
            self.__cause__ = validation_outcome
            # possibly hide the cause of the cause
            if hasattr(validation_outcome, '__cause__') and should_be_hidden_as_cause(validation_outcome.__cause__):
                validation_outcome.__cause__ = None
        else:
            self.__cause__ = None

    def __str__(self):
        """ Overrides the default exception message by relying on HelpMsgMixIn """
        try:
            if self.append_details:
                return self.get_help_msg(dotspace_ending=True, **self.__dict__) + self.get_details()
            else:
                return self.get_help_msg(**self.__dict__)
        except HelpMsgFormattingException as f:
            return str(f)
        except Exception as e:
            return "Error while formatting help message: {}".format(e)

    def __repr__(self):
        """ Overrides the default exception representation """
        fields = [name + '=' + str(val) for name, val in self.__dict__.items() if not name.startswith('_')]
        return type(self).__name__ + '(' + ','.join(fields) + ')'

    def get_details(self):
        """ The function called to get the details appended to the help message when self.append_details is True """

        # create the exception main message according to the type of result
        if isinstance(self.validation_outcome, Exception):

            prefix = 'Validation function [{val}] raised ' if self.display_prefix_for_exc_outcomes else ''

            # new: we now remove  "Root validator was [{validator}]", users can get it through e.validator
            contents = ('Error validating {what}. ' + prefix + '{exception}: {details}')\
                         .format(what=self.get_what_txt(),
                                 val=self.validator.get_main_function_name(),
                                 exception=type(self.validation_outcome).__name__,
                                 details=end_with_dot(str(self.validation_outcome)))

        else:
            contents = 'Error validating {what}: validation function [{val}] returned [{result}].' \
                       ''.format(what=self.get_what_txt(), val=self.validator.get_main_function_name(),
                                 result=self.validation_outcome)

        # return 'Wrong value: [{}]'.format(self.var_value)
        return contents

    def get_variable_str(self):
        """ Utility method to get the variable value or 'var_name=value' if name is not None """
        return ('' if self.var_name is None else (self.var_name + '=')) + str(self.var_value)

    def get_what_txt(self):
        """
        Called to create the text defining what was validated. It is used in the error message. The current behaviour
        is to return "[self.var_value]" is self.var_name is none, or [self.var_name=self.var_value] otherwise.

        Subclasses may wish to override this behaviour to add more contextual information about what was being
        validated.
        :return:
        """
        return '[{var}]'.format(var=self.get_variable_str())


class MetaReprForValidator(type):
    """ Utility metaclass used in add_base_type_dynamically """
    def __repr__(cls):
        return repr(cls.__bases__[0])[:-2] + '[' + cls.__bases__[1].__name__ + ']' + repr(cls.__bases__[0])[-2:]


def add_base_type_dynamically(error_type, additional_type):
    """
    Utility method to create a new type dynamically, inheriting from both error_type (first) and additional_type
    (second). The class representation (repr(cls)) of the resulting class reflects this by displaying both names
    (fully qualified for the first type, __name__ for the second)

    For example
    ```
    > new_type = add_base_type_dynamically(ValidationError, ValueError)
    > repr(new_type)
    "<class 'valid8.entry_points.ValidationError+ValueError'>"
    ```
    :return:
    """
    # the new type created dynamically, with the same name
    class new_error_type(error_type, additional_type, metaclass=MetaReprForValidator):
        pass

    new_error_type.__name__ = error_type.__name__ + '[' + additional_type.__name__ + ']'
    new_error_type.__qualname__ = error_type.__qualname__ + '[' + additional_type.__qualname__+ ']'
    new_error_type.__module__ = error_type.__module__

    return new_error_type


class Validator:
    """
    Represents a 'pre-compiled' validator, to avoid as much as possible functions creation overhead when performing
    validation. It is constructed from a list of base validation functions (see constructor for details). Validation
    will succeed if all base validation functions succeed.

    Once created, a `Validator` may be called to either perform defensive programming (using `assert_valid`) or
    case handling (using `is_valid`).

    A Validator object is the only object that knows the full context of validation, and therefore is the only one able
    to raise the top-level `ValidationError` or subclass if user-provided (recommended, use constructor argument
    `error_type`). See `ValidationError` for details.
    """

    def __init__(self, *validation_func: ValidationFuncs, error_type: 'Type[ValidationError]' = None,
                 help_msg: str = None, none_policy: int = None, **kw_context_args):
        """
        Creates a validator from a set of base validation functions. Validation will succeed if all base validation
        functions succeed.

        The most basic validation function to use in a `Validator` is a callable that takes a single argument and
        returns `True` or `None` in case of success - any other result or any exception is a failure. Note that this is
        quite different from the standard python truth value test (where None is equivalent to False), but it seems more
        adapted to an intuitive usage, where a function that returns silently without any output means 'no problem
        there, move one'. Users defining their own base validation functions may wish to raise instances or subclasses
        of `Failure` to provide more user-friendly details and unique failure identifiers. Raw mini_lambda expressions
        are supported and are automatically transformed to functions.

        For example:

        ```python
        # (a) an existing validation function
        from math import isfinite
        Validator(isfinite)

        # (b) a mini_lambda
        from mini_lambda import x
        Validator(x > 0)

        # (c) a user-defined function raising unique Failure
        class NotFriendly(Failure):
            help_msg = "The value should be friendly"

        def my_validator(x):
            if not_friendly(x):
                return True
            else:
                raise NotFriendly(var_value=x)

        Validator(my_validator)
        ```

        Users may perform composition on base validation functions used in a `Validator`:
        - either explicitly using the various operators provided in valid8.composition (`and_`, `or_`, `xor_`,
        `failure_raiser()`, `skip_on_none()`, `fail_on_none()`...)
        - or implicitly using the syntax defined in `ValidationFuncs`: i.e. a list means an implicit `and_()` and a
        tuple means an implicit `failure_raiser()`

        It is possible to provide values for `help_msg` and `error_type` in the constructor so as to reuse them in any
        subsequent call to `assert_valid`. See `assert_valid` for details about those fields

        Finally the `none_policy` argument controls how the creates `Validator` will behave when asked to validate
        `None` values. See `NonePolicy` for details about the possible options.

        :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
        are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
        `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
        :param error_type: a subclass of ValidationError to raise in case of validation failure. By default a
        ValidationError will be raised with the provided help_msg
        :param help_msg: an optional help message to be used in the raised error in case of validation failure.
        :param none_policy: describes how None values should be handled. See `NonePolicy` for the various possibilities.
        Default is `NonePolicy.VALIDATE`, meaning that None values will be treated exactly like other values and follow
        the same validation process.
        :param kw_context_args: optional contextual information to store in the exception, and that may be also used
        to format the help message
        """
        self.none_policy = none_policy or NonePolicy.VALIDATE

        self.error_type = error_type or ValidationError
        if not issubclass(self.error_type, ValidationError):
            raise ValueError('error_type should be a subclass of ValidationError')

        self.help_msg = help_msg

        self.kw_context_args = kw_context_args

        # replace validation_func lists with explicit 'and_' if needed, and tuples with _failure_raiser()
        main_val_func = _process_validation_function_s(list(validation_func))

        # finally wrap in a none handler according to the policy
        self.main_function = _add_none_handler(main_val_func, none_policy=self.none_policy)

    def get_main_function_name(self) -> str:
        """
        Utility method to get a friendly display name for the main validation function used by this Validator.
        Note that the main validation function is potentially a combination of several functions through a 'and_()'
        :return:
        """
        return get_callable_name(self.main_function)

    def __repr__(self) -> str:
        """ Overrides the default string representation for Validator instances """

        info = self.get_additional_info_for_repr()
        return "{validator_type}<{additional_info}validation_function={main_val_function}, none_policy={none_policy}," \
               " exc_type={exc_type}>" \
               "".format(additional_info=(info + ', ') if len(info) > 0 else '',
                         validator_type=type(self).__name__,
                         main_val_function=self.get_main_function_name(),
                         none_policy=get_none_policy_text(self.none_policy),
                         exc_type=self.error_type.__name__)

    def get_additional_info_for_repr(self) -> str:
        """ Subclasses may override this method to add custom information in the string representation of instances """
        return ''

    def assert_valid(self, name: str, value: Any, error_type: 'Type[ValidationError]' = None,
                     help_msg: str = None, **kw_context_args):
        """
        Asserts that the provided named value is valid with respect to the inner base validation functions. It returns
        silently in case of success, and raises a `ValidationError` or a subclass in case of failure. This corresponds
        to a 'Defensive programming' (sometimes known as 'Offensive programming') mode.

        By default this raises instances of `ValidationError` with a default message, in case of failure. There are
        two ways that you can customize this behaviour:

         * if you set `help_msg` in this method or in `Validator` constructor, instances of `ValidationError` created
         will be customized with the provided help message.

         * if you set `error_type` in this method or in `Validator` constructor, instances of your custom class will be
         created. Note that you may still provide a `help_msg`.

        It is recommended that Users define their own validation error types (case 2 above), so as to provide a unique
        error type for each kind of applicative error. This eases the process of error handling at app-level.

        :param name: the name of the variable to validate (for error messages)
        :param value: the value to validate
        :param error_type: a subclass of `ValidationError` to raise in case of validation failure. By default a
        `ValidationError` will be raised with the provided `help_msg`
        :param help_msg: an optional help message to be used in the raised error in case of validation failure.
        :param kw_context_args: optional contextual information to store in the exception, and that may be also used
        to format the help message
        :return: nothing in case of success. Otherwise, raises a ValidationError
        """
        try:
            # perform validation
            res = self.main_function(value)

        except Exception as e:
            # caught any exception: raise ValidationError or subclass with that exception in the details
            # --old bad idea: first wrap into a failure ==> NO !!! I tried and it was making it far too messy/verbose

            # note: we do not have to 'raise x from e' since the ValidationError constructor already sets the __cause__
            # so we can safely take the same handling than for non-exception failures.
            res = e

        # check the result
        if not result_is_success(res):
            raise self._create_validation_error(name, value, validation_outcome=res, error_type=error_type,
                                                help_msg=help_msg, **kw_context_args)

    def _create_validation_error(self, name: str, value: Any, validation_outcome: Any = None,
                                 error_type: 'Type[ValidationError]' = None, help_msg: str = None, **kw_context_args):
        """ The function doing the final error raising.  """

        # first merge the info provided in arguments and in self
        error_type = error_type or self.error_type
        help_msg = help_msg or self.help_msg
        ctx = copy(self.kw_context_args)
        ctx.update(kw_context_args)

        # allow the class to override the name
        name = self._get_name_for_errors(name)

        if issubclass(error_type, TypeError) or issubclass(error_type, ValueError):
            # this is most probably a custom error type, it is already annotated with ValueError and/or TypeError
            # so use it 'as is'
            new_error_type = error_type
        else:
            # Add the appropriate TypeError/ValueError base type dynamically
            additional_type = None
            if isinstance(validation_outcome, Exception):
                if is_error_of_type(validation_outcome, TypeError):
                    additional_type = TypeError
                elif is_error_of_type(validation_outcome, ValueError):
                    additional_type = ValueError
            if additional_type is None:
                # not much we can do here, let's assume a ValueError, that is more probable
                additional_type = ValueError

            new_error_type = add_base_type_dynamically(error_type, additional_type)

        # then raise the appropriate ValidationError or subclass
        return new_error_type(validator=self, var_value=value, var_name=name, validation_outcome=validation_outcome,
                              help_msg=help_msg, **ctx)

    def _get_name_for_errors(self, name: str):
        """ Subclasses may override this """
        return name

    def __call__(self, name: str, value: Any, error_type: 'Type[ValidationError]' = None, help_msg: str = None,
                 **kw_context_args):
        """
        Shortcut for self.assert_valid()

        :param name:
        :param value:
        :param error_type: a subclass of `ValidationError` to raise in case of validation failure. By default a
        `ValidationError` will be raised with the provided `help_msg`
        :param help_msg: an optional help message to be used in the raised error in case of validation failure.
        :param kw_context_args: optional keyword context arguments to use in the error
        :return:
        """
        self.assert_valid(name=name, value=value, error_type=error_type, help_msg=help_msg, **kw_context_args)

    def is_valid(self, value: Any) -> bool:
        """
        Validates the provided value and returns a boolean indicating success or failure. Any Exception happening in
        the validation process will be silently caught.

        :param value: the value to validate
        :return: a boolean flag indicating success or failure
        """
        # noinspection PyBroadException
        try:
            # perform validation
            res = self.main_function(value)

            # return a boolean indicating if success or failure
            return result_is_success(res)

        except Exception:
            # caught exception means failure > return False
            return False


def assert_valid(name: str, value: Any, *validation_func: ValidationFuncs, none_policy: int = None,
                 error_type: 'Type[ValidationError]' = None, help_msg: str = None, **kw_context_args):
    """
    Validates value `value` using validation function(s) `base_validator_s`.
    As opposed to `is_valid`, this function raises a `ValidationError` if validation fails.

    It is therefore designed to be used for defensive programming, in an independent statement before the code that you
    intent to protect.

    ```python
    assert_valid(x, isfinite):
    ...<your code>
    ```

    Note: this is a friendly alias for `_validator(base_validator_s)(value)`

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param name: the name of the variable to validate. It will be used in error messages
    :param value: the value to validate
    :param none_policy: describes how None values should be handled. See `NonePolicy` for the various possibilities.
    Default is `NonePolicy.VALIDATE`, meaning that None values will be treated exactly like other values and follow
    the same validation process.
    :param error_type: a subclass of ValidationError to raise in case of validation failure. By default a
    ValidationError will be raised with the provided help_msg
    :param help_msg: an optional help message to be used in the raised error in case of validation failure.
    :param kw_context_args: optional keyword arguments providing additional context, that will be provided to the error
    in case of validation failure
    :return: nothing in case of success. In case of failure, raises a <error_type> if provided, or a ValidationError.
    """
    return Validator(*validation_func, error_type=error_type, help_msg=help_msg,
                     none_policy=none_policy).assert_valid(name=name, value=value, **kw_context_args)


def is_valid(value, *validation_func: Union[Callable, List[Callable]], none_policy: int=None) -> bool:
    """
    Validates value `value` using validation function(s) `validator_func`.
    As opposed to `assert_valid`, this function returns a boolean indicating if validation was a success or a failure.
    It is therefore designed to be used within if ... else ... statements:

    ```python
    if is_valid(x, isfinite):
        ...<code>
    else
        ...<code>
    ```

    Note: this is a friendly alias for `return _validator(validator_func, return_bool=True)(value)`

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param value: the value to validate
    :param none_policy: describes how None values should be handled. See `NonePolicy` for the various possibilities.
    Default is `NonePolicy.VALIDATE`, meaning that None values will be treated exactly like other values and follow
    the same validation process. Note that errors raised by NonePolicy.FAIL will be caught and transformed into a
    returned value of False
    :return: True if validation was a success, False otherwise
    """
    return Validator(*validation_func, none_policy=none_policy).is_valid(value)
