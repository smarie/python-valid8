from inspect import isfunction
from valid8.tests.readme.examples import test_example1_cases

import pytest

cases = vars(test_example1_cases)

# the initial list of functions
ex1_functions = [f for f in cases.values() if isfunction(f) and f.__module__ == test_example1_cases.__name__
                      and not f.__name__.startswith('test') and f.__name__ != 'isfunction']

for f in ex1_functions:
    f.__doc__ = "Example 1 test with function " + f.__name__

# ----------- the test

ex1_values = [(0, True),
              (100, True),
              ('foo', TypeError),
              (1.0, TypeError),
              (-1, ValueError)]


@pytest.mark.parametrize('x, outcome', ex1_values)
@pytest.mark.parametrize('function', ex1_functions, ids=lambda f: f.__name__)
def test_example_1(x, outcome, function):
    """ Tests that the example 1 provided in the documentation works (positive integer) """

    # if x == 'foo' and function == function_input_mini_lambda:
    #     print('uncomment and put your breakpoint here to debug')

    if outcome is True:
        function(x)
    else:
        with pytest.raises(outcome) as exc_info:
            function(x)
        e = exc_info.value
        print(e)
