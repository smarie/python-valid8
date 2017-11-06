from typing import Tuple

import pytest

from valid8 import validate, ValidationError, on_each_, is_even, lt, on_all_, is_subset, is_superset, is_in


def test_validate_is_in():
    """ Test for the subset and superset validators """

    @validate(a=is_in({'+', '-'}))
    def myfunc(a):
        print('hello')

    # -- check that the validation works
    myfunc('+')
    with pytest.raises(ValidationError):
        myfunc('*')


def test_validate_subset_superset():
    """ Test for the subset and superset validators """

    @validate(a=is_subset({'+', '-'}), b=is_superset({'+', '-'}),
              c=[is_subset({'+', '-'}), is_superset({'+', '-'})])
    def myfunc(a, b, c):
        print('hello')

    # -- check that the validation works
    myfunc({'+'},{'+', '-', '*'}, {'+', '-'})

    with pytest.raises(ValidationError):
        myfunc({'+', '-', '*'}, None, None)

    with pytest.raises(ValidationError):
        myfunc(None, {'+'}, None)

    with pytest.raises(ValidationError):
        myfunc(None, None, {'+', '-', '*'})

    with pytest.raises(ValidationError):
        myfunc(None, None, {'+'})


def test_validate_on_all():
    @validate(a=on_all_(is_even, lt(0)))
    def myfunc(a: Tuple):
        print('hello')

    myfunc((0, -10, -2))

    with pytest.raises(ValidationError):
        myfunc((0, -10, -1))


def test_validate_on_each():
    @validate(a=on_each_(is_even, lt(0)))
    def myfunc(a: Tuple[int, int]):
        print('hello')

    myfunc((0, -1))

    with pytest.raises(ValidationError):
        myfunc((0, 2))