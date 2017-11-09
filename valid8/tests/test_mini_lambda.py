from collections import Mapping
from typing import Iterator

import pytest
import sys

from valid8 import validate, InputVar, Len, Str, Int, Repr, Bytes, Getsizeof, Hash, Bool, Complex_, Float, Oct, Iter, \
    Any, All, _, Slice, Get, Not
from math import sin
from numbers import Real


# Iterable: __iter__
def test_evaluator_iterable():
    """ Iterable: tests that `Iter(li)` leads to a valid evaluator and `iter(li)` raises an exception"""

    li = InputVar(list)

    with pytest.raises(NotImplementedError):
        basic_evaluator = iter(li)

    basic_evaluator = Iter(li)
    basic_evaluator = basic_evaluator.as_function()

    assert type(basic_evaluator([0, 1])).__name__ == 'list_iterator'


# Iterator: __next__
def test_evaluator_iterator():
    """ Iterator/Generator: tests that `next()` leads to a valid evaluator"""

    i = InputVar(Iterator)
    next_elt_accessor = next(i)
    next_elt_accessor = next_elt_accessor.as_function()

    class Alternator:
        def __init__(self):
            self.current = True

        def __next__(self):
            self.current = not self.current
            return self.current

    foo = Alternator()

    assert not next_elt_accessor(foo)
    assert next_elt_accessor(foo)


def test_evaluator_iterator_iterable():
    """ Iterable + Iterator: tests that `next(Iter(li))` leads to a valid evaluator"""

    li = InputVar(list)
    first_elt_accessor = next(Iter(li))
    first_elt_accessor = first_elt_accessor.as_function()

    assert first_elt_accessor([True, False, False])
    assert not first_elt_accessor([False, True])


def test_evaluator_iterable_iterator_and_comparison():
    """ Iterable + Iterator + Comparable : A complex case where the evaluator is `next(Iter(li)) > 0` """

    li = InputVar(list)

    first_elt_test = (next(Iter(li)) > 0) | _
    # first_elt_test = first_elt_test.as_function()

    assert first_elt_test([1, 0, 0])
    assert not first_elt_test([0, 0, 0])


def test_evaluator_comprehension():
    """ List Comprehension : tests that `[i for i in li]` is forbidden and raises the appropriate exception """

    li = InputVar(list)

    with pytest.raises(NotImplementedError):
        a = [i for i in li]


def test_evaluator_iterable_any():
    """ Iterable + any operator: Checks that the any operator  raises an exception but that the Any replacement function
    works """

    li = InputVar(list)

    with pytest.raises(NotImplementedError):
        any(li) | _

    any_is_true = Any(li) | _
    assert any_is_true([False, True, False])
    assert not any_is_true([False, False, False])


def test_evaluator_iterable_all():
    """ Iterable + all operator: Checks that the all operator  raises an exception but that the All replacement function
    works """

    li = InputVar(list)

    with pytest.raises(NotImplementedError):
        all(li) | _

    all_is_true = All(li) | _
    assert all_is_true([True, True, True])
    assert not all_is_true([False, True, False])


# Representable Object: .__repr__, .__str__, .__bytes__, .__format__, __sizeof__
def test_evaluator_repr():
    """ Representable Object : tests that repr() raises the correct error message and that the equivalent Repr()
    works """

    s = InputVar(str)

    # the repr operator cannot be overloaded
    with pytest.raises(NotImplementedError):
        repr(s)

    # so we provide this equivalent
    reasonable_string = Repr(s)
    reasonable_string = reasonable_string.as_function()

    assert reasonable_string('r') == "'r'"  # repr adds some quotes


def test_evaluator_complex_1():
    """ A complex case with a combination of Repr, Len, and comparisons """

    s = InputVar(str)

    reasonable_string = Repr((2 <= Len(s)) & (Len(s) < 3))
    reasonable_string = reasonable_string.as_function()

    assert reasonable_string('r') == 'False'


def test_evaluator_str():
    """ Representable Object : tests that str() raises the correct error message and that the equivalent Str() works """

    s = InputVar(str)

    # the str operator cannot be overloaded
    with pytest.raises(NotImplementedError):
        str(s)

    # so we provide this equivalent
    reasonable_string = Str(s)
    reasonable_string = reasonable_string.as_function()

    assert reasonable_string(1) == '1'


