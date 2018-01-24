import pytest

from valid8 import ValidationError


def test_readme_examples_1():
    """ Tests that the example 1 provided in the documentation works """

    from numbers import Integral
    x = 0

    # inline 1
    from valid8 import validate
    validate('x', x, instance_of=Integral, min_value=0)

    # inline 2
    from valid8 import validator
    with validator('x', x, instance_of=Integral) as v:
        v.alid = x >= 0

    # decorators
    from valid8 import validate_arg, validate_out, validate_io, validate_field, instance_of, gt

    # function input
    @validate_arg('x', instance_of(Integral), gt(0))
    def my_function(x):
        pass

    my_function(0)
    with pytest.raises(ValueError):
        my_function(-1)
    with pytest.raises(TypeError):
        my_function('')

    # function output
    @validate_out(instance_of(Integral), gt(0))
    def my_function2():
        x = 0
        return x

    # function ins and outs
    @validate_io(x=[instance_of(Integral), gt(0)])
    def my_function3(x):
        pass

    my_function3(0)
    with pytest.raises(ValueError):
        my_function3(-1)
    with pytest.raises(TypeError):
        my_function3('')

    # class field
    @validate_field('x', instance_of(Integral), gt(0))
    class Foo:
        def __init__(self, x):
            self.x = x

    Foo(0)
    with pytest.raises(ValueError):
        Foo(-1)
    with pytest.raises(TypeError):
        Foo('')


def test_readme_examples_2():
    s = 'lowww'

    # inline 1
    from valid8 import validate
    validate('s', s, instance_of=str, min_len=1, equals=s.lower())

    # inline 2
    from valid8 import validator
    with validator('s', s, instance_of=str) as v:
        v.alid = (len(s) > 0) and s.islower()

    from mini_lambda import s
    from valid8 import validate_arg, validate_out, validate_io, validate_field, instance_of

    # function input
    @validate_arg('s', instance_of(str), s.islower())
    def my_function(s):
        pass

    my_function('re')
    with pytest.raises(ValueError):
        my_function('Re')
    with pytest.raises(TypeError):
        my_function(1)

    # function output
    @validate_out(instance_of(str), s.islower())
    def my_function2():
        return -1

    # function ins and outs
    @validate_io(s=[instance_of(str), s.islower()])
    def my_function3(s):
        pass

    my_function3('re')
    with pytest.raises(ValueError):
        my_function3('Re')
    with pytest.raises(TypeError):
        my_function3(1)

    # class field
    @validate_field('s', instance_of(str), s.islower())
    class Foo:
        def __init__(self, s):
            self.s = s

    Foo('re')
    with pytest.raises(ValueError):
        Foo('Re')
    with pytest.raises(TypeError):
        Foo(1)


def test_readme_examples_3():
    # list containing tuples of (float between 0 and 1, trigram (string of length 3)

    l = [(1, 'ras'), (0.2, 'abc')]

    # inline 1
    from valid8 import validate
    from numbers import Real

    # first validate the main type
    validate('l', l, instance_of=list)

    for i, v in enumerate(l):
        # each item is a tuple of size 2
        validate('l[{}]'.format(i), l[i], instance_of=tuple, length=2)
        # the first element is a float between 0 and 1
        validate('l[{}][0]'.format(i), l[i][0], instance_of=Real, min_value=0, max_value=1)
        # the second element is a lowercase string of size 3
        validate('l[{}][0]'.format(i), l[i][1], instance_of=str, length=3, equals=l[i][1].lower())

    # inline 2
    from valid8 import validator, instance_of

    l = [(1, 'ras'), (0.2, 'abc')]

    with validator('x', l, instance_of=list) as v:
        v.alid = all(
                    # each item is a tuple of size 2
                    instance_of(item, tuple) and len(item) == 2
                    # the first element is a float between 0 and 1
                    and instance_of(item[0], Real) and (0 <= item[0] <= 1)
                    # the second element is a lowercase string of size 3
                    and instance_of(item[1], str) and len(item[1]) == 3 and item[1].islower()
                 for item in l)


    # function input
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


    # mini_lambda
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
