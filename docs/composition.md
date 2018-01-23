# Built-in composition functions

You can use the following methods to compose **base validation functions**, so as to build a function to be used in one of the `valid8` decorators presented [here](./index).


## not_

`not_(validation_func: ValidationFuncs, catch_all: bool = False)`

Generates the inverse of the provided validation functions: when the validator returns `False` or raises a `Failure`, this function returns `True`. Otherwise it raises a `DidNotFail` failure.

By default, exceptions of types other than `Failure` are not caught and therefore fail the validation (`catch_all=False`). To change this behaviour you can turn the `catch_all` parameter to `True`, in which case all exceptions will be caught instead of just `Failure`s.

Note that you may use `not_all(<validation_functions_list>)` as a shortcut for `not_(and_(<validation_functions_list>))`

See `help(not_)`

## and_

`and_(\*validation_func: ValidationFuncs)`

An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a `AtLeastOneFailed` failure on the first `False` received or `Exception` caught.

Note that an implicit `and_` is performed if you provide a list of validators to any of the entry points (`validate`, `validator`/`validation`, `@validate_arg`, `@validate_field` ...)
    
See `help(and_)`

## or_

`or_(\*validation_func: ValidationFuncs)`

An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be silently caught. In case of failure, a global `AllValidatorsFailed` failure will be raised, together with details about all validation results.

See `help(or_)`

## xor_

`xor_(\*validation_func: ValidationFuncs)`

A 'xor' validation function: returns `True` if exactly one of the provided validators returns `True`. All exceptions will be silently caught. In case of failure, a global `XorTooManySuccess` or `AllValidatorsFailed` will be raised, together with details about the various validation results.

See `help(xor_)`

## not_all

`not_all(\*validation_func: ValidationFuncs, catch_all: bool = False)`

An alias for not_(and_(validators)).

See `help(not_all)`

## failure_raiser

`failure_raiser(\*validation_func: ValidationFuncs, failure_type: 'Type[WrappingFailure]' = None, help_msg: str = None, \*\*kw_context_args)`

This function is automatically used if you provide a tuple `(<function>, <msg>_or_<Failure_type>)`, to any of the methods in this page or to one of the `valid8` decorators. It transforms the provided `<function>` into a failure raiser, raising a subclass of `Failure` in case of failure (either not returning `True` or raising an exception)

See `help(failure_raiser)`

## skip_on_none

`skip_on_none(\*validation_func: ValidationFuncs)`

This function is automatically used if you use `none_policy=SKIP`, you will probably never need to use it explicitly. If wraps the provided function (or implicit `and_` between provided functions) so that `None` values are not validated and the code continues executing.

See `help(skip_on_none)`

## fail_on_none

`fail_on_none(\*validation_func: ValidationFuncs)`

This function is automatically used if you use `none_policy=FAIL`, you will probably never need to use it explicitly.  If wraps the provided function (or implicit `and_` between provided functions) so that `None` values are not validated instead a `ValueIsNone` failure is raised.

See `help(fail_on_none)`
