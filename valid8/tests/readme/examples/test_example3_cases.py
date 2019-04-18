import sys
from numbers import Real


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


if sys.version_info >= (3, 5):
    from ._tests_pep484 import ex3_is_valid_tuple_pep as is_valid_tuple_pep
    from ._tests_pep484 import ex3_check_valid_tuple_pep as check_valid_tuple_pep


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
    from valid8.validation_lib.mini_lambda_ import Instance_of

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
    from valid8.validation_lib.mini_lambda_ import Instance_of

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


if sys.version_info >= (3, 5):
    from ._tests_pep484 import ex3_pep484 as pep484
