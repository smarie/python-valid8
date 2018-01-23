# Usage examples / recipes

In this page we try to provide real-world examples so that you may find an answer for most common validation tasks, according to your coding style (several are proposed). Feel free to propose some examples through a git issue or pull request!

Note: we deliberately do not use any `help_msg` or `error_type` customization here to focus on the validation core. See [here](./index#customizing-the-validationexception) for details on how to customize these examples.


## 1- `x` is a positive integer

In the examples below, we use `numbers.Integral` rather than `int` so as to support both python primitive `int` and other compliant types such as `numpy` `int`.

```python
from numbers import Integral
```

### Inline - validate

```python
from valid8 import validate
validate('x', x, instance_of=Integral, min_value=0)
```

### Inline - with validator

```python
from valid8 import validator
with validator('x', x, instance_of=Integral) as v:
    v.alid = x >= 0
```

### Decorators - built-in lib

We use the built-in `gt` function to check for positiveness here.

```python
from valid8 import validate_arg, validate_out, validate_io, validate_field
from valid8 import instance_of, gt

@validate_arg('x', instance_of(Integral), gt(0))
def my_function(x):
    pass

@validate_out(instance_of(Integral), gt(0))
def my_function2():
    return -1

@validate_io(x=[instance_of(Integral), gt(0)])
def my_function3(x):
    pass

@validate_field('x', instance_of(Integral), gt(0))
class Foo:
    def __init__(self, x):
        self.x = x
```

### Decorators - mini-lambda

We use the mini-lambda `x >= 0` function to check for positiveness here.

```python
from mini_lambda import x
from valid8 import validate_arg, validate_out, validate_io, validate_field
from valid8 import instance_of

@validate_arg('x', instance_of(Integral), x >= 0)
def my_function(x):
    pass

@validate_out(instance_of(Integral), x >= 0)
def my_function2():
    return -1

@validate_io(x=[instance_of(Integral), x >= 0])
def my_function(x):
    pass

@validate_field('x', instance_of(Integral), x >= 0)
class Foo:
    def __init__(self, x):
        self.x = x
```

## 2- `s` is a lowercase non-empty string

### Inline - validate

It is not possible to use `validate` to check that `s` is lowercase (only its type and length).

### Inline - with validator

```python
from valid8 import validator
with validator('s', s, instance_of=str) as v:
    v.alid = s == s.lower()
```

### Decorators - built-in lib

There is no built-in function to check that `s` is lowercase yet (only its type and length).

### Decorators - mini-lambda

We use the mini-lambda `s == s.lower()` function to check for positiveness here.

```python
from mini_lambda import s
from valid8 import validate_arg, validate_out, validate_io, validate_field, 
from valid8 import instance_of

@validate_arg('s', instance_of(str), s == s.lower())
def my_function(s):
    pass

@validate_out(instance_of(str), s == s.lower())
def my_function2():
    return -1

@validate_io(s=[instance_of(str), s == s.lower()])
def my_function3(s):
    pass

@validate_field('s', instance_of(str), s == s.lower())
class Foo:
    def __init__(self, s):
        self.s = s
```
