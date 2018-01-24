# Usage examples / recipes

In this page we try to provide real-world examples so that you may find an answer for most common validation tasks, according to your coding style (several are proposed). Feel free to propose some examples through a git issue or pull request!

Note: we deliberately do not use any `help_msg` or `error_type` customization here to focus on the validation core. See [here](./index#customizing-the-validationexception) for details on how to customize these examples.

## 1- `x` is a positive integer

In the examples below, we use `numbers.Integral` rather than `int` so as to support both python primitive `int` and other compliant types such as `numpy` `int`. The same goes for `numbers.Real` and `valid8.Boolean` (yes such an equivalent boolean type is not provided by the stdlib).

```python
from numbers import Integral, Real
from valid8 import Boolean
```

### (a) Inline - validate

```python
from valid8 import validate
validate('x', x, instance_of=Integral, min_value=0)
```

### (b) Inline - with validator

```python
from valid8 import validator
with validator('x', x, instance_of=Integral) as v:
    v.alid = x >= 0
```

### (c) Decorators - built-in lib

We use the built-in `gt` function to check for positiveness here.

```python
from valid8 import validate_arg, validate_out, validate_io, validate_field
from valid8 import instance_of, gt

# function input
@validate_arg('x', instance_of(Integral), gt(0))
def my_function(x):
    pass

# function output
@validate_out(instance_of(Integral), gt(0))
def my_function2():
    return -1

# function input or output (several at a time possible, but no customization)
@validate_io(x=[instance_of(Integral), gt(0)])
def my_function3(x):
    pass

# class fields (init args or descriptors/properties)
@validate_field('x', instance_of(Integral), gt(0))
class Foo:
    def __init__(self, x):
        self.x = x
```

### (d) Decorators - mini-lambda

We use the mini-lambda `x >= 0` function to check for positiveness here.

```python
from mini_lambda import x
from valid8 import validate_arg, validate_out, validate_io, validate_field
from valid8 import instance_of

# function input
@validate_arg('x', instance_of(Integral), x >= 0)
def my_function(x):
    pass

# function output
@validate_out(instance_of(Integral), x >= 0)
def my_function2():
    return -1

# function input or output (several at a time possible, but no customization)
@validate_io(x=[instance_of(Integral), x >= 0])
def my_function(x):
    pass

# class fields (init args or descriptors/properties)
@validate_field('x', instance_of(Integral), x >= 0)
class Foo:
    def __init__(self, x):
        self.x = x
```

## 2- `s` is a lowercase non-empty string

### (a) Inline - validate

```python
from valid8 import validate
validate('s', s, instance_of=str, min_len=1, equals=s.lower())
```

### (b) Inline - with validator

```python
from valid8 import validator
with validator('s', s, instance_of=str) as v:
    v.alid = (len(s) > 0) and (s == s.lower())
```

### (c) Decorators - built-in lib

There is no built-in function to check that `s` is lowercase yet (only its type and length can be checked).

### (d) Decorators - mini-lambda

We use the mini-lambda `s == s.lower()` function to check for positiveness here.

```python
from mini_lambda import s
from valid8 import validate_arg, validate_out, validate_io, validate_field, 
from valid8 import instance_of

# function input
@validate_arg('s', instance_of(str), s == s.lower())
def my_function(s):
    pass

# function output
@validate_out(instance_of(str), s == s.lower())
def my_function2():
    return -1

# function input or output (several at a time possible, but no customization)
@validate_io(s=[instance_of(str), s == s.lower()])
def my_function3(s):
    pass

# class fields (init args or descriptors/properties)
@validate_field('s', instance_of(str), s == s.lower())
class Foo:
    def __init__(self, s):
        self.s = s
```


## 3- `l` is a list of specific tuples...

...where each tuple contains a float between 0 and 1 and a trigram (three-letter lowercase string).

### (a) Inline - validate

It is not possible to use `validate` to check the tuples inside `l` directly, but it can be used in a `for` loop to validate each tuple, and we can try to be consistent with the naming used for user-friendly error messages:

```python
from valid8 import validate

# first validate the main type
validate('l', l, instance_of=list)

# then validate the contents
for i, v in enumerate(l):
    # each item is a tuple of size 2
    validate('l[{}]'.format(i),    l[i],    instance_of=tuple, length=2)
    # the first element is a float between 0 and 1
    validate('l[{}][0]'.format(i), l[i][0], instance_of=Real, min_value=0, max_value=1)
    # the second element is a lowercase string of size 3 
    validate('l[{}][0]'.format(i), l[i][1], instance_of=str, length=3, equals=l[i][1].lower())
    
    # note that in this loop you would typically actualy USE the contents :) 
```

### (b) Inline - with validator

```python
from valid8 import validator, instance_of
with validator('x', l, instance_of=list) as v:
    v.alid = all(
                # each item is a tuple of size 2
                instance_of(item, tuple) and len(item) == 2
                # the first element is a float between 0 and 1
                and instance_of(item[0], Real) and (0 <= item[0] <= 1)
                # the second element is a lowercase string of size 3
                and instance_of(item[1], str) and len(item[1]) == 3 and item[1] == item[1].lower()
             for item in l)
```

### (c) Decorators - built-in lib

There is no built-in function to check that `l[i][1]` is lowercase yet.
The best we can do is 

```python
from valid8 import validate_arg, instance_of, on_all_, on_each_, has_length, and_, between

@validate_arg('l', instance_of(list), on_all_(
              instance_of(tuple), has_length(2),  # each item is a tuple of size 2
              on_each_(
                  and_(instance_of(Real), between(0, 1)),  # the first element is a float between 0 and 1
                  and_(instance_of(str), has_length(3)),  # the 2d element is a string of len 3 BUT we cannot check lowercase
              )
))
def my_function(l):
    pass
```

Although this proves that the provided built-in library can tackle complex cases, it also shows the limits of performing all validation directly in the decorator. In this case it is much more readable to create a custom function `is_valid_tuple`, and it allows you to actually check the lowercase part:

```python
def is_valid_tuple(t):
    """ Custom validation function. We could also provide a callable """

    # each item is a tuple of size 2
    instance_of(t, tuple)  # reusing an entire method from the built-in lib when it supports direct calling mode
    if len(t) != 2: raise WrongLength(t, ref_length=2)  # reusing a failure class from the built-in lib if the method does not support direct calls

    # the first element is a float between 0 and 1
    if not isinstance(t[0], Real): raise HasWrongType(t[0], Real)  # reusing a failure class from the built-in lib
    if not (0 <= t[0] <= 1): raise NotInRange(t[0], min_value=0, max_value=1)  # reusing a failure class from the built-in lib

    # the second element is a lowercase string of size 3
    instance_of(t[1], str)
    if len(t[1]) != 3: raise WrongLength(t[1], ref_length=3)
    if t[1].lower() != t[1]:
        raise NotLowerCase(t[1])

class NotLowerCase(Failure, ValueError):
    """ Example custom exception class used in custom validation function. `Failure` base class provides some 
    mechanisms to easily build the help message (same mechanisms than ValidationError)"""
    help_msg = "Value is not a lowercase string: {wrong_value}"
```

And finally you would use your custom function in the decorator:

```python
@validate_arg('l', instance_of(list), on_all_(is_valid_tuple))
def my_function(l):
    pass
```


## 4- `df` is a dataframe containing specific columns

TODO


