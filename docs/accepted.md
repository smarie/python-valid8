# Accepted base validation functions

There seem to be two main styles out there when it comes to writing validation functions: 

 * *boolean testers* such as `isfinite` : they return `True` in case of success and `False` in case of failure, and therefore do not provide any details about the failure when they fail. Sometimes they continue to raise exceptions on edge cases (`isfinite(None)`, `isfinite(1+1j)`).
 
 * *failure raisers* such as `check_uniform_sampling` or `assert_series_equal`: they do not return anything in case of success, but raise exceptions with details in case of failure.

In order to be as open as possible, the definition of accepted functions in `valid8` [decorators](./index#validating-functions-classes), and in the [composition framework](./composition) provided, is very large. Is considered a 'valid' validation function any callable that:

 * takes a single argument as input
 * returns `True` or `None` in case of success

That's the two only requirements. That means that base validation functions **may fail the way they like**: returning `False` or something else, raising `Exception`s.

## Name used in error messages

In validation error messages, the name of the function that will be displayed is obtained from the validation callable `v_callable` with the following formula:

```python
name = v_callable.__name__ if hasattr(v_callable, '__name__') else str(v_callable)
```

## Built-in exceptions

As explained above nothing else than returning `True` or `None` in case of success is required by `valid8`. However when creating your own base functions you might wish to create *failure raisers* rather than *boolean checkers* because in case of failure they can provide many useful details in the raised exception. 

If you go that way, you may wish to reuse one of the three exception classes `Failure`, `WrappingFailure` and `CompositionFailure`,  that are provided as goodies in `valid8`. You can find some inspiration [here](https://github.com/smarie/python-valid8/blob/master/valid8/validation_lib/collections.py).
