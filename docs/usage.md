# Validation entry points

## Defensive programming - from `assert` to `validate`

Let's start with a very simple `hello` function:

```python
def hello(age):
    print('Hello, {}-years-old fella !'.format(age))
```

We would like to protect it against bad data, for one of the reasons listed [here](./why_validation.md). A first idea would probably be to use `assert`:
 
```python
from math import isfinite, inf

def hello(age):
    assert isfinite(age)
    print('Hello, {}-years-old fella !'.format(age))

# let's test that it works:
hello(33)   # 'Hello, 33-years-old fella !'
hello(inf)  # AssertionError: assert False \
            #                 where False = <built-in function isfinite>(inf)
```

But as explained [here](./why_validation#how-do-you-do-today) this is maybe not satisfying: 

 - either the code may be used in an optimized environment and we don't want the assertion to disappear,
 - or we think that the type of error raised by `assert` is not satisfying/user-friendly/consistent/good enough for app-wide error handling/i18n...(pick your favorite)

Let's replace `assert` with `validate` from `valid8`:

```python
from math import isfinite, inf
from valid8 import validate

def hello(age):
    validate('age', age, custom=isfinite)
    print('Hello, {}-years-old fella !'.format(age))

# let's test that it works:
hello(inf)   # ValidationError: Error validating [age=inf]: \
             #                  root validator [isfinite] returned [False].
```

As you can see above, our code is very similar to the one with `assert`, but the exception raised is now a `ValidationError` (and would be so even if `isfinite` had raised an exception), displaying all details about the validation context and the failure. We can inspect the exception to check that all this information is also available in the object itself:

```python
try:
    hello(inf)
except ValidationError as e:
    e.validator                           # "Validator<isfinite>"
    e.var_name                            # 'age'
    e.var_value                           # inf
    e.validation_outcome                  # False
```

We will come back later to the notion of `Validator` object that appears here in `e.validator`.

One of the great features of `valid8` is that it will fail consistently, whatever the way the inner validation function fails:

```python
hello(None)  # ValidationError
```


*********** WORK IN PROGRESS : TODO CONTINUE ***************
