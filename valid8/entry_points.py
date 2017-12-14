from inspect import signature, Parameter

from typing import Callable, Any, List, Union, Type

from decorator import decorate

import valid8.core as core
from valid8.utils_typing import is_pep484_nonable
from valid8.core import _create_main_validation_function, result_is_success, get_validation_function_name, \
    ValidationFuncs, NonePolicy
from valid8.utils_decoration import create_function_decorator__robust_to_args, apply_on_each_func_args_sig


class ValidationError(ValueError):
    """
    Exception raised in 'defensive mode' whenever value validation fails. This may be because of an internal exception
    in the validation functions, or of something else (for example validation functions returned False).

    Note that custom base validation functions should not raise this kind of exception - this is reserved to global
    Validator objects. Instead you might wish to raise (a subclass of) valid8.BasicFailure or valid8.Failure
    """

    def __init__(self, validator: 'Validator', var_value, var_name: str = None, validation_outcome: Any = None):
        """
        Creates a ValidationError associated with validation of var_value using validator. Additional details
        about the variable name and validation_outcome (result or exception) can be provided. All of this information
        is stored in the exception object so as to be managed by a global error handler at application-level if needed
        (for example for internationalization purposes)

        :param validator: the Validator that raised this exception
        :param var_value: the value that was being validated
        :param var_name: the optional name associated to that value
        :param validation_outcome: the result of the validation process (either a non-True non-None value, or an
        exception)
        """

        # store details in the object for future access if needed
        self.validator = validator
        self.var_name = var_name
        self.var_value = var_value
        self.validation_outcome = validation_outcome

        # create the exception main message according to the type of result
        if isinstance(validation_outcome, Exception):
            contents = 'Error validating {what}. Root validator [{val}] raised [{exc}: {det}]' \
                       ''.format(what=self.get_what_txt(),
                                 val=validator.get_main_function_name(),
                                 exc=type(validation_outcome).__name__, det=validation_outcome)
            # exception: also link the traceback
            self.__traceback__ = validation_outcome.__traceback__
        else:
            contents = 'Error validating {what}: root validator [{val}] returned [{res}].' \
                       ''.format(what=self.get_what_txt(),
                                 val=validator.get_main_function_name(), res=validation_outcome)

        # call super constructor with the message
        super(ValidationError, self).__init__(contents)

    def get_what_txt(self):
        """
        Called to create the text defining what was validated. It is used in the error message. The current behaviour
        is to return "[self.var_value]" is self.var_name is none, or [self.var_name=self.var_value] otherwise.

        Subclasses may wish to override this behaviour to add more contextual information about what was being
        validated.
        :return:
        """
        var = ('' if self.var_name is None else (self.var_name + '=')) + str(self.var_value)
        return '[{var}]'.format(var=var)


