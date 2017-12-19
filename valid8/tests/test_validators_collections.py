import pytest

from mini_lambda import make_lambda_friendly_method, _, x
from valid8 import on_each_, is_even, lt, on_all_, is_subset, is_superset, is_in, Failure


def test_is_in():
    """ Checks that is_in works """

    is_in({'+', '-'})('+')
    with pytest.raises(Failure):
        is_in({'+', '-'})('*')


def test_is_subset_is_superset():
    """ Checks that is_subset and is_superset work """

    a = is_subset({'+', '-'})
    a({'+'})
    with pytest.raises(Failure):
        a({'+', '-', '*'})

    b = is_superset({'+', '-'})
    b({'+', '-', '*'})
    with pytest.raises(Failure):
        b({'+'})

    Is_subset = make_lambda_friendly_method(is_subset)
    Is_superset = make_lambda_friendly_method(is_superset)
    c = _(Is_subset({'+', '-'})(x) & Is_superset({'+', '-'})(x))
    c({'+', '-'})
    with pytest.raises(Failure):
        c({'+', '-', '*'})
    with pytest.raises(Failure):
        c({'+'})


def test_on_all():
    """ Checks that on_all works """

    a = on_all_(is_even, lt(0))
    a((0, -10, -2))
    with pytest.raises(Failure):
        a((0, -10, -1))


def test_on_each():
    """ Checks that on_each works """

    a = on_each_(is_even, lt(0))
    a((0, -1))
    with pytest.raises(Failure):
        a((0, 2))
