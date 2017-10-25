# python-validate (valid8)

[![Build Status](https://travis-ci.org/smarie/python-valid8.svg?branch=master)](https://travis-ci.org/smarie/python-valid8) [![Tests Status](https://smarie.github.io/python-valid8/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-valid8/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-valid8/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-valid8) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-valid8/) [![PyPI](https://img.shields.io/badge/PyPI-valid8-blue.svg)](https://pypi.python.org/pypi/valid8/)

As always unfortunately it starts with *"I could not find a validation library out there fitting my needs so I built my own"*. 

To be a little bit more precise, when it all started, I was just looking for a library providing a `@validate` annotation with a basic library of validators and some logic to associate them, so as to complete [autoclass](https://smarie.github.io/python-autoclass/). The idea was to show that with `autoclass`, if you annotate the `__init__` constructor with `@validate`, then the validator would be automatically applied to the generated property setters. I searched and found tons of good and less good libraries [out there](#other-validation-libraries). However none of them was really a good fit for `autoclass`, for diverse reasons:

 * only a few of them were available as decorators
 * many of them were mixing type validation and value validation, which is not necessary anymore thanks to PEP484. This was making the `autoclass` examples more confusing
 * only a few of them were providing a simple yet consistent and reusable framework to deal with validators, combine them, etc.
 * and what's more important, none of them was really encouraging the community to collaborate by displaying a catalog of validators per data type, open to contributions.

So I first created the `@validate` goodie in [autoclass](https://smarie.github.io/python-autoclass/). When the project became more mature, I decided to extract it and make it independent, so that maybe the community will find it interesting and will wish to collectively contribute to a catalog of validators.


## Why would I need a validation library ?

Good question, thanks for asking. Having a common understanding of this is key, otherwise this library will miss its target. We try to dig the topic [here](./why_validation)


## Installing

```bash
> pip install valid8
```

Since `valid8` solely focuses on *value* validation, it is recommended to also install a PEP484 *type* checker such as [enforce](https://github.com/RussBaz/enforce) of [pytypes](https://github.com/Stewori/pytypes).

Finally if you wish to create highly compact object classes with field type+value validation, have a look at [autoclass](https://smarie.github.io/python-autoclass/) which is where this project actually comes from.


## Example usage in combination with PEP484-based type validation

The following snippet shows a `build_house` function with four inputs. 

 * Each input is validated against the expected type thanks to the PEP484 type checking library (`enforce` in this example)
 * the `name` and `surface` attribute are further value-validated with `valid8` (`len(name) > 0` and `surface >= 0`).

```python
# for type checking
from valid8 import Boolean
from numbers import Real, Integral
from typing import Optional
from enforce import runtime_validation, config
config(dict(mode='covariant'))  # allow subclasses when validating types

# for value checking
from valid8 import validate, minlens, gt

@runtime_validation
@validate(name=minlens(0),
          surface=gt(0))
def build_house(name: str,
                surface: Real,
                nb_floors: Optional[Integral] = 1,
                with_windows: Boolean = False):
    print('you did it !')
```

We can test that validation works:

```python
# Test
build_house('test', 12, 2)     # validation OK
build_house('test', 12, 2.2)   # Type validation: @typechecked raises a InputTypeError
build_house('test', 12, None)  # Mandatory/Optional validation: Declared 'Optional' with PEP484, no error
build_house('test', -1, 2)     # Value validation: @validate raises a ValidationError
build_house('', 12, 2)         # Value validation: @validate raises a ValidationError
```

Note that the `Real` and `Integral` types come from the [`numbers`](https://docs.python.org/3.6/library/numbers.html) built-in module. They provide an easy way to support both python primitives AND e.g. numpy primitives. Unfortunately the boolean types are not supported by this module, so in this library we provide an additional `Boolean` class to complete the picture.


Check the [Usage](./usage/) page for more details about the framework, and [the validators list page](https://smarie.github.io/python-valid8/validators/) for a complete list of validators available.


## `valid8` Design goals

 * Separation of concerns: we want to separate *value* validation from *type* validation. The library is compliant with the use of an additional PEP484-based type validation library such as enforce and pytypes. Optionality/Mandatoryness is the only feature available on both sides, as it is sometimes not intuitive to do with PEP484.
 * Validation should be available as a decorator, but also **TODO** inline anywhere in the code
 * The validation decorator should be compliant with `autoclass`, to enable automatic creation of validated property setters
 * python-first, not schema-first. Maybe it will be useful to provide bridges with json/xml/etc binding libraries later on, but for now we focus on small, simple, argument value validation
 * Validators should be functions, lambdas, or objects (through the __call__magic method)
 * **TODO** There should be a way to retrofit an existing validation function into a `valid8`-compliant validator
 * We should provide a logic for composition and reuse of validators
 * Enforce explicit validation errors even for lambdas (provide a helper method)
 * Ability to disable validation with no overhead 
 * Most important than everything, provide an easy way to list the available validators while developing : through the doc but also through python package organization


## Main features

* **`@validate`** is a decorator for any method, that adds input validators to the method.

* Many validators are provided out of the box to use with `@validate`: `gt`, `between`, `is_in`, `maxlen`... check them out in [the validators list page](https://smarie.github.io/python-valid8/validators/). But you can of course use your own, too.

* Equivalent manual wrapper methods are provided for all decorators in this library: `validate_decorate(func, **validators)`


## Other Validation libraries

Many validation libraries are available on [PyPi](https://pypi.python.org/pypi?%3Aaction=search&term=valid&submit=search) already. The following list is by far not exhaustive, but gives an overview. Do not hesitate to contribute to this list with a pull request! For each library, the date provided is that of the last commit at the time of writing (10/2017). 

*Note to the authors: due to the large number of libraries below there **must** have been errors in my analysis. Please let me know if I wrote something wrong, the intent is really not to criticize your library but rather to better understand the various mechanisms available out there for reuse.*

### PEP484 type checkers

The following libraries use your PEP484 type and optionality/mandatoryness annotations to check the function inputs and sometimes outputs.

 * [enforce](https://github.com/RussBaz/enforce)
 * [pytypes](https://github.com/Stewori/pytypes)
 * [typeguard](https://github.com/agronholm/typeguard)
 * [typecheck-decorator](https://github.com/prechelt/typecheck-decorator)

### Type+Value validation

The following frameworks provide both type and value validation, and for most of them it would be quite irrelevant to separate value validation from type validation.

 * [PyContracts](https://andreacensi.github.io/contracts/index.html): (2017) Annotation. Parsing-based (the contract is a string when it comes to value validation). Ability to disable through a function call. Validators are functions or specific predefined grammar elements. Logical operations on validators are supported.
 * [thedoctor](https://github.com/hhuuggoo/thedoctor): (2015) Annotation. Ability to disable with an environment variable. Dictionary validation. Helper `true` to support lambdas while throwing validation exceptions. A few validators. Validators are functions. No logical operations on validators.
 * [fivalid](https://github.com/AkiraKito/fivalid) :(2012) number, iterable, basic min/max, many text validators : free text with forbidden sentences, regexp, split on parts, All/Any/Not validator logic, a validator is an object
 * [validate](http://www.voidspace.org.uk/python/validate.html): (2009) quite old, a few basic validators (str/list length, int min/max values, ip_addr) mixed with type validation. Validators are functions.

### Mostly Type validation

These packages seem to mostly have been developed for type validation, not much for value validation:

 * [py-validate](https://github.com/gfyoung/py-validate): (2017) a few non-type validators even, odd, number. Validators ('shortcuts') are functions.
 * [pyvalid](http://uzumaxy.github.io/pyvalid/): (2017) mostly type validation except for value equality or size. Object fields validation. A validator is an object, collection of smaller checkers (StringValidator has min_len checker, max_len_checker, etc.)

### Schema-based validation

These libraries check that data is valid with respect to a **schema**. 

 * [schema](https://github.com/keleshev/schema) (2017) 
 * [validr](https://github.com/guyskk/validr) (2017) "10X faster than jsonschema, 40X faster than schematics". Based on [Isomorph-JSON-Schema](https://github.com/guyskk/validr/blob/master/Isomorph-JSON-Schema.md)
 * [colander](https://docs.pylonsproject.org/projects/colander/en/latest/) (2017). A framework for serialization+deserialization including schema validation. With validators for strings, mappings, and lists
 * [python-jsonschema-objects](https://github.com/cwacek/python-jsonschema-objects) (2017). Automatic Python binding generation from JSON Schemas 
 * [PyValitron](http://clivern.github.io/PyValitron/) (2016) separation of the concepts of validators / sanitizers (for text: lower case, strip, etc.). Quite a number of validators.
 * [pyvalidator](https://github.com/devdoomari/pyvalidator) (2015)
 * [validator](https://github.com/wilhelm-murdoch/validator) (2014) A few built-in validators. validator are objects (Rule)

### Validation of data 'at the entry point'

#### from Forms

Data from forms sometimes requires validation to follow some kind of process with several steps, where a validation context (permissions) may need to be maintained.

 * [formencode](http://www.formencode.org/en/latest/): (2017) a complete framework to validate and convert data entered in forms. Includes a number of domain-specific validators
 * [kanone](https://github.com/doncatnip/kanone) (2013) validation and conversion of data entered in forms. Notion of context. validator logic + composition (to reuse while parametrizing)
 * [django forms](https://docs.djangoproject.com/en/1.11/ref/forms/fields/): (2017) provides a number of built-in Field classes

#### from CLI

 * [click](http://click.pocoo.org/5/) (2017) integrates a number of built-in validators for arguments and options (file paths, etc.)
 * [docopt](https://github.com/docopt/docopt/commits/master) (2016) delegates to [schema](https://github.com/keleshev/schema) for validation

### Domain-specific validators / validators for specific data types / validators without framework

These packages provide validation functions, not validation frameworks. Therefore you could wish to reuse some of these functions in combination with `valid8`.

 * [pandas-validation](http://pandas-validation.readthedocs.io/en/latest/): (2017) pandas dataframes
 * [pandas-validator](https://github.com/c-data/pandas-validator): (2017) pandas dataframes
 * [validators](https://validators.readthedocs.io/en/latest/): (2017) email, iban, ip, slug, truthy, url, uuid, finnish business id...
 * [validatish](https://github.com/ish/validatish) (2011): a few validation functions for integers, strings, required/optional, etc.
 * [python-phonenumbers](https://github.com/daviddrysdale/python-phonenumbers) (2017): guess what?
 * [validate-email-address](https://pypi.python.org/pypi/validate-email-address) (2016): guess what ? It is a fork of [validate_email](https://github.com/syrusakbary/validate_email/commits/master) (2015).
 * ...

### Other resources concerning validation frameworks:
 
 * A [discussion](https://opensourcehacker.com/2011/07/07/generic-python-validation-frameworks/) about the various frameworks out there
 * The [apache commons lib for validation](http://commons.apache.org/proper/commons-validator/apidocs/org/apache/commons/validator/routines/package-summary.html#package_description)


## See Also - Other

 * [decorator](http://pythonhosted.org/decorator/) library, which provides everything one needs to create complex decorators easily (signature and annotations-preserving decorators, decorators with class factory) as well as provides some useful decorators (`@contextmanager`, `@blocking`, `@dispatch_on`). We use it to preserve the signature of wrapped methods.

*Do you like this library ? You might also like [these](https://github.com/smarie?utf8=%E2%9C%93&tab=repositories&q=&type=&language=python)* 


## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-valid8](https://github.com/smarie/python-valid8)
