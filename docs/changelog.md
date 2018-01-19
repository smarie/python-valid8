### 3.0.0 - new inline validators + dynamic exception typing

 * Added two new entry points that should be more useful and usable than `assert_valid` for inline validation:
 
   - `quick_valid` for limited but simple one-line validation (most common tasks)
   - `wrap_valid` for more flexible validation (a contextmanager so it takes 2 lines)
 
 * `ValidationError` does not inherit from `ValueError` anymore. Instead an exception type is dynamically created with the appropriate base class (either `ValueError` or `TypeError`) when a validation exception is raised. This can be disabled by explicitly inheriting from one or the other in custom exception types.
 
 * improved documentation overall

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
    - Tuples indicate an implicit `_failure_raiser`. Combined with mini_lambda, this is a very powerful way to create validation functions: `(Len(s) > 0, 'The value should be an empty string')` or `(Len(s) > 0, EmptyStringFailure)`. 

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
