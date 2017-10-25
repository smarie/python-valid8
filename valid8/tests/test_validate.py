from typing import Tuple
from unittest import TestCase

import pytest

from valid8 import validate, ValidationError, is_even, gt, not_none, not_, is_mod, or_, xor_, is_subset, and_, \
    is_superset, is_in, validate_decorate, on_all_, on_each_, lt, not_all


class TestValidate(TestCase):

    def test_validate_simple(self):
        """ Simple test of the @validate annotation, with built-in validators is_even and gt(1) """

        @validate(a=[not_none, is_even, gt(1)],
                  b=is_even)
        def myfunc(a, b):
            print('hello')

        # -- check that the validation works
        myfunc(84, 82)
        with pytest.raises(ValidationError):
            # a is None
            myfunc(None,0)
        with pytest.raises(ValidationError):
            # a is not even
            myfunc(1,0)
        with pytest.raises(ValidationError):
            # b is not even
            myfunc(2,1)
        with pytest.raises(ValidationError):
            # a is not >= 1
            myfunc(0,0)

    def test_validate_wrong_notnone(self):
        with pytest.raises(ValueError):
            @validate(a=[is_even, not_none, gt(1)],
                      b=is_even)
            def myfunc(a, b):
                print('hello')

    def test_validate_empty(self):
        with pytest.raises(ValueError):
            @validate(a=[],
                      b=is_even)
            def myfunc(a, b):
                print('hello')

    def test_validate_custom(self):
        """ Simple test of the @validate annotation, with custom validators of several styles"""

        def is_mod_3(x):
            """ A simple validator with no parameters"""
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
                raise ValidationError('gt_ex1: x >= 1 does not hold for x=' + str(x))

        def gt_assert2(x):
            """ (not recommended) A validator relying on assert and therefore only valid in 'debug' mode """
            assert x >= 2

        @validate(a=[gt_ex1, gt_assert2, is_mod_3],
                  b=is_mod(5))
        def myfunc(a, b):
            print('hello')

        # -- check that the validation works
        myfunc(21, 15)
        with pytest.raises(ValidationError):
            myfunc(4,21)  # ValidationError: a is not a multiple of 3
        with pytest.raises(ValidationError):
            myfunc(15,1)  # ValidationError: b is not a multiple of 5
        with pytest.raises(AssertionError):
            myfunc(1,0)  # AssertionError: a is not >= 2
        with pytest.raises(ValidationError):
            myfunc(0,0)  # ValidationError: a is not >= 1

    def test_validate_enforce(self):
        """ Tests that a None will be catched by enforce: no need for not_none validator """
        from enforce import runtime_validation, config
        from enforce.exceptions import RuntimeTypeError
        from numbers import Integral

        # we're not supposed to do that but if your python environment is a bit clunky, that might help
        config(dict(mode='covariant'))

        @runtime_validation
        @validate(a=[is_even, gt(1)], b=is_even)
        def myfunc(a: Integral, b):
            print('hello')

        # -- check that the validation works
        myfunc(84, None)  # OK because b has no type annotation nor not_none validator
        with pytest.raises(RuntimeTypeError):
            myfunc(None, 0)  # RuntimeTypeError: a is None

    def test_validate_pytypes(self):
        """ Tests that a None will be catched by pytypes: no need for not_none validator """
        from pytypes import typechecked
        from pytypes import InputTypeError
        from numbers import Integral

        # we're not supposed to do that but if your python environment is a bit clunky, that might help
        # config(dict(mode='covariant'))

        @typechecked
        @validate(a=[is_even, gt(1)], b=is_even)
        def myfunc(a: Integral, b):
            print('hello')

        # -- check that the validation works
        myfunc(84, None)  # OK because b has no type annotation nor not_none validator
        with pytest.raises(InputTypeError):
            myfunc(None, 0)  # InputTypeError: a is None

    def test_validate_name_error(self):
        """ Checks that wrong attribute names cant be provided to @validate"""
        with pytest.raises(ValueError):
            @validate(ab=[])
            def myfunc(a, b):
                print('hello')

    def test_validate_none_is_allowed(self):
        @validate(a=is_even)
        def myfunc(a, b):
            print('hello')

        # -- check that the validation works
        myfunc(84, 82)
        myfunc(None, 0)

    def test_validate_not_not_all(self):
        """ Test for the not_ and not_all validators """

        def gtcustom(x):
            assert x < 10

        @validate(a=not_(is_even), b=not_all([is_even, is_mod(3)]), c=not_(gtcustom, catch_all=True),
                  d=not_(gtcustom))
        def myfunc(a, b, c, d):
            print('hello')

        # -- check that the validation works
        myfunc(11, 11, 11, None)

        with pytest.raises(ValidationError):
            myfunc(84, 82, None, None)  # ValidationError: a is even

        with pytest.raises(ValidationError):
            myfunc(84, 3, None, None)  # ValidationError: b is odd (ok) but it is a multiple of 3 (nok)

        with pytest.raises(ValidationError):
            myfunc(11, 11, 9, 11)  # c is not valid but the not_ operator catches the exception and wraps it

        with pytest.raises(ValidationError):
            myfunc(11, 11, 11, 9)  # d is not valid

        with pytest.raises(AssertionError):
            myfunc(11, 11, 11, 11)  # d is valid but the not_ operator does not catch the exception so we get the error

    def test_validate_or(self):
        """ Test for the or_ validator, also in combination with not_"""

        # empty list error
        with pytest.raises(ValueError):
            @validate(a=or_([]))
            def myfunc(a, b):
                print('hello')

        # single element simplification
        @validate(a=or_([is_even]))
        def myfunc(a):
            print('hello')

        myfunc(4)
        with pytest.raises(ValidationError):
            myfunc(7)

        # lists
        @validate(a=or_([is_even, is_mod(3)]), b=not_(or_([is_even, is_mod(3)])))
        def myfunc(a, b):
            print('hello')

        # -- check that the validation works
        myfunc(9, None)  # a is not even but is a multiple of 3 > ok
        myfunc(4, None)  # a is even but is not a multiple of 3 > ok
        myfunc(6, 7)     # b is not even AND not a multiple of 3 > ok

        with pytest.raises(ValidationError):
            myfunc(7, None)  # ValidationError: a is odd and not multiple of 3

        with pytest.raises(ValidationError):
            myfunc(None, 3)  # ValidationError: b is odd but it is a multiple of 3

    def test_validate_xor(self):
        """ Test for the xor_ validator """

        # empty list error
        with pytest.raises(ValueError):
            @validate(a=xor_([]))
            def myfunc(a, b):
                print('hello')

        # single element simplification
        @validate(a=xor_([is_even]))
        def myfunc(a):
            print('hello')

        myfunc(4)
        with pytest.raises(ValidationError):
            myfunc(7)

        # lists
        @validate(a=xor_([is_even, is_mod(3)]))
        def myfunc(a):
            print('hello')

        # -- check that the validation works
        myfunc(9)  # a is not even but is a multiple of 3 > ok
        myfunc(4)  # a is even but is not a multiple of 3 > ok

        with pytest.raises(ValidationError):
            myfunc(6)  # ValidationError: a is both even and a multiple of 3

        with pytest.raises(ValidationError):
            myfunc(7)  # ValidationError: a is both even and a multiple of 3

    def test_validate_and(self):
        """ Simple test of the @validate annotation, with built-in validators is_even and gt(1) """

        # empty list error
        with pytest.raises(ValueError):
            @validate(a=and_([]))
            def myfunc(a, b):
                print('hello')

        # single element simplification
        @validate(a=and_([is_even]))
        def myfunc(a):
            print('hello')

        myfunc(4)
        with pytest.raises(ValidationError):
            myfunc(7)

        # lists
        @validate(a=[not_none, and_([is_even, gt(1)])])
        def myfunc(a):
            print('hello')

        # -- check that the validation works
        myfunc(84)
        with pytest.raises(ValidationError):
            # a is None
            myfunc(None)
        with pytest.raises(ValidationError):
            # a is not even
            myfunc(1)
        with pytest.raises(ValidationError):
            # a is not >= 1
            myfunc(0)

    def test_validate_is_in(self):
        """ Test for the subset and superset validators """

        @validate(a=is_in({'+', '-'}))
        def myfunc(a):
            print('hello')

        # -- check that the validation works
        myfunc('+')
        with pytest.raises(ValidationError):
            myfunc('*')

    def test_validate_subset_superset(self):
        """ Test for the subset and superset validators """

        @validate(a=is_subset({'+', '-'}), b=is_superset({'+', '-'}),
                  c=[is_subset({'+', '-'}), is_superset({'+', '-'})])
        def myfunc(a, b, c):
            print('hello')

        # -- check that the validation works
        myfunc({'+'},{'+', '-', '*'}, {'+', '-'})

        with pytest.raises(ValidationError):
            myfunc({'+', '-', '*'}, None, None)

        with pytest.raises(ValidationError):
            myfunc(None, {'+'}, None)

        with pytest.raises(ValidationError):
            myfunc(None, None, {'+', '-', '*'})

        with pytest.raises(ValidationError):
            myfunc(None, None, {'+'})

    def test_validate_on_all(self):
        @validate(a=on_all_(is_even, lt(0)))
        def myfunc(a: Tuple):
            print('hello')

        myfunc((0, -10, -2))

        with pytest.raises(ValidationError):
            myfunc((0, -10, -1))

    def test_validate_on_each(self):
        @validate(a=on_each_(is_even, lt(0)))
        def myfunc(a: Tuple[int, int]):
            print('hello')

        myfunc((0, -1))

        with pytest.raises(ValidationError):
            myfunc((0, 2))

    def test_decorate_manually(self):
        """ Tests that the manual decorator works """

        def my_func(a):
            pass

        my_func = validate_decorate(my_func, a=is_even)

        with pytest.raises(ValidationError):
            my_func(9)
