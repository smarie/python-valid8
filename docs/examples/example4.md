## 4- `l` is a list of custom tuples



### (a) Inline - `validate`

It is not possible to use `validate` to check all the tuples inside `l` at once, but it can be used in a `for` loop to validate each tuple. Note that we correctly set the name of each item that is validated, so that users get informative errors:

```python
from valid8 import validate

# first validate the main type
validate('l', l, instance_of=list)

# then validate (and use) the contents
for i, v in enumerate(l):
    # each item is a tuple of size 2
    validate('l[{}]'.format(i),    l[i],    instance_of=tuple, length=2)
    
    # the first element is a float between 0 and 1
    validate('l[{}][0]'.format(i), l[i][0], instance_of=Real, min_value=0, 
             max_value=1)
             
    # the second element is a lowercase string of size 3 
    validate('l[{}][1]'.format(i), l[i][1], instance_of=str, length=3, 
             equals=l[i][1].lower())
    
    # here you can actually USE the current item
```

### (b) Inline - `with validator`

You *can* perform the whole validation at once with `validator` as shown here:

```python
from valid8 import validator, instance_of
with validator('l', l, instance_of=list) as v:
    v.alid = all(
                # each item is a tuple of size 2
                instance_of(item, tuple) and len(item) == 2
                # the first element is a float between 0 and 1
                and instance_of(item[0], Real) and (0 <= item[0] <= 1)
                # the second element is a lowercase string of size 3
                and instance_of(item[1], str) and len(item[1]) == 3 and item[1].islower()
             for item in l)
```

But it might not really make sense if you actually wish to **use** the tuples :). In that case it is much more readable and convenient to write a custom validation function `check_valid_tuple` first. Below is an example in "failure raiser" mode: the function does not return False in case of failure but rather raises more informative errors.

```python
def check_valid_tuple(tup):
    """ custom validation function - here in 'failure raiser' style (returning nothing) """

    # each item is a tuple of size 2
    if not isinstance(tup, tuple):
        raise TypeError('item should be a tuple')
    if len(tup) != 2:
        raise ValueError('tuple length should be 2')

    # the first element is a float between 0 and 1
    if not isinstance(tup[0], Real):
        raise TypeError('first element should be a Real')
    if not (0 <= tup[0] <= 1):
        raise ValueError('first element should be between 0 and 1')
    
    # the second element is a lowercase string of size 3
    if not isinstance(tup[1], str):
        raise TypeError('second element should be a string')
    if not (len(tup[1]) == 3 and tup[1].islower()):
        raise ValueError('second element should be a lowercase string of length 3')
```

We can then use it with a `validation` context manager:

```python
from valid8 import validate, validation

# first validate the main type
validate('l', l, instance_of=list)

# then validate (and use) the contents
for i, v in enumerate(l):
    # each item is a valid tuple
    with validation('l[{}]'.format(i), l[i]):
        check_valid_tuple(l[i])
    
    # here you can actually USE the current item
```

Note that if you choose to use a PEP484 type checker such as [pytypes](https://github.com/Stewori/pytypes), your custom validation function can be much more compact, as the tuple length and tuple elements types are described in the compact PEP484 type hint `Tuple[Real, str]`:

```python
from typing import Tuple
from pytypes import typechecked

@typechecked
def check_valid_tuple(tup: Tuple[Real, str]):
    """ custom validation function - note the PEP484 type hint above """

    # the first element is a float between 0 and 1
    if not (0 <= tup[0] <= 1):
        raise ValueError('first element should be between 0 and 1')
    
    # the second element is a lowercase string of size 3
    if not (len(tup[1]) == 3 and tup[1].islower()):
        raise ValueError('second element should be a lowercase string of length 3')
```

### (c) Decorators - built-in lib

For readability we only show one decorator here, see [this previous example](#c-decorators-built-in-lib) for other decorators and additional comments.

There is no built-in function to check that `l[i][1]` is lowercase yet.
The best we can do is 

```python
from valid8 import validate_arg, instance_of, on_all_, on_each_, has_length, and_, between

@validate_arg('l', instance_of(list), on_all_(
             # each item is a tuple of size 2
              instance_of(tuple), has_length(2),
              on_each_(
                  # the first element is a float between 0 and 1
                  and_(instance_of(Real), between(0, 1)),
                  # the 2d element is a string of len 3 BUT we cannot check lowercase  
                  and_(instance_of(str), has_length(3)),
              )
))
def my_function(l):
    pass
```

Although this proves that the provided built-in library can tackle complex cases, it also shows the limits of performing all validation directly in the decorator. In this case it is much more readable to create a custom function `is_valid_tuple`, and it allows you to actually check the lowercase part:

```python
def is_valid_tuple(t):
    """ Custom validation function. We could also provide a callable """

    # (a) each item is a tuple of size 2
    # --you can reuse an entire method from the built-in lib when it supports direct calling mode
    instance_of(t, tuple)  
    # --otherwise you can reuse a failure class, there are many
    if len(t) != 2: raise WrongLength(t, ref_length=2)  

    # (b) the first element is a float between 0 and 1
    if not isinstance(t[0], Real): raise HasWrongType(t[0], Real)
    if not (0 <= t[0] <= 1): raise NotInRange(t[0], min_value=0, max_value=1)

    # (c) the second element is a lowercase string of size 3
    instance_of(t[1], str)
    if len(t[1]) != 3: raise WrongLength(t[1], ref_length=3)
    ValidationFailurelure types
    if not t[1].islower():
        raise NotLowerCase(t[1])

class NotLowerCase(ValidationFailurValidationFailurenisms than ValidationError)"""
    help_msg = "Value is not a lowercase string: {wrong_value}"
```

And finally you would use your custom function in the decorator:

```python
@validate_arg('l', instance_of(list), on_all_(is_valid_tuple))
def my_function(l):
    pass
```

### (d) Decorators - mini_lambda

For readability we only show one decorator here, see [this previous example](#c-decorators-built-in-lib) for other decorators and additional comments.

```python
from valid8 import validate_arg, instance_of, on_all_

# just for fun: we create our custom mini_lambda variable named 't'
from mini_lambda import InputVar, Len, Isinstance
t = InputVar('t', tuple)

@validate_arg('l', instance_of(list), on_all_(
    # each item is a tuple of size 2
    instance_of(tuple), Len(t) == 2,
    # the first element is a float between 0 and 1
    Isinstance(t[0], Real), (0 <= t[0]) & (t[0] <= 1),
    # the 2d element is a lowercase string of len 3
    Isinstance(t[1], str), Len(t[1]) == 3, t[1].islower()
))
def my_function(l):
    pass
```