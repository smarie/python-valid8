import traceback

import pytest
from enforce.exceptions import RuntimeTypeError
from pytypes import InputTypeError

from valid8 import InputValidationError, ValidationError, failure_raiser


def test_readme_index_usage_quick():
    """ Tests that the example under index/usage/quick works """

    from valid8 import validate

    surf = -1

    with pytest.raises(ValidationError) as exc_info:
        validate('surface', surf, instance_of=int, min_value=0)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "TooSmall: x >= 0 does not hold for x=-1. Wrong value: [-1]."


def test_readme_usage_wrap_valid():
    """ Tests that the example under index/usage/validation works """

    from valid8 import wrap_valid
    from math import isfinite

    surf = -1

    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]: " \
                     "validation function [v.alid = surf > 0 and isfinite(surf)] returned [False]."

    surf = 1j

    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e).startswith("Error validating [surface=1j]. " \
                             "Validation function [v.alid = surf > 0 and isfinite(surf)] raised " \
                             "TypeError:")

    # alternate naming
    surf = -1
    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf) as r:
            r.esults = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]: " \
                     "validation function [r.esults = surf > 0 and isfinite(surf)] returned [False]."

    # type validation
    surf = 1j
    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf, instance_of=int) as v:
            v.alid = surf > 0
    e = exc_info.value
    assert str(e) == "Error validating [surface=1j]. " \
                     "HasWrongType: Value should be an instance of <class 'int'>. Wrong value: [1j]."

    from valid8 import assert_instance_of
    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf) as v:
            assert_instance_of(surf, int)
            v.alid = surf > 0
    e = exc_info.value
    assert str(e) == "Error validating [surface=1j]. " \
                     "Validation function [assert_instance_of(surf, int)] raised " \
                     "HasWrongType: Value should be an instance of <class 'int'>. Wrong value: [1j]."


def test_readme_usage_customization():

    from valid8 import validate, wrap_valid
    from math import isfinite

    surf = -1

    # (A) custom error message (exception is still a ValidationError)
    # with pytest.raises(ValidationError) as exc_info:
    #     validate('surface', surf, instance_of=int, min_value=0,
    #                 help_msg="Surface should be a positive integer")
    # e = exc_info.value
    # assert str(e) == "Surface should be a positive integer. Error validating [surface=-1]. " \
    #                  "TooSmall: x >= 0 does not hold for x=-1. Wrong value: [-1]."

    # (A) custom error message (exception is still a ValidationError)
    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf, help_msg="Surface should be a finite positive integer") as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e) == "Surface should be a finite positive integer. Error validating [surface=-1]: " \
                     "validation function [v.alid = surf > 0 and isfinite(surf)] returned [False]."

    # (B) custom error types (recommended to provide unique applicative errors)
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be a positive integer'

    with pytest.raises(ValidationError) as exc_info:
        validate('surface', surf, instance_of=int, min_value=0, error_type=InvalidSurface)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)
    assert str(e) == "Surface should be a positive integer. " \
                     "Error validating [surface=-1]. " \
                     "TooSmall: x >= 0 does not hold for x=-1. Wrong value: [-1]."

    # (C) custom error types with templating
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be > {minimum}, found {var_value}'

    with pytest.raises(ValidationError) as exc_info:
        validate('surface', surf, instance_of=int, min_value=0,
                 error_type=InvalidSurface, minimum=0)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)
    assert type(e).__name__ == "InvalidSurface[ValueError]"
    assert str(e) == "Surface should be > 0, found -1. Error validating [surface=-1]. " \
                     "TooSmall: x >= 0 does not hold for x=-1. Wrong value: [-1]."

    # (D) ValueError/TypeError
    with pytest.raises(ValidationError) as exc_info:
        validate('surface', -1, instance_of=int, min_value=0)
    e = exc_info.value
    assert traceback.format_exception_only(type(e), e)[0] == \
           "valid8.entry_points.ValidationError[ValueError]: Error validating [surface=-1]. " \
           "TooSmall: x >= 0 does not hold for x=-1. Wrong value: [-1].\n"
    assert repr(type(e)) == "<class 'valid8.entry_points.ValidationError[ValueError]'>"

    with pytest.raises(ValidationError) as exc_info:
        validate('surface', 1j, instance_of=int, min_value=0)
    e = exc_info.value
    assert repr(type(e)) == "<class 'valid8.entry_points.ValidationError[TypeError]'>"


