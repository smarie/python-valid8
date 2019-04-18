from numbers import Integral

import pytest
from typing import Optional

from valid8 import validate_arg, is_multiple_of, InputValidationError


def create_for_test_validate_none_enforce():
    def myfunc(a: Integral, b: Optional[int], c=None):
        print('hello')
    return myfunc


def create_for_test_validate_none_pytypes():
    def myfunc(a: Integral, b = None):
        print('hello')
    return myfunc


def test_function_setter_name_in_valid8_error_message():
    from autoclass import autoclass
    from pytypes import typechecked
    from mini_lambda import s, x, Len

    @typechecked
    @autoclass
    class House:
        @validate_arg('name', Len(s) > 0)
        @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100))
        def __init__(self,
                     name: str,
                     surface: int = 100
                     ):
            pass

    o = House('helo')

    with pytest.raises(InputValidationError) as exc_info:
        o.surface = 150

    assert "Error validating input [surface=150] for function [surface]" in str(exc_info.value)
