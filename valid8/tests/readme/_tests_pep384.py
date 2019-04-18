from numbers import Real, Integral

import pytest
from typing import Optional

from valid8 import Boolean, InputValidationError


def create_for_test_unused_pytypes():
    def build_house(name: str,
                    surface: Real,
                    nb_floors: Optional[Integral] = 1,
                    with_windows: Boolean = False
                    ):
        print('you did it !')
    return build_house


def test_readme_combining_enforce():
    # Imports - for type validation
    from numbers import Integral
    from typing import Tuple, Optional
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # means that subclasses of required types are valid too
    from enforce.exceptions import RuntimeTypeError

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
    def build_house(name: str,
                    surface: Optional[Integral] = None
                    ) -> Tuple[str, Optional[Integral]]:
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
