import pytest
from enforce.exceptions import RuntimeTypeError
from pytypes import InputTypeError

from valid8 import InputValidationError, ValidationError, failure_raiser


def test_readme_index_first_inline():
    from mini_lambda import x
    from valid8 import assert_valid, is_multiple_of, NonePolicy, WrappingFailure

    surf = -1

    # simplest: one validation function and one variable name+value
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, is_multiple_of(100))
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]. ' \
                     'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1].'

    # + explicit validation error on None
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', None, is_multiple_of(100), none_policy=NonePolicy.FAIL)
    e = exc_info.value
    assert str(e) == 'Error validating [surface=None]. ValueIsNone: The value must be non-None. Wrong value: [None].'

    # + custom error message (exception is still ValidationError)
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, x > 0, help_msg='Surface should be positive')
    e = exc_info.value
    assert str(e) == "Surface should be positive. " \
                     "Error validating [surface=-1]: validation function [x > 0] returned [False]."

    # + custom error message (unique applicative exception type)
    class SurfaceNotMul100(ValidationError):
        help_msg = 'Surface should be a multiple of 100'

    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, is_multiple_of(100), error_type=SurfaceNotMul100)
    e = exc_info.value
    assert isinstance(e, SurfaceNotMul100)
    assert str(e) == 'Surface should be a multiple of 100. ' \
                     'Error validating [surface=-1]. ' \
                     'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1].'

    # multiple validation functions
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, (x >= 0) & (x < 10000), is_multiple_of(100))
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [-1]. " \
                     "Successes: [] / Failures: {'(x >= 0) & (x < 10000)': 'False', " \
                     "'is_multiple_of_100': 'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1]'}."

    # + unique applicative error type
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100, found {var_value}'

    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf,
                     (x >= 0) & (x < 10000), is_multiple_of(100),
                     error_type=InvalidSurface)
    e = exc_info.value
    assert str(e) == "Surface should be between 0 and 10000 and be a multiple of 100, found -1. " \
                     "Error validating [surface=-1]. " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [-1]. " \
                     "Successes: [] / Failures: {" \
                     "'(x >= 0) & (x < 10000)': 'False', " \
                     "'is_multiple_of_100': 'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1]'}."

    # *** TEST: custom failure details message. Does it have any interest ? ***
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, (is_multiple_of(100), 'Surface should be a multiple of 100'))
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]. ' \
                     'WrappingFailure: Surface should be a multiple of 100. ' \
                     'Function [is_multiple_of_100] raised ' \
                     '[IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1]].'

    # + failure messages for each
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf,
                     ((x >= 0) & (x < 10000), 'Surface should be between 0 and 10000'),
                     (is_multiple_of(100), 'Surface should be a multiple of 100'))
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "AtLeastOneFailed: At least one validation function failed validation. " \
                     "Successes: [] / Failures: {" \
                     "'(x >= 0) & (x < 10000)': 'WrappingFailure: Surface should be between 0 and 10000. " \
                     "Function [(x >= 0) & (x < 10000)] returned [False] for value [-1].', " \
                     "'is_multiple_of_100': 'WrappingFailure: Surface should be a multiple of 100. " \
                     "Function [is_multiple_of_100] raised [IsNotMultipleOf: Value should be a multiple of 100. " \
                     "Wrong value: [-1]].'}."

    # + unique applicative error type + custom message formatting
    with pytest.raises(ValidationError) as exc_info:
        min_val = 0
        max_val = 10000
        assert_valid('surface', surf,
                     failure_raiser((x >= min_val) & (x < max_val),
                                    help_msg='Surface should be between {min_val} and {max_val}',
                                    min_val=min_val, max_val=max_val),
                     (is_multiple_of(100), 'Surface should be a multiple of 100, found {wrong_value}'),
                     error_type=InvalidSurface)
    e = exc_info.value
    assert str(e) == "Surface should be between 0 and 10000 and be a multiple of 100, found -1. " \
                     "Error validating [surface=-1]. " \
                     "AtLeastOneFailed: At least one validation function failed validation. " \
                     "Successes: [] / Failures: {" \
                     "'(x >= 0) & (x < 10000)': 'WrappingFailure: Surface should be between 0 and 10000. " \
                     "Function [(x >= 0) & (x < 10000)] returned [False] for value [-1].', " \
                     "'is_multiple_of_100': 'WrappingFailure: Surface should be a multiple of 100, found -1. " \
                     "Function [is_multiple_of_100] raised [IsNotMultipleOf: Value should be a multiple of 100. " \
                     "Wrong value: [-1]].'}."


