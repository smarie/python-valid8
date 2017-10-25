from numbers import Integral

from valid8.core import ValidationError


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
            raise ValidationError('is_mod: x % ' + str(ref) + ' == 0 does not hold for x=' + str(x))
    return is_mod
