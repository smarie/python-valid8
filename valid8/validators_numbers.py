from numbers import Integral

from valid8.core import BasicFailure


def is_even(x: Integral):
    """ Validates that x is even (`x % 2 == 0`) """
    return x % 2 == 0


def is_odd(x: Integral):
    """ Validates that x is odd (`x % 2 != 0`) """
    return x % 2 != 0


def is_multiple_of(ref):
    """ Validates that x is a multiple of the reference (`x % ref == 0`) """
    def is_multiple_of_ref(x):
        if x % ref == 0:
            return True
        else:
            raise BasicFailure('x % {ref} == 0 does not hold for x={val}'.format(ref=ref, val=x))

    is_multiple_of_ref.__name__ = 'is_multiple_of_{}'.format(ref)
    return is_multiple_of_ref
