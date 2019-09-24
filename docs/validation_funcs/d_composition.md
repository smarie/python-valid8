# Built-in composition functions

We have seen in [previous section](./c_simple_syntax.md) that an implicit "and" can be easily performed. However in some cases you might need additional ways to compose functions. A few tools are provided out of the box:

## not_

```python
not_(validation_func: ValidationFunc, 
     catch_all: bool = False)
```

Generates the inverse of the provided validation functions: when the validator returns `False` or raises a `ValidationFailure`, this function returns `True`. Otherwise it raises a `DidNotFail` failure.

By default, exceptions of types other than `ValidationFailure` are not caught and therefore fail the validation (`catch_all=False`). To change this behaviour you can turn the `catch_all` parameter to `True`, in which case all exceptions will be caught instead of just `ValidationFailure`s.

Note that the argument is a single callable. You may use `not_all(<validation_functions_list>)` as a shortcut for `not_(and_(<validation_functions_list>))` to support several validation functions in the 'not'.

See `help(not_)`

## and_

```python
and_(*validation_func: ValidationFuncs)
```

An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a `AtLeastOneFailed` failure on the first `False` received or `Exception` caught.

Note that an implicit `and_` is performed if you provide a list of validators to any of the entry points (`validator`/`validation`, `@validate_arg`, `@validate_field` ...). For `validate` you need to use an explicit one in `custom=<f>`.
    
See `help(and_)`

## or_

```python
or_(*validation_func: ValidationFuncs)
```

An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be silently caught. In case of failure, a global `AllValidatorsFailed` failure will be raised, together with details about all validation results.

See `help(or_)`

## xor_

```python
xor_(*validation_func: ValidationFuncs)
```

A 'xor' validation function: returns `True` if exactly one of the provided validators returns `True`. All exceptions will be silently caught. In case of failure, a global `XorTooManySuccess` or `AllValidatorsFailed` will be raised, together with details about the various validation results.

See `help(xor_)`

## not_all

```python
not_all(*validation_func: ValidationFuncs, 
        catch_all: bool = False)
```

An alias for not_(and_(validators)).

See `help(not_all)`

## skip_on_none

`skip_on_none(*validation_func: ValidationFuncs)`

This function is automatically used if you use `none_policy=SKIP`, you will probably never need to use it explicitly. If wraps the provided function (or implicit `and_` between provided functions) so that `None` values are not validated and the code continues executing.

See `help(skip_on_none)`

## fail_on_none

`fail_on_none(*validation_func: ValidationFuncs)`

This function is automatically used if you use `none_policy=FAIL`, you will probably never need to use it explicitly. If wraps the provided function (or implicit `and_` between provided functions) so that `None` values are not validated instead a `ValueIsNone` failure is raised.

See `help(fail_on_none)`
