import pytest
from functools import partial

from valid8 import InputValidationError, ValidationError, assert_valid, is_valid, Validator
from valid8.base import InvalidValue
from valid8.tests.helpers.math import isfinite, inf

# This test file corresponds to usage.md that is actually not used anymore. But we leave it as it can do no harm


def test_tutorial():

    # 1. age: finite
    def hello(age):
        assert isfinite(age)
        print('Hello, %s-years-old fella !' % age)

    hello(21)
    with pytest.raises(AssertionError):
        hello(inf)  # AssertionError: assert False \ where False = <built-in function isfinite>(inf)

    # v1: age is finite
    # from valid8 import assert_valid
    from valid8 import validate

    def hello(age):
        # assert_valid('age', age, isfinite)
        validate('age', age, custom=isfinite)
        print('Hello, %s-years-old fella !' % age)

    hello(21)
    with pytest.raises(ValidationError) as exc_info:
        hello(inf)
    e = exc_info.value
    assert str(e) == "Error validating [age=inf]. InvalidValue: Function [isfinite] returned [False] for value inf."
    assert str(e.validator) == "Validator<validation_function=isfinite, none_policy=VALIDATE, exc_type=ValidationError>"
    assert e.validator.get_main_function_name() == 'isfinite'
    assert e.validator.main_function.__name__ == 'isfinite'
    assert e.var_name == 'age'
    assert e.var_value == inf
    assert isinstance(e.failure, InvalidValue)
    assert e.failure.validation_outcome is False

    # v2: age between 0 and 100
    from valid8.validation_lib import between
    def hello(age):
        assert_valid('age', age, [isfinite, between(0, 150)])
        print('Hello, %s-years-old fella !' % age)

    hello(21)
    with pytest.raises(ValidationError) as exc_info:
        hello(152)
    e = exc_info.value
    assert str(e) == "Error validating [age=152]. " \
                     "At least one validation function failed for value 152. " \
                     "Successes: ['isfinite'] / Failures: {" \
                     "'between_0_and_150': 'NotInRange: 0 <= x <= 150 does not hold for x=152.'}."

    # v3: age is an integer
    # https://stackoverflow.com/questions/3501382/checking-whether-a-variable-is-an-integer-or-not
    from mini_lambda import x, Int
    def hello(age):
        assert_valid('age', age, [isfinite, between(0, 150), Int(x) == x])
        print('Hello, %s-years-old fella !' % age)

    with pytest.raises(ValidationError) as exc_info:
        hello(12.5)
    e = exc_info.value
    assert str(e) == "Error validating [age=12.5]. " \
                     "At least one validation function failed for value 12.5. " \
                     "Successes: ['isfinite', 'between_0_and_150'] / Failures: {'int(x) == x': 'Returned False.'}."


def test_usage_base_validation_functions():
    """ Tests that the examples in the usage section of the documentation work """

    is_multiple_of, is_multiple_of_3 = create_base_functions()


def test_usage_ensure_valid():
    """ Tests that the examples in the usage section of the documentation work """

    is_multiple_of, is_multiple_of_3 = create_base_functions()

    from mini_lambda import s

    # (1) Existing function
    assert_valid('nb', 0, isfinite)
    with pytest.raises(ValidationError):
        assert_valid('nb', inf, isfinite)
    # (2) Functools partial
    assert_valid('typ', int, partial(issubclass, bool))
    with pytest.raises(ValidationError):
        assert_valid('typ', str, partial(issubclass, bool))
    # (3) User-defined, standard
    assert_valid('nb', 3, is_multiple_of_3)
    with pytest.raises(ValidationError):
        assert_valid('nb', 1, is_multiple_of_3)
    # (4) User-defined, lambda
    assert_valid('txt', 'abc', lambda s: s.islower())
    with pytest.raises(ValidationError):
        assert_valid('txt', 'aBc', lambda s: s.islower())
    # (5) User-defined, mini-lambda
    assert_valid('txt', 'Abc', s.lower().startswith('a'))
    with pytest.raises(ValidationError):
        assert_valid('txt', 'Bbc', s.lower().startswith('a'))
    # (6) User-defined, factory
    assert_valid('nb', 15, is_multiple_of(5))
    with pytest.raises(ValidationError):
        assert_valid('nb', 1, is_multiple_of(5))

    gt_0, gt_1, gt_2, gt_3 = create_base_functions_2()
    assert_valid('nb', 1, gt_0)
    with pytest.raises(ValidationError):
        assert_valid('nb', -0.2, gt_0)
    assert_valid('nb', 1, gt_1)
    with pytest.raises(ValidationError):
        assert_valid('nb', 0.2, gt_1)
    assert_valid('nb', 2, gt_2)
    with pytest.raises(ValidationError):
        assert_valid('nb', 0.2, gt_2)
    assert_valid('nb', 3, gt_3)
    with pytest.raises(ValidationError):
        assert_valid('nb', 0.2, gt_3)