def test_evaluator_bytes():
    """ Representable Object : tests that bytes() raises the correct error message and that the equivalent Bytes()
    works """

    s = InputVar(str)

    # the str operator cannot be overloaded
    with pytest.raises(NotImplementedError):
        bytes(s)

    # so we provide this equivalent
    reasonable_string = Bytes(s)
    reasonable_string = reasonable_string.as_function()

    assert reasonable_string(1) == bytes(1)


def test_evaluator_sizeof():
    """ Object : tests that sys.getsizeof() raises the correct error message and that the equivalent Getsizeof()
    works """

    s = InputVar(str)

    # the str operator cannot be overloaded
    with pytest.raises(NotImplementedError):
        sys.getsizeof(s)

    # so we provide this equivalent
    reasonable_string = Getsizeof(s)
    reasonable_string = reasonable_string.as_function()

    assert reasonable_string('r') == sys.getsizeof('r')


# Comparable Objects: .__lt__, .__le__, .__eq__, .__ne__, .__gt__, .__ge__
def test_evaluator_comparable():
    """ Comparable Object : tests that lt, le, eq, ne, gt, and ge are correctly supported """

    x = InputVar(float)

    is_big = (x > 4.5) | _
    # is_big = is_big.as_function()

    assert is_big(5.2)
    assert not is_big(-1.1)

    is_very_special = ((3.2 <= x) & (x < 4.5) & (x != 4)) | (x == 2) | _
    # is_very_special = is_very_special.as_function()

    assert is_very_special(2)
    assert is_very_special(3.4)
    assert not is_very_special(-1.1)
    assert not is_very_special(4)


# Hashable Object: .__hash__
def test_evaluator_hashable():
    """ Hashable Object : tests that hash() raises the correct error message and that the equivalent Hash() works """

    x = InputVar(float)

    with pytest.raises(NotImplementedError):
        hash(x)

    h = Hash(x)
    h = h.as_function()

    assert h(5.2) == hash(5.2)
    assert h('nkl,m;@\'') == hash('nkl,m;@\'')


# Truth-testable Object: .__bool__ >> Bool
def test_evaluator_truth_testable():
    """ Truth-Testable Object : tests that bool() raises the correct error message and that the equivalent Bool()
    works. """

    x = InputVar(float)

    with pytest.raises(NotImplementedError):
        bool(x)

    h = Bool(x)
    h = h.as_function()

    assert h(5.2)
    assert not h(0)


def test_evaluator_truth_testable_not():
    """ Truth-Testable Object : tests that not x raises the correct error message and that the equivalent x.nnot()
    works. """

    x = InputVar(float)

    with pytest.raises(NotImplementedError):
        not x

    h = Not(x)
    h = h.as_function()

    assert h(0)
    assert not h(5.2)

# Object: .__getattr__
def test_evaluator_attribute():
    """ Object: Tests that obj.foo_field works """

    o = InputVar(object)
    field_accessor = o.foo_field
    field_accessor = field_accessor.as_function()

    class Foo:
        pass

    f = Foo()
    f.foo_field = 2
    assert field_accessor(f) == 2

    g = Foo()
    with pytest.raises(AttributeError):
        field_accessor(g)  # AttributeError: 'Foo' object has no attribute 'foo_field'


def test_evaluator_nonexistent_attribute_2():
    """ Object: Tests that a valid evaluator accessing a nonexistent attribute will behave as expected and raise the
    appropriate exception when evaluated """

    li = InputVar(list)
    first_elt_test = li.toto()
    first_elt_test = first_elt_test.as_function()

    with pytest.raises(AttributeError):
        first_elt_test([1, 0, 0])  # AttributeError: 'list_iterator' object has no attribute 'next'


