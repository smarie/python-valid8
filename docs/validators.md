## Validators list

Several validators are bundled in the package to be used with `@validate`. Don't hesitate to propose new ones !

### All objects

#### not_none

Checks that the input is not None. It should be first in the validators' list to apply. When it applies, the whole list of validators will be **bypassed** for `None` inputs. In other words when it applies, `None` inputs will always be accepted whatever the other validators present. 

Note that if you use `@validate` in combination with a PEP484 type checker such as enforce, you don't need to include the `not_none` validator. Indeed if an input is not explicitly declared with type `Optional[...]` or `Union[NoneType, ...]`, a good type checker should already raise an error:

```python
from enforce import runtime_validation
from numbers import Integral
from valid8 import validate, is_even, gt

@runtime_validation
@validate(a=[is_even, gt(1)], b=is_even)
def myfunc(a: Integral, b):
    print('hello')

# -- check that the validation works
myfunc(84, None) # OK because b has no type annotation nor not_none validator
myfunc(None, 0)  # RuntimeTypeError: a is None
```


### Comparables

#### gt(min_value, strict: bool = False)

'Greater than' validator generator. Returns a validator to check that `x >= min_value` (strict=False, default) or `x > min_value` (strict=True)

#### gts(min_value)

Alias for 'greater than' validator generator in strict mode

#### lt(max_value, strict: bool = False)

'Lesser than' validator generator. Returns a validator to check that `x <= max_value` (strict=False, default) or `x < max_value` (strict=True)

#### lts(max_value)

Alias for 'lesser than' validator generator in strict mode

#### between(min_value, max_value, open_left: bool = False, open_right: bool = False)

'Is between' validator generator. Returns a validator to check that `min_val <= x <= max_val` (default). `open_right` and `open_left` flags allow to transform each side into strict mode. For example setting `open_left=True` will enforce `min_val < x <= max_val`

### Numbers

#### is_even

Validates that x is even (`x % 2 == 0`)

#### is_odd

Validates that x is odd (`x % 2 != 0`)

#### is_mod(ref)

Validates that x is a multiple of the reference (`x % ref == 0`)


### Collections

#### minlen(min_length, strict: bool = False)

'Minimum length' validator generator. Returns a validator to check that `len(x) >= min_length` (strict=False, default) or `len(x) > min_length` (strict=True)

#### minlens(min_length)

Alias for minlen in strict mode

#### maxlen(max_length, strict: bool = False)

'Maximum length' validator generator. Returns a validator to check that `len(x) <= max_length` (strict=False, default) or `len(x) < max_length` (strict=True)

#### maxlens(max_length)

Alias for maxlen in strict mode

#### is_in(allowed_values)

'Values in' validator generator. Returns a validator to check that x is in the provided set `allowed_values`

#### is_subset(reference_set)

'Is subset' validator generator. Returns a validator to check that `x` is a subset of `reference_set`. That is, `len(x - reference_set) == 0`

#### is_superset(reference_set)

'Is superset' validator generator. Returns a validator to check that `x` is a superset of `reference_set`. That is, `len(reference_set - x) == 0`

#### on_all_(*validators_for_all_elts)

Generates a validator for collection inputs where each element of the input will be validated against the validators provided. For convenience, a list of validators can be provided and will be replaced with an `and_`.

Note that if you want to apply DIFFERENT validators for each element in the input collection, you should rather use `on_each_`.

#### on_each_(*validators_collection)

Generates a validator for collection inputs where each element of the input will be validated against the corresponding validator(s) in the validators_collection. Validators inside the tuple can be provided as a list for convenience, this will be replaced with an `and_` operator if the list has more than one element.

Note that if you want to apply the SAME validators to all elements in the input, you should rather use `on_all_`.
