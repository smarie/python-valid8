import pytest
from typing import Optional

from valid8 import validate_io, InputValidationError, is_even, gt, not_, is_multiple_of, or_, xor_, and_, \
    decorate_with_validation, lt, not_all, Failure, validate_arg, NonePolicy, validate_out, OutputValidationError, \
    ValidationError, validate_field, ClassFieldValidationError, skip_on_none


def test_validate_field():
    """ Tests that the @validate_field decorator works on class descriptors """

    from mini_lambda import x

    class SurfaceField:
        """ An example descriptor implementing everything (although only one of the three methods is required) """

        def __init__(self, value=None):
            self.val = value

        def __get__(self, obj, objtype):
            return self.val

        def __set__(self, obj, val=None):  # note the None default value
            self.val = val

        def __delete__(self, obj):
            self.val = None

    @validate_field('x', x <= 42, help_msg="x must be smaller or equal to 42")
    class House:
        x = SurfaceField(10)
        y = 5
        def foo(self):
            pass

    obj = House()

    obj.x = None

    with pytest.raises(ClassFieldValidationError) as exc_info:
        obj.x = 43
    assert str(exc_info.value) == "x must be smaller or equal to 42. " \
                                  "Error validating field [x=43] for class [House]: " \
                                  "validation function [skip_on_none(x <= 42)] returned [False]."

    # wrong name
    with pytest.raises(ValueError):
        @validate_field('y')
        class House:
            x = SurfaceField(10)
            y = 5


def test_validate_field_property():
    """ Tests that the @validate_field decorator works when the class descriptor to validate is a @property """

    from mini_lambda import x

    def getx(self):
        return self.__x

    def setx(self, value=None):
        self.__x = value

    def delx(self):
        del self.__x

    @validate_field('x', x <= 42, help_msg="x must be smaller or equal to 42")
    class House:
        x = property(getx, setx, delx, "I'm the 'x' property.")
        y = 5
        def foo(self):
            pass

    obj = House()

    obj.x = 42
    obj.x = None

    with pytest.raises(ClassFieldValidationError):
        obj.x = 43

    # wrong name
    with pytest.raises(ValueError):
        @validate_field('y', x <= 42, help_msg="x must be smaller or equal to 42")
        class House:
            x = property(getx, setx, delx, "I'm the 'x' property.")
            y = 5

            def foo(self):
                pass

    # wrong name
    with pytest.raises(ValueError):
        @validate_field('foo', x <= 42, help_msg="x must be smaller or equal to 42")
        class House:
            x = property(getx, setx, delx, "I'm the 'x' property.")
            y = 5

            def foo(self):
                pass


def test_validate_field_custom_type():
    """"""
    from valid8 import validate_field, instance_of, is_multiple_of, ClassFieldValidationError
    from mini_lambda import x, s, Len

    class InvalidNameError(ClassFieldValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(ClassFieldValidationError):
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000.'

    @validate_field('name', instance_of(str), Len(s) > 0,
                    error_type=InvalidNameError)
    @validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                    error_type=InvalidSurfaceError)
    class House:
        def __init__(self, name, surface=None):
            self.name = name
            self.surface = surface

        @property
        def surface(self):
            return self.__surface

        @surface.setter
        def surface(self, surface=None):
            self.__surface = surface

    h = House('sweet home')
    h.name = ''  # DOES NOT RAISE InvalidNameError

    with pytest.raises(InvalidNameError):
        h = House('')

    h.surface = 100
    with pytest.raises(InvalidSurfaceError):
        h.surface = 10000


def test_validate_attr():
    """ Tests that the @validate_field decorator works when the class descriptor is from attrs """

    import attr
    from mini_lambda import x

    @validate_field('x', x <= 42, help_msg="x must be smaller or equal to 42")
    @attr.s
    class C(object):
        x = attr.ib()


def test_validate_arg_nominal_builtin_validators():
    """ Simple test of the @validate_arg annotation, with built-in validators is_even and gt(1) """

    @validate_arg('a', [is_even, gt(1)])
    @validate_arg('b', is_even)
    @validate_arg('b', gt(2), none_policy=NonePolicy.SKIP)
    def myfunc(a, b = None):
        print('hello')

    # -- check that the validation works
    myfunc(84, 82)
    with pytest.raises(InputValidationError):
        # a is None
        myfunc(None, 4)
    with pytest.raises(InputValidationError):
        # a is not even
        myfunc(1, 4)
    with pytest.raises(InputValidationError):
        # a is not >= 1
        myfunc(0, 4)
    with pytest.raises(InputValidationError):
        # b is not even
        myfunc(2, 3)
    with pytest.raises(InputValidationError):
        # b is not greater than 2
        myfunc(2, 0)

    myfunc(84, None)  # None is silently skipped since the first validator for b has 'skip'


