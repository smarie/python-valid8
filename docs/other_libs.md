# Other Validation libraries

Many validation libraries are available on [PyPI](https://pypi.python.org/pypi?%3Aaction=search&term=valid&submit=search) already. The following list is by far not exhaustive, but gives an overview. Do not hesitate to contribute to this list with a pull request! For each library, the date provided is that of the last commit at the time of writing (10/2017). 

*Note to the authors: due to the large number of libraries below there **must** have been errors in my analysis. Please let me know if I wrote something wrong, the intent is really not to criticize your library but rather to better understand the various mechanisms available out there for reuse.*

## PEP484 type checkers

The following libraries use your PEP484 type and optionality/mandatoryness annotations to check the function inputs and sometimes outputs.

 * [enforce](https://github.com/RussBaz/enforce)
 * [pytypes](https://github.com/Stewori/pytypes)
 * [typeguard](https://github.com/agronholm/typeguard)
 * [typecheck-decorator](https://github.com/prechelt/typecheck-decorator)

## Type+Value validation

The following frameworks provide both type and value validation, and for most of them it would be quite irrelevant to separate value validation from type validation.

 * [PyContracts](https://andreacensi.github.io/contracts/index.html): (2017) Annotation. Parsing-based (the contract is a string when it comes to value validation). Ability to disable through a function call. Validators are functions or specific predefined grammar elements. Logical operations on validators are supported.
 * [thedoctor](https://github.com/hhuuggoo/thedoctor): (2015) Annotation. Ability to disable with an environment variable. Dictionary validation. Helper `true` to support lambdas while throwing validation exceptions. A few validators. Validators are functions. No logical operations on validators.
 * [fivalid](https://github.com/AkiraKito/fivalid) :(2012) number, iterable, basic min/max, many text validators : free text with forbidden sentences, regexp, split on parts, All/Any/Not validator logic, a validator is an object
 * [validate](http://www.voidspace.org.uk/python/validate.html): (2009) quite old, a few basic validators (str/list length, int min/max values, ip_addr) mixed with type validation. Validators are functions.

## Value validation

I recently found these two elegant frameworks:

 * [expects](https://expects.readthedocs.io/en/stable/)
 * [grappa](http://grappa.readthedocs.io/en/latest/)

## Mostly Type validation

These packages seem to mostly have been developed for type validation, not much for value validation:

 * [py-validate](https://github.com/gfyoung/py-validate): (2017) a few non-type validators even, odd, number. Validators ('shortcuts') are functions.
 * [pyvalid](http://uzumaxy.github.io/pyvalid/): (2017) mostly type validation except for value equality or size. Object fields validation. A validator is an object, collection of smaller checkers (StringValidator has min_len checker, max_len_checker, etc.)

## Schema-based validation

These libraries check that data is valid with respect to a **schema**. 

 * [voluptuous](https://github.com/alecthomas/voluptuous) (2017)
 * [schema](https://github.com/keleshev/schema) (2017) 
 * [datatyping](https://github.com/Zaab1t/datatyping) (2017)
 * [pyvalidator](https://github.com/devdoomari/pyvalidator) (2015) a modified fork of [schema](https://github.com/keleshev/schema)
 * [validr](https://github.com/guyskk/validr) (2017) "10X faster than jsonschema, 40X faster than schematics". Based on [Isomorph-JSON-Schema](https://github.com/guyskk/validr/blob/master/Isomorph-JSON-Schema.md)
 * [colander](https://docs.pylonsproject.org/projects/colander/en/latest/) (2017). A framework for serialization+deserialization including schema validation. With validators for strings, mappings, and lists
 * [python-jsonschema-objects](https://github.com/cwacek/python-jsonschema-objects) (2017). Automatic Python binding generation from JSON Schemas 
 * [PyValitron](http://clivern.github.io/PyValitron/) (2016) separation of the concepts of validators / sanitizers (for text: lower case, strip, etc.). Quite a number of validators.
 * [validator](https://github.com/wilhelm-murdoch/validator) (2014) A few built-in validators. validator are objects (Rule)
 * [jsonobject](https://github.com/dimagi/jsonobject) (2017): specific to json
 
## Validation of data 'at the application's entry point'

If your application can *only* receive data from the outside world through forms, CLI or web service inputs, you might wish to validate as early as possible (as soon as it is received) that it is correct. This is what these libraries provide:

### from Forms

Data from forms sometimes requires validation to follow some kind of process with several steps, where a validation context (permissions) may need to be maintained.

 * [formencode](http://www.formencode.org/en/latest/): (2017) a complete framework to validate and convert data entered in forms. Includes a number of domain-specific validators
 * [kanone](https://github.com/doncatnip/kanone) (2013) validation and conversion of data entered in forms. Notion of context. validator logic + composition (to reuse while parametrizing)
 * [django forms](https://docs.djangoproject.com/search/?q=forms): (2017) provides a number of built-in Field classes

### from CLI

 * [click](http://click.pocoo.org) (2017) integrates a number of built-in validators for arguments and options (file paths, etc.)
 * [docopt](https://github.com/docopt/docopt/commits/master) (2016) delegates to [schema](https://github.com/keleshev/schema) for validation

## Domain-specific validators / validators for specific data types / validators without framework

These packages provide base validation functions, not validation frameworks. Therefore you could wish to reuse some of these functions in combination with `valid8`.

 * [pandas-validation](http://pandas-validation.readthedocs.io/en/latest/): (2017) pandas dataframes
 * [pandas-validator](https://github.com/c-data/pandas-validator): (2017) pandas dataframes
 * [validators](https://validators.readthedocs.io/en/latest/): (2017) email, iban, ip, slug, truthy, url, uuid, finnish business id...
 * [validatish](https://github.com/ish/validatish) (2011): a few validation functions for integers, strings, required/optional, etc.
 * [python-phonenumbers](https://github.com/daviddrysdale/python-phonenumbers) (2017): guess what?
 * [validate-email-address](https://pypi.python.org/pypi/validate-email-address) (2016): guess what ? It is a fork of [validate_email](https://github.com/syrusakbary/validate_email/commits/master) (2015).
 * ...

## Other resources concerning validation frameworks:
 
 * A [discussion](https://opensourcehacker.com/2011/07/07/generic-python-validation-frameworks/) about the various frameworks out there
 * The [apache commons lib for validation](http://commons.apache.org/proper/commons-validator/apidocs/org/apache/commons/validator/routines/package-summary.html#package_description)
 