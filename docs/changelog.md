# Changelog

### 5.1.0 - PEP561 compliance

 - Package was made PEP561 compatible. Fixed [#55](https://github.com/smarie/python-valid8/issues/55)
 
 - Improved type hints for decorators so that they do not make the decorated item loose its type hints. Fixed [#56](https://github.com/smarie/python-valid8/issues/56)
 
 - Removed usage of `@with_signature` in favour of stub file in the `entry_points_annotations.py`. Fixed [#50](https://github.com/smarie/python-valid8/issues/50)

### 5.0.6 - Minor improvements

Improved `getfullargspec` so as to cover more builtins in python 3.

### 5.0.5 - bugfix - support for numpy True

Numpy `True` can be used (again) as a success condition in validation functions. Fixed [#53](https://github.com/smarie/python-valid8/issues/53)

### 5.0.4 - `pyproject.toml`

Added `pyproject.toml`.

### 5.0.3 - bug fixes

Fixed bug with mini-lambda < 2.2. Fixed [#48](https://github.com/smarie/python-valid8/issues/48).

Fixed bug in `is_in` when the reference object was a non-set container. Fixed [#47](https://github.com/smarie/python-valid8/issues/47).

### 5.0.2 - Bug fix

Fixed regression with non-able detection. Fixed [#46](https://github.com/smarie/python-valid8/issues/46).

### 5.0.0 - More betterness!

**Better syntax for `*validation_func`**:
 
 - you can provide a `tuple` `(<callable>, <help_msg>, <failure_type>)` to define a single failure raiser (before only `(<callable>, <help_msg>)` or `(<callable>, <failure_type>)` were supported). Fixes [#33](https://github.com/smarie/python-valid8/issues/33)

 - you can provide a `dict`-like to define several validation functions, where the key and values can contain `<callable>`, `<help_msg>`, `<failure_type>`. For example `{<help_msg>: (<callable>, <failure_type>)}` is supported. Fixes [#40](https://github.com/smarie/python-valid8/issues/40).

 - nested lists are however not supported anymore

 - the `<callable>` can now either have signature `f(v)`, `f(*args)`, `f(*args, **ctx)` or `f(v, **ctx)`, where `**ctx` can be used to receive contextual information. Fixes [#39](https://github.com/smarie/python-valid8/issues/39)

**`validation_lib` should be imported explicitly**

 - symbols from `valid8.validation_lib` are not imported automatically at package root anymore. You need to import them from `valid8.validation_lib`. This speeds up the library's import especially when you do not use the built-in functions. So instead of `from valid8 import is_even` you should now do `from valid8.validation_lib import is_even` (or `from valid8 import validation_lib as vlib` + `vlib.is_even`). Fixed [#35](https://github.com/smarie/python-valid8/issues/35).

**Major exceptions refactoring**

 - the main validation function in a `Validator` is now always a failure raiser, even if a single callable was provided. This major design choice made many simplifications possible in particular the string representation of exceptions (below). Fixes [#44](https://github.com/smarie/python-valid8/issues/44)

 - The string representation of `ValidationError` and `ValidationFailure` was greatly improved. In particular `ValidationError` does not display the name and outcome of the validation function anymore (since it is always a failure, see above), and `ValidationFailure` now has a "compact" string representation option in a new `to_str()` method, used in composition messages to simplify the result. Composition failures are also represented in a more compact way.

 - `failure_raiser` moved to `base` submodule with its associated type hints `ValidationCallable` and `ValidationCallableOrLambda`. It now only accepts a single validation function argument ; this is more intuitive and separates concerns with the other higher-level functions. If you used it with several inputs in the past, you can use `and_(...)` instead, it will be strictly equivalent to the old behaviour.
 
 - new `@as_failure_raiser` decorator to create a failure raiser by decorating an existing validation function. Fixes [#36](https://github.com/smarie/python-valid8/issues/36).

 - `WrappingFailure` does not exist anymore, it was merged with `Failure` class for architecture simplification. So there are two main exception classes in valid8 now: `ValidationError` and `ValidationFailure`. When the validation callable does not raise an instance of `ValidationFailure` itself, the `Invalid` subclass is used. Fixes [#41](https://github.com/smarie/python-valid8/issues/41)


**Misc**

 - `assert_subclass_of` now exposed at root level (for consistency with `assert_instance_of`, to be used in the context manager entry point)
 
 - Added `__version__` attribute to comply with PEP396, following https://smarie.github.io/python-getversion/#package-versioning-best-practices. Fixes [#38](https://github.com/smarie/python-valid8/issues/38).

 - `result_is_success` is now inlined and does not use a set expression anymore. Fixed [#37](https://github.com/smarie/python-valid8/issues/37)
 - Improved all examples of `Failure` in the validation lib to show how a better practice where the `help_msg` stays at class level but can be overridden failure instance by failure instance.
 - Removed `length_between` `open_left/right` arguments as it does not make sense, to continue fixing [#29](https://github.com/smarie/python-valid8/issues/29)

 - new subpackage `utils` where all util submodules now live
 - New submodule `common_syntax` where all the logic to handle the `*validation_func` input syntax resides
 - some type hints renamed for clarity: 
 
    - before: `ValidationFuncs` / `ValidationFunc` / `CallableType` / `Callable`
    - now: `OneOrSeveralVFDefinitions` / `ValidationFuncDefinition` / `ValidationCallableOrLamba` / `ValidationCallable`. 
    - `ValidationFuncs` still exists as a short alias for `OneOrSeveralVFDefinitions`.
 
 - fixed a few type hints too: tuples with unlimited length were not declared correctly. Now using the ellipsis `Tuple[<type>, ...]`.


### 4.2.1 - Minor error message fix

Error messages improvements: removed the brackets in `Wrong value: [...]` for the `Failure` details. Fixed [#32](https://github.com/smarie/python-valid8/issues/32).

### 4.2.0 - validation lib improvements

 * Removed the useless 'strict' length validators: removed `min_len_strict` and `max_len_strict` in `validate` entry point, and removed `strict` argument in `validation_lib`'s `minlen` and `maxlen`. Indeed length is an integer by python framework definition, so it is always more compact to do +1 or -1 to the number. Fixes [#29](https://github.com/smarie/python-valid8/issues/29).

 * New `empty` and `non_empty` built-in validators in `validation_lib`. New `empty` argument in `validate`. Fixes [#31](https://github.com/smarie/python-valid8/issues/31).

### 4.1.2 - Bugfix for python 3.5.2

Fixed [#30](https://github.com/smarie/python-valid8/issues/30) again, and fixed issue with python 2 appearing with the fix.

### 4.1.1 - Bugfix for python 3.5.2

Fixed [#30](https://github.com/smarie/python-valid8/issues/30).

### 4.1.0 - `validate` instance/subclass fix

 * `assert_instance_of` and `assert_subclass_of` (used in the `validate` inline entry point) fixed so as to support `Enum` types. Fixed [#28](https://github.com/smarie/python-valid8/issues/28). **Important**: only `tuple` are now supported when several types are provided in `validate`'s `instance_of` and `subclass_of` arguments. This is to has a closer behaviour to the python stdlib.

### 4.0.1 - better mini-lambda compliance

 * Adapted code to leverage latest `mini_lambda`. Fixes [#27](https://github.com/smarie/python-valid8/issues/27).

### 4.0.0 - python 2.7 support + minor improvements

 * Python 2.7 is now supported. This fixes [#25](https://github.com/smarie/python-valid8/issues/25).

 * Dependencies updated: now `makefun` is used instead of `decorator` to create signature-preserving wrappers. `decopatch` is also used to create all the decorators consistently.

 * `assert_instance_of` and `assert_subclass_of` (used in the `validate` inline entry point) were improved so as to benefit from python 3's capability to compare with several classes, and so that users can provide the reference classes as an iterable rather than a set. Fixes [#26](https://github.com/smarie/python-valid8/issues/26).

 * More compact tracebacks for `validate` method: removed exception causes.

 * Fixed type inspection for old python 3.5 versions.

### 3.7.3 - python 3.7 support

 * Fixed [#24](https://github.com/smarie/python-valid8/issues/24)

### 3.7.2 - Bug fix

 * Fixed [#23](https://github.com/smarie/python-valid8/issues/23)

### 3.7.1 - Bug fix

 * Fixed [#22](https://github.com/smarie/python-valid8/issues/22)

### 3.7.0 - Typos detection and np.nan handling

 * Fixed typos detection: [#21](https://github.com/smarie/python-valid8/issues/21)
 * Fixed np.nan handling: [#20](https://github.com/smarie/python-valid8/issues/20)

### 3.6.0 - Error messages improvements + create_manually class method in ValidationError

 * values with string representation larger than 100 characters are not anymore displayed in the error messages by default. Fixes [#19](https://github.com/smarie/python-valid8/issues/19)
 * new class method `ValidationError.create_manually` to create validation errors manually in some edge cases, without a validator entry point

### 3.5.5 - Fixed import * issue

 * Fixes [#18](https://github.com/smarie/python-valid8/issues/18)

### 3.5.4 - Improved init

 * The init file has been improved so as not to export symbols from other packages. Fixes [#15](https://github.com/smarie/python-valid8/issues/15)

### 3.5.3 - fixed optionality detection bug

 * internal custom copy of `typing_inspect` module was correct for old versions of python but created a bug on new versions of python: optionality detection was not working anymore when using `Optional[]`. Fixes [#16](https://github.com/smarie/python-valid8/issues/16) 

### 3.5.2 - support for older version of typing.py

 * removed dependency to `typing_inspect` module so that the module also runs with very old versions of typing.py

### 3.5.1 - Improved tracebacks

 * Fixed [#14](https://github.com/smarie/python-valid8/issues/14)

### 3.5.0 - improved PEP484-nonable detection

 * Now relying on typing_inspect to check if an argument is nonable, with support of `TypeVar` and `Union` including nesting.

### 3.4.0 - new features

 * Inline validation:
 
    - `validate` has a new argument `custom` where you can provide a callable method, or a list (same than for the decorators)
   
 * Examples:
 
    - one page per example - now with a dedicated test in the sources
   
 * mini-lambda support: now providing an `Instance_of` mini-lambda equivalent of `instance_of`, to raise proper `TypeError`. See example 3 for usage

### 3.3.0 - new features

 * Inline validation:
 
    - `validate` has several new arguments: `subclass_of`, `contains`, `subset_of`, `superset_of`, `length`, `equals`
    - `validator` has a new argument: `subclass_of`
    - New base function `assert_subclass_of`
    - `instance_of` and `subclass_of` are now dual functions: they can both serve as a function generators or as a simple functions for inline validation for example inside a `validator` context manager.
   
 * Decorators:
 
    - 2 new function generators `has_length` and `contains`
   
 * Bug fixes:
 
    - Fixed bug [#11](https://github.com/smarie/python-valid8/issues/11) where `ValidationError` could not be correctly printed in case of a templating issue.
   
 * New examples in the documentation

### 3.2.0 - new names and aliases for readability

 * `wrap_valid` context manager was renamed `validation` with alias `validator`. The deprecated old name remains accepted until next major release 4.x.
 * `quick_valid` function was renamed `validate`. The deprecated old name remains accepted until next major release 4.x.
 * `@validate` decorator was renamed `@validate_io`. The old name is now used to denote `quick_valid`, see above. Its `alidate` alias was removed (was it used anyway ?)
 

### 3.1.0 - new `instanceof` parameter

 * `quick_valid`'s parameters `allowed_types` and `allowed_values` were renamed `instance_of` and `is_in` respectively. 
 * `instance_of` parameter has been added to `wrap_valid` too. This solved [#10](https://github.com/smarie/python-valid8/issues/10)
 * `assert_instance_of` function is now available for use with `wrap_valid`

### 3.0.1 - fixed bug with `wrap_valid` when run from a terminal

 * Fixed [#8](https://github.com/smarie/python-valid8/issues/8) (OSError when executing from interpreter terminal)

### 3.0.0 - new inline validators + dynamic exception typing

 * Added two new entry points that should be more useful and usable than `assert_valid` for inline validation:
 
    - `quick_valid` for limited but simple one-line validation (most common tasks)
    - `wrap_valid` for more flexible validation (a contextmanager so it takes 2 lines)
 
 * `ValidationError` does not inherit from `ValueError` anymore. Instead an exception type is dynamically created with the appropriate base class (either `ValueError` or `TypeError`) when a validation exception is raised. This can be disabled by explicitly inheriting from one or the other in custom exception types.
 
 * improved documentation overall

 * Now compliant with old versions of `typing` module: `typing.Type` is not imported explicitly anymore.

### 2.1.0 - new annotation @validate_field
 
 * @validate_field allows users to validate class fields, whether they are descriptors, properties, or constructor arguments. Check the documentation for details!


### 2.0.0 - Major improvements and refactoring

 * New and improved entry points:
 
    - **Function inputs validation**: `@validate_arg` may be used instead of `@validate` to add input validation argument by argument instead of all in the same decorator (same functionality, this is just a question of style). A new decorator `@validate_out` is provided. The manual decorator `validate_decorate` was also renamed `decorate_with_validation` for clarity
    - **Inline validation**: two new functions `assert_valid` and `is_valid`, allowing users to perform validation anywhere in their code in defensive programming mode (`assert_valid`) or case handling mode (`is_valid`)
    - **Common Validator class**: the common logic behind all the above entry points. It offers two methods for defensive programming (`validator.assert_valid`) and case handling (`validator.is_valid`). It may also be used directly by users, to 'pre-compile' validators, so that they are not constructed at every call like when using `assert_valid` and `is_valid`. But the difference is probably negligible.

 * Clearer separation of concepts:
 
    - **Entry points** (the above) know the full validation context, and raise `ValidationError` (or a subclass such as `InputValidationError` or *your* custom subclass) when validation fails. The `ValidationError` object holds all information available concerning that validation context, and may be used by your application to improve or internationalize error messages.
    - **Base validation functions** (your methods or the ones from utility libraries including valid8) *may* raise subclasses of `Failure` or `WrappingFailure` if they wish to benefit from this helper type as well as ease application-level error handling and internationalization. The helper method `failure_raiser` allows to add such a friendly exception to a method not raising it (such as a lambda).
 
 * Better syntax to define base validation functions in entry points: 
 
    - base validation function(s) can be provided as a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. 
    - Nested lists are supported and indicate an implicit `and_` (such as the main list). 
    - [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of callables, they will be transformed to functions automatically.
    - Tuples indicate an implicit `failure_raiser`. Combined with mini_lambda, this is a very powerful way to create validation functions: `(Len(s) > 0, 'The value should be an empty string')` or `(Len(s) > 0, EmptyStringFailure)`. 

 * Minor improvements of the base functions library
 
    - split in independent files `collections`, `comparables`, `numbers` in a `validation_lib` submodule so as to ease maintenance and possible contributions in the future
    - added `length_between` validator
    - added type validation functions `instance_of` and `subclass_of`
    - all functions now raise unique subclasses of `Failure` ('eat your own dog food')
    - Most built-in validator generators have their corresponding `__name__` now correctly set resulting in more user-friendly error messages

 * Improvements of the composition operators

    - `and_`, `or_`, `xor_` now support variable number of arguments (no need to pass a list anymore)
    - `not_`, `and_`, `or_`, `xor_` now raise consistent exceptions (subclasses of `CompositionFailure`), with a user-friendly error message indicating the detailed validation results.
    
 * A lot of new tests


### 1.0.0 - First public version

 * Initial fork from autoclass 1.8.1
