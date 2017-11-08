from copy import copy
from numbers import Real, Integral
from typing import Type, TypeVar, Optional, Callable, Union

from collections import Iterable, Iterator, Generator, Hashable, Container, Sized, Reversible, Mapping, Set
from warnings import warn

import sys

T = TypeVar('T')


this_module = sys.modules[__name__]

# class ValidatorDefinitionException(Exception):
#     """ Raised whenever there is a clear issue with the definition of the validator """
#     pass


# it seems that the only way for this to be importable easily is for it to be a class. But we would rather need it to
# be an int if we want no error to be raised in the static code checker
class _:
    """ this special variable is used to 'close' an inputEvaluator """
    pass


class InputEvaluator:
    """ Represents a validator function. It may be called on any input, it will either return True or raise a
    ValidationError """

    __slots__ = ['_fun']

    def __init__(self, fun: Optional[Callable] = None):
        """
        Constructor with an optional nested validation function. It may be used to retrofit an existing function in
        order to
        * make it natively capable of supporting the native python operators
            * boolean: & (and), | (or), ^ (xor),
            * maths: ** (pow), + (add), - (minus), * (times)
            * comparison: < (lt), <= (le), == (eq), != (ne), > (gt), >= (ge)
            * size: len()
            *
        * give it the capability to raise ValidationError whenever the result is not valid (currently the definition
        of success is a result that is either True or None, see `result_is_success`)

        If no argument is provided, this InputEvaluator will return True when the input truth value is True, and
        raise a ValidationError otherwise.

        :param fun:
        """
        if fun is None:
            # then the inner method will be the identity
            def fun(x):
                return x
        self._fun = fun

    def evaluate(self, *args, **kwargs):
        return self._fun(*args, **kwargs)

    class InputEvaluatorCallableView:
        """ A view on the input evaluator, that is only capable of evaluating but is able to do it in a more friendly
        way: simply calling it with arguments is ok, instead of calling .evaluate() like for the InputEvaluator.
        Another side effect is that this object is representable: you can call str() on it """

        def __init__(self, evaluator):
            """
            Constructor from a mandatory existing InputEvaluator.
            :param evaluator:
            """
            self.evaluator = evaluator

        def __call__(self, *args, **kwargs):
            """
            Calling this object is actually evaluating the inner evaluator with the given arguments.
            So it behaves like a normal function.

            :param args:
            :param kwargs:
            :return:
            """
            return self.evaluator.evaluate(*args, **kwargs)

        def as_evaluator(self):
            """
            Returns the underlying evaluator self.evaluator
            :return:
            """
            return self.evaluator

    def as_function(self):
        """
        freezes this evaluator so that it can be called directly, in other words that calling it actally calls
        'evaluate' instead of creating a new evaluator.
        :return:
        """
        return InputEvaluator.InputEvaluatorCallableView(self)

    # def __call__(self, *inputs):
    #     """
    #     This is executed when the function is called to validate some input. It simply calls the inner function on the
    #     input. It is also executed when the user uses
    #
    #     :param input:
    #     :return:
    #     """
    #     # NO: THIS IS NOT THE ROLE OF THIS CLASS to provide a validation logic, see Core instead
    #     # if self._fun is None:
    #     #     # use truth value test
    #     #     if not input:
    #     #         raise ValidationError.create('truth_test', 'bool(x) == True', input)
    #     # else:
    #     # use inner function
    #     if len(inputs) == 1:
    #         return self._fun(inputs[0])
    #     else:
    #         raise ValidatorDefinitionException('InputEvaluator called without argument. If this is '
    #                                            'happening at InputEvaluator definition time, you probably need to '
    #                                            'remove the parenthesis')

    def __iter__(self):
        """
        This method is forbidden so that we can detect and prevent usages in list/set/tuple/dict comprehensions.
        :return:
        """
        raise NotImplementedError('__iter__ cannot be used with an InputEvaluator. If you meant to use iter() '
                                  'explicitly, please use the replacement method valid8.Iter() provided. Otherwise '
                                  'you probably ended in this exception because there is a list/set/tuple/dict '
                                  'comprehension in your expression, such as [i for i in x]. These are not feasible '
                                  'with InputEvaluators unfortunately.')

    def __getattr__(self, item):
        """
        Implementation of 'get attribute' magic method. As always this creates a new InputEvaluator function for later.
        The function will
         * resolve the rest of the stack by evaluating self on its inputs
         * call getattr on the result

        The reason why we do it manually is that the method to call is getattr, not __getattr__.

        :param self:
        :param args:
        :return:
        """
        # def evaluate_inner_function_and_get_attr(*args, **kwargs):
        #     # first evaluate the inner function
        #     res = self.evaluate(*args, **kwargs)
        #     # then get attribute on the result
        #     return getattr(res, item)
        #
        # return InputEvaluator(evaluate_inner_function_and_get_attr)
        return self._create_wrapper_for_method_call(getattr, item)

    # def _bytes(self):
    #     """
    #     Implementation of '__bytes__' magic method. As always this creates a new InputEvaluator function for later.
    #     The function will
    #      * resolve the rest of the stack by evaluating self on its inputs
    #      * call bytes on the result (and not __bytes__ because it does not always exist - thats why this is
    #      implemented manually)
    #
    #     :param self:
    #     :return:
    #     """
    #     return self._create_wrapper_for_method_call(bytes)

    # def __complex__(self):
    #     raise NotImplementedError('complex() cannot be used with an InputEvaluator because python'
    #                               'casts the result as a complex. Therefore this __complex__ method is forbidden. An '
    #                               'alternate valid8.Complex_() method is provided to replace it')

    # def _complex(self):
    #     """
    #     Implementation of '__complex__' magic method. As always this creates a new InputEvaluator function for later.
    #     The function will
    #      * resolve the rest of the stack by evaluating self on its inputs
    #      * call complex on the result (and not __complex__ because it does not always exist - thats why this is
    #      implemented manually)
    #
    #     :param self:
    #     :return:
    #     """
    #     return self._create_wrapper_for_method_call(complex)

    def __bool__(self):
        """
        Implementation of 'truth value' magic method. As always this creates a function for later.
        The function will
         * resolve the rest of the stack by evaluating self on its inputs
         * call __ on the result

        :param self:
        :param args:
        :return:
        """
        # see https://stackoverflow.com/questions/37140933/custom-chained-comparisons
        raise NotImplementedError('__bool__ cannot be used with an InputEvaluator. Please use '
                                  'the valid8.Bool() method provided instead. If you got this error message '
                                  'but you do not call bool(x) or x.__bool__() in your InputEvaluator then you probably'
                                  '\n * use a chained comparison such as 0 < x < 1, in such case please consider '
                                  'rewriting it without chained comparisons, such as in (0 < x) & (x < 1). '
                                  '\n * use a short-circuit operator such as and/or instead of their symbolic '
                                  'non-short-circuit equivalent &/|. Please change to symbolic operators. See'
                                  ' https://stackoverflow.com/questions/37140933/custom-chained-comparisons for'
                                  'more details')

    def __index__(self):
        """

        :return:
        """
        raise NotImplementedError('It is not currently possible to use an InputEvaluator as an index, e.g.'
                                  'o[x], where x is the input variable. Instead, please use the equivalent operator '
                                  'provided valid8.Get(o, x)')

    def __contains__(self, item):
        """

        :return:
        """
        raise NotImplementedError('membership operators in/ not in cannot be used with an InputEvaluator because python'
                                  'casts the result as a bool. Therefore this __contains__ method is forbidden. An '
                                  'alternate x.contains() method is provided to replace it')

    def contains(self, item):
        """
        An equivalent of __contains__
        :param item:
        :return:
        """
        return self._create_wrapper_for_object_method_call('__contains__', item)

    def _not(self):
        """
        Returns a new InputEvaluator performing 'not x' on the result of this evaluator's evaluation

        :return:
        """
        # def evaluate_inner_function_and_not(*args, **kwargs):
        #     # first evaluate the inner function
        #     res = self.evaluate(*args, **kwargs)
        #     # then not on the result
        #     return not res
        #
        # return InputEvaluator(evaluate_inner_function_and_not)
        def __not(x):
            return not x
        return self._create_wrapper_for_method_call(__not)

    def _any(self):
        """
        Returns a new InputEvaluator performing 'any(x)' on the result of this evaluator's evaluation

        :return:
        """
        # def evaluate_inner_function_and_apply_any(*args, **kwargs):
        #     # first evaluate the inner function
        #     res = self.evaluate(*args, **kwargs)
        #     # then any on the result
        #     return any(res)
        #
        # return InputEvaluator(evaluate_inner_function_and_apply_any)
        return self._create_wrapper_for_method_call(any)

    def _all(self):
        """
        Returns a new InputEvaluator performing 'all(x)' on the result of this evaluator's evaluation

        :return:
        """
        # def evaluate_inner_function_and_apply_all(*args, **kwargs):
        #     # first evaluate the inner function
        #     res = self.evaluate(*args, **kwargs)
        #     # then all on the result
        #     return all(res)
        #
        # return InputEvaluator(evaluate_inner_function_and_apply_all)
        return self._create_wrapper_for_method_call(all)

    # *** boolean operators
    def __and__(self, other):
        """
        A logical AND between this InputEvaluator and something else. The other part can either be
        * a scalar
        * a callable
        * an InputEvaluator

        :param other:
        :return:
        """
        if not callable(other):
            # then the other part has already been evaluated, since this operator is not a short-circuit like the 'and'
            # keyword. This is probably an error from the developer ? Warn him/her
            warn("One of the sides of an '&' operator is not an InputEvaluator and therefore will always have the same "
                 "value, whatever the input. This is most probably a mistake in the evaluator expression.")
            if not other:
                # the other part is False, there will never be a need to evaluate.
                return False
            else:
                # the other part is True, return a boolean evaluator of self. (The Bool function is created later)
                return getattr(this_module, 'Bool')(self)
        else:
            # create a new InputEvaluator able to evaluate both sides with short-circuit capability
            def evaluate_both_inner_functions_and_combine(*args, **kwargs):
                # first evaluate self
                left = self.evaluate(*args, **kwargs)
                if not left:
                    # short-circuit: the left part is False, no need to evaluate the right part
                    return False
                else:
                    # evaluate the right part
                    if isinstance(other, InputEvaluator):
                        right = other.evaluate(*args, **kwargs)
                    else:
                        # standard callable
                        right = other(*args, **kwargs)
                    return bool(right)
            return InputEvaluator(evaluate_both_inner_functions_and_combine)

    def __or__(self, other):
        """
        A logical OR between this InputEvaluator and something else. The other part can either be
        * a scalar
        * a callable
        * an InputEvaluator

        A special operation can be performed by doing '| _'. This will 'close' the inputevaluator and return a callable
        view of it

        :param other:
        :return:
        """
        if other is _:
            # special character: close and return
            return self.as_function()

        elif not callable(other):
            # then the other part has already been evaluated, since this operator is not a short-circuit like the 'or'
            # keyword. This is probably an error from the developer ? Warn him/her
            warn("One of the sides of an '|' operator is not an InputEvaluator and therefore will always have the same "
                 "value, whatever the input. This is most probably a mistake in the evaluator expression.")
            if other:
                # the other part is True, there will never be a need to evaluate.
                return True
            else:
                # the other part is False, return a boolean evaluator of self (The Bool function is created later)
                return getattr(this_module, 'Bool')(self)
        else:
            # create a new InputEvaluator able to evaluate both sides with short-circuit capability
            def evaluate_both_inner_functions_and_combine(*args, **kwargs):
                # first evaluate self
                left = self.evaluate(*args, **kwargs)
                if left:
                    # short-circuit: the left part is True, no need to evaluate the right part
                    return True
                else:
                    # evaluate the right part
                    if isinstance(other, InputEvaluator):
                        right = other.evaluate(*args, **kwargs)
                    else:
                        # standard callable
                        right = other(*args, **kwargs)
                    return bool(right)
            return InputEvaluator(evaluate_both_inner_functions_and_combine)

    def __xor__(self, other):
        """
        A logical XOR between this InputEvaluator and something else. The other part can either be
        * a scalar
        * a callable
        * an InputEvaluator

        :param other:
        :return:
        """
        if not callable(other):
            # then the other part has already been evaluated, since this operator is not a short-circuit like the 'or'
            # keyword. This is probably an error from the developer ? Warn him/her
            warn("One of the sides of an '^' operator is not an InputEvaluator and therefore will always have the same "
                 "value, whatever the input. This is most probably a mistake in the evaluator expression.")
            if other:
                # the other part is True, so this becomes a Not evaluator of self (The Not function is created later)
                return self._not()
            else:
                # the other part is False, return a boolean evaluator of self (The Bool function is created later)
                return getattr(this_module, 'Bool')(self)
        else:
            # create a new InputEvaluator able to evaluate both sides
            def evaluate_both_inner_functions_and_combine(*args, **kwargs):
                # first evaluate self
                left = self.evaluate(*args, **kwargs)
                # evaluate the right part
                if isinstance(other, InputEvaluator):
                    right = other.evaluate(*args, **kwargs)
                else:
                    # standard callable
                    right = other(*args, **kwargs)
                return left ^ right

            return InputEvaluator(evaluate_both_inner_functions_and_combine)

    def _create_wrapper_for_method_call(self, method, *m_args):
        """
        Returns a new InputEvaluator whose inner function will be

            method(self.evaluate(input), *m_args)

        :param method:
        :param m_args: optional args to apply in method calls
        :return:
        """

        def evaluate_inner_function_and_apply_method(*args, **kwargs):
            # first evaluate the inner function
            res = self.evaluate(*args, **kwargs)
            # then call the method
            return method(res, *m_args)

        return InputEvaluator(evaluate_inner_function_and_apply_method)

    def _create_wrapper_for_object_method_call(self, method_name, *m_args):
        """
        Returns a new InputEvaluator whose inner function will be

            self.evaluate(inputs).method_name()

        :param method_name:
        :param m_args: optional args to apply in method calls
        :return:
        """
        def evaluate_inner_function_and_apply_object_method(*args, **kwargs):
            # first evaluate the inner function
            res = self.evaluate(*args, **kwargs)
            # then retrieve the (bound) method on the result object, from its name
            object_method = getattr(res, method_name)
            # finally call the method
            return object_method(*m_args)

        return InputEvaluator(evaluate_inner_function_and_apply_object_method)

    @classmethod
    def add_magic_method(cls, magic_method_name: str):
        """
        Helper method to create a magic method with the given name, for example __getitem__(i), and add it to the class

        :param magic_method_name:
        :return:
        """

        # first define the new method
        def __magic_method__(self, *args):
            """
            Generic implementation of -any- magic method on an InputEvaluator.
            For example len(x), x >= 2, etc. when x is an InputEvaluator.

            The principle is that any such operation on an InputEvaluator should return a new InputEvaluator.
            The inner function of this new InputEvaluator is a function with two steps
            * (a) execute inner function
            * (b) apply magic method on result

            Therefore InputEvaluator 'len(x) > 2' decomposes into
            * x is a InputEvaluator with no inner function. It is the identity function, i.e. x(2) returns 2
            * x[2] returns a new InputEvaluator with inner function (a) execute evaluator x ; (b) call __getitem__(2)
            on its results.
            * x[2] > 4 returns a new InputEvaluator with inner function (a) execute evaluator x[2] ; (b)
            call __gt__(4) on its results.

            (x[2] > 4)([0,0,0]) will return False, while (x[2] > 4)([0, 0, 5]) will return True

            :param self:
            :param args:
            :return:
            """
            # this is the magic method `magic_method_name`, called with args *args.
            # it returns a new InputEvaluator that, when called later on, will apply the magic method on its inputs
            return self._create_wrapper_for_object_method_call(magic_method_name, *args)

        __magic_method__.__name__ = magic_method_name
        __magic_method__.__qualname__ = InputEvaluator.__name__ + '.' + magic_method_name

        # add the method to the class
        setattr(cls, name, __magic_method__)


