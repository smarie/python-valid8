import sys


def inline_validate_1(s):
    from valid8 import validate
    validate('s', s, instance_of=str, min_len=1)
    validate('s', s, equals=s.lower())


def inline_validate_2(s):
    from valid8 import validate
    validate('s', s, instance_of=str, min_len=1, custom=str.islower)


def inline_validate_3(s):
    from valid8 import validate
    # we create a custom mini_lambda variable, since the name 's' is already used
    from mini_lambda import InputVar

    txt = InputVar('txt', str)
    validate('s', s, instance_of=str, min_len=1, custom=txt.islower())


def with_validator(s):
    from valid8 import validator
    with validator('s', s, instance_of=str) as v:
        v.alid = (len(s) > 0) and s.islower()


def function_input_builtin_stdlib(value):
    from valid8 import validate_arg, instance_of, minlen

    @validate_arg('s', instance_of(str), minlen(1), str.islower)
    def my_function(s):
        pass

    my_function(value)


def function_input_mini_lambda(value):
    from mini_lambda import s, Len
    from valid8 import validate_arg, instance_of

    @validate_arg('s', instance_of(str), Len(s) > 0, s.islower())
    def my_function(s):
        pass

    my_function(value)


def class_field_builtin_stdlib(value):
    from valid8 import validate_field, instance_of, minlen

    @validate_field('s', instance_of(str), minlen(1), str.islower)
    class Foo:
        def __init__(self, s):
            self.s = s

    Foo(value)


def class_field_mini_lambda(value):
    from mini_lambda import s, Len
    from valid8 import validate_field, instance_of

    @validate_field('s', instance_of(str), Len(s) > 0, s.islower())
    class Foo:
        def __init__(self, s):
            self.s = s

    Foo(value)


if sys.version_info >= (3, 0):
    from ._tests_pep484 import ex2_pep484 as pep484