class Validator:
    """
    Represents a 'pre-compiled' validator, to avoid as much as possible functions creation overhead when performing
    validation. It is constructed from a list of base validation functions, and can then be called to perform defensive
    programming (using `assert_valid`) or case handling (using `is_valid`).

    A Validator object is the only one to know the full context of validation, and therefore is the only one able
    to raise the top-level `ValidationError`. Base validation functions should either return `False` or a non-`None`
    result in case of failure, or they should raise any exception. It is recommended that they raise subclasses of
    `valid8.Failure` for consistency, and that they create very explicit exception messages about what was wrong with
    the value.
    """

    __slots__ = ['main_function', 'none_policy', 'exc_type']

    def __init__(self, validation_func: ValidationFuncs, none_policy: NonePolicy = None,
                 exc_type: Type[ValidationError] = None):
        """
        Creates a validator from a (possibly list of) base validation functions. A list will be converted to an
        implicit 'and_'. A base validation function should return `True` or `None` for the validation to be a success.
        Note that this is quite different from the standard python truth value test (where None is equivalent to False),
        but it seems more adapted to an intuitive usage, where a function that returns silently without any output means
        'no problem there, move one'.

        :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
        are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
        `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
        :param none_policy: describes how None values should be handled. See `NonePolicy` for the various possibilities.
        Default is `NonePolicy.VALIDATE`, meaning that None values will be treated exactly like other values and follow
        the same validation process.
        :param exc_type:
        """
        self.none_policy = none_policy or NonePolicy.VALIDATE

        self.exc_type = exc_type or ValidationError
        if not issubclass(self.exc_type, ValidationError):
            raise ValueError('exc_type should be a subclass of ValidationError')

        # replace validation_func lists with explicit 'and_' if needed, and check if not_none needs to be enforced
        self.main_function = _create_main_validation_function(validation_func, none_policy=self.none_policy)

    def __repr__(self):
        return "{validator_type}<{main_val_function}, none_policy={none_policy}>" \
               "".format(validator_type=type(self).__name__,
                         main_val_function=self.get_main_function_name(),
                         none_policy=get_none_policy_text(self.none_policy))

    def get_main_function_name(self):
        """
        Utility method to get a friendly display name for the main validation function used by this Validator.
        Note that the main validation function is potentially a combination of several functions through a 'and_()'
        :return:
        """
        return get_validation_function_name(self.main_function)

    def __call__(self, name: str=None, value=None, **named_values):
        """
        Shortcut for self.assert_valid, in case you saved a validator in an already explicit variable name.
        Two modes are supported:

        :param name:
        :param value:
        :return:
        """
        # check the mode used
        if value is not None:
            if name is None or len(named_values) > 0:
                raise ValueError('Calling a validator accepts either a non-None name and a non-None value arguments, '
                                 'or a single name-value keyword argument. Received arguments: '
                                 + str(dict(name=name, value=value)) + ', ' + str(**named_values))
        else:
            if name is not None or len(named_values) != 1:
                raise ValueError('Calling a validator accepts either a non-None name and a non-None value arguments, '
                                 'or a single name-value keyword argument. Received arguments: '
                                 + str(dict(name=name, value=value)) + ', ' + str(**named_values))
            else:
                name, value = next(iter(named_values.items()))

        # perform validation
        self.assert_valid(name, value)

    def assert_valid(self, name, value):
        """
        Asserts that the provided value is valid with respect to the inner validation function.
        This corresponds to a 'Defensive programming' (sometimes known as 'Offensive programming') mode: on any kind of
        failure (explicit exception or wrong result returned by a validator), the function will raise a ValidationError,
        or a subclass of it if it was provided in the constructor.

        :param name: the name of the variable to validate (for error messages)
        :param value: the value to validate
        :return: nothing in case of success. Otherwise, raises a ValidationError
        """
        try:
            # perform validation
            res = self.main_function(value)

        except Exception as e:
            # caught any exception: raise ValidationError with that exception in the details
            self._raise_from_exception(name, value, e)

        # check the result
        if not result_is_success(res):
            # failure without exception: raise a ValidationError with some details about the function that failed
            self._raise_from_silent_failure(name, value, res)

    def _raise_from_silent_failure(self, name, value, res):
        """ Called whenever there is a need to raise a validation error because the function returned 'res' """

        # note: we do not use 'raise x from e' but the ValidationError constructor sets the traceback correctly
        raise self.exc_type(self, var_name=name, var_value=value, validation_outcome=res)

    def _raise_from_exception(self, name, value, exc):
        """ Called whenever there is a need to raise a validation error because the function raised 'exc' """

        # note: we do not use 'raise x from e' but the ValidationError constructor sets the traceback correctly
        raise self.exc_type(self, var_name=name, var_value=value, validation_outcome=exc)

    def is_valid(self, value):
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


