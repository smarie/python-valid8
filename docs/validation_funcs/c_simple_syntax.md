# Simple syntax for validation functions

We have seen [in previous section](a_basics.md) that validation functions should either return `True` or `None` in case of success, that's the only requirement from `valid8` standpoint. We also have seen that you can improve them by **explicitly** transforming them into custom *failure raisers*. In the [next section](d_composition.md) we will see how to compose several validation functions together.
 
In this section we will show how to both **compose** several validation functions and **augment** them into failure raisers, using in a **simple and compact syntax**. All `valid8` entry points except the context manager support this simple syntax.

!!! note "using the simple syntax in the `with validation` context manager"
    To use this syntax with the `with validation` context manager, you can use an explicit `and_()` in the code block. `and_` accepts the syntax.

## 1. One validation function

You can define a validation function by providing either a `<callable>`, or a tuple : `(<callable>, <error_msg>)`, `(<callable>, <failure_type>)` or `(<callable>, <error_msg>, <failure_type>)`.

 - `<validation_func>` should be a `callable` with one argument: `f(val)`. It should return `True` or `None` in case of success. If it is a mini-lambda expression it will automatically be transformed into a function using `mini_lambda.as_function`. See `ValidationCallable` type hint.
 - `<err_msg>` should be a string, possibly using the template mechanism
 - `<failure_type>` should be a subclass of `ValidationFailure`


For example we can add a custom message to `isfinite`:

```python
from valid8 import validate
from math import inf, isfinite

x = inf
validate('x', x, custom=(isfinite, 'x is not finite'))
```

yields

```bash
valid8.entry_points.ValidationError[ValueError]: \
  Error validating [x=inf]. InvalidValue: x is not finite. \ 
    Function [isfinite] returned [False] for value inf.
```

or if you prefer defining a reusable failure class:

```python
from valid8 import validate, ValidationFailure
from math import inf, isfinite

class NotFinite(ValidationFailure):
    help_msg = "x is not finite"

x = inf
validate('x', x, custom=(isfinite, NotFinite))
```

yields

```bash
ValidationError[ValueError]: Error validating [x=inf]. 
  NotFinite: x is not finite. Function [isfinite] returned [False] for value inf.
```

This syntax also works in `@validate_arg`, `@validate_out`, `@validate_ios`, `@validate_field`, and in the composition operators such as `and_()`. 


## 2. Several validation functions

You can easily declare that several validators should be combined with an implicit `and_` by **providing a non-tuple iterable** containing [validation function definitions](#1-one-validation-function), in other words a list containing `<callable>`, tuples `(<callable>, <error_msg>)`, `(<callable>, <failure_type>)` or `(<callable>, <error_msg>, <failure_type>)`.
 
For example:

```python
from valid8 import validate, ValidationFailure
from math import isfinite
from mini_lambda import i

class NotFinite(ValidationFailure):
    help_msg = "x is not finite"

x = 2
validate('x', x, custom=[(i ** 2 < 50, 'x should be fairly small'),
                         i % 3 == 0, 
                         (isfinite, NotFinite)])
```  

yields

```bash
ValidationError[ValueError]: Error validating [x=2]. 
   At least one validation function failed for value 2. 
   Successes: ['i ** 2 < 50', 'isfinite'] / 
      Failures: {'i % 3 == 0': 'Returned False.'}.
```

Alternately you can **provide a dictionary**. In that case the key should be one of `<callable>`, `<error_msg>`, or `<failure_type>`, and the value should be one of them or a tuple of them.

For example:

```python
from valid8 import validate, ValidationFailure
from math import isfinite
from mini_lambda import i

class NotFinite(ValidationFailure):
    help_msg = "x is not finite"

x = 2
validate('x', x, custom={'x should be fairly small': i ** 2 < 50,
                         'x should be a multiple of 3': i % 3 == 0,
                         'x should be finite': (isfinite, NotFinite)})
```  

yields

```bash
ValidationError[ValueError]: Error validating [x=2]. 
   At least one validation function failed for value 2. 
   Successes: ['i ** 2 < 50', 'isfinite'] / 
   Failures: {'i % 3 == 0': 'InvalidValue: x should be a multiple of 3. 
                             Returned False.'}.
```


Here again, this syntax also works in `@validate_arg`, `@validate_out`, `@validate_ios`, `@validate_field`, and in the composition operators such as `and_()`.
