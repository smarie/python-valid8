from typing import Type, TypeVar, Union
from warnings import warn
import sys

from valid8.mini_lambda_generated import _InputEvaluatorGenerated

T = TypeVar('T')

this_module = sys.modules[__name__]


# it seems that the only way for this to be importable easily is for it to be a class. But we would rather need it to
# be an int if we want no error to be raised in the static code checker
class _:
    """ this special variable is used to 'close' an inputEvaluator """
    pass


class _InputEvaluator(_InputEvaluatorGenerated):
    """
    Represents a lambda function.
    * It can be evaluated by calling the 'evaluate' method. In such case it will apply its inner function (self._fun)
    on the inputs provided.
    * It can be transformed into a normal function (a callable object) with `self.as_function()`.
    * Any other method called on this object will create a new _InputEvaluator instance with that same method
    stacked on top of the current inner function. For example x.foo() will return a new evaluator, that, when
    executed, will call x._fun first and then perform .foo() on its results.

    To perform this last functionality, for most of the magic methods we have some generic implementation rule that we
    apply to generate the super class  _InputEvaluatorGenerated. The methods that remain here have some specificity that
    required manual intervention:
    * List/Set/Tuple/Dict comprehensions: [i for i in x]
    * Chained comparisons: 1 < x < 2
    * not x, any(x), all(x)
    * boolean operations between evaluators: (x > 1) & (x < 2), (x < 1) | (x > 2), (x > 1) ^ (x < 2)
    * indexing (x[y])
    * membership testing (x in y)
    """

    class InputEvaluatorCallableView:
        """ A view on an input evaluator, that is only capable of evaluating but is able to do it in a more friendly
        way: simply calling it with arguments is ok, instead of calling .evaluate() like for the _InputEvaluator.
        Another side effect is that this object is representable: you can call str() on it. You may return to the
        associated evaluator """

        def __init__(self, evaluator):
            """
            Constructor from a mandatory existing _InputEvaluator.
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

        :return: a callable object created by freezing this input evaluator
        """
        return _InputEvaluator.InputEvaluatorCallableView(self)

    # Special case: List comprehensions
    def __iter__(self):
        """ This method is forbidden so that we can detect and prevent usages in list/set/tuple/dict comprehensions """
        raise NotImplementedError('__iter__ cannot be used with an _InputEvaluator. If you meant to use iter() '
                                  'explicitly, please use the replacement method valid8.Iter() provided. Otherwise '
                                  'you probably ended in this exception because there is a list/set/tuple/dict '
                                  'comprehension in your expression, such as [i for i in x]. These are not feasible '
                                  'with InputEvaluators unfortunately.')

    # Special case: Chained comparisons, not, any, all
    def __bool__(self):
        """ This magic method is forbidden because python casts the result before returning """

        # see https://stackoverflow.com/questions/37140933/custom-chained-comparisons
        raise NotImplementedError('__bool__ cannot be used with an _InputEvaluator. Please use '
                                  'the valid8.Bool() method provided instead. If you got this error message but '
                                  'you do not call bool(x) or x.__bool__() in your _InputEvaluator then you probably'
                                  '\n * use a chained comparison such as 0 < x < 1, in such case please consider '
                                  'rewriting it without chained comparisons, such as in (0 < x) & (x < 1). '
                                  '\n * use a short-circuit boolean operator such as and/or instead of their symbolic '
                                  'equivalent &/|. Please change to symbolic operators &/|. See'
                                  ' https://stackoverflow.com/questions/37140933/custom-chained-comparisons for'
                                  'more details'
                                  '\n * use not x, any(x) or all(x). Please use the equivalent Not(x), Any(x) and All(x)'
                                  ' from valid8 or x.nnot() / x.any() / x.all()')

    def __and__(self, other):
        """
        A logical AND between this _InputEvaluator and something else. The other part can either be
        * a scalar
        * a callable
        * an _InputEvaluator

        :param other:
        :return:
        """
        if not callable(other):
            # then the other part has already been evaluated, since this operator is not a short-circuit like the 'and'
            # keyword. This is probably an error from the developer ? Warn him/her
            warn("One of the sides of an '&' operator is not an _InputEvaluator and therefore will always have the same "
                 "value, whatever the input. This is most probably a mistake in the evaluator expression.")
            if not other:
                # the other part is False, there will never be a need to evaluate.
                return False
            else:
                # the other part is True, return a boolean evaluator of self. (The Bool function is created later)
                return getattr(this_module, 'Bool')(self)
        else:
            # create a new _InputEvaluator able to evaluate both sides with short-circuit capability
            def evaluate_both_inner_functions_and_combine(*args, **kwargs):
                # first evaluate self
                left = self.evaluate(*args, **kwargs)
                if not left:
                    # short-circuit: the left part is False, no need to evaluate the right part
                    return False
                else:
                    # evaluate the right part
                    if isinstance(other, _InputEvaluator):
                        right = other.evaluate(*args, **kwargs)
                    else:
                        # standard callable
                        right = other(*args, **kwargs)
                    return bool(right)
            return _InputEvaluator(evaluate_both_inner_functions_and_combine)

    def __or__(self, other):
        """
        A logical OR between this _InputEvaluator and something else. The other part can either be
        * a scalar
        * a callable
        * an _InputEvaluator

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
            warn("One of the sides of an '|' operator is not an _InputEvaluator and therefore will always have the same "
                 "value, whatever the input. This is most probably a mistake in the evaluator expression.")
            if other:
                # the other part is True, there will never be a need to evaluate.
                return True
            else:
                # the other part is False, return a boolean evaluator of self (The Bool function is created later)
                return getattr(this_module, 'Bool')(self)
        else:
            # create a new _InputEvaluator able to evaluate both sides with short-circuit capability
            def evaluate_both_inner_functions_and_combine(*args, **kwargs):
                # first evaluate self
                left = self.evaluate(*args, **kwargs)
                if left:
                    # short-circuit: the left part is True, no need to evaluate the right part
                    return True
                else:
                    # evaluate the right part
                    if isinstance(other, _InputEvaluator):
                        right = other.evaluate(*args, **kwargs)
                    else:
                        # standard callable
                        right = other(*args, **kwargs)
                    return bool(right)
            return _InputEvaluator(evaluate_both_inner_functions_and_combine)

    def __xor__(self, other):
        """
        A logical XOR between this _InputEvaluator and something else. The other part can either be
        * a scalar
        * a callable
        * an _InputEvaluator

        :param other:
        :return:
        """
        if not callable(other):
            # then the other part has already been evaluated, since this operator is not a short-circuit like the 'or'
            # keyword. This is probably an error from the developer ? Warn him/her
            warn("One of the sides of an '^' operator is not an _InputEvaluator and therefore will always have the same "
                 "value, whatever the input. This is most probably a mistake in the evaluator expression.")
            if other:
                # the other part is True, so this becomes a Not evaluator of self (The Not function is created later)
                return self.nnot()
            else:
                # the other part is False, return a boolean evaluator of self (The Bool function is created later)
                return getattr(this_module, 'Bool')(self)
        else:
            # create a new _InputEvaluator able to evaluate both sides
            def evaluate_both_inner_functions_and_combine(*args, **kwargs):
                # first evaluate self
                left = self.evaluate(*args, **kwargs)
                # evaluate the right part
                if isinstance(other, _InputEvaluator):
                    right = other.evaluate(*args, **kwargs)
                else:
                    # standard callable
                    right = other(*args, **kwargs)
                return left ^ right

            return _InputEvaluator(evaluate_both_inner_functions_and_combine)

    def nnot(self):
        """ Returns a new _InputEvaluator performing 'not x' on the result of this evaluator's evaluation """
        def __not(x):
            return not x
        return self.add_unbound_method_to_stack(__not)

    def any(self):
        """ Returns a new _InputEvaluator performing 'any(x)' on the result of this evaluator's evaluation """
        return self.add_unbound_method_to_stack(any)

    def all(self):
        """ Returns a new _InputEvaluator performing 'all(x)' on the result of this evaluator's evaluation """
        return self.add_unbound_method_to_stack(all)

    # Special case: indexing
    def __index__(self):
        """ This magic method is forbidden because python casts the result before returning """
        raise NotImplementedError('It is not currently possible to use an _InputEvaluator as an index, e.g.'
                                  'o[x], where x is the input variable. Instead, please use the equivalent operator '
                                  'provided valid8.Get(o, x)')

    # Special case: membership testing
    def __contains__(self, item):
        """ This magic method is forbidden because python casts the result before returning """
        raise NotImplementedError('membership operators in/ not in cannot be used with an _InputEvaluator because '
                                  'python casts the result as a bool. Therefore this __contains__ method is forbidden. An '
                                  'alternate x.contains() method is provided to replace it')

    def contains(self, item):
        """ Returns a new _InputEvaluator performing '__contains__' on the result of this evaluator's evaluation """
        # return self.add_bound_method_to_stack('__contains__', item)
        def item_in(x):
            return item in x
        return self.add_unbound_method_to_stack(item_in)

    # Not-so-special case but the code generator does not support it right now (magic method needs to be mapped to the
    # non-magic one)
    def __getattr__(self, item):
        """ Returns a new _InputEvaluator performing 'getattr(x, item)' on the result of this evaluator's evaluation """
        return self.add_unbound_method_to_stack(getattr, item)


