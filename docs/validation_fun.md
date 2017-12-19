# Validation library - reusable base validation functions

Several base validation functions are bundled in the package. It is not recommended to use them "as is" but rather to use them inside any of the validation entry points provided by `valid8`. See [Usage](./usage) for details

A quick way to get the up-to-date list of validation functions provided in this package is to execute the following help commands from within a terminal

```python
# get the list of submodules containing base validation functions
help(valid8.validation_lib)

# get the list of base validation functions for each submodule
help(valid8.validation_lib.numbers)

# help on a specific function
help(valid8.validation_lib.numbers.is_multiple_of)
```

Don't hesitate to propose new ones ! Submit a pull request or an issue [here](https://github.com/smarie/python-valid8).


## Types

### instance_of(ref_type)

'instance of' validation function generator. Returns a validation function to check that `is_instance(x, ref_type)`.

```python
from valid8 import assert_valid, instance_of
assert_valid('Foo', 'r', instance_of(str))
```

### subclass_of(ref_type)

'subclass of' validation function generator. Returns a validation function to check that `is_subclass(x, ref_type)`.

```python
from valid8 import assert_valid, subclass_of
assert_valid('Foo', bool, subclass_of(int))
```

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

### minlen(min_length, strict:bool=False)

'Minimum length' validation function generator. Returns a validation function to check that `len(x) >= min_length` (strict=False, default) or `len(x) > min_length` (strict=True).

### minlens(min_length)

Alias for minlen in strict mode.

### maxlen(max_length, strict:bool=False)

'Maximum length' validation function generator. Returns a validation function to check that `len(x) <= max_length` (strict=False, default) or `len(x) < max_length` (strict=True).

### maxlens(max_length)

Alias for maxlen in strict mode.

### length_between(min_len, max_len, open_left:bool=False, open_right:bool=False)

'Is length between' validation_function generator. Returns a validation_function to check that `min_len <= len(x) <= max_len (default)`. `open_right` and `open_left` flags allow to transform each side into strict mode. For example setting `open_left=True` will enforce `min_len < len(x) <= max_len`.

### is_in(allowed_values)

'Values in' validation function generator. Returns a validation function to check that x is in the provided set `allowed_values`.

### is_subset(reference_set)

'Is subset' validation function generator. Returns a validation function to check that `x` is a subset of `reference_set`. That is, `len(x - reference_set) == 0`.

### is_superset(reference_set)

'Is superset' validation function generator. Returns a validation function to check that `x` is a superset of `reference_set`. That is, `len(reference_set - x) == 0`.

### on_all_(*validation functions_for_all_elts)

Generates a validation function for collection inputs where each element of the input will be validated against the validation functions provided. For convenience, a list of validation functions can be provided and will be replaced with an `and_`.

Note that if you want to apply DIFFERENT validation functions for each element in the input collection, you should rather use `on_each_`.

### on_each_(*validation functions_collection)

Generates a validation function for collection inputs where each element of the input will be validated against the corresponding validation function(s) in the validation functions_collection. Validators inside the tuple can be provided as a list for convenience, this will be replaced with an `and_` operator if the list has more than one element.

Note that if you want to apply the SAME validation functions to all elements in the input, you should rather use `on_all_`.
