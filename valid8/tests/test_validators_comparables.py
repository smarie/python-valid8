import pytest

from valid8 import gt, gts, lt, lts, between, BasicFailure


def test_gt():
    """ tests that the gt() function works """
    assert gt(1)(1)
    with pytest.raises(BasicFailure):
        gt(-1)(-1.1)


def test_gts():
    """ tests that the gts() function works """
    with pytest.raises(BasicFailure):
        gts(1)(1)
    assert gts(-1)(-0.9)


def test_lt():
    """ tests that the lt() function works """
    assert lt(1)(1)
    with pytest.raises(BasicFailure):
        lt(-1)(-0.9)


def test_lts():
    """ tests that the lts() function works """
    with pytest.raises(BasicFailure):
        lts(1)(1)
    assert lts(-1)(-1.1)


def test_between():
    """ tests that the between() function works """
    assert between(0, 1)(0)
    assert between(0, 1)(1)

    with pytest.raises(BasicFailure):
        between(0, 1)(-0.1)

    with pytest.raises(BasicFailure):
        between(0, 1)(1.1)
