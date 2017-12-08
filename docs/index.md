# python-validate (valid8)

[![Build Status](https://travis-ci.org/smarie/python-valid8.svg?branch=master)](https://travis-ci.org/smarie/python-valid8) [![Tests Status](https://smarie.github.io/python-valid8/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-valid8/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-valid8/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-valid8) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-valid8/) [![PyPI](https://img.shields.io/badge/PyPI-valid8-blue.svg)](https://pypi.python.org/pypi/valid8/)

*"valid8ing is not a crime" ;-)*

As always unfortunately it starts with *"I could not find a validation library out there fitting my needs so I built my own"*. Almost. To be a little bit more precise, when it all started, I was just looking for a library providing a `@validate` annotation with a basic library of validators and some logic to associate them, so as to complete [autoclass](https://smarie.github.io/python-autoclass/). The idea was to show that with `autoclass`, if you annotate the `__init__` constructor with `@validate`, then the validator would be automatically applied to the generated property setters. I searched and found tons of good and less good libraries [out there](#other-validation-libraries). However none of them was really a good fit for `autoclass`, for diverse reasons:

 * only a few of them were available as decorators
 * many of them were mixing type validation and value validation, which is not necessary anymore thanks to PEP484. This was making the `autoclass` examples more confusing
 * only a few of them were providing a simple yet consistent and reusable framework to deal with validators, combine them, etc.
 * and what's more important, none of them was really encouraging the community to collaborate by displaying a catalog of validators per data type, open to contributions.

So I first created the `@validate` goodie in [autoclass](https://smarie.github.io/python-autoclass/). When the project became more mature, I decided to extract it and make it independent, so that maybe the community will find it interesting.


## Why would I need a validation library ?

Defensive programming, user-friendly error messages, app-wide consistency of error types, i18n... We try to dig the topic [here](./why_validation)


## Installing

```bash
> pip install valid8
```

Since `valid8` solely focuses on *value* validation, it is recommended to also install a PEP484 *type* checker such as [enforce](https://github.com/RussBaz/enforce) of [pytypes](https://github.com/Stewori/pytypes).

In addition, if you wish to create highly compact object classes with field type+value validation, have a look at [autoclass](https://smarie.github.io/python-autoclass/) which is where this project actually comes from.


## Example usage in combination with type validation

The following snippet shows a `build_house` function with four inputs `name`, `surface`, `nb_floors`, and `with_windows`, where:

 * Each input is validated against the expected type thanks to the PEP484 type checking library ([enforce](https://github.com/RussBaz/enforce) in this example)
 * the `name` and `surface` attribute are further value-validated with valid8 (`len(name) > 0` and `surface >= 0`), with the help of the `mini_lambda` syntax.

```python
# Imports - for type validation
from numbers import Real, Integral
from valid8 import Boolean
from enforce import runtime_validation, config
config(dict(mode='covariant'))  # subclasses of required types are valid too

# Imports - for value validation
from mini_lambda import s, x, Len
from valid8 import validate

# Apply type+value validation to our function
@runtime_validation
@validate(name=Len(s) > 0,
          surface=x >= 0)
def build_house(name: str,
                surface: Real,
                nb_floors: Integral = None,
                with_=windows: Boolean = False):
    print('Building house...')
    # ...
    print('DONE !')
```

We can test that validation works:

```python
# Test
build_house('test', 12, 2)     # validation OK
build_house('test', 12, 2.2)   # Type: @typechecked raises a InputTypeError
build_house('test', 12, None)  # Declared 'Optional' with PEP484, no error
build_house('test', -1, 2)     # ValidationFailure
build_house('', 12, 2)         # ValidationFailure
```

**Remarks concerning type validation** 

The handy `Real` and `Integral` abstract numeric types are provided in the [`numbers`](https://docs.python.org/3.6/library/numbers.html) built-in module. They provide an easy way to support both python primitives AND others, e.g. numpy primitives. Unfortunately the boolean types are not supported by this module, so in this library we provide an additional `Boolean` class supporting numpy, to complete the picture.

**Remarks concerning value validation**

In the above example, [`mini_lambda`](https://smarie.github.io/python-mini-lambda/) is used to create the validation functions. This compact lambda syntax engine has actually been first designed as part of this project, and has now become an independent library. However it is not mandatory to use it as alternate options are supported - check the [Usage](./usage/) page for more details.


## `valid8` Design goals

 * **Separate *value* validation from *type* validation** (Separation of concerns). The library is compliant with the use of an additional PEP484-based type validation library such as enforce and pytypes. Optionality/Mandatoriness is the only feature available on both sides, as it is sometimes not intuitive to do with PEP484.
 * **Provide validation as a function decorator** (`@validate`), and also inline anywhere in the code (`assert_valid` and `is_valid`). This *de facto* creates two distinct concepts: *basic validation* (inline) and *validation of function inputs* (the annotation). 
 * **python-first, not schema-first**. Maybe it will be useful to provide bridges with json/xml/etc binding libraries later on, but for now we focus on small, simple, value validation


 * TODO...
 
 * Validators should be functions, lambdas, or callable objects (through the `__call__` magic method)
 * **Provide the possibility to separate evaluation from validation** (Separation of concerns). Evaluation means taking an input and computing some results. Validation means checking if the result is a success, and throwing a user-friendly error message.
 * There should be a way to retrofit an existing validation function into a `valid8`-compliant validator
 * Provide a logic for composition and reuse of validators
 * Enforce explicit validation errors even for lambdas (provide a helper method)
 * Ability to disable validation with little or no overhead
 * Try to not reinvent new language elements - reuse as much as possible the many great built-in python language capabilities 
 * Most important than everything, provide an easy way to list the available validators while developing : through the doc but also through python package organization
 * The `@validate` function decorator should stay compliant with `autoclass`, to enable automatic creation of validated property setters

 * Exceptions should contain details so as to be processed/translated/etc.

## Main features

* **`@validate`** is a decorator for any method, that adds input validators to the method.

* Many validators are provided out of the box to use with `@validate`: `gt`, `between`, `is_in`, `maxlen`... check them out in [the validators list page](https://smarie.github.io/python-valid8/validators/). But you can of course use your own, too.

* Equivalent manual wrapper methods are provided for all decorators in this library: `decorate_with_validation(func, **validators)`


## Other Validation libraries

Many validation libraries are available on [PyPI](https://pypi.python.org/pypi?%3Aaction=search&term=valid&submit=search) already. The following [list](./other_libs) is by far not exhaustive, but gives an overview. Do not hesitate to contribute to this list with a pull request! 


## See Also

 * [decorator](http://decorator.readthedocs.io/en/stable/) library, which provides everything one needs to create complex decorators easily (signature and annotations-preserving decorators, decorators with class factory) as well as provides some useful decorators (`@contextmanager`, `@blocking`, `@dispatch_on`). We use it to preserve the signature of wrapped methods.

*Do you like this library ? You might also like [these](https://github.com/smarie?utf8=%E2%9C%93&tab=repositories&q=&type=&language=python)* 


## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-valid8](https://github.com/smarie/python-valid8)