def test_index_enforce_mini_lambda():
    """ Tests that the first example of the documentation works """

    # Imports - for type validation
    from numbers import Real, Integral
    from valid8 import Boolean
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # subclasses of required types are valid too

    # Imports - for value validation
    from mini_lambda import s, x, Len
    from valid8 import validate_arg, is_multiple_of, WrappingFailure

    # Example of unique error type for easier handling at app-level
    class EmptyNameString(WrappingFailure):
        help_msg = 'Name should be a non-empty string'

    class SurfaceOutOfRange(WrappingFailure):
        help_msg = 'Surface should be comprised between 0 and 10000 m²'

    class SurfaceNotMultipleOf100(WrappingFailure):
        help_msg = 'Surface should be a multiple of 100'

    @runtime_validation
    @validate_arg('name',    (Len(s) > 0,              EmptyNameString))
    @validate_arg('surface', [((x >= 0) & (x < 10000), SurfaceOutOfRange),
                              (is_multiple_of(100),    SurfaceNotMultipleOf100)])
    def build_house(name: str,
                    surface: Real,
                    nb_floors: Integral = None,
                    with_windows: Boolean = False):
        print('Building house...')
        print('DONE !')

    build_house('test', 100, 2)  # validation OK

    with pytest.raises(RuntimeTypeError):
        build_house('test', 100, 2.2)  # Type: @runtime_validation raises a InputTypeError

    build_house('test', 100, None)  # Declared 'Optional' with PEP484, no error

    with pytest.raises(InputValidationError):
        build_house('', 12, 2)  # Value: @validate raises a EmptyNameString

    with pytest.raises(InputValidationError):
        build_house('test', -1, 2)  # Value: @validate raises a SurfaceOutOfRange

    with pytest.raises(InputValidationError):
        build_house('test', -1, 2)  # Value: @validate raises a SurfaceNotMultipleOf100


def test_index_enforce_old_style():
    """ Tests that the first example of the documentation works """

    # Imports - for type validation
    from valid8 import Boolean
    from numbers import Real, Integral
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # allow subclasses when validating types

    # Imports - for value validation
    from valid8 import validate, minlens, gt

    # Usage
    @runtime_validation
    @validate(name=minlens(0),
              surface=gt(0))
    def build_house(name: str,
                    surface: Real,
                    nb_floors: Integral = None,
                    with_windows: Boolean = False):
        print('you did it !')

    build_house('test', 12, 2)  # validation OK

    with pytest.raises(RuntimeTypeError):
        build_house('test', 12, 2.2)  # Type: @runtime_validation raises a InputTypeError

    build_house('test', 12, None)  # Declared 'Optional' with PEP484, no error

    with pytest.raises(ValidationError):
        build_house('test', -1, 2)  # Value: @validate raises a Failure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value: @validate raises a Failure


@pytest.mark.skip(reason="waiting for the next version of pytypes")
def test_index_pytypes():
    """ Tests that the first example of the documentation would work if we switch to pytypes """

    # for type checking
    from valid8 import Boolean
    from numbers import Real, Integral
    from typing import Optional
    from pytypes import typechecked

    # for value checking
    from valid8 import validate, minlens, gt

    @typechecked
    @validate(name=minlens(0),
              surface=gt(0))
    def build_house(name: str,
                    surface: Real,
                    nb_floors: Optional[Integral] = 1,
                    with_windows: Boolean = False):
        print('you did it !')

    build_house('test', 12, 2)  # validation OK

    with pytest.raises(InputTypeError):
        build_house('test', 12, 2.2)  # Type validation: @typechecked raises a InputTypeError

    build_house('test', 12, None)  # Mandatory/Optional validation: Declared 'Optional' with PEP484, no error

    with pytest.raises(ValidationError):
        build_house('test', -1, 2)  # Value validation: @validate raises a Failure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value validation: @validate raises a Failure
