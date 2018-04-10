import pytest

from valid8 import gt, gts, lt, lts, between, NotInRange, TooSmall, TooBig


def test_gt():
    """ tests that the gt() function works """
    assert gt(1)(1)
    with pytest.raises(TooSmall):
        gt(-1)(-1.1)


def test_gts():
    """ tests that the gts() function works """
    with pytest.raises(TooSmall):
        gts(1)(1)
    assert gts(-1)(-0.9)


def test_lt():
    """ tests that the lt() function works """
    assert lt(1)(1)
    with pytest.raises(TooBig):
        lt(-1)(-0.9)


def test_lts():
    """ tests that the lts() function works """
    with pytest.raises(TooBig):
        lts(1)(1)
    assert lts(-1)(-1.1)


def test_between():
    """ tests that the between() function works """
    assert between(0, 1)(0)
    assert between(0, 1)(1)

    with pytest.raises(NotInRange):
        between(0, 1)(-0.1)

    with pytest.raises(NotInRange):
        between(0, 1)(1.1)


def test_numpy_nan():
    """ Test that a numpy nan is correctly handled """

    from valid8 import validate, gt, TooSmall, lt, TooBig
    import numpy as np

    with pytest.raises(TooSmall) as exc_info:
        gt(5.1)(np.nan)

    with pytest.raises(TooBig) as exc_info:
        lt(5.1)(np.nan)

    with pytest.raises(NotInRange) as exc_info:
        between(5.1, 5.2)(np.nan)
