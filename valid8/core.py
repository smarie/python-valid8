from inspect import getfullargspec
from numbers import Integral
from typing import Callable, Dict, Any, Set, List, Tuple, Union, Iterable, Container

from decorator import decorate

from valid8.mini_lambda import _InputEvaluator
from valid8.utils_decoration import _create_function_decorator__robust_to_args, apply_on_func_args


def validate(**validators: Dict[str, Callable[[Any], bool]]):
    """
    Defines a decorator with parameters, that will execute the provided input validators PRIOR to executing the 
    function. Specific entry 'returns' may contain validators executed AFTER executing the function.
    
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
            raise ValidationError(...)
    ```
    
    :param validators: 
    :return: 
    """
    return _create_function_decorator__robust_to_args(validate_decorate, **validators)


alidate = validate  # a alias for the @validate decorator, to use as follows : import valid8 as v : @v.alidate(...)


def validate_decorate(func: Callable, **validators: Dict[str, Callable[[Any], bool]]) -> Callable:
    """
    Defines a decorator with parameters, that will execute the provided input validators PRIOR to executing the 
    function. Specific entry 'returns' may contain validators executed AFTER executing the function.
    
    :param func: 
    :param include: 
    :param exclude: 
    :return: 
    """
    # (1) retrieve function signature
    # attrs, varargs, varkw, defaults = getargspec(func)
    signature_attrs, signature_varargs, signature_varkw, signature_defaults, signature_kwonlyargs, \
    signature_kwonlydefaults, signature_annotations = getfullargspec(func)
    # TODO better use signature(func) ? but that would be less compliant with python 2

    # (2) check that provided validators dont contain names that are incorrect
    if validators is not None:
        incorrect = set(validators.keys()) - set(signature_attrs)
        if len(incorrect) > 0:
            raise ValueError('@validate definition exception: validators are defined for \'' + str(incorrect) + '\' '
                             'that is/are not part of signature for ' + str(func))
    # for att_name, att_validators in validators.items():
    #     i = att_validators.index(not_none)
    #     if i > 0:
    #         raise ValueError('not_none is a special validator that can only be provided at the beginning of the'
    #                          ' validators list')

    # replace validators lists with explicit and_ if needed
    for att_name, att_validators in validators.items():
        validators[att_name] = create_main_validation_function(att_validators, allow_not_none=True)

    # (3) create a wrapper around the function to add validation
    # -- old:
    # @functools.wraps(func) -> to make the wrapper function look like the wrapped function
    # def wrapper(self, *args, **kwargs):
    # -- new:
    # we now use 'decorate' at the end of this code to have a wrapper that has the same signature, see below
    def wrapper(func, *args, **kwargs):
        # apply _validate_function_inputs on all received arguments
        apply_on_func_args(func, args, kwargs, signature_attrs, signature_defaults, signature_varargs, signature_varkw,
                           _validate_function_inputs, validators)

        # finally execute the method
        return func(*args, **kwargs)

    a = decorate(func, wrapper)
    # save the validators somewhere for reference. This is useful for other decorators example for autoclass/autoprops
    a.__validators__ = validators
    return a


def create_main_validation_function(att_validators, allow_not_none: bool):
    """
    Creates the main validation function to be used for a specific input.
    * if att_validators is not a list, it transforms it into a list
    * if 'not_none' validator is present in the list, it should be the first in the list.

    The function generates a validation function that will
    * either raise an error on None or ignore None values silently, depending respectively on if the user included
    `not_none` in the validators list or not
    * combine all validators from the list (except 'not_none') in an 'and_' validator if more than one validator

    :param att_validators: a validator function or a list of validators
    :param allow_not_none: True to allow 'not_none' to be present in the list of validators
    :return:
    """
    att_validators = _assert_list_and_protect_not_none(att_validators, allow_not_none=allow_not_none)

    if att_validators[0] != not_none:
        ignore_nones_silently = True
        remaining_validators = att_validators
    else:
        # the first element is not_none, it will be removed and replaced with _not_none_checker
        ignore_nones_silently = False
        remaining_validators = att_validators[1:]

    if len(remaining_validators) >= 1:
        # note that and_ automatically reduces to contents when contents is a single element
        main_validation_function = _not_none_checker(and_(remaining_validators),
                                                     ignore_none_silently=ignore_nones_silently)
    else:
        if ignore_nones_silently:
            main_validation_function = _not_none_checker(remaining_validators[0],
                                                         ignore_none_silently=ignore_nones_silently)
        else:
            # there is a single validator here and it is 'not_none'. We cant replace it with
            main_validation_function = not_none

    return main_validation_function


