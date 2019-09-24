# Base validation functions library

Several base validation functions are bundled in the package so as to be reused inside any of the validation entry points provided by `valid8`.

A quick way to get the up-to-date list of validation functions provided in this package is to execute the following help commands from within a terminal

```python
import valid8.validation_lib

# get the list of submodules containing base validation functions
help(valid8.validation_lib)

# get the list of base validation functions for each submodule
help(valid8.validation_lib.numbers)

# help on a specific function
help(valid8.validation_lib.numbers.is_multiple_of)
```

If you do not find the function you're looking for in this list, don't hesitate to propose new ones ! Submit a pull request or an issue [here](https://github.com/smarie/python-valid8).

In parallel, if your function is very specific but writes quite well in plain old python syntax, [mini_lambda](https://smarie.github.io/python-mini-lambda/) may provide a good alternative.


## Types

### instance_of(ref_type)

'instance of' validation function generator. Returns a validation function to check that `is_instance(x, ref_type)`. If ref_type is a set of types, any match with one of the included types will do.

```python
from valid8 import assert_valid
from valid8.validation_lib import instance_of

assert_valid('Foo', 'r', instance_of(str))
```

Note that this function can also be used directly in inline codes, by using its 2-args version: `instance_of(x, str)`.


### subclass_of(ref_type)

'subclass of' validation function generator. Returns a validation function to check that `is_subclass(x, ref_type)`.

```python
from valid8 import assert_valid
from valid8.validation_lib import subclass_of

assert_valid('Foo', bool, subclass_of(int))
```

Note that this function can also be used directly in inline codes, by using its 2-args version: `subclass_of(c, int)`.


## Comparables

### gt(min_value, strict:bool=False)

'Greater than' validation function generator. Returns a validation function to check that `x >= min_value` (strict=False, default) or `x > min_value` (strict=True).

### gts(min_value)

Alias for 'greater than' validation function generator in strict mode.

### lt(max_value, strict:bool=False)

'Lesser than' validation function generator. Returns a validation function to check that `x <= max_value` (strict=False, default) or `x < max_value` (strict=True).

### lts(max_value)

Alias for 'lesser than' validation function generator in strict mode.

### between(min_value, max_value, open_left:bool=False, open_right:bool=False)

'Is between' validation function generator. Returns a validation function to check that `min_val <= x <= max_val` (default). `open_right` and `open_left` flags allow to transform each side into strict mode. For example setting `open_left=True` will enforce `min_val < x <= max_val`.


## Numbers

### is_even

Validates that x is even (`x % 2 == 0`).

### is_odd

Validates that x is odd (`x % 2 != 0`).

### is_multiple_of(ref)

'Is multiple of' validation function generator. Returns a validation function to check that  x is a multiple of the reference (`x % ref == 0`).


## Collections

### empty

'empty' validation function. Raises a `NotEmpty` error in case of failure.

### non_empty

'non empty' validation function. Raises a `Empty` error in case of failure.

### has_length(ref_length)

'length equals' validation function generator. Returns a validation_function to check that `len(x) == ref_length`

### minlen(min_length)

'Minimum length' validation function generator. Returns a validation function to check that `len(x) >= min_length`.

### maxlen(max_length)

'Maximum length' validation function generator. Returns a validation function to check that `len(x) <= max_length`.

### length_between(min_len, max_len)

'Is length between' validation_function generator. Returns a validation_function to check that `min_len <= len(x) <= max_len (default)`.

### is_in(allowed_values)

'Values in' validation function generator. Returns a validation function to check that x is in the provided set `allowed_values`.

### is_subset(reference_set)

'Is subset' validation function generator. Returns a validation function to check that `x` is a subset of `reference_set`. That is, `len(x - reference_set) == 0`.

### contains(ref_value)

'Contains' validation_function generator. Returns a validation_function to check that `ref_value in x`

### is_superset(reference_set)

'Is superset' validation function generator. Returns a validation function to check that `x` is a superset of `reference_set`. That is, `len(reference_set - x) == 0`.

### on_all_(*validation functions_for_all_elts)

Generates a validation function for collection inputs where each element of the input will be validated against the validation functions provided. For convenience, a list of validation functions can be provided and will be replaced with an `and_`.

Note that if you want to apply DIFFERENT validation functions for each element in the input collection, you should rather use `on_each_`.

### on_each_(*validation functions_collection)

Generates a validation function for collection inputs where each element of the input will be validated against the corresponding validation function(s) in the validation functions_collection. Validators inside the tuple can be provided as a list for convenience, this will be replaced with an `and_` operator if the list has more than one element.

Note that if you want to apply the SAME validation functions to all elements in the input, you should rather use `on_all_`.
