import pytest
from enforce.exceptions import RuntimeTypeError
from pytypes import InputTypeError

from valid8 import InputValidationError, ValidationError, failure_raiser


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
                     'IsNotMultipleOf: Value should be a multiple of 100. Wrong value: [-1].'

    # (2) native mini_lambda support to define validation functions
    from mini_lambda import x
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, x > 0)
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]: validation function [x > 0] returned [False].'


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
    assert str(e) == 'Error validating [surface=None]. ValueIsNone: The value must be non-None. Wrong value: [None].'

    # *** (4) TEST: custom Failure (not ValidationError) message. Does it have any interest ? ***
    with pytest.raises(ValidationError) as exc_info:
        assert_valid('surface', surf, (is_multiple_of(100), 'Surface should be a multiple of 100'))
    e = exc_info.value
    assert str(e) == 'Error validating [surface=-1]. ' \
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
                     "AtLeastOneFailed: At least one validation function failed validation. " \
                     "Successes: [] / Failures: {" \
                     "'(x >= 0) & (x < 10000)': 'WrappingFailure: Surface should be between 0 and 10000. " \
                     "Function [(x >= 0) & (x < 10000)] returned [False] for value [-1].', " \
                     "'is_multiple_of_100': 'WrappingFailure: Surface should be a multiple of 100, found -1. " \
                     "Function [is_multiple_of_100] raised [IsNotMultipleOf: Value should be a multiple of 100. " \
                     "Wrong value: [-1]].'}."


def test_readme_index_usage_function():
    """ Tests that the examples provided in the index page under Usage examples/Function are correct """

    from mini_lambda import s, x, l, Len
    from valid8 import validate_arg, validate_out, instance_of, is_multiple_of

    class InvalidNameError(InputValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(InputValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    @validate_arg('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
    @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100), error_type=InvalidSurfaceError)
    @validate_out(instance_of(tuple), Len(l) == 2)
    def build_house(name, surface=None):
        print('Building house... DONE !')
        return name, surface

    build_house('sweet home', 200)
    build_house('sweet home')

    with pytest.raises(InvalidNameError):
        build_house('', 100)  # name is invalid

    with pytest.raises(InvalidSurfaceError):
        build_house('sweet home', 10000)  # surface is invalid


def test_readme_index_usage_class_fields():
    """ Tests that the examples provided in the index page under Usage examples/class fields are correct"""

    from valid8 import validate_field, instance_of, is_multiple_of, ClassFieldValidationError
    from mini_lambda import x, s, Len

    class InvalidNameError(ClassFieldValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(ClassFieldValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    @validate_field('name', instance_of(str), Len(s) > 0,
                    error_type=InvalidNameError)
    @validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                    error_type=InvalidSurfaceError)
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

    with pytest.raises(InvalidNameError):
        h = House('')

    h.surface = 100
    with pytest.raises(InvalidSurfaceError):
        h.surface = 10000


def test_readme_index_combining_enforce():
    """ Tests that the examples provided in the index page under Combining/Enforce are correct """

    # Imports - for type validation
    from numbers import Integral
    from typing import Tuple, Optional
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # means that subclasses of required types are valid too

    # Imports - for value validation
    from mini_lambda import s, x, Len
    from valid8 import validate_arg, is_multiple_of

    # Define our 2 applicative error types
    class InvalidNameError(InputValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(InputValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    # Apply type + value validation
    @runtime_validation
    @validate_arg('name', Len(s) > 0, error_type=InvalidNameError)
    @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                  error_type=InvalidSurfaceError)
    def build_house(name: str, surface: Optional[Integral]=None) \
            -> Tuple[str, Optional[Integral]]:
        print('Building house... DONE !')
        return name, surface

    build_house('sweet home', 200)
    build_house('sweet home')

    with pytest.raises(InvalidNameError):
        build_house('', 100)  # InvalidNameError

    with pytest.raises(InvalidSurfaceError):
        build_house('sweet home', 10000)  # InvalidSurfaceError

    with pytest.raises(RuntimeTypeError):
        build_house('test', 100.1)  # RuntimeTypeError


def test_readme_index_combining_autoclass():
    """ Tests that the examples provided in the index page under Combining/autoclass are correct """

    from autoclass import autoclass
    from mini_lambda import s, x, Len
    from valid8 import validate_field, instance_of, is_multiple_of, ClassFieldValidationError

    class InvalidNameError(ClassFieldValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(ClassFieldValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    @validate_field('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
    @validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                    error_type=InvalidSurfaceError)
    @autoclass
    class House:
        def __init__(self, name, surface=None):
            pass

    h = House('sweet home', 200)

    h.surface = None  # Valid (surface is nonable by signature)

    with pytest.raises(InvalidNameError):
        h.name = ''  # InvalidNameError

    with pytest.raises(InvalidSurfaceError):
        h.surface = 10000  # InvalidSurfaceError


def test_readme_index_combining_autoclass_2():
    """ Tests that the examples provided in the index page under Combining/autoclass are correct (2) """

    from autoclass import autoclass
    from mini_lambda import s, x, l, Len
    from valid8 import validate_arg, instance_of, is_multiple_of

    class InvalidNameError(InputValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(InputValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    @autoclass
    class House:

        @validate_arg('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
        @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100), error_type=InvalidSurfaceError)
        def __init__(self, name, surface=None):
            pass

    h = House('sweet home', 200)
    h.surface = None  # Valid

    with pytest.raises(InvalidNameError):
        h.name = ''

    with pytest.raises(InvalidSurfaceError):
        h.surface = 10000


def test_readme_index_combining_attrs():
    """ Tests that the examples provided in the index page under Combining/autoclass are correct """

    import attr
    from mini_lambda import s, x, Len
    from valid8 import validate_field, instance_of, is_multiple_of, ClassFieldValidationError

    class InvalidNameError(ClassFieldValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(ClassFieldValidationError):
        help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

    @validate_field('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
    @validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                    error_type=InvalidSurfaceError)
    @attr.s
    class House:
        name = attr.ib()
        surface = attr.ib(default=None)

    h = House('sweet home')  # Valid (surface is nonable by generated signature)

    h.name = ''       # DOES NOT RAISE InvalidNameError (no setter!)

    with pytest.raises(InvalidNameError):
        House('', 10000)  # InvalidNameError

    with pytest.raises(InvalidSurfaceError):
        House('sweet home', 10000)  # InvalidSurfaceError


def test_unused_pytypes():
    """ Tests that pytypes and valid8 can work together too """

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
