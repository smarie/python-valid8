import pytest
from enforce.exceptions import RuntimeTypeError
from pytypes import InputTypeError

from valid8 import InputValidationError, ValidationError


def test_readme_index_first_inline():
    from mini_lambda import x
    from valid8 import assert_valid, is_multiple_of, NonePolicy, Failure

    surf = -1

    # simplest: one validation function and one variable name+value
    with pytest.raises(ValidationError) as exc_info:
        assert_valid(is_multiple_of(100), surface=surf)
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]. ' \
                     'Root validator [is_multiple_of_100] raised [BasicFailure: x % 100 == 0 does not hold for x=-1]'

    # + explicit failure on None
    with pytest.raises(ValidationError) as exc_info:
        assert_valid(is_multiple_of(100), surface=surf, none_policy=NonePolicy.FAIL)
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]. ' \
                     'Root validator [reject_none(is_multiple_of_100)] ' \
                     'raised [BasicFailure: x % 100 == 0 does not hold for x=-1]'

    # + explicit failure message
    with pytest.raises(ValidationError) as exc_info:
        assert_valid(x > 0, help_msg='Surface should be positive', surface=surf)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "Root validator [failure_raiser(x > 0, Surface should be positive)] " \
                     "raised [Failure: Surface should be positive. " \
                     "Function [x > 0] returned [False] for value [-1].]"

    # + explicit failure type
    class SurfaceNotMul100(Failure):
        help_msg = 'Surface should be a multiple of 100'

    with pytest.raises(ValidationError) as exc_info:
        assert_valid(is_multiple_of(100), failure_type=SurfaceNotMul100, surface=surf)
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]. ' \
                     'Root validator [failure_raiser(is_multiple_of_100, SurfaceNotMul100)] ' \
                     'raised [SurfaceNotMul100: Surface should be a multiple of 100. ' \
                     'Function [is_multiple_of_100] raised [BasicFailure: x % 100 == 0 does not hold for x=-1] for ' \
                     'value [-1].]'

    # multiple validation functions
    with pytest.raises(ValidationError) as exc_info:
        assert_valid((x >= 0) & (x < 10000), is_multiple_of(100), surface=surf)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "Root validator [and((x >= 0) & (x < 10000), is_multiple_of_100)] raised [AtLeastOneFailed: " \
                     "At least one validator failed validation for value [-1]. " \
                     "Successes: [] / Failures: {'(x >= 0) & (x < 10000)': 'False', " \
                     "'is_multiple_of_100': '[BasicFailure] x % 100 == 0 does not hold for x=-1'}]"

    # + failure messages for each
    with pytest.raises(ValidationError) as exc_info:
        assert_valid(((x >= 0) & (x < 10000), 'Out of range'),
                     (is_multiple_of(100), SurfaceNotMul100), surface=surf)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "Root validator [and(failure_raiser((x >= 0) & (x < 10000), Out of range), " \
                     "failure_raiser(is_multiple_of_100, SurfaceNotMul100))] raised [AtLeastOneFailed: " \
                     "At least one validator failed validation for value [-1]. Successes: [] / Failures: " \
                     "{'failure_raiser((x >= 0) & (x < 10000), Out of range)': '[Failure] Out of range. " \
                     "Function [(x >= 0) & (x < 10000)] returned [False] for value [-1].', " \
                     "'failure_raiser(is_multiple_of_100, SurfaceNotMul100)': '[SurfaceNotMul100] Surface " \
                     "should be a multiple of 100. Function [is_multiple_of_100] raised " \
                     "[BasicFailure: x % 100 == 0 does not hold for x=-1] for value [-1].'}]"


def test_index_enforce_mini_lambda():
    """ Tests that the first example of the documentation works """

    # Imports - for type validation
    from numbers import Real, Integral
    from valid8 import Boolean
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # subclasses of required types are valid too

    # Imports - for value validation
    from mini_lambda import s, x, Len
    from valid8 import validate_arg, is_multiple_of, Failure

    # Example of unique error type for easier handling at app-level
    class EmptyNameString(Failure):
        help_msg = 'Name should be a non-empty string'

    class SurfaceOutOfRange(Failure):
        help_msg = 'Surface should be comprised between 0 and 10000 m²'

    class SurfaceNotMultipleOf100(Failure):
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
        build_house('test', -1, 2)  # Value: @validate raises a BasicFailure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value: @validate raises a BasicFailure


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
        build_house('test', -1, 2)  # Value validation: @validate raises a BasicFailure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value validation: @validate raises a BasicFailure
