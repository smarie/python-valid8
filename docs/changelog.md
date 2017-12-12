### 2.0.0 - Major improvements and refactoring

 * New and improved entry points:
 
    - **Function inputs validation**: `@validate_arg` may be used instead of `@validate` to add input validation argument by argument instead of all in the same decorator (same functionality, this is just a question of style). The manual decorator `validate_decorate` was also renamed `decorate_with_validation` for clarity
    - **Inline validation**: two new functions `assert_valid` and `is_valid`, allowing users to perform validation anywhere in their code in defensive programming mode (`assert_valid`) or case handling mode (`is_valid`)
    - **Common Validator class**: the common logic behind all the above entry points. It offers two methods for defensive programming (`validator.assert_valid`) and case handling (`validator.is_valid`). It may also be used directly by users, to 'pre-compile' validators, so that they are not constructed at every call like when using `assert_valid` and `is_valid`. But the difference is probably negligible.

 * Clearer separation of concepts:
 
    - **Entry points** (the above) know the full validation context, and raise `ValidationError` (or a subclass such as `InputValidationError`) when validation fails. The `ValidationError` object holds all information available concerning that validation context, and may be used by your application to improve or internationalize error messages.
    - **Base validation functions** (your methods or the ones from utility libraries including valid8) *may* raise subclasses of `BaseFailure` such as `Failure` if they wish to benefit from this helper type as well as ease applicatoin-level error handling and internationalization. The helper method `failure_raiser` allows to add such a friendly exception to a method not raising it (such as a lambda).
 
 * Better syntax to define base validation functions in entry points: 
 
    - base validation function(s) can be provided as a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. 
    - Nested lists are supported and indicate an implicit `and_` (such as the main list). 
    - [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of callables, they will be transformed to functions automatically.
    - Tuples indicate an implicit `failure_raiser`. Combined with mini_lambda, this is a very powerful way to create validation functions: `(Len(s) > 0, 'The value should be an empty string')` or `(Len(s) > 0, EmptyStringFailure)`. 

 * Minor improvements of the base functions library
 
    - split in independent files `validators_collections`, `validators_comparables`, `validators_numbers` so as to ease maintenance and possible contributions in the future
    - added `length_between` validator
    - Most built-in validator generators have their corresponding `__name__` now correctly set resulting in more user-friendly error messages

 * Improvements of the boolean operators

    - `and_`, `or_`, `xor_` now support variable number of arguments (no need to pass a list anymore)
    - `not_`, `and_`, `or_`, `xor_` now raise consistent exceptions (subclasses of `BasicFailure`), with a user-friendly error message indicating the detailed validation results.
    
 * A lot of new tests


### 1.0.0 - First public version

 * Initial fork from autoclass 1.8.1