def assert_valid(validation_func: ValidationFuncs, none_policy: NonePolicy = None, **named_values):
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
    :param none_policy: describes how None values should be handled. See `NonePolicy` for the various possibilities.
    Default is `NonePolicy.VALIDATE`, meaning that None values will be treated exactly like other values and follow
    the same validation process.
    :param named_values: the values to validate as named arguments. Currently this can only contain one a single entry.
    :return: nothing
    """
    return Validator(validation_func, none_policy=none_policy)(**named_values)


def is_valid(validation_func: Union[Callable, List[Callable]], value, none_policy: NonePolicy=None) -> bool:
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
    return Validator(validation_func, none_policy=none_policy).is_valid(value)


class NoneArgPolicy(NonePolicy):
    """ This enumeration extends `NonePolicy` to handle optional function arguments automatic handling in @validate
    and @validate_arg """

    __slots__ = []

    SKIP_IF_NONABLE_ELSE_VALIDATE = 4
    """ If this policy is selected, if an input argument appears as optional (default value of None or PEP484 type hint
    Optional) then the policy for this argument is SKIP, otherwise the policy for this argument is VALIDATE """

    SKIP_IF_NONABLE_ELSE_FAIL = 5
    """ If this policy is selected, if an input argument appears as optional (default value of None or PEP484 type hint
    Optional) then the policy for this argument is SKIP, otherwise the policy for this argument is FAIL """


def get_none_policy_text(none_policy: NonePolicy):
    """
    Returns a user-friendly description of a NonePolicy taking into account NoneArgPolicy

    :param none_policy:
    :return:
    """
    if none_policy is NoneArgPolicy.SKIP_IF_NONABLE_ELSE_FAIL:
        return "accept None witout validation if the argument is optional, otherwise fail on None"
    elif none_policy is NoneArgPolicy.SKIP_IF_NONABLE_ELSE_VALIDATE:
        return "accept None witout validation if the argument is optional, otherwise validate None as any other values"
    else:
        # fallback on base none policies
        return core.get_none_policy_text(none_policy)


class InputValidationError(ValidationError):
    """
    Exception raised whenever function input validation fails. It is not meant to be subclassed by users, please rather
    subclass BasicFailure.
    """

    def __init__(self, validator: 'InputValidator', var_value, var_name: str = None, validation_outcome: Any = None):
        """
        Creates a ValidationError associated with validation of var_value as part of function input validation.
        validator is therefore assumed to be a subclass of InputValidator

        :param validator: an InputValidator
        :param var_value:
        :param var_name:
        :param validation_outcome:
        """
        super(InputValidationError, self).__init__(validator, var_value=var_value, var_name=var_name,
                                                   validation_outcome=validation_outcome)

    def get_what_txt(self):
        """
        Overrides the base behaviour defined in ValidationError in order to add details about the function.
        :return:
        """
        var = ('' if self.var_name is None else (self.var_name + '=')) + str(self.var_value)
        return 'input [{var}] for function [{func}]'.format(var=var,
                                                            func=self.validator.get_validated_func_display_name())


class InputValidator(Validator):
    """ Represents a special kind of validator responsible to validate a function input """

    __slots__ = ['validated_func']

    def __init__(self, validated_func: Callable, validation_func: ValidationFuncs, none_policy: NonePolicy = None,
                 exc_type: Type[InputValidationError] = None):
        """

        :param validated_func: the function whose input is being validated.
        :param validation_func: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
        are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
        `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
        :param none_policy: describes how None values should be handled. See `NoneArgPolicy` for the various
        possibilities. Default is `NonePolicy.VALIDATE`.
        :param exc_type:
        """
        super(InputValidator, self).__init__(validation_func=validation_func, none_policy=none_policy,
                                             exc_type=exc_type or InputValidationError)

        self.validated_func = validated_func

    def __repr__(self):
        return "{validator_type}<{main_val_function}, validated_function={func}, " \
               "none_policy={none_policy}>".format(validator_type=type(self).__name__,
                                                   func=self.validated_func,
                                                   main_val_function=self.get_main_function_name(),
                                                   none_policy=get_none_policy_text(self.none_policy))

    def get_validated_func_display_name(self):
        """
        Utility method to get a friendly display name for the function being validated by this InputValidator
        :return:
        """
        return self.validated_func.__name__ or str(self.validated_func)


# TODO: offer the capability to validate function outputs
def validate(none_policy: NoneArgPolicy=None, **kw_validation_funcs: ValidationFuncs):
    """
    A function decorator to add input validation prior to the function execution. It should be called with named
    arguments: for each function arg name, provide a single validation function or a list of validation functions to
    apply. If validation fails, it will raise an InputValidationError with details about the function, the input name,
    and any further information available from the validation function(s)

    For example:

    ```
    def is_even(x):
        return x % 2 == 0

    def gt(a):
        def gt(x):
            return x >= a
        return gt

    @validate(a=[is_even, gt(1)], b=is_even)
    def myfunc(a, b):
        print('hello')
    ```

    will generate the equivalent of :

    ```
    def myfunc(a, b):
        gt1 = gt(1)
        if (is_even(a) and gt1(a)) and is_even(b):
            print('hello')
        else:
            raise InputValidationError(...)
    ```

    :param none_policy: describes how None values should be handled. See `NoneArgPolicy` for the various
    possibilities. Default is `NoneArgPolicy.ACCEPT_IF_OPTIONAl_ELSE_VALIDATE`.
    :param kw_validation_funcs: keyword arguments: for each of the function's input names, the validation function or
    list of validation functions to use. A validation function may be a callable, a tuple(callable, help_msg_str),
    a tuple(callable, failure_type), or a list of several such elements. Nested lists are supported and indicate an
    implicit `and_` (such as the main list). Tuples indicate an implicit `_failure_raiser`.
    [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of callables, they will
    be transformed to functions automatically.
    :return: the decorated function, that will perform input validation before executing the function's code everytime
    it is executed.
    """

    # this is a general technique for decorators, to properly handle both cases of being called with arguments or not
    # this is really not needed in our case since @validate will never be used as is (without a call), but it does not
    # cost much and may be of interest in the future
    return create_function_decorator__robust_to_args(decorate_with_validation, none_policy=none_policy,
                                                     **kw_validation_funcs)


alidate = validate
""" an alias for the @validate decorator, to use as follows : import valid8 as v : @v.alidate(...) """


def validate_arg(arg_name, *validation_func: ValidationFuncs, none_policy: NoneArgPolicy=None) -> Callable:
    """
    A decorator to apply function input validation for the given argument name, with the provided base validation
    function(s). You may use several such decorators on a given function as long as they are stacked on top of each
    other (no external decorator in the middle)

    :param arg_name:
    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :param none_policy: describes how None values should be handled. See `NoneArgPolicy` for the various
    possibilities. Default is `NoneArgPolicy.ACCEPT_IF_OPTIONAl_ELSE_VALIDATE`.
    :return: a function decorator, able to transform a function into a function that will perform input validation
    before executing the function's code everytime it is executed.
    """
    # this is a general technique for decorators, to properly handle both cases of being called with arguments or not
    # this is really not needed in our case since @validate will never be used as is (without a call), but it does not
    # cost much and may be of interest in the future
    return create_function_decorator__robust_to_args(decorate_with_validation, none_policy=none_policy,
                                                     **{arg_name: list(validation_func)})


def _create_input_validator(validated_func, validated_func_arg: Parameter, validation_func: ValidationFuncs,
                            none_policy: NoneArgPolicy):
    """
    Routine used internally to create an InputValidator for a given function argument

    :param validated_func:
    :param validated_func_arg:
    :param validation_func:
    :param none_policy:
    :return:
    """

    is_nonable = (validated_func_arg.default is None) or is_pep484_nonable(validated_func_arg.annotation)

    if none_policy in {NonePolicy.VALIDATE, NonePolicy.SKIP, NonePolicy.FAIL}:
        none_policy_to_use = none_policy

    elif none_policy is NoneArgPolicy.SKIP_IF_NONABLE_ELSE_VALIDATE:
        none_policy_to_use = NonePolicy.SKIP if is_nonable else NonePolicy.VALIDATE

    elif none_policy is NoneArgPolicy.SKIP_IF_NONABLE_ELSE_FAIL:
        none_policy_to_use = NonePolicy.SKIP if is_nonable else NonePolicy.FAIL

    else:
        raise ValueError('Invalid none policy: ' + str(none_policy))

    return InputValidator(validated_func, validation_func, none_policy=none_policy_to_use)


def decorate_with_validation(func: Callable, none_policy: NoneArgPolicy=None,
                             **kw_validation_funcs: ValidationFuncs) -> Callable:
    """
    This method is equivalent to decorating a function with the `@validate` decorator, but can be used a posteriori.

    :param func:
    :param none_policy: describes how None values should be handled. See `NoneArgPolicy` for the various possibilities.
    Default is `NoneArgPolicy.ACCEPT_IF_OPTIONAl_ELSE_REJECT`.
    :param kw_validation_funcs: keyword arguments: for each of the function's input names, the validation function or
    list of validation functions to use. A validation function may be a callable, a tuple(callable, help_msg_str),
    a tuple(callable, failure_type), or a list of several such elements. Nested lists are supported and indicate an
    implicit `and_` (such as the main list). Tuples indicate an implicit `_failure_raiser`.
    [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of callables, they will
    be transformed to functions automatically.
    :return: the decorated function, that will perform input validation (using `_assert_input_is_valid`) before
    executing the function's code everytime it is executed.
    """

    none_policy = none_policy or NoneArgPolicy.SKIP_IF_NONABLE_ELSE_VALIDATE

    # (1) retrieve target function signature
    s = signature(func)

    # (2) check that provided kw_validation_funcs don't contain function input names that are incorrect
    incorrect = set(kw_validation_funcs.keys()) - set(s.parameters.keys())
    if len(incorrect) > 0:
        raise ValueError('@validate[...] definition exception: kw_validation_funcs are defined for \''
                         + str(incorrect) + '\' that is/are not part of signature for ' + str(func))

    # (3) create or update a wrapper around the function to add validation
    if hasattr(func, '__wrapped__') and hasattr(func.__wrapped__, '__validators__'):
        # ---- This function is already wrapped by our validator. ----

        # First check that the new validators to create are for inputs that did not have some validators already
        incorrect = set(kw_validation_funcs.keys()).intersection(set(func.__wrapped__.__validators__.keys()))
        if len(incorrect) > 0:
            raise ValueError('@validate[...] definition exception: kw_validation_funcs are already defined for function input(s)'
                             ' \'' + str(incorrect) + '\', you can not define them twice.')

        # Then update the dictionary of validators with the new validators
        for att_name, att_validators in kw_validation_funcs.items():
            # create the new validators as InputValidator objects according to the none_policy and function signature
            func.__wrapped__.__validators__[att_name] = _create_input_validator(func.__wrapped__,
                                                                                s.parameters[att_name],
                                                                                att_validators, none_policy)

        # return the function, no need to wrap it further (it is already wrapped)
        return func

    else:
        # ---- This function is not yet wrapped by our validator. ----

        # create the new validators as InputValidator objects according to the none_policy and function signature
        for att_name, att_validators in kw_validation_funcs.items():
            kw_validation_funcs[att_name] = _create_input_validator(func, s.parameters[att_name], att_validators,
                                                                    none_policy)

        # Store the dictionary of kw_validation_funcs as an attribute of the function
        if hasattr(func, '__validators__'):
            raise ValueError('Function ' + str(func) + ' already has a defined __validators__ attribute, valid8 '
                             'decorators can not be applied on it')
        func.__validators__ = kw_validation_funcs

        # we used @functools.wraps(), but we now use 'decorate()' to have a wrapper that has the same signature
        def validating_wrapper(f, *args, **kwargs):
            """ This is the wrapper that will be called everytime the function is called """

            # (a) Perform input validation by applying `_assert_input_is_valid` on all received arguments
            apply_on_each_func_args_sig(f, args, kwargs, s,
                                        func_to_apply=_assert_input_is_valid,
                                        func_to_apply_paramers_dict=f.__validators__)

            # (b) execute the function as usual
            return f(*args, **kwargs)

        decorated_function = decorate(func, validating_wrapper)
        return decorated_function


def _assert_input_is_valid(input_value: Any, validator: InputValidator, validated_func: Callable, input_name: str):
    """
    Called by the `validating_wrapper` in the first step (a) `apply_on_each_func_args` for each function input before
    executing the function. It simply delegates to the validator. The signature of this function is hardcoded to
    correspond to `apply_on_each_func_args`'s behaviour and should therefore not be changed.
    
    :param input_value: the value to validate
    :param validator: the Validator object that will be applied on input_value_to_validate
    :param validated_func: the function for which this validation is performed. This is not used since the Validator
    knows it already, but we should not change the signature here.
    :param input_name: the name of the function input that is being validated
    :return: Nothing
    """
    validator.assert_valid(input_name, input_value)
