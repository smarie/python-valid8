from inspect import isfunction

import pytest

from valid8.tests.readme.examples import test_example2_cases

# the list of functions
cases = vars(test_example2_cases)

# the initial list of functions
ex2_functions = [f for f in cases.values() if isfunction(f) and f.__module__ == test_example2_cases.__name__
                 and not f.__name__.startswith('test') and f.__name__ != 'isfunction']

for f in ex2_functions:
    f.__doc__ = "Example 2 test with function " + f.__name__

# ----------- the test

ex2_values = [('foo', True),
              ('foo_123', True),
              (1.1, TypeError),
              ('', ValueError),
              ('fOO', ValueError)]


@pytest.mark.parametrize('s, outcome', ex2_values)
@pytest.mark.parametrize('function', ex2_functions, ids=lambda f: f.__name__)
def test_example_2(s, outcome, function):
    """ Tests that the example 2 provided in the documentation works (lowercase non-empty string) """

    # if s == 'foo' and function == function_input_mini_lambda:
    #     print('uncomment and put your breakpoint here to debug')

    if outcome is True:
        function(s)
    else:
        with pytest.raises(outcome) as exc_info:
            function(s)
        e = exc_info.value
        print(e)


ex2_values_regexp = [('foo@bar.com', True),
                     ('a@a@s', ValueError)]


@pytest.mark.parametrize('s, outcome', ex2_values_regexp)
def test_example_2_regexp(s, outcome):
    import re
    from valid8 import validate

    # basic regex to check that there is one @ and a dot in the second part
    EMAIL_REGEX = re.compile('[^@]+@[^@]+\.[^@]+')

    # you can now use 'EMAIL_REGEX.match' as a custom function anywhere
    function = lambda s: validate('s', s, instance_of=str, custom=lambda s: bool(EMAIL_REGEX.match(s)))

    if outcome is True:
        function(s)
    else:
        with pytest.raises(outcome) as exc_info:
            function(s)
        e = exc_info.value
        print(e)
