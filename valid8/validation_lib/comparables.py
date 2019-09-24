try:  # python 3.5+
    # noinspection PyUnresolvedReferences
    from typing import Any
except ImportError:
    pass

from valid8.base import ValidationFailure


class NotEqual(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by ?? (only by validate for now) """
    help_msg = 'x == {ref_value} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, ref_value, **kwargs):
        super(NotEqual, self).__init__(wrong_value=wrong_value, ref_value=ref_value, **kwargs)


class TooSmall(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by gt """
    help_msg = 'x {symbol} {min_value} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, min_value, strict, **kwargs):
        symbol = '>' if strict else '>='
        super(TooSmall, self).__init__(wrong_value=wrong_value, min_value=min_value, symbol=symbol, **kwargs)


def gt(min_value,    # type: Any
       strict=False  # type: bool
       ):
    """
    'Greater than' validation_function generator.
    Returns a validation_function to check that x >= min_value (strict=False, default) or x > min_value (strict=True)

    :param min_value: minimum value for x
    :param strict: Boolean flag to switch between x >= min_value (strict=False) and x > min_value (strict=True)
    :return:
    """
    if strict:
        def gt_(x):
            if x > min_value:
                return True
            else:
                # raise ValidationFailure('x > ' + str(min_value) + ' does not hold for x=' + str(x))
                # '{val} is not strictly greater than {ref}'
                raise TooSmall(wrong_value=x, min_value=min_value, strict=True)
    else:
        def gt_(x):
            if x >= min_value:
                return True
            else:
                # raise ValidationFailure('x >= ' + str(min_value) + ' does not hold for x=' + str(x))
                # '{val} is not greater than {ref}'
                raise TooSmall(wrong_value=x, min_value=min_value, strict=False)

    gt_.__name__ = '%sgreater_than_%s' % ('strictly_' if strict else '', min_value)
    return gt_


def gts(min_value_strict  # type: Any
        ):
    """ Alias for 'greater than' validation_function generator in strict mode """
    return gt(min_value_strict, True)


class TooBig(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by lt """
    help_msg = 'x {symbol} {max_value} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, max_value, strict, **kwargs):
        symbol = '<' if strict else '<='
        super(TooBig, self).__init__(wrong_value=wrong_value, max_value=max_value, symbol=symbol, **kwargs)


def lt(max_value,    # type: Any
       strict=False  # type: bool
       ):
    """
    'Lesser than' validation_function generator.
    Returns a validation_function to check that x <= max_value (strict=False, default) or x < max_value (strict=True)

    :param max_value: maximum value for x
    :param strict: Boolean flag to switch between x <= max_value (strict=False) and x < max_value (strict=True)
    :return:
    """
    if strict:
        def lt_(x):
            if x < max_value:
                return True
            else:
                # raise ValidationFailure('x < ' + str(max_value) + ' does not hold for x=' + str(x))
                # '{val} is not strictly lesser than {ref}'
                raise TooBig(wrong_value=x, max_value=max_value, strict=True)
    else:
        def lt_(x):
            if x <= max_value:
                return True
            else:
                # raise ValidationFailure('x <= ' + str(max_value) + ' does not hold for x=' + str(x))
                # '{val} is not lesser than {ref}'
                raise TooBig(wrong_value=x, max_value=max_value, strict=False)

    lt_.__name__ = '%slesser_than_%s' % ('strictly_' if strict else '', max_value)
    return lt_


def lts(max_value_strict  # type: Any
        ):
    """ Alias for 'lesser than' validation_function generator in strict mode """
    return lt(max_value_strict, True)


class NotInRange(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by between """
    help_msg = '{min_value} {left_symbol} x {right_symbol} {max_value} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, min_value, left_strict, max_value, right_strict, **kwargs):
        left_symbol = '<' if left_strict else '<='
        right_symbol = '<' if right_strict else '<='
        super(NotInRange, self).__init__(wrong_value=wrong_value, min_value=min_value, left_symbol=left_symbol,
                                         max_value=max_value, right_symbol=right_symbol, **kwargs)


def between(min_val,          # type: Any
            max_val,          # type: Any
            open_left=False,  # type: bool
            open_right=False  # type: bool
            ):
    """
    'Is between' validation_function generator.
    Returns a validation_function to check that min_val <= x <= max_val (default). open_right and open_left flags allow
    to transform each side into strict mode. For example setting open_left=True will enforce min_val < x <= max_val

    :param min_val: minimum value for x
    :param max_val: maximum value for x
    :param open_left: Boolean flag to turn the left inequality to strict mode
    :param open_right: Boolean flag to turn the right inequality to strict mode
    :return:
    """
    if open_left and open_right:
        def between_(x):
            if (min_val < x) and (x < max_val):
                return True
            else:
                raise NotInRange(wrong_value=x, min_value=min_val, left_strict=True,
                                 max_value=max_val, right_strict=True)
    elif open_left:
        def between_(x):
            if (min_val < x) and (x <= max_val):
                return True
            else:
                raise NotInRange(wrong_value=x, min_value=min_val, left_strict=True,
                                 max_value=max_val, right_strict=False)
    elif open_right:
        def between_(x):
            if (min_val <= x) and (x < max_val):
                return True
            else:
                raise NotInRange(wrong_value=x, min_value=min_val, left_strict=False,
                                 max_value=max_val, right_strict=True)
    else:
        def between_(x):
            if (min_val <= x) and (x <= max_val):
                return True
            else:
                raise NotInRange(wrong_value=x, min_value=min_val, left_strict=False,
                                 max_value=max_val, right_strict=False)

    between_.__name__ = 'between_%s_and_%s' % (min_val, max_val)
    return between_
