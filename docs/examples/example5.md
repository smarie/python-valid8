# Example 5 - `df` is a dataframe containing specific columns

For example we want to check that 'foo' and 'bar' are present.

## 1- Example values to validate

```python
import pandas as pd

# Valid
df = pd.DataFrame(data={'foo': [1, 2], 'bar': [None, "hello"]})
df = pd.DataFrame(data={'a': [1, 2], 'foo': ['r', 't'], 'bar': [None, "hello"]})

# Invalid
df = pd.DataFrame(data={'fo': [1, 2], 'bar': [None, "hello"]})  # typo in name
```

## 2- Inline validation

Principles: 

 * type can be checked with `instance_of`
 * required columns can be checked by verifying that the set of actual columns is a superset of the required columns.

Since this validation is simple, we show below how it can be done with `valid8` alone. But to go further we rather recommend [to combine it with another library](#with-validator-dedicated validation lib)

### `validate` + built-ins

`validate` provides both type and superset validation built-in, but they do not apply to the same element so we have to call it twice:

```python
from valid8 import validate
# type validation
validate('df', df, instance_of=pd.DataFrame)
# columns validation
required_cols = {'foo', 'bar'}
validate('df columns', set(df.columns), superset_of=required_cols, 
         help_msg="DataFrame should contain mandatory columns {c}. 
         Found {var_value}", c=required_cols)
```

Note: you see in this example a reminder that the help message is formatted by `valid8` using [str.format()](https://docs.python.org/3.5/library/string.html#custom-string-formatting). You can use in this help message any custom keyword argument (such as `c` above) or any of the already-available variables. The best way to see what is available is to write a wrong help message with an unexistent variable name in the string template:

```python
validate('df columns', set(df.columns), superset_of=required_cols, 
         help_msg="Just kidding {hoho}")
```

yields:

```bash
ValidationError[ValueError]: Error while formatting help msg, 
keyword [hoho] was not found in the validation context. 
Help message to format was 'Just kidding {hoho}'. 
Context elements available: {
   'display_prefix_for_exc_outcomes': False, 
   'append_details': True, 
   'validator': _QuickValidator<validation_function=validate, none_policy=VALIDATE, exc_type=ValidationError>, 
   'var_value': {'fo', 'bar'}, 
   'var_name': 'df columns', 
   'validation_outcome': NotSuperset(append_details=True,wrong_value={'fo', 'bar'},reference_set={'foo', 'bar'},missing={'foo'},help_msg=x superset of {reference_set} does not hold for x={wrong_value}. Missing elements: {missing}), 
   'help_msg': 'Just kidding {hoho}'
}
```

### `with validator` + built-ins

It is relatively straightforward to validate both `df` and its columns

 * either with a pure "boolean test" approach:

```python
from valid8 import validator

required_cols = {'foo', 'bar'}

with validator('df', df, instance_of=pd.DataFrame) as v:
    missing = required_cols - set(df.columns)
    v.alid = len(missing) == 0
```

 * or with a "failure raising" approach, less compact (and not really more explicit error messages):

```python
from valid8 import validation

required_cols = {'foo', 'bar'}

with validation('df', df, instance_of=pd.DataFrame):
    missing = required_cols - set(df.columns)
    if len(missing) > 0:
        raise ValueError('missing dataFrame columns: ' + str(missing))
```

### `with validator` + dedicated validation lib

Of course in real world examples you will want to validate much more things. So you will typically rely on a dedicated library for dataframe validation, and you will use `valid8` only for its primary target: having a strong control about exceptions readability and exceptions types (for i18n). For example:

```python
from my_pandas_validator import assert_df_minimum_size, assert_index_is_unique, \
    assert_index_is_sorted, assert_column_present_with_correct_type 

with validation('df', df, instance_of=pd.DataFrame, 
                error_type=InvalidInputDataFrame):
    assert_df_minimum_size(df, min_nb_rows=10)
    assert_index_is_unique(df)
    assert_index_is_sorted(df)
    assert_column_present_with_correct_type(df, 'foo', int)
```
 

## 3- Functions/classes validation

### Function input

with built-in validation functions it is not possible, we have to create our custom function:

```python
from valid8 import validate_arg, instance_of

required_cols = {'foo', 'bar'}

def has_required_cols(df):
    missing = required_cols - set(df.columns)
    if len(missing) > 0:
        raise ValueError('missing dataFrame columns: ' + str(missing))

@validate_arg('df', instance_of(pd.DataFrame), has_required_cols)
def my_function(df):
    pass
```

or with mini-lambda

```python
from valid8 import validate_arg, instance_of
from mini_lambda import Set, Len
from mini_lambda.pandas_ import df

@validate_arg('df', instance_of(pd.DataFrame), 
              Len(required_cols - Set(df.columns)) > 0)
def my_function(df):
    pass
```

### Function output

identical but with `validate_out`, see other examples.


### Function ios

See other examples

### Class fields

In the examples below the class fields are defined as constructor arguments but this also works if they are defined as class descriptors/properties, and is compliant with [autoclass and attrs](valid8_with_other#for-classes)

using custom function:

```python
from valid8 import validate_field, instance_of

@validate_field('df', instance_of(pd.DataFrame), has_required_cols)
class Foo:
    def __init__(self, df):
        self.df = df
```

or with mini-lambda

```python
from valid8 import validate_field, instance_of
from mini_lambda import Set, Len
from mini_lambda.pandas_ import df

@validate_field('df', instance_of(pd.DataFrame), 
                Len(required_cols - Set(df.columns)) > 0)
class Foo:
    def __init__(self, df):
        self.df = df
```

### With PEP484

See other examples

## 4- Variants