def Not(evaluator: _InputEvaluator):
    """
    Equivalent of 'not x' for an _InputEvaluator.

    :param evaluator:
    :return:
    """
    return evaluator.nnot()


def Any(evaluator: _InputEvaluator):
    """
    Equivalent of 'any(x)' for an _InputEvaluator.

    :param evaluator:
    :return:
    """
    return evaluator.any()


def All(evaluator: _InputEvaluator):
    """
    Equivalent of 'all(x)' for an _InputEvaluator.

    :param evaluator:
    :return:
    """
    return evaluator.all()


def Get(container, evaluator: _InputEvaluator):
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
        elif isinstance(evaluator, _InputEvaluator):
            return evaluator.add_unbound_method_to_stack(container.__getitem__)
        else:
            raise NotImplementedError('TODO')
    else:
        if isinstance(container, _InputEvaluator):
            raise NotImplementedError('TODO')
        else:
            raise NotImplementedError('TODO')


def Slice(a, b=None, c=None):
    """
    Equivalent of 'slice()' for InputEvaluators.

    :param evaluator:
    :return:
    """
    # TODO this is suboptimal since the if is done at every call, but otherwise that's 8 cases to handle..
    if callable(a):
        if isinstance(a, _InputEvaluator):
            a_case = 2
        else:
            a_case = 1
    else:
        a_case = 0

    if callable(b):
        if isinstance(b, _InputEvaluator):
            b_case = 2
        else:
            b_case = 1
    else:
        b_case = 0

    if callable(c):
        if isinstance(c, _InputEvaluator):
            c_case = 2
        else:
            c_case = 1
    else:
        c_case = 0

    # create a new _InputEvaluator able to evaluate both sides with short-circuit capability
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

    return _InputEvaluator(evaluate_both_inner_functions_and_combine)


def InputVar(typ: Type[T] = None) -> Union[T, _InputEvaluator]:
    """
    Creates a variable to use in validator expression. The optional `typ` argument may be used to get a variable with
    appropriate syntactic completion from your IDE, but is not used for anything else.

    :param typ:
    :return:
    """
    return _InputEvaluator()


# Useful input variables
s = InputVar(str)
x = InputVar(int)
