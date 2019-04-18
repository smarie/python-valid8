from inspect import isfunction

import pytest

from valid8.tests.readme.examples import test_example3_cases
from valid8.tests.helpers.utils import append_all_custom_variants

cases = vars(test_example3_cases)

# the initial list of functions
ex3_functions_init = [f for f in cases.values() if isfunction(f) and f.__module__ == test_example3_cases.__name__
                      and not f.__name__.startswith('test') and not f.__name__.startswith('_')
                      and f.__name__ not in {}
                      and 'is_valid' not in f.__name__ and 'check_valid' not in f.__name__]

# the list of custom functions used by the above
ex3_custom_booleans = [f for f in cases.values() if isfunction(f) and 'is_valid' in f.__name__]
ex3_custom_raisers = [f for f in cases.values() if isfunction(f) and 'check_valid' in f.__name__]

# mixing the two to get the final list (cross-product between the list of functions and the list of custom functions)
ex3_functions = []
for ex3_func in ex3_functions_init:
    if 'custom' not in ex3_func.__name__:
        print('{} does not use custom function'.format(ex3_func.__name__))
        ex3_functions.append(ex3_func)
    else:
        # create as many functions as there are custom functions to use
        # Note: we cannot do it directly here we have to use a proper function, otherwise ex3func gets lost somehow
        append_all_custom_variants(ex3_func, ex3_custom_booleans, ex3_custom_raisers, ex3_functions)


for ex3_func in ex3_functions_init:
    ex3_func.__doc__ = "Example 3 test with function " + ex3_func.__name__

# ----------- the test

ex3_values = [((0.2, 'foo'), True),
              ((1.0, 'abc'), True),
              ((0, 'foo'), True),  # we accept integers
              (1.1, TypeError),  # wrong type (not a tuple)
              ((0.2, 'foo', True), ValueError),  # wrong size (size 3)
              (('1.0', 'foo'), TypeError),  # wrong type ('1.0' is not a float)
              ((1.1, 'foo'), ValueError),  # wrong value (1.1 is not between 0 and 1)
              ((1.0, False), TypeError),  # wrong type (False is not a string)
              ((0.5, 'a'), ValueError),  # wrong value ('a' is not of size 3)
              ((0.5, 'AAA'), ValueError),  # wrong value ('AAA' is not lowercase)
              ]


@pytest.mark.parametrize('t, outcome', ex3_values, ids=str)
@pytest.mark.parametrize('function', ex3_functions, ids=lambda f: f.__name__)
def test_example_3(t, outcome, function):
    """ Tests that the example 3 provided in the documentation works (custom tuple) """

    if 'function_input_mini_' in function.__name__:  # and t == 'foo'
        print('uncomment and put your breakpoint here to debug')

    # known edge cases with PEP484
    if isinstance(t, tuple) and len(t) != 2 and 'pep' in function.__name__:
        # PEP484 type checkers will consider that this is not a ValueError but a TypeError
        if outcome is ValueError:
            outcome = TypeError

    if outcome is True:
        function(t)
    else:
        with pytest.raises(outcome) as exc_info:
            function(t)
        e = exc_info.value
        print(e)
