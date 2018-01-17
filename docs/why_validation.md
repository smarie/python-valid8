# Why would I need a validation library ?

*As for the whole `valid8` project, this page is open to contribution, do not hesitate to submit issues or pull requests !*


## What is validation

A variable `x`, or several variables, are to be used as inputs in a piece of code. These variables might have been received from an external, untrusted/error-prone source such as a caller code, a cli, web form, a web service client, data files, etc. 

Validation is the process of handling bad values so as to make the sender of these bad values aware that they are bad, and possibly to stop processing them.


## Purpose of validation

The purpose may vary, but it is often one of these (please feel free to suggest other benefits here):

 * let users get **explicit error messages** when they did not input correct data (in the function, or indirectly in web forms, web service inputs, cli, etc.)
 * **defensive programming**: do not let the code get an opportunity to fall into a harder-to-detect bug. This is also called [offensive programming](https://en.wikipedia.org/wiki/Offensive_programming).
 * **avoid performing a computationally expensive task** if it is to discover at the very end of the execution that one of the inputs was a known incorrect situation.


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

 * useless long-running operations: if the exception happens late in the code, that my lead to a long waiting time for the caller before it gets notified
 * 'crap in-crap out': for scientific applications such as machine learning, it might be that invalid data goes all the way through the code until you get a result, without throwing a single exception. It might even be hard to see that the output is actually completely wrong, until much further in the application lifecycle.

(thanks [source for the try-except-else construct](https://openclassrooms.com/courses/apprenez-a-programmer-en-python/les-exceptions-4))


### Explicit / 'traditional' way

More conservative: here you explicitly validate the variables before using them. For this you typically rely on a blend of

 * **custom validation statements** such as `x > 0`, that might contain function calls, such as `sqrt(x) > 0.5`.
 * **user-made or third party base validation functions**, such as `isfinite(x)` or `assert_array_equal(x, ref)`. There are two predominant styles out there:
 
    * *boolean testers* such as `isfinite` : they return `True` in case of success and `False` in case of failure, and therefore do not provide any details about the failure when they fail.
    * *asserters* such as `check_uniform_sampling` or `assert_array_equal`: they do not return anything in case of success, but raise exceptions with details in case of failure.

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

Also note that it is **not easy** to combine *asserters* together, or with *boolean testers*, in a boolean logic style. For example below we perform a virtual `or` between two *asserters*:

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

 * the error raised in case of failure is an `AssertionError`, which is usually not the type of error you want to raise, and lacks customizability
 * if `<validation_statement_on_x>` raises exceptions, they will be raised directly and not wrapped by the `AssertionError`: that might lead to several exception types for the same applicative intent
 * it can be disabled at application-level: the statement won't be executed if the code is executed in optimized mode, as explained in the [documentation](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement). 

To quote [this source](https://mail.python.org/pipermail/python-list/2013-November/660568.html) *"Many people use asserts as a quick and easy way to raise an exception if an argument is given the wrong value. But this is wrong, dangerously wrong, for two reasons. The first is that AssertionError is usually the wrong error to give when testing function arguments. But, and more dangerously, there's a twist with assert: it can be compiled away and never executed, if you run Python with the -O or -OO 
optimization flags [...]"*. In addition here again, note that if the `<validate>` function itself may raise Exceptions, you can end up with two kind of exceptions raised. 


### Note on entry-point validation: Cli, Schema and Forms

If you are sure that nobody will access your code directly (e.g. you do not share it as a library), you may wish to only perform value validation directly at the entry point, whether it is a command line interface, a web form or a soap/rest webservice in json or xml. This is perfectly fine and libraries providing the entry-point often come with validators/decorators bundled inside, such as in [click](http://click.pocoo.org) or [django](https://docs.djangoproject.com/search/?q=forms). See [here](other_libs#validation-of-data-at-the-entry-point).

However as soon as you wish to also share your code as a library, you end up needing to maintain two validation frameworks: one for the entry points, and one for the library. There is no easy solution to solve this problem:

 * you may wish to only perform validation in you core library functions, or core library's API. This can be enhanced by the creation of 'validated objects' for example using [autoclass](https://smarie.github.io/python-autoclass/), so that you do not re-validate in every function the object contents once it has been created
 * you may need to still perform entry point-validation, may it only for the reason that you share a schema as a contract with your customers (through [swagger](https://swagger.io/) or equivalent).


## What are we missing today for general-purpose validation

### Compactness / readability

We saw in the examples above that it often takes several lines of code to implement value validation. This is a pity, as it does not encourage developers to insert validation in their code, and it makes the code less readable/maintainable.

### Functions and classes

Function inputs and outputs as well as class fields could be validated too.

### Consistency

We saw above the most typical ways that validation is done today by developers. As we could see there are many choices left concerning the exception that is raised in case of validation failure, which may make your code rapidly lack consistency except for highly skilled coders. The following points in particular need to be handled consistently... but do we take the time to do it (especially when under pressure for delivery)?

 * validation **root exception types** are not standard across developers and even inside a code base. You *should* use [`TypeError`](https://docs.python.org/3/library/exceptions.html#TypeError) for type validation and [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError) for value validation, or any subclass of those 
 * when failure comes from a caught inner exception, the **`__cause__`** flag of the wrapper validation exception would need to be correctly set (or `raise e from f`), everywhere, consistently 
 * if you wish validation exceptions to easily be associated with **error codes** when exchanged with the rest of the application (web front-end, etc.), for **internationalization (i18n)** purposes, the best practice in python would be to create one exception class per type of error, so that an exception class = an error code. You *can* do this, but here again you'll have to think about it everywhere to keep consistency.
 * even in plain english, validation **messages** should be user-friendly otherwise the user of your function may struggle some time to understand why the value he entered was not correct. Of course if you have some error code handling at the top of your application this is ok since you probably re-write the appropriate internationalized message before sending it back to the user.

### Reuse

At some point you will probably want to reuse validation functions. For example to validate that a dataframe has certain column names, or that a text string follows a certain regex. Today this can be done by finding some libraries [out there](#other-validation-libraries) and cherry-picking. It would be encouraged by a central catalog/page listing what kind of validation you can find in each library.
