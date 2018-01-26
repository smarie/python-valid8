# Example 3 - `t` is a custom tuple

For example `t` is a tuple that contains a float between 0 and 1 and a lowercase trigram (three-letter lowercase string).

## 1- Example values to validate

```python
# Valid
t = (0.2, 'foo')
t = (1.0, 'abc')
t = (0, 'foo')  # we accept integers

# Invalid
t = 1.1                 # wrong type (not a tuple)
t = (0.2, 'foo', True)  # wrong size (size 3)
t = ('1.0', 'foo')      # wrong type ('1.0' is not a float)
t = (1.1, 'foo')        # wrong value (1.1 is not between 0 and 1)
t = (1.0, False)        # wrong type (False is not a string)
t = (0.5, 'a')          # wrong value ('a' is not of size 3)
t = (0.5, 'AAA')        # wrong value ('AAA' is not lowercase)
```

## 2- Inline validation

### `validate` + built-ins

`validate` can not perform everything at once without a [custom validation function](#better-custom-function), but you can easily validate each element:

```python
from valid8 import validate
validate('t',    t,    instance_of=tuple, length=2)
validate('t[0]', t[0], instance_of=Real,  min_value=0, max_value=1)
validate('t[1]', t[1], instance_of=str,   length=3, custom=str.islower)
```

Note that we prefer to user `custom=str.islower` to check if a string is lowercase, rather than `equals=s.lower()`, as explained in [previous example 2](./example2).

### `with validator` + built-ins

It is relatively straightforward to validate both `t` and its contents

 * either with a pure "boolean test" approach (where we use `instance_of` instead of `isinstance` so that `valid8` can distinguish between `TypeError` and `ValueError`):

```python
from valid8 import validator, instance_of
with validator('t', t, instance_of=tuple) as v:
    v.alid = len(t) == 2\
             and instance_of(t[0], Real) and (0 <= t[0] <= 1)\
             and instance_of(t[1], str)  and len(t[1]) == 3 and t[1].islower()
```

 * or with a "failure raising" approach, less compact but with more explicit error messages:

```python
from valid8 import validation
with validation('t', t, instance_of=tuple):
    # the tuple should be of length 2
    if len(t) != 2:
        raise ValueError('tuple length should be 2, found ' + str(t))

    # the first element is a float between 0 and 1
    if not isinstance(t[0], Real):
        raise TypeError('first elt should be a Real, found ' + str(t[0]))
    if not (0 <= t[0] <= 1):
        raise ValueError('first elt should be between 0 and 1,found ' + str(t[0]))

    # the second element is a lowercase string of size 3
    if not isinstance(t[1], str):
        raise TypeError('second elt should be a string, found ' + str(t[1]))
    if not (len(t[1]) == 3 and t[1].islower()):
        raise ValueError('second elt should be a lowercase string of length 3,'
                         'found ' + str(t[1]))
```


## 3- Functions/classes validation

### Principles

 * Type can be checked with built-in `instance_of`
 * Length can be checked with built-in `has_length` or mini-lambda `Len(t) == 2` or custom functions
 * There is no built-in function to check that `s` is lowercase yet, but as we saw above we can use the unbound class function `str.islower` or the mini-lambda `s.islower()`.

We will not show all combinations here (please refer to example 1 for all kind of decorators), only a few examples:

### Function input

With pure built-in and stdlib. Note: we have to use `on_each_` to map validation functions to each element of the tuple:

```python
from valid8 import validate_arg, instance_of, has_length, on_each_, and_, between

@validate_arg('t', instance_of(tuple), has_length(2), on_each_(
                  # the first element is a float between 0 and 1
                  and_(instance_of(Real), between(0, 1)),
                  # the 2d element is a lowercase string of len 3
                  and_(instance_of(str), has_length(3), str.islower),
              ))
def my_function(t):
    pass
```

With pure mini-lambda. Note that mini-lambda allows you to directly access the inner elements inside the tuple with traditional indexing: 

```python
from mini_lambda import InputVar, Len
from valid8 import validate_arg, instance_of
from valid8.validation_lib.mini_lambda import Instance_of

# we need a mini_lambda variable named 't'
t = InputVar('t', tuple)


@validate_arg('t', instance_of(tuple), Len(t) == 2,
                   # the first element is a float between 0 and 1
                   Instance_of(t[0], Real), (0 <= t[0]) & (t[0] <= 1),
                   # the 2d element is a lowercase string of len 3
                   Instance_of(t[1], str), Len(t[1]) == 3, t[1].islower()
)
def my_function(t):
    pass
```

Also note that here as in all previous examples we want to use `instance_of` instead of `isinstance` in order to raise the correct `TypeError`. But `instance_of` is a standard function, it is not composable with mini-lambda expressions such as `t[0]`. Therefore we use the mini-lambda version of `instance_of` provided in this package, named `Instance_of`. This allows us to write type tests for sub-elements in the tuple, for example `Instance_of(t[0], Real)`.


### Class fields

In the examples below the class fields are defined as constructor arguments but this also works if they are defined as class descriptors/properties, and is compliant with [autoclass and attrs](valid8_with_other#for-classes)

with pure built-in and stdlib:

```python
from valid8 import validate_field, 
from valid8 import instance_of, has_length, on_each_, and_, between

@validate_field('t', instance_of(tuple), has_length(2), on_each_(
                  # the first element is a float between 0 and 1
                  and_(instance_of(Real), between(0, 1)),
                  # the 2d element is a lowercase string of len 3
                  and_(instance_of(str), has_length(3), str.islower),
              ))
class Foo:
    def __init__(self, t):
        self.t = t
```

or with pure mini-lambda

```python
from mini_lambda import InputVar, Len
from valid8 import validate_field, instance_of
from valid8.validation_lib.mini_lambda import Instance_of

# we need a mini_lambda variable named 't'
t = InputVar('t', tuple)


@validate_field('t', instance_of(tuple), Len(t) == 2,
                   # the first element is a float between 0 and 1
                   Instance_of(t[0], Real), (0 <= t[0]) & (t[0] <= 1),
                   # the 2d element is a lowercase string of len 3
                   Instance_of(t[1], str), Len(t[1]) == 3, t[1].islower()
)
class Foo:
    def __init__(self, t):
        self.t = t
```

### With PEP484

In the above code samples the type was checked by `instance_of(str)` in the decorator, but you could also rather declare a type hint in the function/class signature and rely on a PEP484 checker [library](./other_libs#pep484-type-checkers), that makes the decorator much more compact and focused on value validation only:

```python
from typing import Tuple
from pytypes import typechecked
from mini_lambda import InputVar, Len
from valid8 import validate_arg

# we need a mini_lambda variable named 't'
t = InputVar('t', tuple)

@typechecked
@validate_arg('t', # the first element is a float between 0 and 1
                   (0 <= t[0]) & (t[0] <= 1),
                   # the 2d element is a lowercase string of len 3
                   Len(t[1]) == 3, t[1].islower()
)
def my_function(t: Tuple[Real, str]):
    pass
```

However note that in this particular case, a tuple of wrong size will appear as a `TypeError` instead of a `ValueError` as we obtained previously.


## 4- Much easier: custom function

The examples above demonstrate that even if you *can* validate complex types directly, at some point you will naturally want to create a dedicated custom validation function for each complex type to validate. Thus separating the validation **means** (the custom function) from the validation **intent** (naming, context, error message customization that you provide to `validate` or `validator`/`validation`). That's exactly what `valid8` is meant for! 

Let's start by creating a custom base validation function. The only constraint is to return `True` or nothing/`None` in case of success, so we can implement
 
  * a simple **boolean checker**. Note that we use `instance_of` instead of `isinstance` so that `valid8` can distinguish between `TypeError` and `ValueError`:

```python
from valid8 import instance_of

def is_valid_tuple(t):
    """ custom function - 'boolean tester' style (returning a bool) """
    return instance_of(t, tuple) and len(t) == 2\
           and instance_of(t[0], Real) and (0 <= t[0] <= 1)\
           and instance_of(t[1], str)  and len(t[1]) == 3 and t[1].islower()
```

  * or, better for our users (and even for our debug sessions), a **failure raiser**. In this case we do not need to use `instance_of` since we raise `TypeError` and `ValueError` explicitly:

```python
def check_valid_tuple(t):
    """ custom function - 'failure raiser' style (returning nothing) """

    # item should be a tuple of length 2
    if not isinstance(t, tuple):
        raise TypeError('item should be a tuple')
    if len(t) != 2:
        raise ValueError('tuple length should be 2, found ' + str(t))

    # the first element is a float between 0 and 1
    if not isinstance(t[0], Real):
        raise TypeError('first elt should be a Real, found ' + str(t[0]))
    if not (0 <= t[0] <= 1):
        raise ValueError('first elt should be between 0 and 1,found ' + str(t[0]))

    # the second element is a lowercase string of size 3
    if not isinstance(t[1], str):
        raise TypeError('second elt should be a string, found ' + str(t[1]))
    if not (len(t[1]) == 3 and t[1].islower()):
        raise ValueError('second elt should be a lowercase string of length 3,'
                         'found ' + str(t[1]))
```

We can then use either function with the `valid8` tools.

### `validate`

With `is_valid_tuple` (boolean tester):

```python
from valid8 import validate
validate('t', t, custom=is_valid_tuple)
```

or with `check_valid_tuple` (failure raiser):

```python
from valid8 import validate
validate('t', t, custom=check_valid_tuple)
```

It is exactly the same usage.

### `validation` / `validator`

With `is_valid_tuple` (boolean tester) we need to return the flag in the context manager, so it is more natural to use the `validator` alias:

```python
from valid8 import validator
with validator('t', t) as v:
    v.alid = is_valid_tuple(t)
```

whereas with `check_valid_tuple` (failure raiser) we do not need to return anything, and the `validation` alias seems more natural:

```python
from valid8 import validation
with validation('t', t):
    check_valid_tuple(t)
```

### function inputs

With `is_valid_tuple` (boolean tester):

```python
from valid8 import validate_arg

@validate_arg('t', is_valid_tuple)
def my_function(t):
    pass
```

or with `check_valid_tuple` (failure raiser):

```python
from valid8 import validate_arg

@validate_arg('t', check_valid_tuple)
def my_function(t):
    pass
```

it is exactly the same usage

### classes fields

With `is_valid_tuple` (boolean tester):

```python
from valid8 import validate_field

@validate_field('t', is_valid_tuple)
class Foo:
    def __init__(self, t):
        self.t = t
```

or with `check_valid_tuple` (failure raiser):

```python
from valid8 import validate_field

@validate_field('t', check_valid_tuple)
class Foo:
    def __init__(self, t):
        self.t = t
```

it is exactly the same usage


### more compact with pep484

Note that if you choose to use a PEP484 type checker such as [pytypes](https://github.com/Stewori/pytypes), your custom validation function can be much more compact, as the tuple length and tuple elements types can be already described in the PEP484 type hint `Tuple[Real, str]`:

```python
from typing import Tuple
from pytypes import typechecked

@typechecked
def is_valid_tuple_pep(t: Tuple[Real, str]):
    """ custom validation function - note the PEP484 type hint above """
    return len(t) == 2 and (0 <= t[0] <= 1) and len(t[1]) == 3 and t[1].islower()
```

or

```python
from typing import Tuple
from pytypes import typechecked

@typechecked
def check_valid_tuple_pep(t: Tuple[Real, str]):
    """ custom validation function - note the PEP484 type hint above """

    # the first element is a float between 0 and 1
    if not (0 <= t[0] <= 1):
        raise ValueError('first elt should be between 0 and 1,found ' + str(t[0]))

    # the second element is a lowercase string of size 3
    if not (len(t[1]) == 3 and t[1].islower()):
        raise ValueError('second elt should be a lowercase string of length 3,'
                         'found ' + str(t[1]))
```

However note that in this particular case, a tuple of wrong size will appear as a `TypeError` instead of a `ValueError` as we obtained previously.


## 4- Variants

TODO