def __get_all_magic_methods(*classes):
    """
    Helper method to return all magic methods in a given type
    :param classes:
    :return:
    """
    return {name for clazz in classes for name in dir(clazz) if name.startswith('__')}


def add_module_method_and_local_exception(module_method_name: str, magic_method_name: str, method_to_call):
    """
    Helper method for cases where a magic method cannot be overloaded in InputEvaluator because python does not
    tolerate that the return type is an InputEvaluator and not a bool, a str, etc.
    In all these cases the best we can do is to provide a module-level equivalent method.

    :param module_method_name:
    :param magic_method_name:
    :param method_to_call: an optional callable to call on the object instead of magic_method_name
    :return:
    """

    # first define the new method
    if method_to_call is None:
        def magic_method(evaluator: InputEvaluator, *args):
            """
            Equivalent of a magic method provided at valid8 module level because the magic method cannot return an
            InputEvaluator. This method does.

            :param evaluator:
            :param args:
            :return:
            """
            # this is the equivalent of the magic method `magic_method_name`, called with args *args.
            # it returns a new InputEvaluator that, when called later on, will apply the magic method on its inputs
            return evaluator._create_wrapper_for_object_method_call(magic_method_name, *args)
    else:
        def magic_method(evaluator: InputEvaluator, *args):
            """
            Equivalent of a magic method provided at valid8 module level because the magic method cannot return an
            InputEvaluator. This method does.

            :param evaluator:
            :param args:
            :return:
            """
            # this is the equivalent of the magic method `magic_method_name`, called with args *args.
            # it returns a new InputEvaluator that, when called later on, will apply the magic method on its inputs
            return evaluator._create_wrapper_for_method_call(method_to_call, *args)

    magic_method.__name__ = module_method_name
    magic_method.__qualname__ = module_method_name  # because this is a top-level method see PEP3155

    # add the method to the module
    setattr(this_module, module_method_name, magic_method)

    # then define the magic method throwing an exception, to add to the class.
    if getattr(InputEvaluator, magic_method_name, 'a') == getattr(object, magic_method_name, 'a'):
        def __magic_method__(self):
            raise NotImplementedError(magic_method_name + ' is not supported by InputEvaluator, since python raises an'
                                      ' error when its output is not directly an object of the type it expects. Since'
                                      ' we return an InputEvaluator Please '
                                      'use the valid8.' + module_method_name + '() method provided instead')

        __magic_method__.__name__ = magic_method_name
        __magic_method__.__qualname__ = InputEvaluator.__name__ + '.' + magic_method_name

        # add the method to the class
        setattr(InputEvaluator, magic_method_name, __magic_method__)
    else:
        warn('Not overriding method ' + magic_method_name + ': already overriden manually')
        # pass


