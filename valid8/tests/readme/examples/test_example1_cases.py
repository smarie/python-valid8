import sys
from numbers import Integral


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


if sys.version_info >= (3, 0):
    from ._tests_pep484 import ex1_pep484 as pep484
