# Validation functions - basics

Below you will learn what is required to integrate any user-defined or 3d party function, and how to improve existing functions.

## 1. Accepted validation functions

There seem to be two main styles out there when it comes to writing validation functions: 

 * *boolean testers* such as `isfinite` : they return `True` in case of success and `False` in case of failure, and therefore do not provide any details about the failure when they fail. Sometimes they continue to raise exceptions on edge cases (`isfinite(None)`, `isfinite(1+1j)`).
 
 * *failure raisers* such as `check_uniform_sampling` or `assert_series_equal`: they do not return anything in case of success, but raise exceptions with details in case of failure.

In order to be as open as possible, the definition of accepted functions in `valid8` is very large. Is considered a 'valid' validation function any callable that:

 * takes a single argument as input
 * returns `True` or `None` in case of success

That's the two only requirements. That means that base validation functions **may fail the way they like**: returning `False` or something else, raising `Exception`s.

### Name used in error messages

In validation error messages, the name of the function that will be displayed is obtained from the validation callable `v_callable` with the following formula:

```python
name = v_callable.__name__ if hasattr(v_callable, '__name__') else str(v_callable)
```

## 2. Creating *failure raisers* for better user experience

As explained above, nothing else than returning `True` or `None` in case of success is required by `valid8`. 

However, you might wish to use *failure raisers* rather than *boolean testers* because in case of failure they can provide **many useful details in the raised exception**. This is how you can do it:


### a - Writing your own

You may wish to create a custom validation function that directly raises an instance or subclass of the `valid8.ValidationFailure` class: it provides a simple way to define help messages as class members, with a templating mechanism. All functions in the built-in library are done that way.

For example this is the code for the `non_empty` validation function:

```python
from valid8 import ValidationFailure

class Empty(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by non_empty """
    help_msg = 'len(x) > 0 does not hold for x={wrong_value}'


def non_empty(x):
    """
    'non empty' validation function. Raises a `Empty` error in case of failure.
    """
    if len(x) > 0:
        return True
    else:
        raise Empty(wrong_value=x)
```

You can find some inspiration [here](https://github.com/smarie/python-valid8/blob/master/valid8/validation_lib/collections.py).

Sometimes it might be easier for a quick test, to add the "failure raiser" facet to one of your existing functions. For this you can use the `@as_failure_raiser` decorator:

```python
from valid8 import as_failure_raiser

@as_failure_raiser(help_msg='x should be strictly positive')
def is_strictly_positive(x):
    return x > 0
```


### b - Enriching an existing function

An alternative is to transform existing functions into failure raisers by adding help messages or custom `ValidationFailure` subtypes. Indeed, often the validation functions that you want to reuse are designed to be efficient, therefore their outcome in case of failure might be cryptic for the end user.

#### on the fly in the entry point

Most `valid8` entry points and composition operators support the *simple validation function definition syntax* explained [here](c_simple_syntax.md). Thanks to this syntax, you can transform existing functions into failure raisers on the fly, when you use them. 

For example you can add a custom message to `isfinite`:

```python
>>> from valid8 import validate
>>> from math import inf, isfinite
>>> x = inf
>>> validate('x', x, custom={'x is not finite': isfinite})

valid8.entry_points.ValidationError[ValueError]: \
  Error validating [x=inf]. InvalidValue: x is not finite. \ 
    Function [isfinite] returned [False] for value inf.
```

You can also specify a custom failure class that should be raised:

```python
>>> from valid8 import validate, ValidationFailure
>>> from math import inf, isfinite
>>> class NotFinite(ValidationFailure):
...     help_msg = "x is not finite"
...
>>> x = inf
>>> validate('x', x, custom={NotFinite: isfinite})

valid8.entry_points.ValidationError[ValueError]: \
  Error validating [x=inf]. NotFinite: x is not finite. \ 
    Function [isfinite] returned [False] for value inf.
```

#### permanently for reuse

If you wish to reuse a validation function in many places, it might be simpler to convert it to a failure raiser once.
You can transform an existing validation function in a failure raiser with `failure_raiser()`:

```python
from valid8 import failure_raiser
from math import isfinite

# custom message only
new_func = failure_raiser(isfinite, help_msg='x is not finite')

# custom failure type
new_func = failure_raiser(isfinite, failure_type=NotFinite)
```

You can do the same with the `@as_failure_raiser` decorator already presented above.


### c - Docstring

#### failure_raiser

```python
def failure_raiser(validation_callable,   # type: ValidationCallableOrLambda
                   help_msg=None,         # type: str
                   failure_type=None,     # type: Type[ValidationFailed]
                  **kw_context_args):
    # type: (...) -> ValidationCallable
```

Wraps the provided validation function so that in case of failure it raises the given `failure_type` or a
`WrappingFailure`ValidationFailed help message.

mini-lambda functions are automatically transformed to functions.

See `help(failure_raiser)`

#### @as_failure_raiser

```python
def as_failure_raiser(failure_type=None,     # type: Type[ValidationFailure]
                      help_msg=None,         # type: str
                      **kw_context_args):
```

A decorator to define a failure raiser. Same functionality then `failure_raiser`:

```python
from valid8 import as_failure_raiser

@as_failure_raiser(help_msg="x should be smaller than 4")
def is_small_with_details(x):
    return x < 4
```

    >>> is_small_with_details(2)
    >>> is_small_with_details(11)
    Traceback (most recent call last):
    ...
    valid8.base.InvalidValue: x should be smaller than 4. Function [is_small_with_details] returned [False] for
        value 11.
