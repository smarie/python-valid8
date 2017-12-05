from typing import Any

from valid8.core import Failure


def gt(min_value: Any, strict: bool = False):
    """
    'Greater than' validator generator.
    Returns a validator to check that x >= min_value (strict=False, default) or x > min_value (strict=True)

    :param min_value: minimum value for x
    :param strict: Boolean flag to switch between x >= min_value (strict=False) and x > min_value (strict=True)
    :return:
    """
    if strict:
        def gt(x):
            if x > min_value:
                return True
            else:
                raise Failure('gt: x > ' + str(min_value) + ' does not hold for x=' + str(x))
    else:
        def gt(x):
            if x >= min_value:
                return True
            else:
                raise Failure('gt: x >= ' + str(min_value) + ' does not hold for x=' + str(x))

    gt.__name__ = '{}greater_than_{}'.format('strictly_' if strict else '', min_value)
    return gt


def gts(min_value_strict: Any):
    """ Alias for 'greater than' validator generator in strict mode """
    return gt(min_value_strict, True)


def lt(max_value: Any, strict: bool = False):
    """
    'Lesser than' validator generator.
    Returns a validator to check that x <= max_value (strict=False, default) or x < max_value (strict=True)

    :param max_value: maximum value for x
    :param strict: Boolean flag to switch between x <= max_value (strict=False) and x < max_value (strict=True)
    :return:
    """
    if strict:
        def lt(x):
            if x < max_value:
                return True
            else:
                raise Failure('lt: x < ' + str(max_value) + ' does not hold for x=' + str(x))
    else:
        def lt(x):
            if x <= max_value:
                return True
            else:
                raise Failure('lt: x <= ' + str(max_value) + ' does not hold for x=' + str(x))

    lt.__name__ = '{}lesser_than_{}'.format('strictly_' if strict else '', max_value)
    return lt


def lts(max_value_strict: Any):
    """ Alias for 'lesser than' validator generator in strict mode """
    return lt(max_value_strict, True)


def between(min_val: Any, max_val: Any, open_left: bool = False, open_right: bool = False):
    """
    'Is between' validator generator.
    Returns a validator to check that min_val <= x <= max_val (default). open_right and open_left flags allow to
    transform each side into strict mode. For example setting open_left=True will enforce min_val < x <= max_val

    :param min_val: minimum value for x
    :param max_val: maximum value for x
    :param open_left: Boolean flag to turn the left inequality to strict mode
    :param open_right: Boolean flag to turn the right inequality to strict mode
    :return:
    """
    if open_left and open_right:
        def between(x):
            if (min_val < x) and (x < max_val):
                return True
            else:
                raise Failure('between: {} < x < {} does not hold for x={}'.format(min_val, max_val, x))
    elif open_left:
        def between(x):
            if (min_val < x) and (x <= max_val):
                return True
            else:
                raise Failure('between: {} < x <= {} does not hold for x={}'.format(min_val, max_val, x))
    elif open_right:
        def between(x):
            if (min_val <= x) and (x < max_val):
                return True
            else:
                raise Failure('between: {} <= x < {} does not hold for x={}'.format(min_val, max_val, x))
    else:
        def between(x):
            if (min_val <= x) and (x <= max_val):
                return True
            else:
                raise Failure('between: {} <= x <= {} does not hold for x={}'.format(min_val, max_val, x))

    between.__name__ = 'between_{}_and_{}'.format(min_val, max_val)
    return between
