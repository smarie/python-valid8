from numbers import Integral

from valid8.core import Failure


def is_even(x: Integral):
    """ Validates that x is even (`x % 2 == 0`) """
    return x % 2 == 0


def is_odd(x: Integral):
    """ Validates that x is odd (`x % 2 != 0`) """
    return x % 2 != 0


def is_mod(ref):
    """ Validates that x is a multiple of the reference (`x % ref == 0`) """
    def is_mod(x):
        if x % ref == 0:
            return True
        else:
            raise Failure('x % {ref} == 0 does not hold for x={val}'.format(ref=ref, val=x))

    is_mod.__name__ = 'is_mod_{}'.format(ref)
    return is_mod
