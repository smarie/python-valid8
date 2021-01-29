import pytest

from valid8 import ValidationError, validate


def test_err_msg_formatting():
    """Test for https://github.com/smarie/python-valid8/issues/58"""

    class CustomError(ValidationError):
        help_msg = "{a}='{b}': hello"

    with pytest.raises(CustomError) as err:
        validate('dummy', False, equals=True, error_type=CustomError, a=0, b=1)

    assert str(err.value) == "0='1': hello. Error validating [dummy=False]. " \
                             "NotEqual: x == True does not hold for x=False. " \
                             "Wrong value: False."
