import numpy as np

from mini_lambda import x
from valid8 import validate, validate_arg, and_


def test_numpy_bool_is_ok():
    """ Tests that numpy booleans can be used as success result by validation functions"""

    # a numpy float is not a python float
    np_float = np.float_(1.0)

    # numpy bools are not python bools
    assert np_float > 0 is not True
    assert 'numpy' in "%s" % (np_float > 0).__class__

    # simple checker
    validate('np_float', np_float, min_value=1)

    # more complex checker
    @validate_arg('a', lambda x: x >= 1)
    def foo(a):
        return

    foo(np_float)

    # even more complex checker
    @validate_arg('a', and_(x > 0, lambda x: x >= 1))
    def foo(a):
        return

    foo(np_float)