#
method_names_to_override = set()
methods_that_should_not_be_overriden = set()
methods_impossible_to_override = set()

# Base
# .__class__, .__mro__
# .__doc__, .__name__, __module__, .__dict__
methods_that_should_not_be_overriden.update({'__class__', '__mro__', '__doc__', '__name__', '__module__', '__dict__'})

# Iterable
# .__iter__
# method_names_to_override.update(__get_all_magic_methods(Iterable))
# Actually this COULD work but creates infinite loops when a list comprehension is used in the expression [i for i in x]
# so we prefer to raise an exception and tell users that list comprehensions are forbidden
# methods_that_should_not_be_overriden.update({'__iter__'})
methods_impossible_to_override.update({('Iter', '__iter__', None)})

# Iterator and Generator
# .__next__
method_names_to_override.update(__get_all_magic_methods(Iterator, Generator))

# Initializable Object
# .__new__, .__init__, .__del__
methods_that_should_not_be_overriden.update({'__new__', '__init__', '__del__'})

# Representable Object
# .__repr__, .__str__, .__bytes__, .__format__,
# __sizeof__
methods_impossible_to_override.update({('Str', '__str__', None),
                                       ('Repr', '__repr__', None),
                                       ('Bytes', '__bytes__', bytes),
                                       ('Format', '__format__', None),
                                       ('Getsizeof', '__sizeof__', None)})