def _not_none_checker(validator, ignore_none_silently: bool = True):
    """
    Generates a checker handling None values. When a None value is received, it is not passed to the validator.
    Instead this operator will either drop silently (ignore_none_silently = True) or return a False
    (ignore_none_silently=False)

    :param validator:
    :param ignore_none_silently:
    :return:
    """
    if ignore_none_silently:
        def drop_none_silently(x):
            if x is not None:
                return validator(x)
            else:
                # value is None: skip validation (users should explicitly include 'not_none' as the first validator to
                # change this behaviour)
                return True
        return drop_none_silently

        # use the `decorate` helper method to preserve name and signature of the inner object
        # ==> NO, we want to support also non-function callable objects
        # def drop_none_silently_wrapper(validator, x):
        #     if x is not None:
        #         return validator(x)
        #     else:
        #         # value is None : skip validation (users should explicitly include 'not_none' as the first validator to
        #         # change this behaviour)
        #         return True
        # drop_none_silently = decorate(validator, drop_none_silently_wrapper)
        # return drop_none_silently

    else:
        def check_not_none(x):
            # not_none will perform the Exception raising
            if not_none(x):
                return validator(x)
            else:
                # this should never happen, except if not_none changed behaviour and we forgot to align everything..
                raise Exception('Internal error - please create an issue on the project page')
        return check_not_none


def _validate_function_inputs(input_value_to_validate, validator_func, validated_func, input_name):
    """
    Subroutine of the @validate function annotation that actually performs validation, by executing

        `validator_func(input_value_to_validate)`

    The statement should return `True` or `None` for the validation to be considered valid. Note that this is
    quite different from the standard python truth value test (where None is equivalent to False), but it seems
    more adapted to an intuitive usage, where a function that returns silently without any output means a
    successful validation. The checking is done using helper function `result_is_success` across the board, so as to
    ensure a consistent behaviour if this changes in the future.

    This function is often the only one to know the context (func, input_name), and therefore is also the only one able
    to raise the top-level ValidationError using ValidationError.create. The top-level however
    does not now anything about the validators' structure, because we do not want to maintain a reflective structure
    about validators, while good exceptions may do the job nicely.

    Therefore validators (and validator logic operators) are responsible to raise explicit exception messages
    (ValidationError may be used but is not mandatory). The only exception (haha) to that rule is when a single custom
    validator is used and returns False (or not True, not None). That case is properly handled here.

    :param input_value_to_validate: the value to validate
    :param validator_func: the validator function that will be applied on input_value_to_validate
    :param validated_func: the method for which this validation is performed. This is used just for errors
    :param input_name: the name of the function input that is being validated
    :return: Nothing
    """
    try:
        # perform validation
        res = validator_func(input_value_to_validate)

    except Exception as e:
        # caught inner ValidationError: treat as other errors
        # caught other error
        raise InputValidationError.create(validated_func, input_name, input_value_to_validate,
                                          exc=e)

    if not result_is_success(res):
        # failure without explicit exception ! special handling
        extra = ' custom validation function [' + (validator_func.__name__ or str(validator_func)) \
                + '] returned [' + str(res) + '] that is not ' + SUCCESS_CONDITIONS
        raise InputValidationError.create(validated_func, input_name, input_value_to_validate,
                                          extra_msg=extra)


class ValidationError(ValueError):
    """
    An Exception raised whenever validation fails. It is typically raised by Validators themselves. It is recommended
    that validators subclass this exception type in order to provide a unique exception identifier for each validation
    error type.

    `InputValidationError` is a special subclass raised by function input validator (i.e. the @validate annotation)
    """

    def __init__(self, contents):
        """
        We actually can't put more than 1 argument in the constructor, it creates a bug in Nose tests
        https://github.com/nose-devs/nose/issues/725. Please use ValidationError.create() instead

        TODO: at some point we should maybe remove this behaviour since we dont use Nose anymore :)

        :param contents:
        """
        super(ValidationError, self).__init__(contents)

    @staticmethod
    def create(validator_name, validation_formula, var_value, var_name: str = None,
               extra_msg: str = None):
        """
        Creates a simple standard Validation Error such as:

        'is_mod: y % 3 == 0 does not hold for y=5. <extra details>'

        Where
        * validator_name = 'is_mod'
        * validation_formula = 'y % 3 == 0'
        * input_value = 5
        * var_name = 'y' (default is 'x')
        * extra_msg = '<extra details>' (default is '')

        :param validator_name:
        :param validation_formula:
        :param var_value:
        :param var_name: to change the variable name ('x' by default)
        :param extra_msg:
        :return:
        """
        return ValidationError(validator_name + ': ' + validation_formula + ' does not hold for variable '
                               + (var_name or 'x') + '=' + str(var_value) + (('. ' + extra_msg) if extra_msg else '.'))