# deprecated
def test_readme_index_usage_basic():
    """ Tests that the examples provided in the index page under Usage examples/Basic are correct """

    from valid8 import assert_valid, instance_of, is_multiple_of

    surf = -1

    # (1) simplest: one named variable to validate, one validation function
    assert_valid('surface', surf, instance_of(int))
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, is_multiple_of(100))
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]. ' \
                     'Validation function [is_multiple_of_100] raised ' \
                     'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1].'

    # (2) native mini_lambda support to define validation functions
    from mini_lambda import x
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, x > 0)
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]: validation function [x > 0] returned [False].'


def test_readme_index_usage_function():
    """ Tests that the examples provided in the index page under Usage examples/Function are correct """

    from mini_lambda import s, Len
    from valid8 import validate_arg, instance_of

    @validate_arg('name', instance_of(str), Len(s) > 0,
                  help_msg='name should be a non-empty string')
    def build_house(name, surface=None):
        print('Building house... DONE !')
        return name, surface

    build_house('sweet home', 200)

    with pytest.raises(InputValidationError) as exc_info:
        build_house('', 100)  # name is invalid
    e = exc_info.value
    assert str(e) == "name should be a non-empty string. " \
                     "Error validating input [name=] for function [build_house]. " \
                     "Validation function [and(instance_of_<class 'str'>, len(s) > 0)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation for value []. " \
                     "Successes: [\"instance_of_<class 'str'>\"] / Failures: {'len(s) > 0': 'False'}."

    from mini_lambda import s, x, l, Len
    from valid8 import validate_arg, validate_out, instance_of, is_multiple_of

    @validate_arg('name', instance_of(str), Len(s) > 0,
                  help_msg='name should be a non-empty string')
    @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                  help_msg='Surface should be a multiple of 100 between 0 and 10000.')
    @validate_out(instance_of(tuple), Len(l) == 2)
    def build_house(name, surface=None):
        print('Building house... DONE !')
        return name, surface

    build_house('sweet home')
    build_house('sweet home', None)  # No error !

    with pytest.raises(TypeError):
        is_multiple_of(100)(None)

    with pytest.raises(TypeError):
        (Len(s) > 0).evaluate(None)


def test_readme_index_usage_class_fields():
    """ Tests that the examples provided in the index page under Usage examples/class fields are correct"""

    from valid8 import validate_field, instance_of, is_multiple_of, ClassFieldValidationError
    from mini_lambda import x, s, Len

    @validate_field('name', instance_of(str), Len(s) > 0,
                    help_msg='name should be a non-empty string')
    @validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                    help_msg='Surface should be a multiple of 100 between 0 and 10000.')
    class House:
        def __init__(self, name, surface=None):
            self.name = name
            self.surface = surface

        @property
        def surface(self):
            return self.__surface

        @surface.setter
        def surface(self, surface=None):
            self.__surface = surface

    h = House('sweet home')
    h.name = ''  # DOES NOT RAISE InvalidNameError

    with pytest.raises(ClassFieldValidationError):
        h = House('')

    h.surface = 100
    with pytest.raises(ClassFieldValidationError):
        h.surface = 10000


def test_testing():
    """ """
    from mini_lambda import s, Len
    from valid8 import assert_valid, Validator, instance_of

    name = 'sweet_home'

    assert_valid('name', name, instance_of(str), Len(s) > 0,
                 help_msg='name should be a non-empty string')

    v = Validator(instance_of(str), Len(s) > 0,
                  help_msg='name should be a non-empty string')
    v.assert_valid('name', name)


def test_advanced_composition():
    """ """

    from mini_lambda import x
    from valid8 import Validator, is_multiple_of

    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000'

    v = Validator(((x >= 0) & (x < 10000), 'Surface should be between 0 and 10000'),
                  (x % 100 == 0, 'Surface should be a multiple of 100'),
                  error_type=InvalidSurface)

    # v.assert_valid('surface', -100)

    # v.assert_valid('surface', 99)


