# Example 2 - `s` is a lowercase non-empty string

## 1- Example values to validate

```python
# Valid
s = 'foo'
s = 'foo_123'

# Invalid
s = 1.1    # wrong type
s = ''     # empty string
s = 'fOO'  # not-lowercase
```

## 2- Inline validation

### `validate`

We use a trick here since `validate` does not provide built-in parameters to check that a string is lowercase. We therefore can check equality with the lowercase version of the string (`equals=s.lower()`). This will not lead to a very friendly error message, but remember that you can [customize it](./index#customizing-the-validationexception).

```python
from valid8 import validate
validate('s', s, instance_of=str)
validate('s', s, min_len=1, equals=s.lower())
```

You can remark in the above that we have to split the validation in two steps. If we don't do this, then `s.lower()` may raise an exception such as a `AttributeError`, that won't be captured and wrapped correctly by `ValidationError`. In that case users will not get contextual information (name, custom error message...).

A much better way to do this is to use the unbound class function `str.islower` as a custom function, it will be more readable:

```python
from valid8 import validate
validate('s', s, instance_of=str, min_len=1, custom=str.islower)
```

Remember that most functions available on objects can be used as unbound class functions like this! This opens a lot of possibilities to `validate`. Also note that you can provide a list of functions to the `custom=` argument, and that it accepts lambda functions like the decorators:

```python
from valid8 import validate

# we create a custom mini_lambda variable, since the name 's' is already used
from mini_lambda import InputVar
txt = InputVar('txt', str)

validate('s', s, instance_of=str, min_len=1, custom=txt.islower())
```

### `with validator`

```python
from valid8 import validator
with validator('s', s, instance_of=str) as v:
    v.alid = (len(s) > 0) and s.islower()
```

## 3- Functions/classes validation

### Principles

 * Type can be checked with built-in `instance_of`
 * Length can be checked with built-in `minlen` or mini-lambda `Len(s) > 0` or custom functions
 * There is no built-in function to check that `s` is lowercase yet, but as we saw above we can use the unbound class function `str.islower` or the mini-lambda `s.islower()`.

We will not show all combinations here (please refer to example 1 for all kind of decorators), only a few examples:


### Function input

with pure built-in and stdlib:

```python
from valid8 import validate_arg, instance_of, minlen

@validate_arg('s', instance_of(str), minlen(1), str.islower)
def my_function(s):
    pass
```

or with pure mini-lambda

```python
from mini_lambda import s, Len
from valid8 import validate_arg, instance_of

@validate_arg('s', instance_of(str), Len(s) > 0, s.islower())
def my_function(s):
    pass
```


### Class fields

In the examples below the class fields are defined as constructor arguments but this also works if they are defined as class descriptors/properties, and is compliant with [autoclass and attrs](valid8_with_other#for-classes)

with pure built-in and stdlib:

```python
from valid8 import validate_field, instance_of, minlen

@validate_field('s', instance_of(str), minlen(1), str.islower)
class Foo:
    def __init__(self, s):
        self.s = s
```

or with pure mini-lambda

```python
from mini_lambda import s, Len
from valid8 import validate_field, instance_of

@validate_field('s', instance_of(str), Len(s) > 0, s.islower())
class Foo:
    def __init__(self, s):
        self.s = s
```

### With PEP484

In the above code samples the type was checked by `instance_of(str)` in the decorator, but you could also rather declare a type hint in the function/class signature and rely on a PEP484 checker [library](./other_libs#pep484-type-checkers), that makes the decorator much more compact and focused on value validation only:

```python
from pytypes import typechecked
from mini_lambda import s, Len
from valid8 import validate_arg

@typechecked
@validate_arg('s', Len(s) > 0, s.islower())
def my_function(s: str):  # <- type hint in signature
    pass
```

## 4- Variants

This example could be easily modified with regular expression validation for the string. To that end you could either 
 * create your own custom function
 * use an existing regular expression validation function generator. For example:
 
```python
import re

# basic regex to check that there is one @ and a dot in the second part
EMAIL_REGEX = re.compile('[^@]+@[^@]+\.[^@]+')

# you can now use 'EMAIL_REGEX.match' in a custom function or lambda, 
# as long as that returns True or None in case of success
validate('s', s, instance_of=str, custom=lambda s: bool(EMAIL_REGEX.match(s)))
```