# Comparable Objects >> we will get them from Set
# .__lt__, .__le__, .__eq__, .__ne__, .__gt__, .__ge__
method_names_to_override.update({'__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__'})

# Hashable Object
# .__hash__
# method_names_to_override.update(__get_all_magic_methods(Hashable))
methods_impossible_to_override.update({('Hash', '__hash__', None)})

# Truth-testable Object
# .__bool__
methods_impossible_to_override.update({('Bool', '__bool__', None)})

# Object = Field container
#  .__getattribute__ (to avoid)
# .__getattr__,.__setattr__, .__delattr__
# .__dir__
# .__slots__
# method_names_to_override.update({'__getattr__'}) >> WE ACTUALLY DO IT MANUALLY
methods_that_should_not_be_overriden.update({'__getattr__', '__getattribute__', '__setattr__', '__delattr__', '__dir__', '__slots__'})

# Object Descriptors
# .__get__ , .__set__, .__delete__, .__set_name__
# method_names_to_override.update({'__get__'})
methods_that_should_not_be_overriden.update({'__get__', '__set__', '__delete__', '__set_name__'})

# Callable
# .__call__
method_names_to_override.update({'__call__'})

# Class
# .__instancecheck__, .__subclasscheck__
# .__init_subclass__
# .__subclasshook__, .__abstractmethods__
#
# PROBLEM: these 2 methods are CLASS methods, carried by the SECOND argument, not the first.
# so isintance(x, int) calls __instancecheck__ on int, not on x !
methods_that_should_not_be_overriden.update({'__instancecheck__', '__subclasscheck__'})
methods_that_should_not_be_overriden.update({'__init_subclass__', '__subclasshook__', '__abstractmethods__'})