class InputValidationError(ValidationError):
    """
    Exception raised whenever function input validation fails. It is not meant to be subclassed by users, please rather
    subclass ValidationError directly.
    """

    def __init__(self, contents):
        """
        We actually can't put more than 1 argument in the constructor, it creates a bug in Nose tests
        https://github.com/nose-devs/nose/issues/725. Please use InputValidationError.create() instead

        TODO: at some point we should maybe remove this behaviour since we dont use Nose anymore :)

        :param contents:
        """
        super(InputValidationError, self).__init__(contents)

    @staticmethod
    def create(validated_function, var_name, var_value, extra_msg: str = None,
               exc: Exception = None):
        """
        Internal utility method called by the @validate annotation to produce the top-level error message, containing
        the validated function and the input name. The top-level however does not now anything about the validators'
        structure. Therefore validators (and validator logic operators) are responsible to raise explicit exception
        messages. The only exception is when a single custom validator is used and returns False (or not True, not None)
        That case is properly handled in _validate_function_inputs.

        :param validated_function:
        :param var_name:
        :param var_value:
        :param extra_msg:
        :param exc: a caught inner exception, if any
        :return:
        """
        common_text = 'Error validating input [' + str(var_name) + '=' + str(var_value) \
                      + '] for function [' + (validated_function.__name__ or str(validated_function)) + ']' \
                      + ((': ' + extra_msg) if extra_msg else '')
        if exc is not None:
            return InputValidationError(common_text + '.\n  Caught error: ' + str(exc))\
                .with_traceback(exc.__traceback__)
        else:
            return InputValidationError(common_text)


def get_names(validators):
    return ', '.join([val.__name__ for val in validators])


# this validator is too tied to the above to be moved elsewhere
def not_none(x: Any):
    """ 'Is not None' validator """
    if x is None:
        raise ValidationError('not_none: failure, x is None')
    else:
        return True


def _assert_list_and_protect_not_none(validators, allow_not_none: bool = False):
    """
     * if validators is an empty list, throw error
     * If validators is a singleton, turns it into a list.
     * If validators contains not_none and allow_not_none is set to True, asserts that not_none is first in the list
     * If validators contains not_none and allow_not_none is set to False, asserts that not_none is not present at all
     in the list

    :param validators:
    :param allow_not_none:
    :return:
    """
    i = -1
    if isinstance(validators, _InputEvaluator):
        # special case of an _InputEvaluator: convert to a function
        validators = [validators.as_function()]
    else:
        try:
            i = validators.index(not_none)
        except ValueError:
            # not_none not found in validators list : ok
            pass
        except AttributeError:
            # validators is not a list (no attribute 'index'): turn it into a list
            validators = [validators]

    # not_none ?
    # obviously this does not prevent users to embed a not_none inside an 'and_' or something else... but we cant
    # prevent all mistakes :)
    if i > 0 or (i == 0 and not allow_not_none):
        raise ValueError('not_none is a special validator that can only be provided at the beginning of the'
                         ' global validators list')
    # empty list ?
    if len(validators) == 0:
        raise ValueError('provided validators list is empty')

    return validators


# ----------- composition : we cant move these away since and_() is quite tight to the core
def and_(validators):
    """
    An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a
    `ValidationException` on the first `False` received or `Exception` caught.

    Note that an implicit `and_` is performed if you provide a list of validators to `@validate`.

    :param validators:
    :return:
    """

    validators = _assert_list_and_protect_not_none(validators)

    if len(validators) == 1:
        return validators[0]  # simplification for single validator case
    else:
        def and_v_(x):
            for validator in validators:
                res = validator(x)
                if not result_is_success(res):
                    # one validator was unhappy > raise
                    raise ValidationError('and(' + get_names(validators) + '): validator '
                                          + (validator.__name__ or str(validator)) + ' failed validation for input '
                                          + str(x))
            return True

        return and_v_


