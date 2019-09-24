import sys
from collections import OrderedDict

import pytest

from valid8 import validate, ValidationError, ValidationFailure
from valid8.validation_lib import is_even


@pytest.mark.skipif(sys.version_info < (3, 0), reason="math.inf is not available in python 2")
def test_syntax():
    from math import inf, isfinite

    x = inf
    with pytest.raises(ValidationError) as exc_info:
        validate('x', x, custom=(isfinite, 'x is not finite'))

    assert str(exc_info.value) == "Error validating [x=inf]. " \
                                  "InvalidValue: x is not finite. " \
                                  "Function [isfinite] returned [False] for value inf."


@pytest.mark.skipif(sys.version_info < (3, 0), reason="math.inf is not available in python 2")
def test_syntax2():
    from math import inf, isfinite

    class NotFinite(ValidationFailure):
        help_msg = "x is not finite"

    x = inf
    with pytest.raises(ValidationError) as exc_info:
        validate('x', x, custom=(isfinite, NotFinite))

    assert str(exc_info.value) == "Error validating [x=inf]. " \
                                  "NotFinite: x is not finite. " \
                                  "Function [isfinite] returned [False] for value inf."


@pytest.mark.skipif(sys.version_info < (3, 0), reason="math.isfinite is not available in python 2")
def test_syntax_collection():
    from math import isfinite
    from mini_lambda import i

    class NotFinite(ValidationFailure):
        help_msg = "x is not finite"

    x = -1
    with pytest.raises(ValidationError) as exc_info:
        validate('x', x, custom=[(isfinite, NotFinite),
                                 is_even,
                                 (i > 0, 'x should be strictly positive')])

    assert str(exc_info.value) == "Error validating [x=-1]. " \
                                  "At least one validation function failed for value " \
                                  "-1. Successes: ['isfinite'] / Failures: " \
                                  "{'is_even': 'IsNotEven: Value should be even.', " \
                                  "'i > 0': 'InvalidValue: x should be strictly positive. Returned False.'}."


@pytest.mark.skipif(sys.version_info < (3, 0), reason="math.isfinite is not available in python 2")
def test_syntax_dict():
    from math import isfinite
    from mini_lambda import i

    class NotFinite(ValidationFailure):
        help_msg = "x is not finite"

    x = 2
    with pytest.raises(ValidationError):
        validate('x', x, custom={'x should be fairly small': i ** 2 < 50,
                                 'x should be a multiple of 3': i % 3 == 0})

    x = -1
    with pytest.raises(ValidationError):
        validate('x', x, custom={'x should be finite': (isfinite, NotFinite),
                                 'x should be even': is_even,
                                 'x should be strictly positive': (i > 0)})

    with pytest.raises(ValidationError) as exc_info:
        # we need an ordered dict for reproducible tests
        validate('x', x, custom=OrderedDict([('x should be finite', (isfinite, NotFinite)),
                                             ('x should be even', is_even),
                                             ('x should be strictly positive', (i > 0))]))

    # NOTE:
    assert str(exc_info.value) == "Error validating [x=-1]. " \
                                  "At least one validation function failed for value " \
                                  "-1. Successes: ['isfinite'] / Failures: " \
                                  "{'is_even': 'InvalidValue: x should be even. IsNotEven: Value should be even.', " \
                                  "'i > 0': 'InvalidValue: x should be strictly positive. Returned False.'}."