# Container
# .__contains__
# method_names_to_override.update(__get_all_magic_methods(Container))
methods_that_should_not_be_overriden.update({'__contains__'})

# Sized Container
# .__len__, .__length_hint__
methods_impossible_to_override.update({('Len', '__len__', None)})

# Iterable Container : see Iterable
# Reversible Container
# .__reversed__,
method_names_to_override.update(__get_all_magic_methods(Reversible))

# Subscriptable / Mapping Container
# .__getitem__, .__missing__, .__setitem__, .__delitem__,
method_names_to_override.update(__get_all_magic_methods(Mapping))
methods_that_should_not_be_overriden.update({'__setitem__', '__delitem__'})

# Numeric types
#  .__add__, .__radd__, .__sub__, .__rsub__, .__mul__, .__rmul__, .__truediv__, .__rtruediv__,
# .__mod__, .__rmod__, .__divmod__, .__rdivmod__, .__pow__, .__rpow__
# .__matmul__, .__floordiv__, .__rfloordiv__
# .__lshift__, .__rshift__, __rlshift__, __rrshift__
# .__neg__, .__pos__, .__abs__, .__invert__
method_names_to_override.update(__get_all_magic_methods(Integral))
# Boolean types
# .__and__, .__xor__, .__or__, __rand__, __rxor__, __ror__
methods_that_should_not_be_overriden.update({'__and__', '__xor__', '__or__', '__rand__', '__rxor__', '__ror__'})

