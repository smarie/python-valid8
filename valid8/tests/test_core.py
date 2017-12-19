import pytest

from valid8.composition import _process_validation_function_s


def test_empty_validators_list():
    """ Validates that an empty list of validators leads to a ValueError """

    with pytest.raises(ValueError) as exc_info:
        _process_validation_function_s([])