# # Class
# # .__instancecheck__, .__subclasscheck__
# def test_is_instance_is_subclass():
#     """ Object: Tests that isinstance and issubclass work """
#
#     o = InputVar(object)
#     #
#     int_instance_tester = isinstance(o, int)
#     int_instance_tester = int_instance_tester.as_function()
#
#     assert int_instance_tester(1)
#     assert int_instance_tester(True)
#     assert not int_instance_tester(1.1)
#
#     t = InputVar(type)
#     int_subclass_tester = issubclass(t, int)
#     int_subclass_tester = int_subclass_tester.as_function()
#
#     assert int_subclass_tester(bool)
#     assert not int_subclass_tester(str)
#
#     class Foo:
#         pass
#
#     foo_instance_tester = isinstance(o, Foo)
#     foo_instance_tester = foo_instance_tester.as_function()
#     foo_subclass_tester = issubclass(t, Foo)
#     foo_subclass_tester = foo_subclass_tester.as_function()
#
#     f = Foo()
#     assert foo_instance_tester(f)
#
#     class Bar(Foo):
#         pass
#
#     assert foo_subclass_tester(Bar)


# Container .__contains__
def test_evaluator_container():
    """ Container Object : tests that `1 in x` raises the correct error message and that the equivalent x.contains()
    works """

    x = InputVar(list)

    with pytest.raises(NotImplementedError):
        is_one_in = 1 in x

    is_one_in = x.contains(1)
    is_one_in = is_one_in.as_function()

    assert is_one_in([0, 1, 2])
    assert not is_one_in([0, 0, 0])


# Sized Container .__len__,  >> Len
def test_evaluator_sized():
    """ Sized Container Object: tests that len() raises the appropriate error but that the equivalent Len() works """

    s = InputVar(str)

    with pytest.raises(NotImplementedError):
        len(s)

    string_length = Len(s)
    string_length = string_length.as_function()

    assert string_length('tho') == 3


def test_evaluator_sized_compared():
    """ Tests that Len(s) > 2 works as well as (2 <= Len(s)) & (Len(s) < 3)"""

    s = InputVar(str)

    big_string = Len(s) > 2
    big_string = big_string.as_function()

    assert big_string('tho')
    assert not big_string('r')

    reasonable_string = (2 <= Len(s)) & (Len(s) < 3) | _
    # reasonable_string = reasonable_string.as_function()

    assert reasonable_string('th')
    assert not reasonable_string('r')
    assert not reasonable_string('rats')


# Iterable Container : see Iterable


# Reversible Container .__reversed__,
def test_evaluator_reversible():
    """ Reversible Container Object : tests that `reversed(x)` works """

    x = InputVar(list)

    reversed_x = reversed(x)
    reversed_x = reversed_x.as_function()

    assert list(reversed_x([0, 1, 2])) == [2, 1, 0]


# Subscriptable / Mapping Container .__getitem__, .__missing__,
def test_evaluator_mapping():
    """ Mapping Container Object : tests that `x[i]` works"""

    x = InputVar(dict)

    item_i_selector = x['i']
    item_i_selector = item_i_selector.as_function()

    assert item_i_selector(dict(a=1, i=2)) == 2

    # test the `missing` behaviour
    class Custom(dict):
        def __missing__(self, key):
            return 0

    c = Custom(a=1)
    assert c['i'] == 0
    assert item_i_selector(c) == 0


# Numeric types
#  .__add__, .__radd__, .__sub__, .__rsub__, .__mul__, .__rmul__, .__truediv__, .__rtruediv__,
# .__mod__, .__rmod__, .__divmod__, .__rdivmod__, .__pow__, .__rpow__
# .__matmul__, .__floordiv__, .__rfloordiv__
# .__lshift__, .__rshift__, __rlshift__, __rrshift__
# .__neg__, .__pos__, .__abs__, .__invert__
def test_evaluator_numeric():
    """ Numeric-like Object : tests that +,-,*,/,%,divmod(),pow(),**,@,//,<<,>>,-,+,abs,~ work """

    x = InputVar(int)

    add_one = x + 1 |_
    assert add_one(1) == 2

    remove_one = x - 1 | _
    assert remove_one(1) == 0

    times_two = x * 2 | _
    assert times_two(1) == 2

    div_two = x / 2 | _
    assert div_two(1) == 0.5

    neg = x % 2 | _
    assert neg(3) == 1

    pos = divmod(x, 3) | _
    assert pos(16) == (5, 1)

    pow_two = x ** 2 | _
    assert pow_two(2) == 4

    pow_two = pow(x, 2) | _
    assert pow_two(2) == 4

    # TODO matmul : @...

    floor_div_two = x // 2 | _
    assert floor_div_two(1) == 0

    lshift_ = 256 << x | _
    assert lshift_(1) == 512

    rshift_ = 256 >> x | _
    assert rshift_(1) == 128

    neg = -x | _
    assert neg(3) == -3

    pos = +x | _
    assert pos(-16) == -16

    abs_ = abs(x) | _
    assert abs_(-22) == 22

    inv = ~x | _
    assert inv(2) == -3