def test_usage_is_valid():
    """ Tests that the examples in the usage section of the documentation work """

    is_multiple_of, is_multiple_of_3 = create_base_functions()

    from mini_lambda import s

    # (1) Existing function
    assert is_valid(0, isfinite) is True
    assert is_valid(inf, isfinite) is False
    # (2) Functools partial
    assert is_valid(int, partial(issubclass, bool)) is True
    assert is_valid(str, partial(issubclass, bool)) is False
    # (3) User-defined, standard
    assert is_valid(9, is_multiple_of_3) is True
    assert is_valid(1, is_multiple_of_3) is False
    # (4) User-defined, lambda
    assert is_valid('abc', lambda s: s.islower()) is True
    assert is_valid('aBc', lambda s: s.islower()) is False
    # (5) User-defined, mini-lambda
    assert is_valid('Abc', s.lower().startswith('a')) is True
    assert is_valid('Bbc', s.lower().startswith('a')) is False
    # (6) User-defined, factory
    assert is_valid(15, is_multiple_of(5)) is True
    assert is_valid(1, is_multiple_of(5)) is False

    gt_0, gt_1, gt_2, gt_3 = create_base_functions_2()
    assert is_valid(0, gt_0) is True
    assert is_valid(-0.2, gt_0) is False
    assert is_valid(1, gt_1) is True
    assert is_valid(0.2, gt_1) is False
    assert is_valid(2, gt_2) is True
    assert is_valid(0.2, gt_2) is False
    assert is_valid(3, gt_3) is True
    assert is_valid(0.2, gt_3) is False


def test_usage_validators():
    """ Tests that the examples in the usage section of the documentation work """

    is_multiple_of, is_multiple_of_3 = create_base_functions()
    gt_0, gt_1, gt_2, gt_3 = create_base_functions_2()

    from mini_lambda import s

    validate_is_finite = Validator(isfinite)
    _is_subclass_of_bool = partial(issubclass, bool)
    validate_is_superclass_of_bool = Validator(_is_subclass_of_bool)
    validate_is_multiple_of_3 = Validator(is_multiple_of_3)
    validate_is_lowercase = Validator(lambda s: s.islower())
    validate_starts_with_a = Validator(s.lower().startswith('a'))
    validate_is_multiple_of_5 = Validator(is_multiple_of(5))
    validate_is_greater_than_0 = Validator(gt_0)
    validate_is_greater_than_1 = Validator(gt_1)
    validate_is_greater_than_2 = Validator(gt_2)
    validate_is_greater_than_3 = Validator(gt_3)

    # -- check that the validation works

    # (1) Existing function
    validate_is_finite('val', 0.5)  # ok
    with pytest.raises(ValidationError) as exc_info:
        validate_is_finite('val', inf)
    e = exc_info.value
    assert str(e) == 'Error validating [val=inf]. InvalidValue: Function [isfinite] returned [False] for value inf.'

    validate_is_superclass_of_bool('typ', int)  # ok
    with pytest.raises(ValidationError) as exc_info:
        validate_is_superclass_of_bool('typ', str)
    e = exc_info.value
    assert str(e) == "Error validating [typ=%r]. InvalidValue: Function [%r] returned [False] for value %r." \
                     "" % (str, _is_subclass_of_bool, str)

    validate_is_multiple_of_3('val', 21)  # ok
    with pytest.raises(ValidationError) as exc_info:
        validate_is_multiple_of_3('val', 4)
    e = exc_info.value
    assert str(e) == "Error validating [val=4]. InvalidValue: Function [is_multiple_of_3] returned [False] for value 4."

    validate_is_lowercase('txt', 'abc')  # ok
    with pytest.raises(ValidationError) as exc_info:
        validate_is_lowercase('txt','aBc')
    e = exc_info.value
    assert str(e) == "Error validating [txt=aBc]. InvalidValue: Function [<lambda>] returned [False] for value 'aBc'."

    validate_starts_with_a('txt','Abc')  # ok
    with pytest.raises(ValidationError) as exc_info:
        validate_starts_with_a('txt','bac')
    e = exc_info.value
    assert str(e) == "Error validating [txt=bac]. InvalidValue: Function [s.lower().startswith('a')] returned [False] " \
                     "for value 'bac'."

    validate_is_multiple_of_5('val',15)  # ok
    with pytest.raises(ValidationError) as exc_info:
        validate_is_multiple_of_5('val',1)
    e = exc_info.value
    assert str(e) == "Error validating [val=1]. InvalidValue: Function [is_multiple_of_5] returned [False] for value 1."

    # last batch of functions: with exceptions
    validate_is_greater_than_0('val', 0)
    with pytest.raises(ValidationError) as exc_info:
        validate_is_greater_than_0('val', -0.2)
    e = exc_info.value
    assert str(e) == "Error validating [val=-0.2]. InvalidValue: Function [gt_0] raised " \
                     "ValueError: x is not greater than 0, x=-0.2."
    validate_is_greater_than_1('val', 1)
    with pytest.raises(ValidationError) as exc_info:
        validate_is_greater_than_1('val', 0.2)
    e = exc_info.value
    assert str(e) == "Error validating [val=0.2]. ValidationFailure: x is not greater than 1, x=0.2. Wrong value: 0.2."
    validate_is_greater_than_2('val', 2)
    with pytest.raises(ValidationError) as exc_info:
        validate_is_greater_than_2('val', 0.2)
    e = exc_info.value
    assert str(e) == "Error validating [val=0.2]. InvalidValue: Function [gt_2] raised AssertionError: assert 0.2 >= 2"
    validate_is_greater_than_3('val', 3)
    with pytest.raises(ValidationError) as exc_info:
        validate_is_greater_than_3('val', 0.2)
    e = exc_info.value
    assert str(e) == "Error validating [val=0.2]. InvalidValue: Function [gt_3] returned " \
                     "[x is not greater than 3, x=0.2] for value 0.2."


