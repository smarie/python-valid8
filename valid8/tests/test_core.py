import pytest

from core import _create_main_validation_function, NonePolicy


def test_empty_validators_list():
    """ Validates that an empty list of validators leads to a ValueError """

    with pytest.raises(ValueError) as exc_info:
        _create_main_validation_function([], none_policy=NonePolicy.VALIDATE)
