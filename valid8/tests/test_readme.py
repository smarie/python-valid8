import pytest
from enforce.exceptions import RuntimeTypeError
from pytypes import InputTypeError

from valid8 import InputValidationError, ValidationError


def test_index_enforce_mini_lambda():
    """ Tests that the first example of the documentation works """

    # Imports - for type validation
    from numbers import Real, Integral
    from valid8 import Boolean
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # subclasses of required types are valid too

    # Imports - for value validation
    from mini_lambda import s, x, Len
    from valid8 import validate

    @runtime_validation
    @validate(name=Len(s) > 0,
              surface=x >= 0)
    def build_house(name: str,
                    surface: Real,
                    nb_floors: Integral = None,
                    with_windows: Boolean = False):
        print('Building house...')
        print('DONE !')

    build_house('test', 12, 2)  # validation OK

    with pytest.raises(RuntimeTypeError):
        build_house('test', 12, 2.2)  # Type: @runtime_validation raises a InputTypeError

    build_house('test', 12, None)  # Declared 'Optional' with PEP484, no error

    with pytest.raises(ValidationError):
        build_house('test', -1, 2)  # Value: @validate raises a Failure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value: @validate raises a Failure


def test_index_enforce_old_style():
    """ Tests that the first example of the documentation works """

    # Imports - for type validation
    from valid8 import Boolean
    from numbers import Real, Integral
    from enforce import runtime_validation, config
    config(dict(mode='covariant'))  # allow subclasses when validating types

    # Imports - for value validation
    from valid8 import validate, minlens, gt

    # Usage
    @runtime_validation
    @validate(name=minlens(0),
              surface=gt(0))
    def build_house(name: str,
                    surface: Real,
                    nb_floors: Integral = None,
                    with_windows: Boolean = False):
        print('you did it !')

    build_house('test', 12, 2)  # validation OK

    with pytest.raises(RuntimeTypeError):
        build_house('test', 12, 2.2)  # Type: @runtime_validation raises a InputTypeError

    build_house('test', 12, None)  # Declared 'Optional' with PEP484, no error

    with pytest.raises(ValidationError):
        build_house('test', -1, 2)  # Value: @validate raises a Failure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value: @validate raises a Failure


@pytest.mark.skip(reason="waiting for the next version of pytypes")
def test_index_pytypes():
    """ Tests that the first example of the documentation would work if we switch to pytypes """

    # for type checking
    from valid8 import Boolean
    from numbers import Real, Integral
    from typing import Optional
    from pytypes import typechecked

    # for value checking
    from valid8 import validate, minlens, gt

    @typechecked
    @validate(name=minlens(0),
              surface=gt(0))
    def build_house(name: str,
                    surface: Real,
                    nb_floors: Optional[Integral] = 1,
                    with_windows: Boolean = False):
        print('you did it !')

    build_house('test', 12, 2)  # validation OK

    with pytest.raises(InputTypeError):
        build_house('test', 12, 2.2)  # Type validation: @typechecked raises a InputTypeError

    build_house('test', 12, None)  # Mandatory/Optional validation: Declared 'Optional' with PEP484, no error

    with pytest.raises(ValidationError):
        build_house('test', -1, 2)  # Value validation: @validate raises a Failure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value validation: @validate raises a Failure


def test_tutorial():

    # 1. age: finite
    from math import isfinite, inf

    def hello(age):
        assert isfinite(age)
        print('Hello, {}-years-old fella !'.format(age))

    with pytest.raises(AssertionError):
        hello(inf)  # AssertionError: assert False \ where False = <built-in function isfinite>(inf)

    # v1: age is finite
    from valid8 import assert_valid
    def hello(age):
        assert_valid(isfinite, age=age)
        print('Hello, {}-years-old fella !'.format(age))

    try:
        hello(inf)
    except ValidationError as e:
        assert str(e) == "Error validating [age=inf]: root validator [isfinite] returned [False]."

    # v2: age between 0 and 100
    from valid8 import between
    def hello(age):
        assert_valid([isfinite, between(0, 150)], age=age)
        print('Hello, {}-years-old fella !'.format(age))

    try:
        hello(152)
    except ValidationError as e:
        assert str(e) == "Error validating [age=152]. " \
                         "Root validator [and(isfinite, between_0_and_150)] raised [AtLeastOneFailed: " \
                         "At least one validator failed validation for value [152]. Successes: ['isfinite'] / " \
                         "Failures: {'between_0_and_150': '[Failure] between: 0 <= x <= 150 does not hold for x=152'} ]"

    # v3: age is an integer
    # https://stackoverflow.com/questions/3501382/checking-whether-a-variable-is-an-integer-or-not
    from mini_lambda import x, Int
    def hello(age):
        assert_valid([isfinite, between(0, 150), Int(x) == x], age=age)
        print('Hello, {}-years-old fella !'.format(age))

    try:
        hello(12.5)
    except ValidationError as e:
        assert str(e) == "Error validating [age=12.5]. " \
                         "Root validator [and(isfinite, between_0_and_150, int(x) == x)] raised [AtLeastOneFailed: " \
                         "At least one validator failed validation for value [12.5]. " \
                         "Successes: ['isfinite', 'between_0_and_150'] / Failures: {'int(x) == x': 'False'} ]"
    # TODO continue !


