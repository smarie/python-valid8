# Usage examples / recipes

In these pages we try to provide real-world examples so that you may find an answer for most common validation tasks, according to your coding style (several are proposed). Feel free to propose some examples through a [git issue](https://github.com/smarie/python-valid8/issues) or [pull request](https://github.com/smarie/python-valid8/pulls)!

## Common imports

In all examples, we use `numbers.Integral` rather than `int` so as to support both python primitive `int` and other compliant types such as `numpy` `int`. The same goes for `numbers.Real` and `valid8.Boolean` (yes, unfortunately such an equivalent boolean type is not provided by the stdlib).

```python
from numbers import Integral, Real
from valid8 import Boolean
```

## Examples list

 * [Example 1](./example1): `x` is a positive integer. This is the most simple example.
 * [Example 2](./example2): `s` is a lowercase non-empty string. In this example we start to see the limits of built-in functions and parameters, but are still able to find workarounds without writing custom functions.
 * [Example 3](./example3): `t` is a custom tuple. In this example it becomes clearly easier/more readable to write a custom function and use it in the validation tools
 * [Example 4](./example4): `l` is a list of custom tuples. This is to demonstrate iterative validation on container objects.
 * [Example 5](./example5): `df` is a dataframe containing specific columns
 * [Example 6](./example6): `x` and `y` should be such that either `x` is `A` or `B` and `y` is `None`, or `x` is `C` and `y` is a positive integer. This example demonstrates how to use the validation tools for combination of variables (**TODO**)

Note: we deliberately do not use any `help_msg` or `error_type` customization in any of the examples to focus on the validation core. See [here](./index#customizing-the-validationexception) for details on how to customize these examples.
