from typing import Callable, Any


class StackableFunctionEvaluator:
    """
    A StackableFunctionEvaluator is a wrapper for a function (self._fun) with a SINGLE argument.
    It can be evaluated on any input by calling the 'evaluate' method. This will execute self._fun() on this input.

    A StackableFunctionEvaluator offers the capability to add (stack) a function on top of the inner function. This
    operation does not modify the instance but rather returns a new object. Two versions of this operation are provided:
     * add_unbound_method_to_stack: this would execute the provided method (meth) on the result of the execution of
     self._fun (res) by doing meth(res, *other_args)
     * add_bound_method_to_stack: this would execute the provided method (meth) on the result of the execution of
     self._fun (res) by doing res.meth(*other_args)
    """

    __slots__ = ['_fun']

    def __init__(self, fun: Callable = None):
        """
        Constructor with an optional nested evaluation function. If no argument is provided, the nested evaluation
        function is the identity function with one single parameter x

        :param fun:
        """
        # if no function is provided, then the inner method will be the identity
        if fun is None:
            def fun(x):
                return x
        # remember the evaluation function for later use
        self._fun = fun

    def evaluate(self, arg):
        """
        The method that should be used to evaluate this InputEvaluator for a given input. Indeed, by default the
        InputEvaluator is not callable: if your inputevaluator is x, doing x(0) will not execute the evaluator x on
        input 0, but will instead create a new evaluator x(0), able to perform y(0) for any input y.

        If you wish to 'freeze' an evaluator so that calling it triggers an evaluation, you should use x.as_function()
        (or append the magic expression '|_' at the end of your evaluator, see _InputEvaluator).

        :param arg:
        :return:
        """
        return self._fun(arg)

    def add_unbound_method_to_stack(self, method, *m_args):
        """
        Returns a new StackableFunctionEvaluator whose inner function will be

            method(self.evaluate(input), input, *m_args)

        :param method:
        :param m_args: optional args to apply in method calls
        :return:
        """

        def evaluate_inner_function_and_apply_method(input):
            # first evaluate the inner function
            res = self.evaluate(input)
            # then call the method
            return method(res, *m_args)

        # return a new InputEvaluator of the same type than self, with the new function as inner function
        return type(self)(evaluate_inner_function_and_apply_method)

    def add_bound_method_to_stack(self, method_name, *m_args):
        """
        Returns a new StackableFunctionEvaluator whose inner function will be

            self.evaluate(inputs).method_name(*m_args)

        :param method_name:
        :param m_args: optional args to apply in method calls
        :return:
        """

        def evaluate_inner_function_and_apply_object_method(raw_input):
            # first evaluate the inner function
            res = self.evaluate(raw_input)
            # then retrieve the (bound) method on the result object, from its name
            object_method = getattr(res, method_name)
            # finally call the method
            return object_method(*m_args)

        # return a new InputEvaluator of the same type than self, with the new function as inner function
        return type(self)(evaluate_inner_function_and_apply_object_method)


def evaluate(statement: Any, arg):
    """
    A helper function to evaluate something, whether it is a StackableFunctionEvaluator, a callable, or a non-callable.
    * if that something is not callable, it returns it directly
    * if it is a StackableFunctionEvaluator, it evaluates it on the given input
    * if it is another type of callable, it calls it on the given input.

    :param statement:
    :return:
    """
    if not callable(statement):
        # a non-callable object
        return statement

    elif isinstance(statement, StackableFunctionEvaluator):
        # a StackableFunctionEvaluator
        return statement.evaluate(arg)

    else:
        # a standard callable
        return statement(arg)
