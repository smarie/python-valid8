import pytest

from valid8 import is_even, is_odd, is_multiple_of, IsNotMultipleOf, IsNotOdd, IsNotEven


def test_is_even():
    assert is_even(2)
    with pytest.raises(IsNotEven):
        is_even(-1)


def test_is_odd():
    assert is_odd(-1)
    with pytest.raises(IsNotOdd):
        is_odd(-2)


def test_is_multiple_of():
    assert is_multiple_of(3)(-9)
    with pytest.raises(IsNotMultipleOf):
        is_multiple_of(3)(-10)
