# Usage details

## 1 - Applying validation to a function

### The `@validate` decorator

Adds input validation to a function. Simply declare the name of the input to validate and associate to it a validator or a list of validators:

```python
@validate(<input_name>=<validator_or_list_of_validators>, ...)
def myfun(<input_name>, ...):
    ...
```

Many validators are provided out of the box to use with `@validate`: `gt`, `between`, `is_in`, `maxlen`... check them out in [the validators list page](https://smarie.github.io/python-valid8/validators/). For example below we check that input `a` is not `None`, is even, and is greater than 1, and that input `b` is even:

```python
from valid8 import validate, not_none, is_even, gt

@validate(a=[not_none, is_even, gt(1)], b=is_even)
def myfunc(a, b):
    pass
    
myfunc(84, 82)  # OK
myfunc(None,0)  # ValidationError: a is None
myfunc(1,0)     # ValidationError: a is not even
myfunc(2,1)     # ValidationError: b is not even
myfunc(0,0)     # ValidationError: a is not >= 1
```

### Alternative to `@validate`: manual function wrapper

If you wish to add validation to a function *a posteriori*, you may use `validate_decorate(func, **validators)`:

```python
from valid8 import validate_decorate, is_even

# existing function without validation
def my_func(a):
    pass

# manually add validation afterwards
my_func = validate_decorate(my_func, a=is_even)
my_func(9)  # ValidationError
```

### Using validators directly inline

**TODO** explain how the validators may be used directly inline, with and without `assert`.

## 2 - Combining validators: logical operations

Validating a value will rarely check only one aspect. Therefore you might often wish to combine existing validators, or to combine existing validators with your own custom validators, to provide complete validation. `valid8` provides the following operators for validators composition.


#### and_(<validators_list>)

An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a `ValidationException` on the first `False` received or `Exception` caught.

Note that an implicit `and_` is performed if you provide a list of validators to `@validate`.

```python
@validate(a=[and_([is_even, gt(1)])])
def myfunc(a):
    pass

myfunc(84)  # ok
myfunc(1)   # ValidationError a is not even
myfunc(0)   # ValidationError a is not >= 1
```

#### not_(<validator> or <validators_list>, catch_all: bool=False)

Generates the inverse of the provided validator: when the validator returns `False` or raises a `ValidationError`, this validator returns `True`. Otherwise it returns `False`.
 
By default, `Expection` other than `ValidationError` are not caught and therefore fail the validation (`catch_all=False`). To change this behaviour you can turn the `catch_all` parameter to `True`, in which case all exceptions will be caught instead of just `ValidationError`s.

```python
@validate(a=not_(is_even))
def myfunc(a):
    pass

myfunc(11)  # ok
myfunc(84)  # ValidationError! a is even
```

#### not_all(<validator> or <validators_list>, catch_all: bool=False)

An alias for `not_(and_(validators))`.

```python
@validate(b=not_all([is_even, is_mod(3)]))
def myfunc(b):
    pass

myfunc(11)  # ok
myfunc(3)   # ValidationError: b is odd (ok) but it is a multiple of 3 (nok)
```

#### or_(validators_list)

An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught exception's message if any.

#### xor_(validators_list)

A 'xor' validator: returns `True` if exactly one of the provided validators returns `True`. All exceptions will be silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught exception's message if any.


## 3 - Implementing custom validators

### Standard functions

You may implement your own validators: simply provide a function that returns `True` in case of correct validation, and either raises an exception or returns `False` in case validation fails. The `ValidationError` type is provided for convenience, but you may wish to use another exception type. The example below shows four styles of validators 

```python
from valid8 import validate, ValidationError

def is_mod_3(x):
    """ A simple validator with no parameters """
    return x % 3 == 0

def is_mod(ref):
    """ A validator generator, with parameters """
    def is_mod_ref(x):
        return x % ref == 0
    return is_mod_ref

def gt_ex1(x):
    """ A validator raising a custom exception in case of failure """
    if x >= 1:
        return True
    else:
        raise ValidationError('gt_ex1: x >= 1 does not hold for x=' + str(x))

def gt_assert2(x):
    """(not recommended) relying on assert, only valid in 'debug' mode"""
    assert x >= 2

@validate(a=[gt_ex1, gt_assert2, is_mod_3],
          b=is_mod(5))
def myfunc(a, b):
    pass

# -- check that the validation works
myfunc(21, 15)  # ok
myfunc(4,21)    # ValidationError: a is not a multiple of 3
myfunc(15,1)    # ValidationError: b is not a multiple of 5
myfunc(1,0)     # AssertionError: a is not >= 2
myfunc(0,0)     # ValidationError: a is not >= 1
```

### Lambda functions

**TODO**
