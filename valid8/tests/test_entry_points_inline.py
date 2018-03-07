import pytest
from valid8 import ValidationError


def test_validate_():
    """ Tests the validate function """

    from valid8 import validate

    # nominal
    surf = 2
    validate('surface', surf, instance_of=int, min_value=0)

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
        validate('surface', surf, instance_of=int, min_value=0)
    e = exc_info.value
    assert str(e) == "Error validating [surface=1j]. " \
                     "HasWrongType: Value should be an instance of <class 'int'>. Wrong value: [1j]."


def test_readme_usage_validate__customization():
    """ Tests the various customization options for validate """

    from valid8 import validate
    from math import isfinite

    surf = 1j

    # (A) custom error message (exception is still a ValidationError)
    with pytest.raises(ValidationError) as exc_info:
        validate('surface', surf, instance_of=int, min_value=0,
                 help_msg="Surface should be a positive integer")
    e = exc_info.value
    assert str(e) == "Surface should be a positive integer. Error validating [surface=1j]. " \
                     "HasWrongType: Value should be an instance of <class 'int'>. Wrong value: [1j]."

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
                     "HasWrongType: Value should be an instance of <class 'int'>. Wrong value: [1j]."


def test_wrap_valid():
    """ Tests the validation context manager """

    from valid8 import wrap_valid
    from math import isfinite

    # nominal
    surf = 2
    with wrap_valid('surface', surf) as v:
        v.alid = surf > 0 and isfinite(surf)

    # wrong value (no inner exception)
    surf = -1
    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e) == "Error validating [surface=-1]: " \
                     "validation function [v.alid = surf > 0 and isfinite(surf)] returned [False]."

    # wrong type (inner exception)
    with pytest.raises(ValidationError) as exc_info:
        surf = 1j
        with wrap_valid('surface', surf) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e) == "Error validating [surface=1j]. " \
                     "Validation function [v.alid = surf > 0 and isfinite(surf)] raised " \
                     "TypeError: '>' not supported between instances of 'complex' and 'int'."


def test_readme_usage_wrap_valid_customization():

    from valid8 import wrap_valid
    from math import isfinite

    surf = 1j

    # (A) custom error message (exception is still a ValidationError)
    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf, help_msg="Surface should be a finite positive integer") as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert str(e).startswith("Surface should be a finite positive integer. Error validating [surface=1j]. " \
                             "Validation function [v.alid = surf > 0 and isfinite(surf)] raised " \
                             "TypeError:")

    # (B) custom error types (recommended to provide unique applicative errors)
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be a positive integer'

    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf, error_type=InvalidSurface) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)

    # (C) custom error types with templating
    class InvalidSurface(ValidationError):
        help_msg = 'Surface should be > {minimum}, found {var_value}'

    with pytest.raises(ValidationError) as exc_info:
        with wrap_valid('surface', surf, error_type=InvalidSurface, minimum=0) as v:
            v.alid = surf > 0 and isfinite(surf)
    e = exc_info.value
    assert isinstance(e, InvalidSurface)
    assert str(e).startswith("Surface should be > 0, found 1j. Error validating [surface=1j]. " \
                             "Validation function [v.alid = surf > 0 and isfinite(surf)] raised " \
                             "TypeError:")


def test_validate_tracebacks():
    """ Tests that the traceback is reduced for instance_of checks """

    from valid8 import validate
    x = "hello"

    # cause is none for HasWrongType
    with pytest.raises(ValidationError) as exc_info:
        validate('x', x, instance_of=int)

    e = exc_info.value
    assert e.__cause__ is None

    # cause is not none otherwise
    with pytest.raises(ValidationError) as exc_info:
        validate('x', x, equals=2)

    e = exc_info.value
    assert e.__cause__ is not None
