from inspect import getfullargspec
from typing import Callable, Dict, Any, List, Union, Type

from decorator import decorate

from valid8.core import _create_main_validation_function, result_is_success, get_validator_display_name
from valid8.utils_decoration import create_function_decorator__robust_to_args, apply_on_each_func_args


class ValidationError(ValueError):
    """
    Exception raised in 'defensive mode' whenever value validation fails. This may be because of an internal exception
    in the validation functions, or of something else (for example validation functions returned False).

    Note that custom base validation functions should not raise this kind of exception - this is reserved to global
    Validator objects. Instead you might wish to raise (a subclass of) valid8.Failure
    """

    def __init__(self, validator, var_value, var_name: str = None, validation_outcome: Any = None):
        """
        Creates a ValidationError associated with validation of var_value using validator. Additional details
        about the variable name and validation_outcome (result or exception) can be provided

        :param validator:
        :param var_value:
        :param var_name:
        :param validation_outcome:
        """

        # store details in the object for future access if needed
        self.validator = validator
        self.var_name = var_name
        self.var_value = var_value
        self.validation_outcome = validation_outcome

        # create the exception main message according to the type of result
        if isinstance(validation_outcome, Exception):
            contents = 'Error validating {what}. Root validator [{val}] raised [{exc}: {det}]' \
                       ''.format(what=self.get_what_txt(var_name, var_value),
                                 val=validator.get_main_validator_display_name(),
                                 exc=type(validation_outcome).__name__, det=validation_outcome)
            # exception: also link the traceback
            self.__traceback__ = validation_outcome.__traceback__
        else:
            contents = 'Error validating {what}: root validator [{val}] returned [{res}].' \
                       ''.format(what=self.get_what_txt(var_name, var_value),
                                 val=validator.get_main_validator_display_name(), res=validation_outcome)

        # call super constructor with the message
        super(ValidationError, self).__init__(contents)

    def get_what_txt(self, name, value):
        """
        Called to create the text defining what was validated. Used in the error message. Subclasses may wish to
        override this.

        :param name:
        :param value:
        :return:
        """
        var = ('' if name is None else (name + '=')) + str(value)
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

    __slots__ = ['validator_func_main', 'exc_type']

    def __init__(self, base_validator_s: Union[Callable, List[Callable]], exc_type: Type[ValidationError] = None):
        """
        Creates a validator from a (possibly list of) base validation functions. A list will be converted to an
        implicit 'and_'. A base validation function should return `True` or `None` for the validation to be a success.
        Note that this is quite different from the standard python truth value test (where None is equivalent to False),
        but it seems more adapted to an intuitive usage, where a function that returns silently without any output means
        'no problem there, move one'.

        :param base_validator_s: the base validator function or list of base validator functions to use. A list will be
        considered an implicit `and_`. If present, `not_none` should be alone, or first in the list
        """
        self.exc_type = exc_type or ValidationError
        if not issubclass(self.exc_type, ValidationError):
            raise ValueError('exc_type should be a subclass of ValidationError')

        # replace base_validator_s lists with explicit 'and_' if needed, and check if not_none needs to be enforced
        self.validator_func_main = _create_main_validation_function(base_validator_s, allow_not_none=True)

    def get_main_validator_display_name(self):
        """
        Utility method to get a friendly display name for the main validation function used by this Validator.
        Note that the main validation function is potentially a combination of several functions through a 'and_()'
        :return:
        """
        return get_validator_display_name(self.validator_func_main)

    def __call__(self, name = None, value = None, **named_values):
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
        Asserts that the provided value is valid with respect to the inner validator function.
        This corresponds to a 'Defensive programming' (sometimes known as 'Offensive programming') mode: on any kind of
        failure (explicit exception or wrong result returned by a validator), the function will raise a ValidationError,
        or a subclass of it if it was provided in the constructor.

        :param name: the name of the variable to validate (for error messages)
        :param value: the value to validate
        :return: nothing in case of success. Otherwise, raises a ValidationError
        """
        try:
            # perform validation
            res = self.validator_func_main(value)

        except Exception as e:
            # caught any exception: raise ValidationError with that exception in the details
            self._raise_from_exception(name, value, e)

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
        try:
            # perform validation
            res = self.validator_func_main(value)

        except Exception:
            # caught exception means failure > return False
            return False

        # return a boolean indicating if success or failure
        return result_is_success(res)


def assert_valid(validator_func: Union[Callable, List[Callable]], **named_values):
    """
    Validates value `value` using validation function(s) `validator_func`.
    As opposed to `is_valid`, this function raises a `ValidationError` if validation fails.

    It is therefore designed to be used for defensive programming, in an independent statement before the code that you
    intent to protect.

    ```python
    assert_valid(x, isfinite):
    ...<your code>
    ```

    Note: this is a friendly alias for `_validator(validator_func)(value)`

    :param validator_func: the validator function or list of validator functions to use. A list will be considered an
    implicit `and_`. If present, `not_none` should be alone or first in the list
    :param named_values: the values to validate as named arguments. Currently this can only contain one a single entry.
    :return: nothing
    """
    return Validator(validator_func)(**named_values)


def is_valid(validator_func: Union[Callable, List[Callable]], value) -> bool:
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

    :param value: the value to validate
    :param validator_func: the validator function or list of validator functions to use. A list will be considered an
    implicit `and_`. If present, `not_none` should be alone or first in the list
    :return: True if validation was a success, False otherwise
    """
    return Validator(validator_func).is_valid(value)


