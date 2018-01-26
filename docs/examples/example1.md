# Example 1 - `x` is a positive integer

## 1- Example values to validate

```python
# Valid
x = 0
x = 100

# Invalid
x = 'foo'  # wrong type
x = 1.0    # wrong type
x = -1     # negative
```


## 2- Inline validation

### `validate`

```python
from valid8 import validate
validate('x', x, instance_of=Integral, min_value=0)
```

### `with validator`

```python
from valid8 import validator
with validator('x', x, instance_of=Integral) as v:
    v.alid = x >= 0
```

## 3- Functions/classes validation

### Principles

We can either use the built-in `gt` function to check for positiveness here, or the mini-lambda function `x >= 0` (or a plain old lambda/function).


### Function input

with built-in:

```python
from valid8 import validate_arg, instance_of, gt

@validate_arg('x', instance_of(Integral), gt(0))
def my_function(x):
    pass
```

or with mini-lambda

```python
from mini_lambda import x
from valid8 import validate_arg, instance_of

@validate_arg('x', instance_of(Integral), x >= 0)
def my_function(x):
    pass
```

### Function output

with built-in:

```python
from valid8 import validate_out, instance_of, gt

@validate_out(instance_of(Integral), gt(0))
def my_function2():
    return -1
```

or with mini-lambda

```python
from mini_lambda import x
from valid8 import validate_out, instance_of

@validate_out(instance_of(Integral), x >= 0)
def my_function2():
    return -1
```


### Function ios

With `validate_io` you can check several inputs+output in the same decorator, but no customization is possible.

with built-in:

```python
from valid8 import validate_io, instance_of, gt

@validate_io(x=[instance_of(Integral), gt(0)])
def my_function3(x):
    pass
```

or with mini-lambda

```python
from mini_lambda import x
from valid8 import validate_io, instance_of

@validate_io(x=[instance_of(Integral), x >= 0])
def my_function3(x):
    pass
```

### Class fields

In the examples below the class fields are defined as constructor arguments but this also works if they are defined as class descriptors/properties, and is compliant with [autoclass and attrs](valid8_with_other#for-classes)

using built-in `gt`:

```python
from valid8 import validate_field, instance_of, gt

@validate_field('x', instance_of(Integral), gt(0))
class Foo:
    def __init__(self, x):
        self.x = x
```

or with mini-lambda

```python
from mini_lambda import x
from valid8 import validate_field, instance_of

@validate_field('x', instance_of(Integral), x >= 0)
class Foo:
    def __init__(self, x):
        self.x = x
```

### With PEP484

In the above code samples the type was checked by `instance_of(Integral)` in the decorators, but you could also rather declare a type hint in the function/class signature and rely on a PEP484 checker [library](./other_libs#pep484-type-checkers), that makes the decorator much more compact and focused on value validation only. For example for to check a function input:

```python
from pytypes import typechecked
from mini_lambda import x
from valid8 import validate_arg

@typechecked
@validate_arg('x', x >= 0)
def my_function(x: Integral):  # <- type hint in signature
    pass
```

## 4- Variants

This example could be easily modified so that floating point integers are accepted, such as `1.0`. The way to do it is very similar to [example 2](./example2): you should validate that type is `Real` instead of `Integral`, and that `x == int(x)`. You can also do it with a custom function like in [example 3](./example3).