def create_base_functions():

    # Existing - already ok
    is_finite = isfinite

    # Existing + Functools Partial
    is_superclass_of_bool = partial(issubclass, bool)
    """ Checks that c is a superclass of the bool type """

    # User-defined, standard
    def is_multiple_of_3(x):
        """ Checks that x is a multiple of 3 """
        return x % 3 == 0

    # User-defined, Lambda
    is_lowercase = lambda s: s.islower()
    is_lowercase.__doc__ = "Checks that s is lowercase"

    # User-defined, mini-lambda
    from mini_lambda import _, s
    starts_with_a = _(s.lower().startswith('a'))

    # The factory of validator functions
    def is_multiple_of(ref):
        """
        Returns a validation function to validate that x is a multiple of <ref>

        :param ref: the reference to compare x to
        :return: a validation function
        """

        def is_multiple_of_ref(x):
            return x % ref == 0

        is_multiple_of_ref.__doc__ = "Checks that x is a multiple of %s" % ref
        is_multiple_of_ref.__name__ = "is_multiple_of_" + str(ref)
        return is_multiple_of_ref

    # Here we use the factory to create two validator functions
    is_multiple_of_5 = is_multiple_of(5)
    is_multiple_of_9 = is_multiple_of(9)

    return is_multiple_of, is_multiple_of_3


def create_base_functions_2():
    from valid8 import ValidationFailure

    # (recommended) raising an exception
    def gt_0(x):
        if not (x >= 0):
            raise ValueError('x is not greater than 0, x=%s.' % x)
    def gt_1(x):
        if x < 1:
            raise ValidationFailure(x, 'x is not greater than 1, x=%s.' % x)

    # (not recommended) relying on assert, only valid in 'debug' mode
    def gt_2(x):
        assert x >= 2

    # returning details
    def gt_3(x):
        if x < 3:
            return 'x is not greater than 3, x=%s' % x

    return gt_0, gt_1, gt_2, gt_3


def test_usage_validate_annotation():
    """ """
    from valid8 import validate_io

    @validate_io(arg2=isfinite, arg3=isfinite)
    def myfunc(arg1, arg2, arg3):
        pass

    with pytest.raises(InputValidationError) as exc_info:
        myfunc(None, inf, inf)
        pytest.fail("InputValidationError was not raised")
    e = exc_info.value
    assert str(e) == 'Error validating input [arg2=inf] for function [myfunc]. ' \
                     'InvalidValue: Function [isfinite] returned [False] for value inf.'


def test_usage_custom_validators():
    """ """

    from valid8 import validate_io, ValidationError, ValidationFailure

    def is_mod_3(x):
        """ A simple validator with no parameters """
        return x % 3 == 0

    def is_mod(ref):
        """ A validator generator, with parameters """

        def is_mod_ref(x):
            return x % ref == 0

        return is_mod_ref

    def gt_ex1(x):
        """ A validator raising a custom exception in case of failure """
        if x >= 1:
            return True
        else:
            raise ValidationFailure(x, 'x >= 1 does not hold for x=%s' % x)

    def gt_assert2(x):
        """(not recommended) relying on assert, only valid in 'debug' mode"""
        assert x >= 2

    @validate_io(a=[gt_ex1, gt_assert2, is_mod_3],
                 b=is_mod(5))
    def myfunc(a, b):
        pass

    # -- check that the validation works
    myfunc(21, 15)  # ok
    with pytest.raises(ValidationError):
        myfunc(4, 21)  # inner ValidationFailure: a is not a multiple of 3
    with pytest.raises(ValidationError):
        myfunc(15, 1)  # inner ValidationFailure: b is not a multiple of 5
    with pytest.raises(ValidationError):
        myfunc(1, 0)  # inner AssertionError: a is not >= 2
    with pytest.raises(ValidationError):
        myfunc(0, 0)  # inner ValidationFailure: a is not >= 1