class InputValidationError(ValidationError):
    """
    Exception raised whenever function input validation fails. It is not meant to be subclassed by users, please rather
    subclass Failure.
    """

    def __init__(self, validator, var_value, var_name: str = None, validation_outcome: Any = None):
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

    def get_what_txt(self, name, value):
        var = ('' if name is None else (name + '=')) + str(value)
        return 'input [{var}] for function [{func}]'.format(var=var,
                                                            func=self.validator.get_validated_func_display_name())


class InputValidator(Validator):
    """ Represents a special kind of validator responsible to validate function inputs """

    __slots__ = ['validated_func']

    def __init__(self, validated_func, base_validator_s: Union[Callable, List[Callable]]):
        super(InputValidator, self).__init__(base_validator_s=base_validator_s)
        self.validated_func = validated_func

    def get_validated_func_display_name(self):
        """
        Utility method to get a friendly display name for the function being validated by this InputValidator
        :return:
        """
        return self.validated_func.__name__ or str(self.validated_func)

    def _raise_from_silent_failure(self, name, value, res):
        """
        Called whenever there is a need to raise a validation error because the function returned 'res'.
        Overridden so as to raise the proper exception type and message.

        :param name:
        :param value:
        :param res:
        :return:
        """
        raise InputValidationError(self, var_name=name, var_value=value, validation_outcome=res)

    def _raise_from_exception(self, name, value, exc):
        """
        Called whenever there is a need to raise a validation error because the function raised 'exc'.
        Overridden so as to raise the proper exception type and message.

        :param name:
        :param value:
        :param exc:
        :return:
        """
        raise InputValidationError(self, var_name=name, var_value=value, validation_outcome=exc)


# TODO: offer the capability to validate function outputs

def validate(**validators: Dict[str, Union[Callable, List[Callable]]]):
    """
    A function decorator to add input validation prior to the function execution. It should be called with named
    arguments: for each function input name, provide a single validation function or a list of validation functions to
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
        if is_even(a) and gt1(a) and is_even(b):
            print('hello')
        else:
            raise InputValidationError(...)
    ```

    :param validators: keyword args: for each of the function's input names, the validator function or list of validator
    functions to use. A list will be considered an  implicit `and_`. If present, `not_none` should be alone or first in
    the list
    :return: the decorated function, that will perform input validation before executing the function's code everytime
    it is executed.
    """

    # this is a general technique for decorators, to properly handle both cases of being called with arguments or not
    # this is really not needed in our case since @validate will bever be used as is (without a call), but it does not
    # cost much and may be of interest in the future
    return create_function_decorator__robust_to_args(decorate_with_validation, **validators)


alidate = validate
""" an alias for the @validate decorator, to use as follows : import valid8 as v : @v.alidate(...) """


