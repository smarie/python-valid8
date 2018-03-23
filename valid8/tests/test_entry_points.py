from valid8 import ValidationError


def test_validate_create_manually():
    """ Tests that ValidationError.create_manually works """

    class CustomError(ValidationError):
        help_msg = "Something is not valid in {var_value}"

    foo = 1
    e = CustomError.create_manually('custom_validation_function', 'foo', foo)
    assert str(e) == "Something is not valid in 1. " \
                     "Error validating [foo=1]: validation function [custom_validation_function] returned [None]."
