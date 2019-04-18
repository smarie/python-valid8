from numbers import Real, Integral
from typing import Tuple
from pytypes import typechecked
from valid8 import validate_arg


def ex1_pep484(value):
    from mini_lambda import x

    @typechecked
    @validate_arg('x', x >= 0)
    def my_function(x: Integral):  # <- type hint in signature
        pass

    my_function(value)


def ex2_pep484(value):
    from mini_lambda import s, Len

    @typechecked
    @validate_arg('s', Len(s) > 0, s.islower())
    def my_function(s: str):  # <- type hint in signature
        pass

    my_function(value)


def ex3_pep484(value):
    from mini_lambda import InputVar, Len

    # we need a mini_lambda variable named 't'
    t = InputVar('t', tuple)

    @typechecked
    @validate_arg('t',  # the first element is a float between 0 and 1
                  (0 <= t[0]) & (t[0] <= 1),
                  # the 2d element is a lowercase string of len 3
                  Len(t[1]) == 3, t[1].islower()
                  )
    def my_function(t: Tuple[Real, str]):
        pass

    my_function(value)


@typechecked
def ex3_is_valid_tuple_pep(t: Tuple[Real, str]):
    """ custom validation function - note the PEP484 type hint above """
    return len(t) == 2 and (0 <= t[0] <= 1) and len(t[1]) == 3 and t[1].islower()


@typechecked
def ex3_check_valid_tuple_pep(t: Tuple[Real, str]):
    """ custom validation function - note the PEP484 type hint above """

    # the first element is a float between 0 and 1
    if not (0 <= t[0] <= 1):
        raise ValueError('first elt should be between 0 and 1,found ' + str(t[0]))

    # the second element is a lowercase string of size 3
    if not (len(t[1]) == 3 and t[1].islower()):
        raise ValueError('second elt should be a lowercase string of length 3,'
                         'found ' + str(t[1]))
