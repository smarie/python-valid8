import sys

import pytest
from valid8 import ValidationError, validate, validator

try:
    from math import isfinite
except ImportError:
    def isfinite(x):
        return True


def test_validate_():
    """ Tests the validate function """

    # nominal
    surf = 2
    validate('surface', surf, instance_of=int, min_value=0)
    validate('surface', surf, instance_of=(int, ), min_value=0)
    validate('surface', surf, instance_of=(int, str), min_value=0)

    # error wrong value
    surf = -1
    with pytest.raises(ValidationError) as exc_info:
        validate('surface', surf, instance_of=int, min_value=0)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]. " \
                     "TooSmall: x >= 0 does not hold for x=-1. Wrong value: [-1]."

    # error wrong type
    surf = 1j
    with pytest.raises(ValidationError) as exc_info:
        # note: we use a length-1 tuple on purpose to see if the error msg takes length into account
        validate('surface', surf, instance_of=(int, ), min_value=0)
    e = exc_info.value
    assert str(e) == "Error validating [surface=1j]. " \
                     "HasWrongType: Value should be an instance of %s. Wrong value: [1j]." % repr(int)


def test_readme_usage_validate__customization():
    """ Tests the various customization options for validate """

    surf = 1j

    # (A) custom error message (exception is still a ValidationError)
    with pytest.raises(ValidationError) as exc_info:
        validate('surface', surf, instance_of=int, min_value=0,
                 help_msg="Surface should be a positive integer")
    e = exc_info.value
    assert str(e) == "Surface should be a positive integer. Error validating [surface=1j]. " \
                     "HasWrongType: Value should be an instance of %s. Wrong value: [1j]." % repr(int)

    # (B) custom error types (recommended to provide unique applicative errors)
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be a positive integer'

    with pytest.raises(ValidationError) as exc_info:
        validate('surface', surf, instance_of=int, min_value=0, error_type=InvalidSurface)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)

    # (C) custom error types with templating
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be > {minimum}, found {var_value}'

    with pytest.raises(ValidationError) as exc_info:
        validate('surface', surf, instance_of=int, min_value=0,
                 error_type=InvalidSurface, minimum=0)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)
    assert str(e) == "Surface should be > 0, found 1j. Error validating [surface=1j]. " \
                     "HasWrongType: Value should be an instance of %s. Wrong value: [1j]." % repr(int)


def test_validator_context_manager():
    """ Tests the validation context manager """

    # nominal
    surf = 2
    with validator('surface', surf) as v:
        v.alid = surf > 0 and isfinite(surf)

    # wrong value (no inner exception)
    surf = -1
    with pytest.raises(ValidationError) as exc_info:
        with validator('surface', surf) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]: " \
                     "validation function [v.alid = surf > 0 and isfinite(surf)] returned [False]."

    # wrong type (inner exception)
    with pytest.raises(ValidationError) as exc_info:
        surf = 1j
        with validator('surface', surf) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    with pytest.raises(TypeError) as typ_err_info:
        1j > 0
    t = typ_err_info.value
    assert str(e) == "Error validating [surface=1j]. " \
                     "Validation function [v.alid = surf > 0 and isfinite(surf)] raised %s: %s." \
                     "" % (t.__class__.__name__, t)


def test_readme_usage_validator_customization():

    surf = 1j

    # (A) custom error message (exception is still a ValidationError)
    with pytest.raises(ValidationError) as exc_info:
        with validator('surface', surf, help_msg="Surface should be a finite positive integer") as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e).startswith("Surface should be a finite positive integer. Error validating [surface=1j]. " \
                             "Validation function [v.alid = surf > 0 and isfinite(surf)] raised " \
                             "TypeError:")

    # (B) custom error types (recommended to provide unique applicative errors)
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be a positive integer'

    with pytest.raises(ValidationError) as exc_info:
        with validator('surface', surf, error_type=InvalidSurface) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)

    # (C) custom error types with templating
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be > {minimum}, found {var_value}'

    with pytest.raises(ValidationError) as exc_info:
        with validator('surface', surf, error_type=InvalidSurface, minimum=0) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)
    assert str(e).startswith("Surface should be > 0, found 1j. Error validating [surface=1j]. " \
                             "Validation function [v.alid = surf > 0 and isfinite(surf)] raised " \
                             "TypeError:")


def test_validate_tracebacks():
    """ Tests that the traceback is reduced for all validate() checks """

    x = "hello"

    # cause is none for HasWrongType
    with pytest.raises(ValidationError) as exc_info:
        validate('x', x, instance_of=int)

    e = exc_info.value
    assert e.__cause__ is None

    # cause is none for all others
    with pytest.raises(ValidationError) as exc_info:
        validate('x', x, equals=2)

    e = exc_info.value
    assert e.__cause__ is None


def test_typos_in_kwargs():
    """ """

    a = 3
    with pytest.raises(ValueError):
        validate('a', a, minvalue=5.1, max_value=5.2)


def test_validate_auto_disable_display():
    """ Tests that objects that have a too big string representation do not get added in the error message """

    # TODO test with a pandas object... one day, when we know how to install pandas in travis :)

    class Foo:
        def __str__(self):
            return "x" * 101

    o = Foo()

    with pytest.raises(ValidationError) as exc_info:
        validate('o', o, equals=2)

    e = exc_info.value
    assert str(e) == "Error validating [o]. NotEqual: x == 2 does not hold for x=(too big for display). " \
                     "(Actual value is too big to be printed in this message)."


def test_numpy_nan():
    """ Test that a numpy nan is correctly handled """

    import numpy as np

    with pytest.raises(ValidationError) as exc_info:
        validate('np.nan', np.nan, min_value=5.1, max_value=5.2)


def test_numpy_nan_like_lengths():
    """ Test that a strange int length with bad behaviour is correctly handled """

    # Actually the test below shows that in current versions of python it is not possible to create a len

    class NanInt(int):
        """
        An int that behaves like numpy NaN (comparison always returns false)
        """

        def __le__(self, other):
            return False

        def __lt__(self, other):
            return False

        def __gt__(self, other):
            return False

        def __ge__(self, other):
            return False

    nanlength = NanInt()

    class Foo:
        def __len__(self):
            return nanlength

    if isinstance(len(Foo()), NanInt):
        # in current version of python this does not happen, but the test is ready for future evolutions
        with pytest.raises(ValidationError) as exc_info:
            validate('Foo()', Foo(), min_len=0, max_len=10)


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints not supported in python 2")
def test_function_setter_name_in_valid8_error_message():
    """ Tests that the correct function name appears in the valid8 error message """

    from ._test_pep484 import test_function_setter_name_in_valid8_error_message
    test_function_setter_name_in_valid8_error_message()


def test_enum_isinstance():
    """Tests that enum can be used in validate/instance_of"""
    from enum import Enum

    class MyEnum(Enum):
        a = 1
        b = 2

    validate('a', MyEnum.a, instance_of=MyEnum)
