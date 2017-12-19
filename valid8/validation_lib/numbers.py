from numbers import Integral

from valid8.base import Failure


class IsNotEven(Failure):
    help_msg = 'Value should be even'


def is_even(x: Integral):
    """ Validates that x is even (`x % 2 == 0`) """
    if x % 2 == 0:
        return True
    else:
        raise IsNotEven(wrong_value=x)


class IsNotOdd(Failure):
    help_msg = 'Value should be odd'


def is_odd(x: Integral):
    """ Validates that x is odd (`x % 2 != 0`) """
    if x % 2 != 0:
        return True
    else:
        raise IsNotOdd(wrong_value=x)


class IsNotMultipleOf(Failure):
    help_msg = 'Value should be a multiple of {ref}'


def is_multiple_of(ref):
    """ Validates that x is a multiple of the reference (`x % ref == 0`) """
    def is_multiple_of_ref(x):
        if x % ref == 0:
            return True
        else:
            raise IsNotMultipleOf(wrong_value=x, ref=ref)
            # raise Failure('x % {ref} == 0 does not hold for x={val}'.format(ref=ref, val=x))

    is_multiple_of_ref.__name__ = 'is_multiple_of_{}'.format(ref)
    return is_multiple_of_ref
