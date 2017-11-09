from typing import Callable


class StackableFunctionEvaluator:
    """
    A StackableFunctionEvaluator is a wrapper for a function (self._fun). It can be evaluated on any set of inputs by
    calling the 'evaluate' method. This will execute self._fun() on this set of inputs.

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

    def evaluate(self, *args, **kwargs):
        """
        The method that should be used to evaluate this InputEvaluator for a given input. Indeed, by default the
        InputEvaluator is not callable: if your inputevaluator is x, doing x(0) will not execute the evaluator x on
        input 0, but will instead create a new evaluator x(0), able to perform y(0) for any input y.

        If you wish to 'freeze' an evaluator so that calling it triggers an evaluation, you should use x.as_function()
        or append the magic expression '|_' at the end of your evaluator.

        :param args:
        :param kwargs:
        :return:
        """
        return self._fun(*args, **kwargs)

    def add_unbound_method_to_stack(self, method, *m_args):
        """
        Returns a new StackableFunctionEvaluator whose inner function will be

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

        def evaluate_inner_function_and_apply_object_method(*args, **kwargs):
            # first evaluate the inner function
            res = self.evaluate(*args, **kwargs)
            # then retrieve the (bound) method on the result object, from its name
            object_method = getattr(res, method_name)
            # finally call the method
            return object_method(*m_args)

        # return a new InputEvaluator of the same type than self, with the new function as inner function
        return type(self)(evaluate_inner_function_and_apply_object_method)
