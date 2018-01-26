from inspect import isfunction
from numbers import Integral

import pytest

# --------- the functions

def inline_validate(x):
    from valid8 import validate
    validate('x', x, instance_of=Integral, min_value=0)


def with_validator(x):
    from valid8 import validator
    with validator('x', x, instance_of=Integral) as v:
        v.alid = x >= 0


def function_input_builtin(value):
    from valid8 import validate_arg, instance_of, gt

    @validate_arg('x', instance_of(Integral), gt(0))
    def my_function(x):
        pass

    my_function(value)


def function_input_mini_lambda(value):
    from mini_lambda import x
    from valid8 import validate_arg, instance_of

    @validate_arg('x', instance_of(Integral), x >= 0)
    def my_function(x):
        pass

    my_function(value)


def function_output_builtin(value):
    from valid8 import validate_out, instance_of, gt

    @validate_out(instance_of(Integral), gt(0))
    def my_function2():
        return value

    my_function2()


def function_output_mini_lambda(value):
    from mini_lambda import x
    from valid8 import validate_out, instance_of

    @validate_out(instance_of(Integral), x >= 0)
    def my_function2():
        return value

    my_function2()


def function_io_builtin(value):
    from valid8 import validate_io, instance_of, gt

    @validate_io(x=[instance_of(Integral), gt(0)])
    def my_function3(x):
        pass

    my_function3(value)


def function_io_mini_lambda(value):
    from mini_lambda import x
    from valid8 import validate_io, instance_of

    @validate_io(x=[instance_of(Integral), x >= 0])
    def my_function3(x):
        pass

    my_function3(value)


def class_field_builtin_stdlib(value):
    from valid8 import validate_field, instance_of, gt

    @validate_field('x', instance_of(Integral), gt(0))
    class Foo:
        def __init__(self, x):
            self.x = x

    Foo(value)


def class_field_mini_lambda(value):
    from mini_lambda import x
    from valid8 import validate_field, instance_of

    @validate_field('x', instance_of(Integral), x >= 0)
    class Foo:
        def __init__(self, x):
            self.x = x

    Foo(value)


def pep484(value):
    from pytypes import typechecked
    from mini_lambda import x
    from valid8 import validate_arg

    @typechecked
    @validate_arg('x', x >= 0)
    def my_function(x: Integral):  # <- type hint in signature
        pass

    my_function(value)


# the list of functions
ex1_functions = [f for f in locals().values() if isfunction(f)
                 and not f.__name__.startswith('test') and f.__name__ != 'isfunction']

for f in ex1_functions:
    f.__doc__ = "Example 1 test with function " + f.__name__

# ----------- the test

ex1_values = [(0, True),
              (100, True),
              ('foo', TypeError),
              (1.0, TypeError),
              (-1, ValueError)]


@pytest.mark.parametrize('x, outcome', ex1_values)
@pytest.mark.parametrize('function', ex1_functions, ids=lambda f: f.__name__)
def test_example_1(x, outcome, function):
    """ Tests that the example 1 provided in the documentation works (positive integer) """

    # if x == 'foo' and function == function_input_mini_lambda:
    #     print('uncomment and put your breakpoint here to debug')

    if outcome is True:
        function(x)
    else:
        with pytest.raises(outcome) as exc_info:
            function(x)
        e = exc_info.value
        print(e)