def or_(validators):
    """
    An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught
    exception's message if any.

    :param validators:
    :return:
    """

    validators = _assert_list_and_protect_not_none(validators)

    if len(validators) == 1:
        return validators[0]  # simplification for single validator case
    else:
        def or_v_(x):
            err = None
            for validator in validators:
                try:
                    res = validator(x)
                    if result_is_success(res):
                        # we can return : one validator was happy
                        return True
                except Exception as e:
                    if err is None:
                        err = e  # remember the first exception

            # no validator accepted: raise
            msg = 'or(' + get_names(validators) + '): All validators failed validation for input \'' + str(x) + '\'. '
            if err is not None:
                msg += 'First exception caught was: \'' + str(err) + '\''
            raise ValidationError(msg)

        return or_v_


def xor_(validators):
    """
    A 'xor' validator: returns `True` if exactly one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught
    exception's message if any.

    :param validators:
    :return:
    """

    validators = _assert_list_and_protect_not_none(validators)

    if len(validators) == 1:
        return validators[0]  # simplification for single validator case
    else:
        def xor_v_(x):
            ok_validator = None
            sec_validator = None
            err = None
            for validator in validators:
                try:
                    res = validator(x)
                    if result_is_success(res):
                        if ok_validator is not None:
                            # we found the second validator happy
                            sec_validator = validator
                        else:
                            # we found the first one happy
                            ok_validator = validator
                except Exception as e:
                    if err is None:
                        err = e  # remember the first exception

            # return if were happy or not
            if ok_validator is not None:
                if sec_validator is None:
                    # one unique validator happy: success
                    return True
                else:
                    # second validator happy : fail, too many validators happy
                    raise ValidationError('xor(' + get_names(validators) + ') : Too many validators succeeded : '
                                          + str(ok_validator) + ' + ' + str(sec_validator))
            else:
                # no validator happy
                msg = 'xor(' + get_names(validators) + '): All validators failed validation for input \'' + str(x) + '\'. '
                if err is not None:
                    msg += 'First exception caught was: \'' + str(err) + '\''
                raise ValidationError(msg)

        return xor_v_


def not_(validator, catch_all: bool = False):
    """
    Generates the inverse of the provided validator: when the validator returns `False` or raises a `ValidationError`,
    this validator returns `True`. Otherwise it returns `False`.

    By default, `Expection` other than `ValidationError` are not caught and therefore fail the validation
    (`catch_all=False`). To change this behaviour you can turn the `catch_all` parameter to `True`, in which case all
    exceptions will be caught instead of just `ValidationError`s.

    Note that you may provide a list of validators to `not_()`. It will be interpreted as `not_(and_(<valiators_list>))`

    :param validator:
    :param catch_all: an optional boolean flag. By default, only ValidationError are silently catched and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be catched and turned to a
    'ok' result
    :return:
    """

    # in case this is a validator list, create a 'and_' around it (otherwise this returns the validator)
    # not any more, this is not very intuitive
    # validator = and_(validator)

    def not_v_(x):
        if catch_all:
            try:
                res = validator(x)
                if not result_is_success(res):  # inverse the result
                    return True
            except:
                return True  # caught exception: return True

            # if we're here that's a failure
            raise ValidationError('not(' + str(validator) + '): Validator validated input \'' + str(x) + '\' with success, '
                                  'therefore the not() is a failure')
        else:
            try:
                res = validator(x)
                if not result_is_success(res):  # inverse the result
                    return True
            except ValidationError:
                return True  # caught exception: return True

            # if we're here that's a failure
            raise ValidationError('not(' + str(validator) + '): Validator validated input \'' + str(x) + '\' with success, '
                                  'therefore the not() is a failure')
    return not_v_


def not_all(validators, catch_all: bool = False):
    """
    An alias for not_(and_(validators)).

    :param validators: a validators list or a single validator
    :param catch_all: an optional boolean flag. By default, only ValidationError are silently catched and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be catched and turned to a
    'ok' result
    :return:
    """

    # in case this is a validator list, create a 'and_' around it (otherwise this returns the validator)
    validators = and_(validators)
    return not_(validators, catch_all=catch_all)


SUCCESS_CONDITIONS = 'in {None, True}'  # used in some error messages


def result_is_success(validation_result):
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
