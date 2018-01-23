import pytest

from valid8 import ValidationError


def test_readme_examples_1():
    """ Tests that the example 1 provided in the documentation works """

    from numbers import Integral
    x = 0

    from valid8 import validate
    validate('x', x, instance_of=Integral, min_value=0)

    from valid8 import validator
    with validator('x', x, instance_of=Integral) as v:
        v.alid = x >= 0


    from valid8 import validate_arg, validate_out, validate_io, validate_field, instance_of, gt

    @validate_arg('x', instance_of(Integral), gt(0))
    def my_function(x):
        pass

    my_function(0)
    with pytest.raises(ValueError):
        my_function(-1)
    with pytest.raises(TypeError):
        my_function('')

    @validate_out(instance_of(Integral), gt(0))
    def my_function2():
        x = 0
        return x

    @validate_io(x=[instance_of(Integral), gt(0)])
    def my_function3(x):
        pass

    my_function3(0)
    with pytest.raises(ValueError):
        my_function3(-1)
    with pytest.raises(TypeError):
        my_function3('')

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

    from mini_lambda import s
    from valid8 import validate_arg, validate_out, validate_io, validate_field, instance_of

    @validate_arg('s', instance_of(str), s == s.lower())
    def my_function(s):
        pass

    my_function('re')
    with pytest.raises(ValueError):
        my_function('Re')
    with pytest.raises(TypeError):
        my_function(1)

    @validate_out(instance_of(str), s == s.lower())
    def my_function2():
        return -1

    @validate_io(s=[instance_of(str), s == s.lower()])
    def my_function3(s):
        pass

    my_function3('re')
    with pytest.raises(ValueError):
        my_function3('Re')
    with pytest.raises(TypeError):
        my_function3(1)

    @validate_field('s', instance_of(str), s == s.lower())
    class Foo:
        def __init__(self, s):
            self.s = s

    Foo('re')
    with pytest.raises(ValueError):
        Foo('Re')
    with pytest.raises(TypeError):
        Foo(1)
