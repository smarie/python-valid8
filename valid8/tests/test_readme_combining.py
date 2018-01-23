import pytest
from enforce.exceptions import RuntimeTypeError
from pytypes import InputTypeError

from valid8 import ValidationError, InputValidationError


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
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000.'

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
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000.'

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
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000.'

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
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000.'

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
    from valid8 import validate_io, minlens, gt

    @typechecked
    @validate_io(name=minlens(0),
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
        build_house('test', -1, 2)  # Value validation: @validate_io raises a Failure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value validation: @validate_io raises a Failure