def test_usage_base_validation_functions():
    """ Tests that the examples in the usage section of the documentation work """

    is_multiple_of, is_multiple_of_3 = create_base_functions()


def test_usage_ensure_valid():
    """ Tests that the examples in the usage section of the documentation work """

    is_multiple_of, is_multiple_of_3 = create_base_functions()

    from valid8 import assert_valid
    from math import isfinite, inf
    from functools import partial
    from mini_lambda import s

    # (1) Existing function
    assert_valid(isfinite, nb=0)
    with pytest.raises(ValidationError):
        assert_valid(isfinite, nb=inf)
    # (2) Functools partial
    assert_valid(partial(issubclass, bool), typ=int)
    with pytest.raises(ValidationError):
        assert_valid(partial(issubclass, bool), typ=str)
    # (3) User-defined, standard
    assert_valid(is_multiple_of_3, nb=3)
    with pytest.raises(ValidationError):
        assert_valid(is_multiple_of_3, nb=1)
    # (4) User-defined, lambda
    assert_valid(lambda s: s.islower(), txt='abc')
    with pytest.raises(ValidationError):
        assert_valid(lambda s: s.islower(), txt='aBc')
    # (5) User-defined, mini-lambda
    assert_valid(s.lower().startswith('a'), txt='Abc')
    with pytest.raises(ValidationError):
        assert_valid(s.lower().startswith('a'), txt='Bbc')
    # (6) User-defined, factory
    assert_valid(is_multiple_of(5), nb=15)
    with pytest.raises(ValidationError):
        assert_valid(is_multiple_of(5), nb=1)

    gt_0, gt_1, gt_2, gt_3 = create_base_functions_2()
    assert_valid(gt_0, nb=1)
    with pytest.raises(ValidationError):
        assert_valid(gt_0, nb=-0.2)
    assert_valid(gt_1, nb=1)
    with pytest.raises(ValidationError):
        assert_valid(gt_1, nb=0.2)
    assert_valid(gt_2, nb=2)
    with pytest.raises(ValidationError):
        assert_valid(gt_2, nb=0.2)
    assert_valid(gt_3, nb=3)
    with pytest.raises(ValidationError):
        assert_valid(gt_3, nb=0.2)


def test_usage_is_valid():
    """ Tests that the examples in the usage section of the documentation work """

    is_multiple_of, is_multiple_of_3 = create_base_functions()

    from valid8 import is_valid
    from math import isfinite, inf
    from functools import partial
    from mini_lambda import s

    # (1) Existing function
    assert is_valid(isfinite, 0) is True
    assert is_valid(isfinite, inf) is False
    # (2) Functools partial
    assert is_valid(partial(issubclass, bool), int) is True
    assert is_valid(partial(issubclass, bool), str) is False
    # (3) User-defined, standard
    assert is_valid(is_multiple_of_3, 9) is True
    assert is_valid(is_multiple_of_3, 1) is False
    # (4) User-defined, lambda
    assert is_valid(lambda s: s.islower(), 'abc') is True
    assert is_valid(lambda s: s.islower(), 'aBc') is False
    # (5) User-defined, mini-lambda
    assert is_valid(s.lower().startswith('a'), 'Abc') is True
    assert is_valid(s.lower().startswith('a'), 'Bbc') is False
    # (6) User-defined, factory
    assert is_valid(is_multiple_of(5), 15) is True
    assert is_valid(is_multiple_of(5), 1) is False

    gt_0, gt_1, gt_2, gt_3 = create_base_functions_2()
    assert is_valid(gt_0, 0) is True
    assert is_valid(gt_0, -0.2) is False
    assert is_valid(gt_1, 1) is True
    assert is_valid(gt_1, 0.2) is False
    assert is_valid(gt_2, 2) is True
    assert is_valid(gt_2, 0.2) is False
    assert is_valid(gt_3, 3) is True
    assert is_valid(gt_3, 0.2) is False