# Type conversion
# __int__, __long__, __float__, __complex__, __oct__, __hex__, __index__, __trunc__, __coerce__
method_names_to_override.update({'__trunc__', '__coerce__'})
methods_that_should_not_be_overriden.update({'__index__'})
methods_impossible_to_override.update({('Int', '__int__', None),
                                       ('Long', '__long__', None),
                                       ('Float', '__float__', None),
                                       ('Complex_', '__complex__', complex),  # overriden: int does not implement __complex__
                                       ('Oct', '__oct__', oct), # overriden: int does not implement __oct__
                                       ('Hex', '__hex__', hex), # overriden: int does not implement __hex__
                                       # ('Index', '__index__', None)
                                      })

# Pickle
# __reduce__, __reduce_ex__
methods_that_should_not_be_overriden.update({'__reduce__', '__reduce_ex__'})

# do this first so that we can detect method overriden manually
for new_method_name, magic_method_name, method_to_call in methods_impossible_to_override:
    print('Cannot Override ' + magic_method_name + ' because python checks the return type, creating module-level '
          'equivalent function ' + new_method_name + ' instead, calling '
          + (str(method_to_call) if method_to_call else magic_method_name))
    add_module_method_and_local_exception(new_method_name, magic_method_name, method_to_call)

# then add the generated ones
for name in method_names_to_override:
    if name not in methods_that_should_not_be_overriden \
            and name not in [nam[1] for nam in methods_impossible_to_override]:
        print('Overriding ' + name)
        InputEvaluator.add_magic_method(name)


