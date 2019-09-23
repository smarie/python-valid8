import pytest
from functools import partial

from pytest_cases import cases_data, THIS_MODULE, cases_generator

from valid8.base import make_callable


def case_builtin_func():
    return [True], any


def case_builtin_inst_method():
    return "he", "hello".startswith

# TODO
#
# builtin_class_func =  find one ?


def case_user_function():
    def user_func(x):
        return x == 12
    return 12, user_func


def case_partialized_builtin_function():
    return bool, partial(isinstance, True)


def case_partialized_builtin_class_method():
    return "hell", partial(str.startswith, "hello")


def case_partial_user_function_positional():
    def user_func(x, y):
        return x[0:2] == y
    return "he", partial(user_func, "hey")


def case_partial_user_function_keyword():
    def user_func(x, y):
        return x[0:2] == y
    return "hey", partial(user_func, y="he")


def case_partial_user_function_both():
    def user_func(x, y, z):
        return (x[0:2] == y) and not z
    return "he", partial(user_func, "hey", z=False)


def case_partial_user_function_both_defaults():
    def user_func(x, y=2, z=True, o=False):
        return (x[0:2] == y) and not z and not o
    return "he", partial(user_func, "hey", z=False)


def case_partial_user_function_both_defaults2():
    def user_func(x=12, y=2, z=True, o=False):
        return (x[0:2] == y) and not z and not o
    return "he", partial(user_func, "hey", z=False)


@cases_generator("user_{typ}_method_newstyle={new_style}",
                 typ=['inst', 'unbound_inst', 'class', 'unbound_class', 'static'],
                 new_style=[False, True])
def case_user_inst_method(typ, new_style):
    if new_style:
        class Foo(object):
            def inst_method(self, x):
                return x == 12

            def unbnd_inst_method(self):
                return self == 12

            def __eq__(self, other):
                return other == 12

            @classmethod
            def class_method(cls, x):
                return x == 12

            @classmethod
            def unbnd_class_method(cls):
                return cls is Foo

            @staticmethod
            def static_method(x):
                return x == 12
    else:
        class Foo:
            def inst_method(self, x):
                return x == 12

            def unbnd_inst_method(self):
                return self == 12

            def __eq__(self, other):
                return other == 12

            @classmethod
            def class_method(cls, x):
                return x == 12

            @classmethod
            def unbnd_class_method(cls):
                return cls is Foo

            @staticmethod
            def static_method(x):
                return x == 12

    if typ == 'inst':
        return 12, Foo().inst_method
    elif typ == 'unbound_inst':
        return Foo(), Foo.unbnd_inst_method
    elif typ == 'class':
        return 12, Foo.class_method
    elif typ == 'unbound_class':
        # from https://stackoverflow.com/questions/14574641/python-get-unbound-class-method
        try:
            from new import instancemethod
            unbndmethod = instancemethod(Foo.unbnd_class_method.im_func, None, Foo.unbnd_class_method.im_class)
            return Foo, unbndmethod
        except ImportError:
            pytest.skip("Unbound class methods are Not supported in this version of python")
    elif typ == 'static':
        return 12, Foo.static_method
    else:
        raise ValueError()


@cases_data(module=THIS_MODULE)
def test_getfullargspec(case_data):
    input, f = case_data.get()

    # make sure the case works
    assert f(input)

    # inspect the signature and create the validator
    callit = make_callable(f)

    # test the validator
    assert callit(input, ctx_a=0)