def test_usage_validators():
    """ Tests that the examples in the usage section of the documentation work """

    is_multiple_of, is_multiple_of_3 = create_base_functions()
    gt_0, gt_1, gt_2, gt_3 = create_base_functions_2()

    from valid8 import Validator
    from functools import partial
    from math import isfinite, inf
    from mini_lambda import s

    validate_is_finite = Validator(isfinite)
    validate_is_superclass_of_bool = Validator(partial(issubclass, bool))
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
    validate_is_finite(val=0.5)  # ok
    try:
        validate_is_finite(val=inf)
    except ValidationError as e:
        assert str(e) == 'Error validating [val=inf]: root validator [isfinite] returned [False].'

    validate_is_superclass_of_bool(typ=int)  # ok
    try:
        validate_is_superclass_of_bool(typ=str)
    except ValidationError as e:
        assert str(e) == "Error validating [typ=<class 'str'>]: root validator [functools.partial(<built-in function " \
                         "issubclass>, <class 'bool'>)] returned [False]."

    validate_is_multiple_of_3(val=21)  # ok
    try:
        validate_is_multiple_of_3(val=4)
    except ValidationError as e:
        assert str(e) == "Error validating [val=4]: root validator [is_multiple_of_3] returned [False]."

    validate_is_lowercase(txt='abc')  # ok
    try:
        validate_is_lowercase(txt='aBc')
    except ValidationError as e:
        assert str(e) == "Error validating [txt=aBc]: root validator [<lambda>] returned [False]."

    validate_starts_with_a(txt='Abc')  # ok
    try:
        validate_starts_with_a(txt='bac')
    except ValidationError as e:
        assert str(e) == "Error validating [txt=bac]: root validator [s.lower().startswith('a')] returned [False]."

    validate_is_multiple_of_5(val=15)  # ok
    try:
        validate_is_multiple_of_5(val=1)
    except ValidationError as e:
        assert str(e) == "Error validating [val=1]: root validator [is_multiple_of_5] returned [False]."

    # last batch of functions: with exceptions
    validate_is_greater_than_0(val=0)
    try:
        validate_is_greater_than_0(val=-0.2)
    except ValidationError as e:
        assert str(e) == "Error validating [val=-0.2]. Root validator [gt_0] raised [ValueError: x is not greater than 0, x=-0.2]"
    validate_is_greater_than_1(val=1)
    try:
        validate_is_greater_than_1(val=0.2)
    except ValidationError as e:
        assert str(e) == "Error validating [val=0.2]. Root validator [gt_1] raised [Failure: x is not greater than 1, x=0.2]"
    validate_is_greater_than_2(val=2)
    try:
        validate_is_greater_than_2(val=0.2)
    except ValidationError as e:
        assert str(e) == "Error validating [val=0.2]. Root validator [gt_2] raised [AssertionError: assert 0.2 >= 2]"
    validate_is_greater_than_3(val=3)
    try:
        validate_is_greater_than_3(val=0.2)
    except ValidationError as e:
        assert str(e) == "Error validating [val=0.2]: root validator [gt_3] returned [x is not greater than 3, x=0.2]."


def create_base_functions():

    # Existing - already ok
    from math import isfinite
    is_finite = isfinite
    # Existing + Functools Partial
    from functools import partial
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

        is_multiple_of_ref.__doc__ = "Checks that x is a multiple of {}".format(ref)
        is_multiple_of_ref.__name__ = "is_multiple_of_" + str(ref)
        return is_multiple_of_ref

    # Here we use the factory to create two validator functions
    is_multiple_of_5 = is_multiple_of(5)
    is_multiple_of_9 = is_multiple_of(9)

    return is_multiple_of, is_multiple_of_3


def create_base_functions_2():
    from valid8 import Failure

    # (recommended) raising an exception
    def gt_0(x):
        if not (x >= 0):
            raise ValueError('x is not greater than 0, x={}'.format(x))
    def gt_1(x):
        if x < 1:
            raise Failure('x is not greater than 1, x={}'.format(x))

    # (not recommended) relying on assert, only valid in 'debug' mode
    def gt_2(x):
        assert x >= 2

    # returning details
    def gt_3(x):
        if x < 3:
            return 'x is not greater than 3, x={}'.format(x)

    return gt_0, gt_1, gt_2, gt_3


def test_usage_validate_annotation():
    """ """
    from valid8 import validate
    from math import isfinite, inf

    @validate(arg2=isfinite, arg3=isfinite)
    def myfunc(arg1, arg2, arg3):
        pass

    try:
        myfunc(None, inf, inf)
        pytest.fail("InputValidationError was not raised")
    except InputValidationError as e:
        assert str(e) == 'Error validating input [arg2=inf] for function [myfunc]: root validator ' \
                         '[isfinite] returned [False].'


def test_usage_custom_validators():
    """ """

    from valid8 import validate, ValidationError, Failure

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
            raise Failure('x >= 1 does not hold for x={}'.format(x))

    def gt_assert2(x):
        """(not recommended) relying on assert, only valid in 'debug' mode"""
        assert x >= 2

    @validate(a=[gt_ex1, gt_assert2, is_mod_3],
              b=is_mod(5))
    def myfunc(a, b):
        pass

    # -- check that the validation works
    myfunc(21, 15)  # ok
    with pytest.raises(ValidationError):
        myfunc(4, 21)  # inner Failure: a is not a multiple of 3
    with pytest.raises(ValidationError):
        myfunc(15, 1)  # inner Failure: b is not a multiple of 5
    with pytest.raises(ValidationError):
        myfunc(1, 0)  # inner AssertionError: a is not >= 2
    with pytest.raises(ValidationError):
        myfunc(0, 0)  # inner Failure: a is not >= 1
