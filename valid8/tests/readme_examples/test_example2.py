from inspect import isfunction

import pytest

# --------- the functions

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


def pep484(value):
    from pytypes import typechecked
    from mini_lambda import s, Len
    from valid8 import validate_arg

    @typechecked
    @validate_arg('s', Len(s) > 0, s.islower())
    def my_function(s: str):  # <- type hint in signature
        pass

    my_function(value)


# the list of functions
ex2_functions = [f for f in locals().values() if isfunction(f)
                 and not f.__name__.startswith('test') and f.__name__ != 'isfunction']

for f in ex2_functions:
    f.__doc__ = "Example 2 test with function " + f.__name__

# ----------- the test

ex2_values = [('foo', True),
              ('foo_123', True),
              (1.1, TypeError),
              ('', ValueError),
              ('fOO', ValueError)]


@pytest.mark.parametrize('s, outcome', ex2_values)
@pytest.mark.parametrize('function', ex2_functions, ids=lambda f: f.__name__)
def test_example_2(s, outcome, function):
    """ Tests that the example 2 provided in the documentation works (lowercase non-empty string) """

    # if s == 'foo' and function == function_input_mini_lambda:
    #     print('uncomment and put your breakpoint here to debug')

    if outcome is True:
        function(s)
    else:
        with pytest.raises(outcome) as exc_info:
            function(s)
        e = exc_info.value
        print(e)


ex2_values_regexp = [('foo@bar.com', True),
                     ('a@a@s', ValueError)]


@pytest.mark.parametrize('s, outcome', ex2_values_regexp)
def test_example_2_regexp(s, outcome):
    import re
    from valid8 import validate

    # basic regex to check that there is one @ and a dot in the second part
    EMAIL_REGEX = re.compile('[^@]+@[^@]+\.[^@]+')

    # you can now use 'EMAIL_REGEX.match' as a custom function anywhere
    function = lambda s: validate('s', s, instance_of=str, custom=lambda s: bool(EMAIL_REGEX.match(s)))

    if outcome is True:
        function(s)
    else:
        with pytest.raises(outcome) as exc_info:
            function(s)
        e = exc_info.value
        print(e)
