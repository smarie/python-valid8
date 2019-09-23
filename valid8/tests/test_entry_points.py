from valid8 import ValidationError


def test_validate_create_manually():
    """ Tests that ValidationError.create_without_validator works """

    class CustomError(ValidationError):
        help_msg = "Something is not valid in {var_value}"

    foo = 1
    e = CustomError.create_without_validator(validation_function_name='custom_validation_function', var_name='foo',
                                             var_value=foo)
    assert str(e) == "Something is not valid in 1. " \
                     "Error validating [foo=1] with function [custom_validation_function] (no failure details available)"
