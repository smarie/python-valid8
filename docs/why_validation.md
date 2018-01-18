# Why would I need a validation library ?

*As for the whole `valid8` project, this page is open to contribution, do not hesitate to submit issues or pull requests !*


## What is validation - goals

A variable `x`, or several variables, are to be used as inputs in a piece of code. These variables might have been received from an external, untrusted/error-prone source such as a caller code, a cli, web form, a web service client, data files, etc. 

Validation is *the process of handling bad values* so as to 

 * **make the sender of these bad values aware that they are bad**, and aware of *why* they are bad. This is typically done with *explicit, user-friendly error messages* sent if anything went wrong during validation (even the unexpected!). What is key here is to remember that the caller's primary concern is *first* to know what was validated and why (**intent / requirement for good data**), *then* the **means / inner details** about e.g. what library you are using to validate his data, and its particular error message.

 * **stop processing early**, so that the code does not get an opportunity to fall into a harder-to-detect bug, or so as to avoid performing a computationally expensive task if it is useless. This is also called defensive programming, or [offensive programming](https://en.wikipedia.org/wiki/Offensive_programming).
 

## How do you write validation today

If you are an experienced coder, you probably *already* implement validation in a number of ways, whether to check the variables' types and/or values. Below we present the main styles.


### Implicit / 'pythonic' way

The good old *"better ask for forgiveness than for permission"*: do not validate, just try to use the variable and see if it works. If something goes wrong, wrap it with a more appropriate user-friendly exception.

```python
def pythonic_function(x):
    try:
        # try to use x as if it were valid
        ...
    except <ExceptionType> as e:
        # raise the appropriate error message based on the caught exception
        raise <AppropriateException>.with_traceback(e.__traceback__)
    else:
        # here we can use x safely
        ...
        # yes this is a valid construct :) you can use it to distinguish the lines
        # of code that may raise an error from those that may not. In practice it
        # is rarely used, you would put everything in the try block. 
```

This style has the advantage of being compact but has two major drawbacks:

 * **useless long-running operations**: if the exception happens late in the code, that my lead to a long waiting time for the caller before it gets notified
 * **undetected bad data / 'crap in-crap out'**: for scientific applications such as machine learning, it might be that invalid data goes all the way through the code until you get a result, without throwing a single exception. It might even be hard to see that the output is actually completely wrong, until much further in the application lifecycle.

(thanks [source for the try-except-else construct](https://openclassrooms.com/courses/apprenez-a-programmer-en-python/les-exceptions-4))


### Explicit / 'traditional' way

With this style you explicitly validate the variables before using them. To that end you typically rely on a blend of

 * **custom validation statements** such as `x > 0`, that might contain function calls, such as `sqrt(x) > 0.5`. These functions might raise exceptions on some edge cases (`sqrt(-1)`)
 * **reused user-made or third party validation functions**, such as `isfinite(x)` or `assert_array_equal(x, ref)`. Many, many such functions are available out there from various libraries - here is an [extract](other_libs#domain-specific-validators-validators-for-specific-data-types-validators-without-framework). There are two predominant styles out there:
 
    * *boolean testers* such as `isfinite` : they return `True` in case of success and `False` in case of failure, and therefore do not provide any details about the failure when they fail. Sometimes they continue to raise exceptions on edge cases (`isfinite(None)`, `isfinite(1+1j)`).
    * *failure raisers* such as `check_uniform_sampling` or `assert_array_equal`: they do not return anything in case of success, but raise exceptions with details in case of failure.

Blending all of the above to get a consistent validation process is 'the art of the master blender', a case-by-case story, where you typically wrap everything in a master try/except since even boolean testers and custom validation statements can raise exceptions (`sqrt(x) > 0.5` raises an exception if x is `-1`). For example:

```python
def conservative_function(x):

    try:
        if isfinite(x) and sqrt(x) < 10:  # <- even these can raise exceptions!
            raise <AppropriateException>
    
        check_uniform_sampling(x)
        
    except Exception as e:
        # raise the appropriate error message based on the caught exception
        raise <AppropriateException> from e
    
    # here we can use x safely
    ...
```

Also note that it is **not easy** to combine *failure raisers* together, or with *boolean testers*, in a boolean logic style. For example below we perform a virtual `or` between two *failure raisers*:

```python
def conservative_function(x):

    try:
        check_uniform_sampling(x)
    except Exception as e:
        # First asserter failed, let's try the other one
        try:
            assert_array_equal(x, ref)
        except Exception as f:
            # raise the appropriate error message based on the caught exception
            raise <AppropriateException> from e  # or f ?
    
    # here we can use x safely
    ...
```

#### Special case of `assert`

`assert` could be thought of as a good tool to perform validation:

```python
def function_with_assert(x):
    
    assert <validation_statement_on_x>, "invalid x : ..."

    # here we can use x safely
```

However it has three major drawbacks that make it unusable in practice:

 * the error raised in case of failure is an `AssertionError`, which is usually not the type of error you want to raise if you want unique error types for each kind of applicative validation, and it lacks customizability
 * if `<validation_statement_on_x>` raises exceptions, they will be raised directly and not wrapped by the `AssertionError` and used as the `__cause__`: that might lead to several exception types for the same applicative intent
 * `assert` can be disabled at application-level: the statement won't be executed if the code is executed in optimized mode, as explained in the [documentation](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement). 

To quote [this source](https://mail.python.org/pipermail/python-list/2013-November/660568.html) *"Many people use asserts as a quick and easy way to raise an exception if an argument is given the wrong value. But this is wrong, dangerously wrong, for two reasons. The first is that AssertionError is usually the wrong error to give when testing function arguments. But, and more dangerously, there's a twist with assert: it can be compiled away and never executed, if you run Python with the -O or -OO 
optimization flags [...]"*. In addition here again, note that if the `<validate>` function itself may raise Exceptions, you can end up with two kind of exceptions raised. 


## What are we missing today for general-purpose validation

We saw in the examples above that [implicit validation](#implicit-pythonic-way) and [asserts](#special-case-of-assert) are not satisfying, therefore we are left with [explicit handcrafted validation](#explicit-traditional-way). What are the drawbacks as of today, where could we make progress ?


### Compactness / readability

It takes far too many lines of code to implement [explicit handcrafted validation](#explicit-traditional-way). This is a pity, as it does not encourage developers to insert validation in their code, and it makes the code less readable/maintainable. 

Having a solution to write most validation tasks in **one or two lines of code** would completely change the game: people would actually do it more often (and with actual pleasure doing it), and hopefully the amount of annoying cryptic exceptions we receive daily from our favorite opensource libraries would reduce significantly. 

If this goal is reached, this would improve quality of small open source projects over time. Indeed, with limited resources (time+human), validation is often skipped, which is not the case for "more serious" projects with a full team of developers.


### Exceptions consistency

There are many choices left in [explicit handcrafted validation](#explicit-traditional-way) concerning the exception that is raised in case of validation failure. This may make any application/library rapidly lack consistency except for highly skilled coders. The following points in particular need to be handled consistently... but do we take the time to do it (especially when under pressure for delivery)?

 * validation **root exception types** are not standard across developers and even inside a code base. It is recommended to use [`TypeError`](https://docs.python.org/3/library/exceptions.html#TypeError) for type validation and [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError) for value validation, or any subclass of those, but at the same time we might wish to have **a common `ValidationError` type** holding validation context and intent ; so we have to use multiple inheritance to do this right
 * when failure comes from a caught inner exception, the **`__cause__`** flag of the wrapper validation exception would need to be correctly set (or `raise e from f`), everywhere, consistently 
 * if we wish validation exceptions to easily be associated with **error codes** when exchanged with the rest of the application (web front-end, etc.), for **internationalization (i18n)** purposes, the best practice in python would be to create one exception class per type of error, so that an exception class = an error code. We *can* do this, but here again we have to think about it everywhere to keep consistency.
 * even in plain english, validation **messages** should be user-friendly otherwise the user may struggle some time to understand why the value he entered was not correct. This can be mitigated if we have a global error code handler at the top of our application, that re-writes the appropriate internationalized message before sending it back to the user.

### Easy blending to reuse base validation functions

We saw above that with [explicit handcrafted validation](#explicit-traditional-way), we often end up reusing functions that are written in two incompatible styles (*boolean testers* and *failure raisers*), not to mention our own custom *validation statements*.

Providing ways to easily blend those would encourage a larger reuse of privately made or community-grown validation libraries such as [these](other_libs#domain-specific-validators-validators-for-specific-data-types-validators-without-framework). Less boring copy/paste, more leveraging existing good work.
 

### Functions and classes

Function inputs and outputs as well as class fields could be validated at function/class definition directly, instead of inside the function body / attribute setter.


## Note on entry-point validation: Cli, Schema and Forms

If you are sure that nobody will access your code directly (e.g. you do not share it as a library), you may wish to only perform value validation directly at the entry point, whether it is a command line interface, a web form or a soap/rest webservice in json or xml. This is perfectly fine and libraries providing the entry-point often come with validators/decorators bundled inside, such as in [click](http://click.pocoo.org) or [django](https://docs.djangoproject.com/search/?q=forms). See [here](other_libs#validation-of-data-at-the-entry-point).

However as soon as you wish to also share your code as a library, you end up needing to maintain two validation frameworks: one for the entry points, and one for the library. There is no easy solution to solve this problem:

 * you may wish to only perform validation in you core library functions, or core library's API. This can be enhanced by the creation of 'validated objects' for example using [autoclass](https://smarie.github.io/python-autoclass/), so that you do not re-validate in every function the object contents once it has been created
 * you may need to still perform entry point-validation, may it only for the reason that you share a schema as a contract with your customers (through [swagger](https://swagger.io/) or equivalent).
 