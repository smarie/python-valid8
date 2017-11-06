import pytest
from enforce.exceptions import RuntimeTypeError
from pytypes import InputTypeError

from valid8 import ValidationError


def test_first_example_enforce():
    # for type checking
    from valid8 import Boolean
    from numbers import Real, Integral
    from typing import Optional
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # allow subclasses when validating types

    # for value checking
    from valid8 import validate, minlens, gt

    @runtime_validation
    @validate(name=minlens(0),
              surface=gt(0))
    def build_house(name: str,
                    surface: Real,
                    nb_floors: Optional[Integral] = 1,
                    with_windows: Boolean = False):
        print('you did it !')

    build_house('test', 12, 2)  # validation OK

    with pytest.raises(RuntimeTypeError):
        build_house('test', 12, 2.2)  # Type validation: @runtime_validation raises a InputTypeError

    build_house('test', 12, None)  # Mandatory/Optional validation: Declared 'Optional' with PEP484, no error

    with pytest.raises(ValidationError):
        build_house('test', -1, 2)  # Value validation: @validate raises a ValidationError

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value validation: @validate raises a ValidationError


def test_first_example_pytypes():
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
        build_house('test', -1, 2)  # Value validation: @validate raises a ValidationError

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value validation: @validate raises a ValidationError

def test_custom_validators():
    from valid8 import validate, ValidationError

    def is_mod_3(x):
        """ A simple validator with no parameters """
        return x % 3 == 0

    def is_mod(ref):
        """ A validator generator, with parameters """

        def is_mod_ref(x):
            return x % ref == 0

        return is_mod_ref

    def gt_ex1(x):
        """ A validator raising a custom exception in case of failure """
        if x >= 1:
            return True
        else:
            raise ValidationError('gt_ex1: x >= 1 does not hold for x=' + str(x))

    def gt_assert2(x):
        """(not recommended) relying on assert, only valid in 'debug' mode"""
        assert x >= 2

    @validate(a=[gt_ex1, gt_assert2, is_mod_3],
              b=is_mod(5))
    def myfunc(a, b):
        pass

    # -- check that the validation works
    myfunc(21, 15)  # ok
    with pytest.raises(ValidationError):
        myfunc(4, 21)  # ValidationError: a is not a multiple of 3
    with pytest.raises(ValidationError):
        myfunc(15, 1)  # ValidationError: b is not a multiple of 5
    with pytest.raises(ValidationError):
        myfunc(1, 0)  # AssertionError: a is not >= 2
    with pytest.raises(ValidationError):
        myfunc(0, 0)  # ValidationError: a is not >= 1
