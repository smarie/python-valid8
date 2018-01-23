# Usage examples / recipes

In this page we try to provide real-world examples so that you may find an answer for most common validation tasks, according to your coding style (several are proposed). Feel free to propose some examples through a git issue or pull request!

Note: we deliberately do not use any `help_msg` or `error_type` customization here to focus on the validation core. See [here](./index#customizing-the-validationexception) for details on how to customize these examples.


## 1- `x` is a positive integer

In the examples below, we use `numbers.Integral` rather than `int` so as to support both python primitive `int` and other compliant types such as `numpy` `int`.

```python
from numbers import Integral
```

**Inline 1 (quick & simple)**

```python
from valid8 import quick_valid
quick_valid('x', x, instance_of=Integral, min_value=0)
```

**Inline 2 (extensible)**

```python
from valid8 import validator
with validator('x', x, instance_of=Integral) as v:
    v.alid = x >= 0
```

**Function input/output or Class 1 (built-in lib)**

```python
from valid8 import validate_arg, validate_out, validate_field, instance_of, gt

@validate_arg('x', instance_of(Integral), gt(0))
def my_function(x):
    pass

@validate_out(instance_of(Integral), gt(0))
def my_function2():
    return ...

@validate_field('x', instance_of(Integral), gt(0))
class Foo:
    ...
```

**Function input/output or Class 2 (mini-lambda)**

```python
from mini_lambda import x
from valid8 import validate_arg, validate_out, validate_field, instance_of

@validate_arg('x', instance_of(Integral), x >= 0)
def my_function(x):
    pass

@validate_out(instance_of(Integral), x >= 0)
def my_function2():
    return ...

@validate_field('x', instance_of(Integral), x >= 0)
class Foo:
    ...
```

## 2- `s` is a lowercase non-empty string

TODO
