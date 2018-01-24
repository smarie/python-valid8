import pytest

from mini_lambda import make_lambda_friendly_method, _, x
from valid8 import on_each_, is_even, maxlen, on_all_, is_subset, is_superset, is_in, Failure, minlen, TooShort, \
    minlens, TooLong, length_between, maxlens, LengthNotInRange, lt, contains, has_length, WrongLength


def test_is_in():
    """ Checks that is_in works """

    is_in({'+', '-'})('+')
    with pytest.raises(Failure):
        is_in({'+', '-'})('*')


def test_contains():
    """ Checks that contains works """
    contains('+')(['+', '-'])
    with pytest.raises(Failure):
        contains('*')(['+', '-'])


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


def test_haslen():
    """ tests that the has_length() function works """
    assert has_length(1)(['a'])
    with pytest.raises(WrongLength):
        has_length(1)([])


def test_minlen():
    """ tests that the minlen() function works """
    assert minlen(1)(['a'])
    with pytest.raises(TooShort):
        minlen(1)([])


def test_minlens():
    """ tests that the minlens() function works """
    with pytest.raises(TooShort):
        minlens(1)(['a'])
    assert minlens(1)(['a', 'a'])


def test_maxlen():
    """ tests that the maxlen() function works """
    assert maxlen(1)(['a'])
    with pytest.raises(TooLong):
        maxlen(1)(['a', 'a'])


def test_maxlens():
    """ tests that the maxlens() function works """
    with pytest.raises(TooLong):
        maxlens(1)(['a'])
    assert maxlens(3)(['a', 'a'])


def test_length_between():
    """ tests that the length_between() function works """
    assert length_between(0, 1)([])
    assert length_between(0, 1)(['a'])

    with pytest.raises(LengthNotInRange):
        length_between(0, 1)(['a', 'a'])

    with pytest.raises(LengthNotInRange):
        length_between(0, 1, open_left=True)([])