# Type conversion
# __int__,  __long__, __float__, __complex__, __oct__, __hex__, __index__, __trunc__, __coerce__
def test_evaluator_int_convertible():
    """ Int convertible Object : tests that `int` raises the appropriate exception and that equivalent Int() works """

    s = InputVar(float)

    with pytest.raises(NotImplementedError):
        int(s)

    to_int = Int(s)
    to_int = to_int.as_function()

    assert to_int(5.5) == 5


def test_evaluator_long_convertible():
    """ Long convertible Object : tests that `long` raises the appropriate exception and that equivalent Long()
    works """

    s = InputVar(float)

    # with pytest.raises(NotImplementedError):
    #     int(s)

    to_long = long(s)
    to_long = to_long.as_function()

    assert to_long(5.5) == 5


def test_evaluator_float_convertible():
    """ Float convertible Object : tests that `float` raises the appropriate exception and that equivalent Float()
    works """

    s = InputVar(int)

    with pytest.raises(NotImplementedError):
        float(s)

    to_float = Float(s)
    to_float = to_float.as_function()

    assert to_float(5) == 5.0


def test_evaluator_complex_convertible():
    """ Complex convertible Object : tests that `complex` raises the appropriate exception and that equivalent
    Complex_() works """

    s = InputVar(int)

    with pytest.raises(NotImplementedError):
        complex(s)

    to_cpx = Complex_(s)
    to_cpx = to_cpx.as_function()

    assert to_cpx(5) == 5+0j
    assert to_cpx('5+1j') == 5+1j


def test_evaluator_oct_convertible():
    """ oct convertible Object : tests that `oct` raises the appropriate exception and that equivalent Oct()
    works """

    s = InputVar(int)

    with pytest.raises(NotImplementedError):
        oct(s)

    to_octal = Oct(s)
    to_octal = to_octal.as_function()

    assert to_octal(55) == '0o67'


def test_evaluator_index_slice():
    """ Object is used as an index : tests that `__index__` raises the appropriate exception and that equivalent Get()
    works, and also that Slice works and not slice() """

    l = [0,1,2,3,4]
    x = InputVar(int)

    with pytest.raises(NotImplementedError):
        l[x]

    get_view = Get(l,x)
    get_view = get_view.as_function()

    assert get_view(3) == 3

    with pytest.raises(NotImplementedError):
        l[1:x]

    slice_view = Get(l, Slice(1, x))
    slice_view = slice_view.as_function()

    assert slice_view(3) == [1,2]


def test_new_operators():
    s = InputVar(str)
    x = InputVar(int)

    @validate(name=(0 < Len(s)) & (Len(s) <= 10),
              age=(x > 0) & (Int(x) == x))
    def hello_world(name: str, age: float):
        print('Hello, ' + name + ' your age is ' + str(age))

    hello_world('john', 20)


def test_normal_function_first():
    """ Tests that it works when the first function is not a function converted to valid8 """

    x = InputVar(Real)

    @validate(number=(sin > x) & (x > x ** 2))
    def hard_validation(number: float):
        print('Your input number ' + str(number) + ' is correct, congrats !')

    hard_validation(0.01)


# def test_normal_function_first_second():
#     """ Tests that it works when the first and second functions are not functions converted to valid8 """
#
#     x = InputVar(Real)
#
#     @validate(number=sin >= sin > x > x ** 2)
#     def hard_validation(number: float):
#         print('Your input number ' + str(number) + ' is correct, congrats !')
#
#     hard_validation(0.01)


def test_retrofit():
    """ Tests that a retrofited function behaves in a standard way """
    pass
