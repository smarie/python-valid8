import pytest

from valid8.composition import _process_validation_function_s, or_, AllValidatorsFailed, xor_, XorTooManySuccess, and_
from valid8 import not_, is_even, gt, AtLeastOneFailed, not_all, is_multiple_of, DidNotFail, Failure, IsNotEven


def test_empty_validators_list():
    """ Validates that an empty list of validators leads to a ValueError """

    with pytest.raises(ValueError) as exc_info:
        _process_validation_function_s([])


def test_list_implicit_and():
    """ Asserts that a list of validators leads to a 'and_' and behaves correctly """
    main = _process_validation_function_s([is_even, gt(1)])

    assert main(2) is True
    with pytest.raises(AtLeastOneFailed):
        main(3)


def test_not_not_all():
    """ Test for the not_ and not_all validators """

    def gtcustom(x):
        assert x < 10

    a=not_(is_even)
    b=not_all(is_even, is_multiple_of(3))
    c=not_(gtcustom, catch_all=True)
    d=not_(gtcustom)

    assert a(11) is True
    assert b(11) is True
    assert c(11) is True  # 11 leads to an AssertionError (not a Failure), but the not_ handles the exception correctly

    with pytest.raises(DidNotFail) as exc_info:
        a(84)  # 84 is invalid (not even)
    e = exc_info.value
    assert str(e) == 'is_even validated value 84 with success, therefore the not() is a failure. ' \
                     'Function [is_even] returned [True] for value [84].'

    with pytest.raises(DidNotFail):
        b(6)   # 6 is invalid (is even and it is a multiple of 3)

    with pytest.raises(DidNotFail):
        c(9)   # 9 is invalid (is less than 10)

    with pytest.raises(DidNotFail):
        d(9)   # 9 is invalid (is less than 10)

    with pytest.raises(AssertionError):
        d(11)  # 11 is a *valid* value, but the not_ operator does not catch the exception so we get the error


def test_validate_or():
    """ Test for the or_ validator, also in combination with not_"""

    # empty list error
    with pytest.raises(ValueError):
        or_([])

    # single element simplification
    assert or_(is_even) == is_even

    # lists
    a=or_(is_even, is_multiple_of(3))
    b=not_(or_(is_even, is_multiple_of(3)))

    # -- check that the validation works
    assert a(9) is True  # a is not even but is a multiple of 3 > ok
    assert a(4) is True  # a is even but is not a multiple of 3 > ok
    assert b(7) is True  # b is not even AND not a multiple of 3 > ok

    with pytest.raises(AllValidatorsFailed):
        a(7)  # 7 is odd and not multiple of 3

    with pytest.raises(DidNotFail):
        b(3)  # 3 is odd but it is a multiple of 3


def test_validate_xor():
    """ Test for the xor_ validator """

    # empty list error
    with pytest.raises(ValueError):
        xor_([])

    # single element simplification
    assert xor_(is_even) == is_even

    # lists
    a=xor_(is_even, is_multiple_of(3))

    # -- check that the validation works
    assert a(9) is True  # a is not even but is a multiple of 3 > ok
    assert a(4) is True  # a is even but is not a multiple of 3 > ok

    with pytest.raises(XorTooManySuccess):
        a(6)  # a is both even and a multiple of 3

    with pytest.raises(AllValidatorsFailed):
        a(7)  # a is neither even nor a multiple of 3


def test_validate_and():
    """ Simple test of the @validate_io annotation, with built-in validators is_even and gt(1) """

    # empty list error
    with pytest.raises(ValueError):
        and_([])

    # single element simplification
    assert and_([is_even]) == is_even

    # list with nested list (implicit and_)
    a=and_(is_even, gt(1))

    # -- check that the validation works
    assert a(84) is True
    with pytest.raises(AtLeastOneFailed):
        # a is not even
        a(1)
    with pytest.raises(AtLeastOneFailed):
        # a is not >= 1
        a(0)

    # list with nested list (implicit and_)
    a = and_([is_even, gt(1)])

    # -- check that the validation works
    assert a(84) is True
    with pytest.raises(AtLeastOneFailed):
        # a is not even
        a(1)
    with pytest.raises(AtLeastOneFailed):
        # a is not >= 1
        a(0)
