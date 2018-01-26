from inspect import isfunction
from numbers import Real
from typing import Tuple

import pytest


# --------- the functions
from pytypes import typechecked
from utils import append_all_custom_variants  # this works because in conftest.py we add it to the path


def inline_validate_1(t):
    from valid8 import validate
    validate('t', t, instance_of=tuple, length=2)
    validate('t[0]', t[0], instance_of=Real, min_value=0, max_value=1)
    validate('t[1]', t[1], instance_of=str, length=3, custom=str.islower)


def with_validator_boolean_tester(t):
    from valid8 import validator, instance_of
    with validator('t', t, instance_of=tuple) as v:
        v.alid = len(t) == 2 \
                 and instance_of(t[0], Real) and (0 <= t[0] <= 1) \
                 and instance_of(t[1], str) and len(t[1]) == 3 and t[1].islower()


def with_validator_failure_raiser(t):
    from valid8 import validation
    with validation('t', t, instance_of=tuple):
        # the tuple should be of length 2
        if len(t) != 2:
            raise ValueError('tuple length should be 2, found ' + str(t))

        # the first element is a float between 0 and 1
        if not isinstance(t[0], Real):
            raise TypeError('first elt should be a Real, found ' + str(t[0]))
        if not (0 <= t[0] <= 1):
            raise ValueError('first elt should be between 0 and 1,found ' + str(t[0]))

        # the second element is a lowercase string of size 3
        if not isinstance(t[1], str):
            raise TypeError('second elt should be a string, found ' + str(t[1]))
        if not (len(t[1]) == 3 and t[1].islower()):
            raise ValueError('second elt should be a lowercase string of length 3,'
                             'found ' + str(t[1]))


# 2 custom functions


def is_valid_tuple(t):
    """ custom validation function - here in 'boolean tester' style (returning a bool) """
    from valid8 import instance_of
    return instance_of(t, tuple) and len(t) == 2 \
           and instance_of(t[0], Real) and (0 <= t[0] <= 1) \
           and instance_of(t[1], str) and len(t[1]) == 3 and t[1].islower()


@typechecked
def is_valid_tuple_pep(t: Tuple[Real, str]):
    """ custom validation function - note the PEP484 type hint above """
    return len(t) == 2 and (0 <= t[0] <= 1) and len(t[1]) == 3 and t[1].islower()


@typechecked
def check_valid_tuple_pep(t: Tuple[Real, str]):
    """ custom validation function - note the PEP484 type hint above """

    # the first element is a float between 0 and 1
    if not (0 <= t[0] <= 1):
        raise ValueError('first elt should be between 0 and 1,found ' + str(t[0]))

    # the second element is a lowercase string of size 3
    if not (len(t[1]) == 3 and t[1].islower()):
        raise ValueError('second elt should be a lowercase string of length 3,'
                         'found ' + str(t[1]))


def check_valid_tuple(t):
    """ custom validation function - here in 'failure raiser' style (returning nothing) """

    # item should be a tuple of length 2
    if not isinstance(t, tuple):
        raise TypeError('item should be a tuple')
    if len(t) != 2:
        raise ValueError('tuple length should be 2, found ' + str(t))

    # the first element is a float between 0 and 1
    if not isinstance(t[0], Real):
        raise TypeError('first elt should be a Real, found ' + str(t[0]))
    if not (0 <= t[0] <= 1):
        raise ValueError('first elt should be between 0 and 1,found ' + str(t[0]))

    # the second element is a lowercase string of size 3
    if not isinstance(t[1], str):
        raise TypeError('second elt should be a string, found ' + str(t[1]))
    if not (len(t[1]) == 3 and t[1].islower()):
        raise ValueError('second elt should be a lowercase string of length 3,'
                         'found ' + str(t[1]))


def inline_validate_custom(t, custom):
    from valid8 import validate
    validate('t', t, custom=custom)


def inline_validator_custom_boolean(t, custom):
    from valid8 import validator
    with validator('t', t) as v:
        v.alid = custom(t)


def inline_validation_custom_raiser(t, custom):
    from valid8 import validation
    with validation('t', t):
        custom(t)


def function_input_custom(t, custom):
    from valid8 import validate_arg

    @validate_arg('t', custom)
    def my_function(t):
        pass

    my_function(t)


def class_fields_custom(t, custom):
    from valid8 import validate_field

    @validate_field('t', custom)
    class Foo:
        def __init__(self, t):
            self.t = t

    Foo(t)

def function_input_builtin_stdlib(value):
    from valid8 import validate_arg, instance_of, has_length, on_each_, and_, between

    @validate_arg('t', instance_of(tuple), has_length(2), on_each_(
        # the first element is a float between 0 and 1
        and_(instance_of(Real), between(0, 1)),
        # the 2d element is a lowercase string of len 3
        and_(instance_of(str), has_length(3), str.islower),
    ))
    def my_function(t):
        pass

    my_function(value)


