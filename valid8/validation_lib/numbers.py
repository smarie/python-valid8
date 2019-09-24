try:  # python 3.5+
    # noinspection PyUnresolvedReferences
    from numbers import Integral
except ImportError:
    pass

from valid8.base import ValidationFailure


class IsNotEven(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by is_even """
    help_msg = 'Value should be even'


def is_even(x  # type: Integral
            ):
    """ Validates that x is even (`x % 2 == 0`) """
    if x % 2 == 0:
        return True
    else:
        raise IsNotEven(wrong_value=x)


class IsNotOdd(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by is_odd """
    help_msg = 'Value should be odd'


def is_odd(x  # type: Integral
           ):
    """ Validates that x is odd (`x % 2 != 0`) """
    if x % 2 != 0:
        return True
    else:
        raise IsNotOdd(wrong_value=x)


class IsNotMultipleOf(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by is_multiple_of """
    help_msg = 'Value should be a multiple of {ref}'


def is_multiple_of(ref):
    """ Validates that x is a multiple of the reference (`x % ref == 0`) """
    def is_multiple_of_ref(x):
        if x % ref == 0:
            return True
        else:
            raise IsNotMultipleOf(wrong_value=x, ref=ref)

    is_multiple_of_ref.__name__ = 'is_multiple_of_%s' % ref
    return is_multiple_of_ref
