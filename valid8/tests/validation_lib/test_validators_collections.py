import pytest

from mini_lambda import make_lambda_friendly_method, _, x
from valid8 import ValidationFailure
from valid8.validation_lib import on_each_, is_even, maxlen, on_all_, is_subset, is_superset, is_in, minlen, TooShort, \
    TooLong, length_between, LengthNotInRange, lt, contains, has_length, WrongLength, empty, NotEmpty, non_empty, Empty


def test_is_in():
    """ Checks that is_in works """

    is_in({'+', '-'})('+')
    with pytest.raises(ValidationFailure):
        is_in({'+', '-'})('*')

    # also test non-set iterable types
    is_in(('+', '-'))('+')


def test_contains():
    """ Checks that contains works """
    contains('+')(['+', '-'])
    with pytest.raises(ValidationFailure):
        contains('*')(['+', '-'])


def test_is_subset_is_superset():
    """ Checks that is_subset and is_superset work """

    a = is_subset({'+', '-'})
    a({'+'})
    with pytest.raises(ValidationFailure):
        a({'+', '-', '*'})

    b = is_superset({'+', '-'})
    b({'+', '-', '*'})
    with pytest.raises(ValidationFailure):
        b({'+'})

    Is_subset = make_lambda_friendly_method(is_subset)
    Is_superset = make_lambda_friendly_method(is_superset)
    c = _(Is_subset({'+', '-'})(x) & Is_superset({'+', '-'})(x))
    c({'+', '-'})
    with pytest.raises(ValidationFailure):
        c({'+', '-', '*'})
    with pytest.raises(ValidationFailure):
        c({'+'})


def test_on_all():
    """ Checks that on_all works """

    a = on_all_(is_even, lt(0))
    a((0, -10, -2))
    with pytest.raises(ValidationFailure):
        a((0, -10, -1))


def test_on_each():
    """ Checks that on_each works """

    a = on_each_(is_even, lt(0))
    a((0, -1))
    with pytest.raises(ValidationFailure):
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


def test_maxlen():
    """ tests that the maxlen() function works """
    assert maxlen(1)(['a'])
    with pytest.raises(TooLong):
        maxlen(1)(['a', 'a'])


def test_empty():
    """ tests that the empty() function works """
    assert empty([])
    with pytest.raises(NotEmpty):
        empty(['a', 'a'])


def test_nonempty():
    """ tests that the non_empty() function works """
    assert non_empty(['a', 'a'])
    with pytest.raises(Empty):
        non_empty([])


def test_length_between():
    """ tests that the length_between() function works """
    assert length_between(0, 1)([])
    assert length_between(0, 1)(['a'])

    with pytest.raises(LengthNotInRange):
        length_between(0, 1)(['a', 'a'])


def test_numpy_nan_like_lengths():
    """ Test that a strange int length with bad behaviour is correctly handled """

    class NanInt(int):
        """
        An int that behaves like numpy NaN (comparison always returns false)
        """
        def __le__(self, other):
            return False

        def __lt__(self, other):
            return False

        def __gt__(self, other):
            return False

        def __ge__(self, other):
            return False

    nanlength = NanInt()

    class Foo:
        def __len__(self):
            return nanlength

    f = Foo()

    if isinstance(len(f), NanInt):
        # in current version of python this does not happen, but the test is ready for future evolutions
        with pytest.raises(TooShort) as exc_info:
            minlen(0)(f)

        with pytest.raises(TooLong) as exc_info:
            maxlen(10)(f)

        with pytest.raises(LengthNotInRange) as exc_info:
            length_between(0, 10)(f)