def test_validate_out():
    @validate_out([is_even, gt(1)])
    @validate_out(lt(12))
    def myfunc(x):
        return x

    myfunc(4)  # 4 is even and betwen 1 and 12
    with pytest.raises(OutputValidationError):
        myfunc(14)

    with pytest.raises(OutputValidationError):
        myfunc(0)

    with pytest.raises(OutputValidationError):
        myfunc(11)


def test_validate_nominal_builtin_validators():
    """ Simple test of the @validate_io annotation, with built-in validators is_even and gt(1) """

    @validate_io(a=[is_even, gt(1)],
                 b=is_even,
                 _out_=lt(100))
    def myfunc(a, b):
        print('hello')
        return a

    # -- check that the validation works
    myfunc(84, 82)
    with pytest.raises(InputValidationError):
        # a is None
        myfunc(None,0)
    with pytest.raises(InputValidationError):
        # a is not even
        myfunc(1,0)
    with pytest.raises(InputValidationError):
        # b is not even
        myfunc(2,1)
    with pytest.raises(InputValidationError):
        # a is not >= 1
        myfunc(0,0)

    with pytest.raises(OutputValidationError):
        # result is not <= 100
        myfunc(102,0)


def test_validate_custom_validators_basic():
    """ Checks that basic custom functions can be used as validators """

    def is_mod_3(x):
        """ A simple validator with no parameters"""
        return x % 3 == 0

    def is_mod(ref):
        """ A validator generator, with parameters """
        def is_mod(x):
            return x % ref == 0
        return is_mod

    def gt_assert2(x):
        """ (not recommended) A validator relying on assert and therefore only valid in 'debug' mode """
        assert x >= 2

    @validate_io(a=[gt_assert2, is_mod_3],
                 b=is_mod(5))
    def myfunc(a, b):
        print('hello')

    # -- check that the validation works
    myfunc(21, 15)

    with pytest.raises(InputValidationError) as exc_info:
        myfunc(4, 21)  # InputValidationError: a is not a multiple of 3
    e = exc_info.value
    assert str(e) == "Error validating input [a=4] for function [myfunc]. " \
                     "Validation function [and(gt_assert2, is_mod_3)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [4]. " \
                     "Successes: ['gt_assert2'] / Failures: {'is_mod_3': 'False'}."

    with pytest.raises(InputValidationError) as exc_info:
        myfunc(15, 1)  # InputValidationError: b is not a multiple of 5
    e = exc_info.value
    assert str(e) == "Error validating input [b=1] for function [myfunc]: " \
                     "validation function [is_mod] returned [False]."

    with pytest.raises(InputValidationError) as exc_info:
        myfunc(1, 0)  # InputValidationError caused by AssertionError: a is not >= 2
    e = exc_info.value
    assert str(e) == "Error validating input [a=1] for function [myfunc]. " \
                     "Validation function [and(gt_assert2, is_mod_3)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [1]. " \
                     "Successes: [] / Failures: {'gt_assert2': 'AssertionError: assert 1 >= 2', 'is_mod_3': 'False'}."


