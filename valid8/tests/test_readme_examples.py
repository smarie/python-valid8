from numbers import Integral, Real

import pytest

from valid8 import ValidationError


def test_readme_examples_4():
    """ Tests that the example 4 provided in the documentation works (list of custom tuples) """

    l = [(1, 'ras'), (0.2, 'abc')]

    # ---- inline 1
    from valid8 import validate

    # first validate the main type
    validate('l', l, instance_of=list)

    for i, v in enumerate(l):
        # each item is a tuple of size 2
        validate('l[{}]'.format(i), l[i], instance_of=tuple, length=2)
        # the first element is a float between 0 and 1
        validate('l[{}][0]'.format(i), l[i][0], instance_of=Real, min_value=0, max_value=1)
        # the second element is a lowercase string of size 3
        validate('l[{}][1]'.format(i), l[i][1], instance_of=str, length=3, equals=l[i][1].lower())

    # ---- inline 2
    from valid8 import validator, instance_of

    l = [(1, 'ras'), (0.2, 'abc')]

    # all at once
    with validator('l', l, instance_of=list) as v:
        v.alid = all(
                    # each item is a tuple of size 2
                    instance_of(item, tuple) and len(item) == 2
                    # the first element is a float between 0 and 1
                    and instance_of(item[0], Real) and (0 <= item[0] <= 1)
                    # the second element is a lowercase string of size 3
                    and instance_of(item[1], str) and len(item[1]) == 3 and item[1].islower()
                 for item in l)

    # custom validation function
    def check_valid_tuple(tup):
        """ custom validation function - here in 'failure raiser' style (returning nothing) """

        # each item is a tuple of size 2
        if not isinstance(tup, tuple):
            raise TypeError('item should be a tuple')
        if len(tup) != 2:
            raise ValueError('tuple length should be 2')

        # the first element is a float between 0 and 1
        if not isinstance(tup[0], Real):
            raise TypeError('first element should be a Real')
        if not (0 <= tup[0] <= 1):
            raise ValueError('first element should be between 0 and 1')

        # the second element is a lowercase string of size 3
        if not isinstance(tup[1], str):
            raise TypeError('second element should be a string')
        if not (len(tup[1]) == 3 and tup[1].islower()):
            raise ValueError('second element should be a lowercase string of length 3')

    from valid8 import validate, validation

    # first validate the main type
    validate('l', l, instance_of=list)

    # then validate (and use) the contents
    for i, v in enumerate(l):
        # each item is a valid tuple
        with validation('l[{}]'.format(i), l[i]):
            check_valid_tuple(l[i])

        # here you can actually USE the current item


    # ---- function input
    from valid8 import validate_arg, instance_of, on_all_, on_each_, has_length, and_, between

    @validate_arg('l', instance_of(list), on_all_(
                  instance_of(tuple), has_length(2),  # each item is a tuple of size 2
                  on_each_(
                      and_(instance_of(Real), between(0, 1)),  # the first element is a float between 0 and 1
                      and_(instance_of(str), has_length(3)),  # the 2d element is a string of len 3 BUT we cannot check lowercase
                  )
    ))
    def my_function(l):
        pass

    l = [(1, 'ras'), (0.2, 'aBc')]  # we cannot check lowercase
    my_function(l)

    # much better:
    from valid8 import validate_arg, instance_of, on_all_, HasWrongType, WrongLength, NotInRange, Failure

    def is_valid_tuple(t):
        """ Custom validation function. We could also provide a callable """

        # (a) each item is a tuple of size 2
        # --you can reuse an entire method from the built-in lib when it supports direct calling mode
        instance_of(t, tuple)
        # --otherwise you can reuse a failure class, there are many
        if len(t) != 2: raise WrongLength(t, ref_length=2)

        # (b) the first element is a float between 0 and 1
        if not isinstance(t[0], Real): raise HasWrongType(t[0], Real)
        if not (0 <= t[0] <= 1): raise NotInRange(t[0], min_value=0, max_value=1)

        # (c) the second element is a lowercase string of size 3
        instance_of(t[1], str)
        if len(t[1]) != 3: raise WrongLength(t[1], ref_length=3)
        # -- finally you can write custom Failure types
        if not t[1].islower():
            raise NotLowerCase(t[1])

    class NotLowerCase(Failure, ValueError):
        """ Example custom exception class used in custom validation function. `Failure` base class provides some
        mechanisms to easily build the help message (same mechanisms than ValidationError)"""
        help_msg = "Value is not a lowercase string: {wrong_value}"

    @validate_arg('l', instance_of(list), on_all_(is_valid_tuple))
    def my_function(l):
        pass

    l = [(1, 'ras'), (0.2, 'abc')]
    my_function(l)


    # ---- mini_lambda
    from valid8 import validate_arg, instance_of, on_all_

    # just for fun: we create our custom mini_lambda variable named 't'
    from mini_lambda import InputVar, Len, Isinstance
    t = InputVar('t', tuple)

    @validate_arg('l', instance_of(list), on_all_(
        # each item is a tuple of size 2
        instance_of(tuple), Len(t) == 2,
        # the first element is a float between 0 and 1
        Isinstance(t[0], Real), (0 <= t[0]) & (t[0] <= 1),
        # the 2d element is a lowercase string of len 3
        Isinstance(t[1], str), Len(t[1]) == 3, t[1].islower()
    ))
    def my_function(l):
        pass

    l = [(1, 'ras'), (0.2, 'abc')]
    my_function(l)
