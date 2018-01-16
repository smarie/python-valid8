# python-validate (valid8)

[![Build Status](https://travis-ci.org/smarie/python-valid8.svg?branch=master)](https://travis-ci.org/smarie/python-valid8) [![Tests Status](https://smarie.github.io/python-valid8/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-valid8/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-valid8/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-valid8) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-valid8/) [![PyPI](https://img.shields.io/badge/PyPI-valid8-blue.svg)](https://pypi.python.org/pypi/valid8/)

*"valid8ing is not a crime" ;-)*

As always unfortunately it starts with *"I could not find a validation library out there fitting my needs so I built my own"*. Almost. To be a little bit more precise, when it all started, I was just looking for a library providing a `@validate` annotation with a basic library of validators and some logic to associate them, so as to complete [autoclass](https://smarie.github.io/python-autoclass/). The idea was to show that with `autoclass`, if you annotate the `__init__` constructor with `@validate`, then the validator would be automatically applied to the generated property setters. I searched and found tons of good and less good libraries [out there](#other-validation-libraries). However none of them was really a good fit for `autoclass`, for diverse reasons:

 * only a few of them were available as decorators
 * many of them were strongly mixing type validation and value validation, which is not necessary anymore thanks to PEP484. This was making the `autoclass` examples more confusing.
 * only a few of them were providing a simple yet consistent and reusable framework to deal with validation functions, combine them, etc. And the good ones were based on defining a Schema first, which seemed a bit 'too much' for me already.
 * finally, none of them was really encouraging the community to collaborate by displaying a catalog of base validation functions per data type, open to contributions.

So I first created the `@validate` goodie in [autoclass](https://smarie.github.io/python-autoclass/). When the project became more mature, I decided to extract it and make it independent, so that maybe the community will find it interesting. 

When this project grew, I found that its [embedded library of base validation functions](./base_validation_lib) was not flexible enough to cover a large variety of use cases, and will probably **never** be even if we try our best, so I came up with the complementary [mini_lambda syntax](https://smarie.github.io/python-mini-lambda/) which is now an independent project, typically used when your base validation function is very specific, but yet quite simple to write in plain python.


## Why would I need a validation library ?

Defensive programming, user-friendly error messages, app-wide consistency of error types, i18n... We try to dig the topic [here](./why_validation).


## Installing

```bash
> pip install valid8
```

Optional but recommended:

 - If you wish to define your own validation functions dynamically you may wish to also install [mini_lambda](https://smarie.github.io/python-mini-lambda/).

 - Since `valid8` does not support complex *type* validation, it is recommended to also install a PEP484 *type* checker such as [enforce](https://github.com/RussBaz/enforce) of [pytypes](https://github.com/Stewori/pytypes).

 - In addition, if you wish to create highly compact object classes with field type+value validation, have a look at [autoclass](https://smarie.github.io/python-autoclass/) which is where `valid8` actually originates from.


## Usage examples - inline

### Basic

`assert_valid` is a replacement for `assert`, to validate some value anywhere in the code (see [here](./why_validation) if you wonder why `assert` is not good enough):

```python
from valid8 import assert_valid, instance_of, is_multiple_of

surf = -1

# (1) simplest: one named variable to validate + one validation function
assert_valid('surface', surf, instance_of(int))
assert_valid('surface', surf, is_multiple_of(100))

# (2) native mini_lambda support to define validation functions
from mini_lambda import x
assert_valid('surface', surf, x > 0)
```

The main benefit from this is that you are **guaranteed** that any exception happening in the validation process will be caught and turned into a `ValidationError`, whatever the cause (`None` handling, known validation failures, unknown other errors). You therefore do not have to write the usual if/else/try/except wrappers to handle all cases. Yay!

In (1) we used the validation functions from the bundled [validation functions library](./base_validation_lib). In (2) we used [`mini_lambda`](https://smarie.github.io/python-mini-lambda/) to define the validation function inline (`x > 0`). Other options are supported including defining your own validation functions very easily, as explained in the [Usage](./usage/) page.

!!! note "Note on type validation"
    Although simple type validation may be performed using the bundled `instance_of` or `subclass_of` function as shown above in (1), `valid8` is not meant for advanced type validation as it does not "know" anything about types. It is recommended to rely on a proper PEP484 type checker to support type validation more extensively.


### Customization

Various options are provided to adapt `valid8` to your needs:

```python
from valid8 import NonePolicy

# (3) explicit validation policy for None (FAIL/SKIP/VALIDATE*)
assert_valid('surface', None, x > 0, none_policy=NonePolicy.FAIL)

# (4) custom error message (exception is still a ValidationError)
assert_valid('surface', surf, x > 0, help_msg='Surface should be positive')

# (5) *YOUR* error type (recommended to provide unique applicative errors / i18n)
class InvalidSurface(ValidationError):
    help_msg = 'Surface should be a positive number'

assert_valid('surface', surf, x > 0, error_type=InvalidSurface)

# (6) Templating is supported in all `help_msg` texts
class InvalidSurface(ValidationError):
    help_msg = 'Surface should be > {minimum}, found {var_value}'

min_value = 0
with pytest.raises(ValidationError) as exc_info:
    assert_valid('surface', surf, x > min_value, 
                 error_type=InvalidSurface, minimum=min_value)
```

### Composition

You can combine several base validation functions together:

```python
# (8) composition of several base validation functions...
assert_valid('surface', surf, (x >= 0) & (x < 10000), is_multiple_of(100))

# (9) you can still provide a global custom error type
class InvalidSurface(ValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'
assert_valid('surface', surf, (x >= 0) & (x < 10000), is_multiple_of(100),
             error_type=InvalidSurface)

# (10) you can also provide user-friendly intermediate failure messages/types
assert_valid('surface', surf,
             ((x >= 0) & (x < 10000), 'Surface should be between 0 and 10000'),
             (is_multiple_of(100), 'Surface should be a multiple of 100'),
             error_type=InvalidSurface)
```

## Usage examples - decorators

### Validating function inputs/outputs

You can decorate any function with `@validate_arg` and `@validate_out` to validate its inputs and outputs. Both work exactly the same way than `assert_valid`, but they are a bit smarter when it comes to `None` handling (see note below). Here is an example where we add validation to a `build_house` function with two inputs:

```python
from mini_lambda import s, x, l, Len
from valid8 import validate_arg, validate_out, instance_of, is_multiple_of

# Define our 2 applicative error types
class InvalidNameError(InputValidationError):
    help_msg = 'name should be a non-empty string'

class InvalidSurfaceError(InputValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

# Apply validation
@validate_arg('name',    instance_of(str), Len(s) > 0,             
              error_type=InvalidNameError)
@validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
              error_type=InvalidSurfaceError)
@validate_out(instance_of(tuple), Len(l) == 2)
def build_house(name, surface=None):
    print('Building house... DONE !')
    return name, surface
```

Let's try to call it with various input values:

```python
build_house('sweet home', 200)    # Valid
build_house('sweet home')         # Valid, see note below
build_house('', 200)              # InvalidNameError
build_house('sweet home', 10000)  # InvalidSurfaceError
```

!!! note "Note on None handling policies"
    We saw [earlier](#customization) that for `assert_valid` you can customize the policy so that `None` are not validated (`VALIDATE`, the default behaviour) but rather accepted (`SKIP`) or rejected (`FAIL`). For function input and output validation, two additional policies may be selected in addition to these 3: the first `SKIP_IF_NONABLE_ELSE_VALIDATE` (default) will skip validation of `None` values if the argument has a default value of `None` in the function signature or if the argument or output has a PEP484 `Optional[...]` type hint, and otherwise will perform validation as usual. The second, `SKIP_IF_NONABLE_ELSE_FAIL`, will do the same but its last resort fallback is a failure instead of a validation. 


### Validating class fields

You can decorate any class with `@validate_field` to validate a field defined as 

 * a [descriptor](https://docs.python.org/3.6/howto/descriptor.html#descriptor-example) - in which case it is equivalent to a `@validate_arg` added on the `__set__` function of the descriptor, but with a more user-friendly error message
 * a [property](https://docs.python.org/3.6/howto/descriptor.html#properties), in which case it is equivalent to a `@validate_arg` added on the `fset` function of the descriptor, but with a more user-friendly error message.
 * or a constructor input, in which case it is equivalent to a `@validate_arg` added on the constructor. In such case WARNING validation will only be called at initial object creation, not at subsequent field modifications!
 
Here is an example where we add validation to a `House` class with two fields:

```python
from valid8 import validate_field, instance_of, is_multiple_of
from mini_lambda import x, s, Len

class InvalidNameError(ClassFieldValidationError):
    help_msg = 'name should be a non-empty string'

class InvalidSurfaceError(ClassFieldValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

@validate_field('name', instance_of(str), Len(s) > 0,
                error_type=InvalidNameError)
@validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                error_type=InvalidSurfaceError)
class House:
    def __init__(self, name, surface=None):
        self.name = name
        self.surface = surface

    @property
    def surface(self):
        return self.__surface

    @surface.setter
    def surface(self, surface=None):
        self.__surface = surface

```

Let's try it:

```python
h = House('sweet home')  # valid
h.name = ''              # DOES NOT RAISE InvalidNameError (no setter!)

h = House('')            # InvalidNameError
h.surface = 10000        # InvalidSurfaceError
```

## `valid8` + other tools

### PEP484 type checkers

As said previously, even if you can rely on `instance_of` and `subclass_of` for basic type validation, it is not the purpose of `valid8` to do serious type validation, especially when PEP484 is now mainstream and many type checkers are available. It is better to combine their strengths. 

The following snippet shows a `build_house` function with four inputs `name`, `surface`, `nb_floors`, and `with_windows`, where:

 * Each input is validated against the expected type thanks to the PEP484 type checking library ([enforce](https://github.com/RussBaz/enforce) in this example)
 * the `name` and `surface` attribute are further value-validated with valid8 (`len(name) > 0` and `surface >= 0`), with the help of the `mini_lambda` syntax.

```python
# Imports - for type validation
from numbers import Integral
from typing import Tuple, Optional
from enforce import runtime_validation, config
config(dict(mode='covariant'))  # type validation will accept subclasses too

# Imports - for value validation
from mini_lambda import s, x, Len
from valid8 import validate_arg, is_multiple_of, InputValidationError

# Define our 2 applicative error types
class InvalidNameError(InputValidationError):
    help_msg = 'name should be a non-empty string'

class InvalidSurfaceError(InputValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

# Apply type + value validation
@runtime_validation
@validate_arg('name', Len(s) > 0, error_type=InvalidNameError)
@validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
              error_type=InvalidSurfaceError)
def build_house(name: str, surface: Optional[Integral]=None) \
        -> Tuple[str, Optional[Integral]]:
    print('Building house... DONE !')
    return name, surface
```

We can test that validation works:

```python
build_house('sweet home', 200)    # valid
build_house('sweet home')         # valid (PEP484 Optional, default=None)

build_house('', 100)              # InvalidNameError (valid8)
build_house('sweet home', 10000)  # InvalidSurfaceError (valid8)
build_house('test', 100.1)        # RuntimeTypeError (enforce)
```

**Note concerning PEP484 type validation**: how can you make sure to accept both plain old `float`, `int` and `bool`, as well as their `numpy` equivalents ? Use the handy `Real` (=float) and `Integral` (=int) abstract numeric types provided in the [`numbers`](https://docs.python.org/3.6/library/numbers.html) built-in module ! They provide an easy way to support both python primitives AND others, e.g. numpy primitives. Unfortunately no equivalent type is provided for booleans, so in `valid8` we provide an additional `Boolean` class supporting numpy, to complete the picture.


### autoclass

`valid8` plays well with [autoclass](https://smarie.github.io/python-autoclass/): 

 * if you decorate the whole class with `@validate_field` it will obviously work since `autoclass` generates plain old properties:

```python
from autoclass import autoclass
from mini_lambda import s, x, Len
from valid8 import validate_arg, instance_of, is_multiple_of

class InvalidNameError(ClassFieldValidationError):
    help_msg = 'name should be a non-empty string'

class InvalidSurfaceError(ClassFieldValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

@validate_field('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
@validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100), 
                error_type=InvalidSurfaceError)
@autoclass
class House:
    def __init__(self, name, surface=None):
        pass

h = House('sweet home', 200)

h.surface = None   # Valid (surface is nonable by signature)
h.name = ''        # InvalidNameError
h.surface = 10000  # InvalidSurfaceError
```
 
 * if you decorate a class constructor with `@validate_arg`, the property setters generated by `@autoclass` will include validation too. 

```python
from autoclass import autoclass
from mini_lambda import s, x, Len
from valid8 import validate_arg, instance_of, is_multiple_of, InputValidationError

class InvalidNameError(InputValidationError):
    help_msg = 'name should be a non-empty string'

class InvalidSurfaceError(InputValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

@autoclass
class House:

    @validate_arg('name', instance_of(str), Len(s) > 0, 
                  error_type=InvalidNameError)
    @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100), 
                  error_type=InvalidSurfaceError)
    def __init__(self, name, surface=None):
        pass

h = House('sweet home', 200)

h.surface = None   # Valid (surface is nonable by signature)
h.name = ''        # InvalidNameError
h.surface = 10000  # InvalidSurfaceError
```

Of course you can also add type checking on top of that, see [autoclass documentation](https://smarie.github.io/python-autoclass/) for details.


### attrs

`valid8` also integrates well with [attrs](http://www.attrs.org/en/stable/): if you decorate a class with `@validate_field` it will work because `attrs` generates a compliant class constructor behind the scenes. However WARNING validation will only be called at initial object creation, not at subsequent field modifications!
 
```python
import attr
from mini_lambda import s, x, Len
from valid8 import validate_field, instance_of, is_multiple_of, ClassFieldValidationError

class InvalidNameError(ClassFieldValidationError):
    help_msg = 'name should be a non-empty string'

class InvalidSurfaceError(ClassFieldValidationError):
    help_msg = 'Surface should be between 0 and 10000 and be a multiple of 100.'

@validate_field('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
@validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                error_type=InvalidSurfaceError)
@attr.s
class House:
    name = attr.ib()
    surface = attr.ib(default=None)

h = House('sweet home')  # Valid (surface is nonable by generated signature)

h.name = ''       # DOES NOT RAISE InvalidNameError (no setter!)

with pytest.raises(InvalidNameError):
    House('', 10000)  # InvalidNameError

with pytest.raises(InvalidSurfaceError):
    House('sweet home', 10000)  # InvalidSurfaceError
``` 
 
As of today `attrs` does not transform fields into descriptors or properties so there is no way to add validation to field setters. Note that this is actually also the case if you rely on the validation mechanisms built in attrs, as explained [here](http://www.attrs.org/en/stable/examples.html#callables). This feature has been requested [here](https://github.com/python-attrs/attrs/issues/160).


## Main features

 * **Separation of validation intent** (entry points) **from validation means** (base validation functions). Entry points provide a clear and consistent behaviour matching your applicative intent, hiding the diversity of base validation functions that you rely on to do it.
 
 * **Clear entry points** to serve most common needs related with validation:
 
    - *Inline validation*: two functions `assert_valid` and `is_valid`, to perform validation anywhere in your code in defensive programming mode (`assert_valid`) or case handling mode (`is_valid`)
    
    - *Function validation*: two decorators `@validate_arg` and `@validate_out`, as well as a more limited `@validate`, to add input and output validation to any function. A manual decorator `decorate_with_validation` provides the same functionality for retrofit purposes.
 
 * **Consistent behaviour**: all defensive mode entry points provide the same behaviour, raising subclasses of `ValidationError` in case of failure, whatever the diversity of failure modes that can happen in base validation functions. The exception object contains all contextual information in its fields so as to be easily usable by a global exception handler at application-level, for example for internationalization. Consistency is ensured by the fact that all entry points rely on a **common `Validator` class**, which can also be used for advanced purposes, such as speeding up inline validation by creating validators ahead of time.
 
 * **Highly customizable**: all entry points can be customized so as to fit your application needs. In particular you probably do not want users to see `valid8` exceptions and messages, but rather *your* exceptions and messages. This is easy to do with the two `help_msg` and `error_type` options.
 
 * **Compliant with most validation functions out there**. You may use base validation functions from anywhere including your own, and including `functools.partial`, `lambda` or even callable objects implementing the `__call__` magic method. The *only* requirement is that they return `True` or `None` in case of success ! The way they fail is not important, `valid8` tolerates all. 

 * **Built-in [library](./base_validation_lib) of base validation functions**, by object type. Do not hesitate to contribute! Also, do not hesitate to rely on other libraries for dedicated object types such as [these](./other_libs#domain-specific-validators-validators-for-specific-data-types-validators-without-framework), or to build your own !

 * **Built-in support for [mini_lambda](https://smarie.github.io/python-mini-lambda/)** to define base validation functions, so that you do not need to write `lambda x:` everywhere, and the failure messages are far more easy to read.
 
 * **Tools to build user-friendly base validation functions**. Three exception classes `Failure`, `WrappingFailure` and `CompositionFailure`, are provided as goodies if you wish to write your own validation functions while providing a maximum amount of details in the raised failure exception. You can find some inspiration [here](https://github.com/smarie/python-valid8/blob/master/valid8/validation_lib/collections.py). As explained above this is not mandatory, as `valid8` will catch any kind of failure even without exception.

 * **Composition of base validation functions**. Built-in functions `and_`, `or_`, `xor_`, `not_`, `not_all`, `failure_raiser`, `skip_on_none` and `fail_on_none` allow you to quickly create complex validation functions by reusing simpler ones, if you do not want to do it using `lambda` or `mini_lambda`. Note that `and_` is implicitly used if you provide a list of base validation functions to any of the `valid8` entry points.

 * **python-first, not schema-first**. This library is intended to provide validation anywhere in your code, not only when data enters a web service, a CLI or a form. There already are [libs out there](./other_libs#validation-of-data-at-the-entry-point) for that purpose. `valid8` is rather meant to be as simple as possible and as open as possible to any kind of validation, even those that can not easily be described in a schema. To bridge the gap, maybe it will be useful at some point to provide a more restrictive class of base validation objects so that users may be able to generate a schema from a function annotated with `@validate_arg`. Of course, only if interest is confirmed...

 * **Separation of *value* validation from *type* validation**. Using `valid8` for function input validation is compliant with the use of any PEP484-based type validation library such as `enforce` or `pytypes`.

 * **Compliant with [autoclass](https://github.com/smarie/python-autoclass)**. Declare validation once by annotating the class constructor with `@validate` or `@validate_arg`, and the generated property setters will be validated too!


## Other Validation libraries

Many validation libraries are available on [PyPI](https://pypi.python.org/pypi?%3Aaction=search&term=valid&submit=search) already. The following [list](./other_libs) is by far not exhaustive, but gives an overview. Do not hesitate to contribute to this list with a pull request! 


## See Also

 * [decorator](http://decorator.readthedocs.io/en/stable/) library, which provides everything one needs to create complex decorators easily (signature and annotations-preserving decorators, decorators with class factory) as well as provides some useful decorators (`@contextmanager`, `@blocking`, `@dispatch_on`). We use it to preserve the signature of wrapped methods.
 * Julien Danjou's [Definitive Guide to Python Exceptions](https://julien.danjou.info/blog/2016/python-exceptions-guide). It was of great inspiration and help to design `valid8`'s exception hierarchy.

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie?utf8=%E2%9C%93&tab=repositories&q=&type=&language=python)* 


## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-valid8](https://github.com/smarie/python-valid8)
