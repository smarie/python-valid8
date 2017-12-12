import pytest

from core import _create_main_validation_function


def test_empty_validators_list():
    """ Validates that an empty list of validators leads to a ValueError """

    with pytest.raises(ValueError):
        _create_main_validation_function([], allow_not_none=True)