def function_input_mini_lambda(value):
    from mini_lambda import InputVar, Len
    from valid8 import validate_arg, instance_of
    from valid8.validation_lib.mini_lambda import Instance_of

    # just for fun: we create our custom mini_lambda variable named 't'
    t = InputVar('t', tuple)

    @validate_arg('t', instance_of(tuple), Len(t) == 2,
                  # the first element is a float between 0 and 1
                  Instance_of(t[0], Real), (0 <= t[0]) & (t[0] <= 1),
                  # the 2d element is a lowercase string of len 3
                  Instance_of(t[1], str), Len(t[1]) == 3, t[1].islower()
                  )
    def my_function(t):
        pass

    my_function(value)


def class_field_builtin_stdlib(value):
    from valid8 import validate_field, instance_of, has_length, on_each_, and_, between

    @validate_field('t', instance_of(tuple), has_length(2), on_each_(
        # the first element is a float between 0 and 1
        and_(instance_of(Real), between(0, 1)),
        # the 2d element is a lowercase string of len 3
        and_(instance_of(str), has_length(3), str.islower),
    ))
    class Foo:
        def __init__(self, t):
            self.s = t

    Foo(value)


def class_field_mini_lambda(value):
    from mini_lambda import InputVar, Len
    from valid8 import validate_field, instance_of
    from valid8.validation_lib.mini_lambda import Instance_of

    # just for fun: we create our custom mini_lambda variable named 't'
    t = InputVar('t', tuple)

    @validate_field('t', instance_of(tuple), Len(t) == 2,
                    # the first element is a float between 0 and 1
                    Instance_of(t[0], Real), (0 <= t[0]) & (t[0] <= 1),
                    # the 2d element is a lowercase string of len 3
                    Instance_of(t[1], str), Len(t[1]) == 3, t[1].islower()
                    )
    class Foo:
        def __init__(self, t):
            self.s = t

    Foo(value)


def pep484(value):
    from typing import Tuple
    from pytypes import typechecked
    from mini_lambda import InputVar, Len
    from valid8 import validate_arg

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


# the initial list of functions
ex3_functions_init = [f for f in locals().values() if isfunction(f) and f.__module__ == __name__
                      and not f.__name__.startswith('test') and not f.__name__.startswith('_')
                      and f.__name__ not in {}
                      and 'is_valid' not in f.__name__ and 'check_valid' not in f.__name__]

# the list of custom functions used by the above
ex3_custom_booleans = [f for f in locals().values() if isfunction(f) and 'is_valid' in f.__name__]
ex3_custom_raisers = [f for f in locals().values() if isfunction(f) and 'check_valid' in f.__name__]

# mixing the two to get the final list (cross-product between the list of functions and the list of custom functions)
ex3_functions = []
for ex3_func in ex3_functions_init:
    if 'custom' not in ex3_func.__name__:
        print('{} does not use custom function'.format(ex3_func.__name__))
        ex3_functions.append(ex3_func)
    else:
        # create as many functions as there are custom functions to use
        # Note: we cannot do it directly here we have to use a proper function, otherwise ex3func gets lost somehow
        append_all_custom_variants(ex3_func, ex3_custom_booleans, ex3_custom_raisers, ex3_functions)


for ex3_func in ex3_functions_init:
    ex3_func.__doc__ = "Example 3 test with function " + ex3_func.__name__

# ----------- the test

ex3_values = [((0.2, 'foo'), True),
              ((1.0, 'abc'), True),
              ((0, 'foo'), True),  # we accept integers
              (1.1, TypeError),  # wrong type (not a tuple)
              ((0.2, 'foo', True), ValueError),  # wrong size (size 3)
              (('1.0', 'foo'), TypeError),  # wrong type ('1.0' is not a float)
              ((1.1, 'foo'), ValueError),  # wrong value (1.1 is not between 0 and 1)
              ((1.0, False), TypeError),  # wrong type (False is not a string)
              ((0.5, 'a'), ValueError),  # wrong value ('a' is not of size 3)
              ((0.5, 'AAA'), ValueError),  # wrong value ('AAA' is not lowercase)
              ]


@pytest.mark.parametrize('t, outcome', ex3_values, ids=str)
@pytest.mark.parametrize('function', ex3_functions, ids=lambda f: f.__name__)
def test_example_3(t, outcome, function):
    """ Tests that the example 3 provided in the documentation works (custom tuple) """

    if 'function_input_mini_' in function.__name__:  # and t == 'foo'
        print('uncomment and put your breakpoint here to debug')

    # known edge cases with PEP484
    if isinstance(t, tuple) and len(t) != 2 and 'pep' in function.__name__:
        # PEP484 type checkers will consider that this is not a ValueError but a TypeError
        if outcome is ValueError:
            outcome = TypeError

    if outcome is True:
        function(t)
    else:
        with pytest.raises(outcome) as exc_info:
            function(t)
        e = exc_info.value
        print(e)