def Slice(a, b=None, c=None):
    """
    Equivalent of 'slice()' for InputEvaluators.

    :param evaluator:
    :return:
    """
    # TODO this is suboptimal since the if is done at every call, but otherwise that's 8 cases to handle..
    if callable(a):
        if isinstance(a, InputEvaluator):
            a_case = 2
        else:
            a_case = 1
    else:
        a_case = 0

    if callable(b):
        if isinstance(b, InputEvaluator):
            b_case = 2
        else:
            b_case = 1
    else:
        b_case = 0

    if callable(c):
        if isinstance(c, InputEvaluator):
            c_case = 2
        else:
            c_case = 1
    else:
        c_case = 0

    # create a new InputEvaluator able to evaluate both sides with short-circuit capability
    def evaluate_both_inner_functions_and_combine(*args, **kwargs):
        # a
        if a_case == 2:
            a_res = a.evaluate(*args, **kwargs)
        elif a_case == 1:
            a_res = a(*args, **kwargs)
        else:
            a_res = a

        # b
        if b_case == 2:
            b_res = b.evaluate(*args, **kwargs)
        elif b_case == 1:
            b_res = b(*args, **kwargs)
        else:
            b_res = b

        # c
        if c_case == 2:
            c_res = c.evaluate(*args, **kwargs)
        elif b_case == 1:
            c_res = c(*args, **kwargs)
        else:
            c_res = c

        return slice(a_res, b_res, c_res)

    return InputEvaluator(evaluate_both_inner_functions_and_combine)


def Not(evaluator: InputEvaluator):
    """
    Equivalent of 'not x' for an InputEvaluator.

    :param evaluator:
    :return:
    """
    return evaluator._not()


def Any(evaluator: InputEvaluator):
    """
    Equivalent of 'any(x)' for an InputEvaluator.

    :param evaluator:
    :return:
    """
    return evaluator._any()


def All(evaluator: InputEvaluator):
    """
    Equivalent of 'all(x)' for an InputEvaluator.

    :param evaluator:
    :return:
    """
    return evaluator._all()


def Get(container, evaluator: InputEvaluator):
    """
    A workaround to implement o[x] where x is an input evaluator.
    Note: to implement o[1:x] or other kind of slicing, you should use explicit Slice() operator:

        Get(o, Slice(1, x))

    This is definitely not a great use case for minilambda :)

    :param container:
    :param evaluator:
    :return:
    """
    if not callable(container):
        if not callable(evaluator):
            raise NotImplementedError('TODO')
        elif isinstance(evaluator, InputEvaluator):
            return evaluator._create_wrapper_for_method_call(container.__getitem__)
        else:
            raise NotImplementedError('TODO')
    else:
        if isinstance(container, InputEvaluator):
            raise NotImplementedError('TODO')
        else:
            raise NotImplementedError('TODO')

# def Bytes(evaluator: InputEvaluator):
#     """
#
#     :param evaluator:
#     :return:
#     """
#     return evaluator._bytes()
#
#
# def Complex_(evaluator: InputEvaluator):
#     """
#
#     :param evaluator:
#     :return:
#     """
#     return evaluator._complex()


# def Iter(evaluator: InputEvaluator):
#     """
#     __iter__ could work directly in InputEvaluator, except when used inside list/set/tuple/dict comprehensions. For this
#     reason we prefer to raise an exception in __iter__ and provide this helper method for explicit iter() calls.
#
#     :param evaluator:
#     :return:
#     """
#     return evaluator._create_wrapper_for_object_method_call('__iter__')


# def Bool(evaluator: InputEvaluator):
#     """
#     Unfortunately __bool__ cannot be fooled with a non-bool output, so this is the equivalent method to get a truth
#     value evaluator.
#
#     :param evaluator:
#     :return:
#     """
#     return evaluator._create_wrapper_for_object_method_call('__bool__')
#
#
# def Str(evaluator: InputEvaluator):
#     """
#     Unfortunately __str__ cannot be fooled with a non-str output, so this is the equivalent method to get a string
#     representation
#
#     :param evaluator:
#     :return:
#     """
#     return evaluator._create_wrapper_for_object_method_call('__str__')
#
#
# def Len(evaluator: InputEvaluator):
#     """
#     Unfortunately len() cannot be fooled with a non-int output, so this is the equivalent method.
#
#     see https://stackoverflow.com/questions/42521449/how-does-python-ensure-the-return-value-of-len-is-an-integer-when-len-is-cal
#     :param evaluator:
#     :return:
#     """
#     return evaluator._create_wrapper_for_object_method_call('__len__')


def InputVar(typ: Optional[Type[T]] = None) -> Union[T, InputEvaluator]:
    """
    Creates a variable to use in validator expression. The optional `typ` argument may be used to get a variable with
    appropriate syntactic completion from your IDE, but is not used for anything else.

    :param typ:
    :return:
    """
    return InputEvaluator()