# deprecated
def test_readme_index_usage_customization():
    """ Tests that the examples provided in the index page under Usage examples/Customization are correct """

    from valid8 import assert_valid, is_multiple_of, ValidationError
    from mini_lambda import x

    from valid8 import NonePolicy

    surf = -1

    # (3) explicit validation policy for None
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', None, x > 0, none_policy=NonePolicy.FAIL)
    e = exc_info.value
    assert str(e) == 'Error validating [surface=None]. Validation function [reject_none(x > 0)] raised ' \
                     'ValueIsNone: The value must be non-None. Wrong value: [None].'

    # *** (4) TEST: custom Failure (not ValidationError) message. Does it have any interest ? ***
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, (is_multiple_of(100), 'Surface should be a multiple of 100'))
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]. ' \
                     'Validation function [is_multiple_of_100] raised ' \
                     'WrappingFailure: Surface should be a multiple of 100. ' \
                     'Function [is_multiple_of_100] raised ' \
                     '[IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1]].'

    # (4) custom error message (exception is still a ValidationError)
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, x > 0, help_msg='Surface should be positive')
    e = exc_info.value
    assert str(e) == "Surface should be positive. " \
                     "Error validating [surface=-1]: validation function [x > 0] returned [False]."

    # (5) custom error types (recommended to provide unique applicative errors)
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be a positive number'

    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, is_multiple_of(100), error_type=InvalidSurface)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)
    assert str(e) == 'Surface should be a positive number. ' \
                     'Error validating [surface=-1]. ' \
                     'Validation function [is_multiple_of_100] raised ' \
                     'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1].'

    # (6) custom error types with templating
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be > {minimum}, found {var_value}'

    min_value = 0
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, x > min_value, error_type=InvalidSurface, minimum=min_value)
    e = exc_info.value
    assert str(e) == "Surface should be > 0, found -1. " \
                     "Error validating [surface=-1]: validation function [x > 0] returned [False]."


def test_readme_index_usage_composition():
    """ Tests that the examples provided in the index page under Usage examples/Composition are correct """

    from valid8 import assert_valid, is_multiple_of
    from mini_lambda import x

    surf = -1

    # (7) composition of several base validation functions
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, (x >= 0) & (x < 10000), is_multiple_of(100))
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "Validation function [and((x >= 0) & (x < 10000), is_multiple_of_100)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [-1]. " \
                     "Successes: [] / Failures: {'(x >= 0) & (x < 10000)': 'False', " \
                     "'is_multiple_of_100': 'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1]'}."

    # (8) ... with a global custom error type. Oh by the way this supports templating
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be between {min_s} and {max_s} and be a multiple of {mul_s}, found {var_value}'

    min_surface, mul_surface, max_surface = 0, 100, 10000
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, (x >= min_surface) & (x < max_surface), is_multiple_of(mul_surface),
                     error_type=InvalidSurface, min_s=min_surface, mul_s=mul_surface, max_s=max_surface)
    e = exc_info.value
    assert str(e) == "Surface should be between 0 and 10000 and be a multiple of 100, found -1. " \
                     "Error validating [surface=-1]. " \
                     "Validation function [and((x >= 0) & (x < 10000), is_multiple_of_100)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [-1]. " \
                     "Successes: [] / Failures: {" \
                     "'(x >= 0) & (x < 10000)': 'False', " \
                     "'is_multiple_of_100': 'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1]'}."

    # (9) ... and possible user-friendly intermediate failure messages
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf,
                     ((x >= 0) & (x < 10000), 'Surface should be between 0 and 10000'),
                     (is_multiple_of(100), 'Surface should be a multiple of 100'))
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "Validation function [and((x >= 0) & (x < 10000), is_multiple_of_100)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation. " \
                     "Successes: [] / Failures: {" \
                     "'(x >= 0) & (x < 10000)': 'WrappingFailure: Surface should be between 0 and 10000. " \
                     "Function [(x >= 0) & (x < 10000)] returned [False] for value [-1].', " \
                     "'is_multiple_of_100': 'WrappingFailure: Surface should be a multiple of 100. " \
                     "Function [is_multiple_of_100] raised [IsNotMultipleOf: Value should be a multiple of 100. " \
                     "Wrong value: [-1]].'}."

    # *********** other even more complex tests ***********

    # + unique applicative error type
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf,
                     failure_raiser((x >= min_surface) & (x < max_surface),
                                    help_msg='Surface should be between {min_val} and {max_val}',
                                    min_val=min_surface, max_val=max_surface),
                     (is_multiple_of(100), 'Surface should be a multiple of 100, found {wrong_value}'),
                     error_type=InvalidSurface, min_s=min_surface, mul_s=mul_surface, max_s=max_surface)
    e = exc_info.value
    assert str(e) == "Surface should be between 0 and 10000 and be a multiple of 100, found -1. " \
                     "Error validating [surface=-1]. " \
                     "Validation function [and((x >= 0) & (x < 10000), is_multiple_of_100)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation. " \
                     "Successes: [] / Failures: {" \
                     "'(x >= 0) & (x < 10000)': 'WrappingFailure: Surface should be between 0 and 10000. " \
                     "Function [(x >= 0) & (x < 10000)] returned [False] for value [-1].', " \
                     "'is_multiple_of_100': 'WrappingFailure: Surface should be a multiple of 100, found -1. " \
                     "Function [is_multiple_of_100] raised [IsNotMultipleOf: Value should be a multiple of 100. " \
                     "Wrong value: [-1]].'}."
