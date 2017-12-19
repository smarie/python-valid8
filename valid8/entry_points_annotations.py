from inspect import signature, Parameter

from typing import Callable, Any, List, Type

from decorator import decorate

from valid8.utils_typing import is_pep484_nonable
from valid8.utils_decoration import create_function_decorator__robust_to_args, apply_on_each_func_args_sig
from valid8.base import get_callable_name
from valid8.composition import ValidationFuncs
from valid8.entry_points import ValidationError, Validator, NonePolicy, NoneArgPolicy


class InputValidationError(ValidationError):
    """
    Exception raised whenever function input validation fails. It is almost identical to `ValidationError`, except that
    the inner validator is a `InputValidator`, which provides more contextual information to display.

    Users may (recommended) subclass this type the same way they do for `ValidationError`, so as to generate unique
    error codes for their applications.

    See `ValidationError` for details.
    """

    def get_what_txt(self):
        """
        Overrides the base behaviour defined in ValidationError in order to add details about the function.
        :return:
        """
        return 'input [{var}] for function [{func}]'.format(var=self.get_variable_str(),
                                                            func=self.validator.get_validated_func_display_name())


class InputValidator(Validator):
    """
    Represents a special kind of `Validator` responsible to validate a function input.
    """

    def __init__(self, validated_func: Callable, *validation_func: ValidationFuncs,
                 error_type: Type[InputValidationError] = None, help_msg: str = None, none_policy: int = None,
                 **kw_context_args):
        """

        :param validated_func: the function whose input is being validated.
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
        # store this additional info
        self.validated_func = validated_func

        # super constructor with default error type 'InputValidationError'
        error_type = error_type or InputValidationError
        super(InputValidator, self).__init__(*validation_func, none_policy=none_policy, error_type=error_type,
                                             help_msg=help_msg, **kw_context_args)

    def get_additional_info_for_repr(self):
        return 'validated_function={func}'.format(func=get_callable_name(self.validated_func))

    def get_validated_func_display_name(self):
        """
        Utility method to get a friendly display name for the function being validated by this InputValidator
        :return:
        """
        return self.validated_func.__name__ or str(self.validated_func)


# TODO: offer the capability to validate function outputs
def validate(none_policy: int = None, **kw_validation_funcs: ValidationFuncs):
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


def validate_arg(arg_name, *validation_func: ValidationFuncs, none_policy: int = None) -> Callable:
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
                            none_policy: int):
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


def decorate_with_validation(func: Callable, none_policy: int = None,
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

        # # First check that the new validators to create are for inputs that did not have some validators already
        # incorrect = set(kw_validation_funcs.keys()).intersection(set(func.__wrapped__.__validators__.keys()))
        # if len(incorrect) > 0:
        #     raise ValueError('@validate[...] definition exception: kw_validation_funcs are already defined for '
        #                      'function input(s) \'' + str(incorrect) + '\', you can not define them twice.')
        # ==> NO, we now support that - it is actually a good way to separate applicative error codes

        # Then update the dictionary of validators with the new validators
        for att_name, att_validators in kw_validation_funcs.items():
            # create the new validators as InputValidator objects according to the none_policy and function signature
            new_validator = _create_input_validator(func.__wrapped__, s.parameters[att_name], att_validators,
                                                    none_policy=none_policy)
            if hasattr(func.__wrapped__.__validators__, att_name):
                func.__wrapped__.__validators__[att_name].append(new_validator)
            else:
                func.__wrapped__.__validators__[att_name] = [new_validator]

        # return the function, no need to wrap it further (it is already wrapped)
        return func

    else:
        # ---- This function is not yet wrapped by our validator. ----

        # create the new validators as InputValidator objects according to the none_policy and function signature
        for att_name, att_validators in kw_validation_funcs.items():
            kw_validation_funcs[att_name] = [_create_input_validator(func, s.parameters[att_name], att_validators,
                                                                     none_policy=none_policy)]

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


def _assert_input_is_valid(input_value: Any, validators: List[InputValidator], validated_func: Callable,
                           input_name: str):
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
    for validator in validators:
        validator.assert_valid(input_name, input_value)