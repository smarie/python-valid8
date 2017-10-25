# Why would I need a validation library ?

Good question, thanks for asking. Having a common understanding of this is key, otherwise this library will miss its target. As for the whole `valid8` project, this page is open to contribution, do not hesitate to submit issues or pull requests !

## How do you do today ?

If you are an experienced coder, you have probably *already* implemented validation in a number of ways:

 * 'pythonic' way: (thanks [source for the else-in-try construct](Thanks, https://openclassrooms.com/courses/apprenez-a-programmer-en-python/les-exceptions-4))

```python
def pythonic_function(x):
    try:
        # try to use x as if it were valid
        ...
    except <ExceptionType> as e:
        # raise the appropriate error message based on the caught exception
        raise <AppropriateException>.with_traceback(e.__traceback__)
    else:
        # yes this is a valid construct :) you can use it to distinguish the lines
        # of code that may raise an error from those that may not. In practice it
        # is rarely used, you would put everything in the try block. 
        
        # here we can use x safely
        ...
        
```

 * 'traditional' way:

```python
def conservative_function(x):
    if not <validate>(x):
        raise <AppropriateException>
    
    # here we can use x safely
    ...
```

 * 'assert' way. Note that this has a special behaviour since the statement won't be executed if the code is executed in optimized mode, as explained in the [documentation](https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement). To quote [this source](https://mail.python.org/pipermail/python-list/2013-November/660568.html) *"Many people use asserts as a quick and easy way to raise an exception if 
an argument is given the wrong value. But this is wrong, dangerously wrong, for two reasons. The first is that AssertionError is usually the wrong error to give when testing function arguments. But, and more dangerously, there's a twist with assert: it can be 
compiled away and never executed, if you run Python with the -O or -OO 
optimization flags [...]"*

```python
def function_with_assert(x):
    
    assert <validate>(x), "invalid x : ..."
    IndexError
    # here we can use x safely
```

 * other ways... (please suggest!)

## Purpose of validation

The purpose may vary, but it is often one of these (please feel free to suggest other benefits here):

 * let users get **explicit error messages** when they did not input correct data (in the function, or indirectly in web forms, web service inputs, cli, etc.)
 * **defensive programming**: do not let the code get an opportunity to fall into a harder-to-detect bug.
 * **avoid performing a computationally expensive task** if it is to discover at the very end of the execution that one of the inputs was incorrect

## Consistency

So you implement validation in your code. However there are many choices left in the implementation, that make your code rapidly lack consistency, except for highly skilled coders:

 * validation **exception types** are not standard across developers and even inside a code base. You *should* use [`TypeError`](https://docs.python.org/3/library/exceptions.html#TypeError) for type validation and [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError) for value validation, or any subclass of those, but when under pressure for delivery, we all end up from time to time raising plain old `Exception`... 
 * validation exceptions can not easily be associated with **error codes** when exchanged with the rest of the application (web front-end, etc.). This makes internationalization of errors difficult
 * even in plain english, validation **messages** are not always user-friendly: the user of your function may struggle some time to understand why the value he entered was not correct.

## Reuse

At some point you want to reuse validation functions. For example to validate that a dataframe has certain column names, or that a text string follows a certain regex.

## Cli, Schema and Forms

One validation strategy if you are sure that nobody will access your code directly (e.g. you do not share it as a library), is to perform value validation directly at the entry point, whether it is a command line interface, a web form or a soap/rest webservice in json or xml. However as soon as you wish to also share your code as a library, you end up needing to maintain two validation frameworks: one for the entry points, and one for the library. There is no easy solution to solve this problem:

 * you may wish to only perform validation in you core library functions, or core library's API. This can be enhanced by the creation of 'validated objects' for example using [autoclass](https://smarie.github.io/python-autoclass/), so that you do not re-validate in every function the object contents once it has been created
 * you may need to still perform entry point-validation, may it only for the reason that you share a schema as a contract with your customers (through [swagger](https://swagger.io/) or equivalent).