def validate_arg(arg_name, base_validator_s: Union[Callable, List[Callable]]):
    """
    A decorator to apply function input validation for the given argument name, with the provided base validation
    function(s). You may use several such decorators on a given function as long as they are stacked on top of each
    other (no external decorator in the middle)

    :param arg_name:
    :param base_validator_s: the validator function or list of validator functions to use. A list will be considered an
    implicit `and_`. If present, `not_none` should be alone or first in the list
    :return: the decorated function, that will perform input validation before executing the function's code everytime
    it is executed.
    """
    # this is a general technique for decorators, to properly handle both cases of being called with arguments or not
    # this is really not needed in our case since @validate will bever be used as is (without a call), but it does not
    # cost much and may be of interest in the future
    return create_function_decorator__robust_to_args(decorate_with_validation, **{arg_name: base_validator_s})


def decorate_with_validation(func: Callable, **validators: Dict[str, Union[Callable, List[Callable]]]) -> Callable:
    """
    This method is equivalent to decorating a function with the `@validate` decorator, but can be used a posteriori.

    :param func:
    :param validators: keyword args: for each of the function's input names, the validator function or list of
    validator functions to use. A list will be considered an implicit `and_`. If present, `not_none` should be alone
    or first in the list.
    :return: the decorated function, that will perform input validation (using `_assert_input_is_valid`) before
    executing the function's code everytime it is executed.
    """

    # (1) retrieve target function signature
    # attrs, varargs, varkw, defaults = getargspec(func)
    sig_attrs, sig_varargs, sig_varkw, sig_defaults, signature_kwonlyargs, \
    signature_kwonlydefaults, signature_annotations = getfullargspec(func)
    # TODO better use signature(func) ? but that would be less compliant with python 2

    # (2) check that provided validators don't contain function input names that are incorrect
    incorrect = set(validators.keys()) - set(sig_attrs)
    if len(incorrect) > 0:
        raise ValueError('@validate[...] definition exception: validators are defined for \''
                         + str(incorrect) + '\' that is/are not part of signature for ' + str(func))

    # (3) create or update a wrapper around the function to add validation
    if hasattr(func, '__wrapped__') and hasattr(func.__wrapped__, '__validators__'):
        # This function is already wrapped by the validator.
        # First check that the new validators are for inputs that did not have some already
        incorrect = set(validators.keys()) - set(func.__wrapped__.__validators__.keys())
        if len(incorrect) > 0:
            raise ValueError('@validate[...] definition exception: validators are already defined for function input(s)'
                             ' \'' + str(incorrect) + '\', you can not define them twice.')
        # Then update the dictionary of validators
        for att_name, att_validators in validators.items():
            func.__wrapped__.__validators__[att_name] = InputValidator(func.__wrapped__, att_validators)

    else:
        # create the validators
        for att_name, att_validators in validators.items():
            validators[att_name] = InputValidator(func, att_validators)

        # Store the dictionary of validators as an attribute of the function
        if hasattr(func, '__validators__'):
            raise ValueError('Function ' + str(func) + ' already has a defined __validators__ attribute, valid8 '
                             'decorators can not be applied on it')
        func.__validators__ = validators

        # we used @functools.wraps(func), we now use 'decorate()' to have a wrapper that has the same signature
        def validating_wrapper(func, *args, **kwargs):
            """ This is the wrapper that will be called everytime the function is called """

            # (a) Perform input validation by applying `_assert_input_is_valid` on all received arguments
            apply_on_each_func_args(func, args, kwargs, sig_attrs, sig_defaults, sig_varargs, sig_varkw,
                                    func_to_apply=_assert_input_is_valid,
                                    func_to_apply_paramers_dict=func.__validators__)

            # (b) execute the function as usual
            return func(*args, **kwargs)

        decorated_function = decorate(func, validating_wrapper)
        return decorated_function


def _assert_input_is_valid(input_value: Any, validator: InputValidator,
                           validated_func: Callable, input_name: str):
    """
    Called for each function input before executing the function. It simply delegates to the validator.
    The signature of this function is hardcoded in `apply_on_each_func_args` and should not be changed.
    
    :param input_value: the value to validate
    :param validator_func: the validator function that will be applied on input_value_to_validate
    :param validated_func: the method for which this validation is performed. This is used just for errors
    :param input_name: the name of the function input that is being validated
    :return: Nothing
    """
    validator.assert_valid(input_name, input_value)