def test_validate_custom_validators_with_exception():
    """ Checks that custom functions throwing Failure can be used as validators """

    def gt_ex1(x):
        """ A validator raising a custom exception in case of failure """
        if not x >= 1:
            raise Failure('x >= 1 does not hold for x={val}'.format(val=x))

    def is_mod(ref):
        """ A validator generator, with parameters and which raises a custom exception """
        def is_mod(x):
            if x % ref != 0:
                raise Failure('x % {ref} == 0 does not hold for x={val}'.format(ref=ref, val=x))
        return is_mod

    @validate_io(a=[gt_ex1, lt(12), is_mod(5)])
    def myfunc(a):
        print('hello')

    # -- check that the validation works
    myfunc(5)

    with pytest.raises(InputValidationError) as exc_info:
        print(1)
        myfunc(0)  # InputValidationError: a >= 1 does not hold
    e = exc_info.value
    assert str(e) == "Error validating input [a=0] for function [myfunc]. " \
                     "Validation function [and(gt_ex1, lesser_than_12, is_mod)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [0]. " \
                     "Successes: ['lesser_than_12', 'is_mod'] / " \
                     "Failures: {'gt_ex1': 'Failure: Wrong value: [x >= 1 does not hold for x=0]'}."

    with pytest.raises(InputValidationError) as exc_info:
        print(2)
        myfunc(3)  # InputValidationError: a % 5 == 0 does not hold
    e = exc_info.value
    assert str(e) == "Error validating input [a=3] for function [myfunc]. " \
                     "Validation function [and(gt_ex1, lesser_than_12, is_mod)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [3]. " \
                     "Successes: ['gt_ex1', 'lesser_than_12'] / " \
                     "Failures: {'is_mod': 'Failure: Wrong value: [x % 5 == 0 does not hold for x=3]'}."

    with pytest.raises(InputValidationError) as exc_info:
        print(3)
        myfunc(15)  # InputValidationError: a < 12 does not hold
    e = exc_info.value
    assert str(e) == "Error validating input [a=15] for function [myfunc]. " \
                     "Validation function [and(gt_ex1, lesser_than_12, is_mod)] raised " \
                     "AtLeastOneFailed: At least one validation function failed validation for value [15]. " \
                     "Successes: ['gt_ex1', 'is_mod'] / " \
                     "Failures: {'lesser_than_12': 'TooBig: x <= 12 does not hold for x=15. Wrong value: [15]'}."


def test_validate_mini_lambda():
    """ Tests that mini_lambda works with @validate_io """

    from mini_lambda import Len, s, x, Int

    @validate_io(name=(0 < Len(s)) & (Len(s) <= 10),
                 age=(x > 0) & (Int(x) == x))
    def hello_world(name: str, age: float):
        print('Hello, ' + name + ' your age is ' + str(age))

    hello_world('john', 20)


def test_validate_none_enforce():
    """ Tests that a None will be caught by enforce: no need for not_none validator """

    from enforce import runtime_validation, config
    from enforce.exceptions import RuntimeTypeError
    from numbers import Integral

    # we're not supposed to do that but if your python environment is a bit clunky, that might help
    config(dict(mode='covariant'))

    @runtime_validation
    @validate_io(a=[is_even, gt(1)], b=is_even, c=is_even)
    def myfunc(a: Integral, b: Optional[int], c=None):
        print('hello')

    # -- check that the validation works
    myfunc(84, None)     # OK because b is Nonable and c is optional with default value None
    with pytest.raises(RuntimeTypeError):
        myfunc(None, 0)  # RuntimeTypeError: a is None


def test_validate_none_pytypes():
    """ Tests that a None will be caught by pytypes: no need for not_none validator """

    from pytypes import typechecked
    from pytypes import InputTypeError
    from numbers import Integral

    # we're not supposed to do that but if your python environment is a bit clunky, that might help
    # config(dict(mode='covariant'))

    @typechecked
    @validate_io(a=[is_even, gt(1)], b=is_even)
    def myfunc(a: Integral, b = None):
        print('hello')

    # -- check that the validation works
    myfunc(84, None)  # OK because b has no type annotation nor not_none validator
    with pytest.raises(InputTypeError):
        myfunc(None, 0)  # InputTypeError: a is None


def test_validate_none_is_allowed():
    """ Tests that a None input is allowed by default and that in this case the validators are not executed """

    @validate_io(a=is_even)
    def myfunc(a = None, b = int):
        print('hello')

    # -- check that the validation works
    myfunc(84, 82)
    myfunc(None, 0)


def test_validate_name_error():
    """ Checks that wrong attribute names cant be provided to @validate_io"""

    with pytest.raises(ValueError):
        @validate_io(ab=[])
        def myfunc(a, b):
            print('hello')


def test_decorate_manually():
    """ Tests that the manual decorator works """

    def my_func(a):
        pass

    my_func = decorate_with_validation(my_func, 'a', is_even)

    with pytest.raises(InputValidationError):
        my_func(9)


def test_validate_tracebacks():
    """ Tests that the traceback is reduced for instance_of checks """

    from valid8 import validate_arg, instance_of
    from mini_lambda import x

    @validate_arg('foo', instance_of(int), x > 2)
    def dofoo(foo):
        pass

    # cause is none for HasWrongType
    with pytest.raises(ValidationError) as exc_info:
        dofoo("hello")

    e = exc_info.value
    assert e.__cause__.__cause__ is None

    # cause is not none otherwise
    with pytest.raises(ValidationError) as exc_info:
        dofoo(1)

    e = exc_info.value
    assert e.__cause__ is not None
