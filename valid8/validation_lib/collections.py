from typing import Set, Tuple

from valid8.composition import _process_validation_function_s
from valid8.base import Failure, WrappingFailure, result_is_success


class TooShort(Failure, ValueError):
    """ Custom Failure raised by minlen """
    def __init__(self, wrong_value, min_length, strict):
        symbol = '>' if strict else '>='
        help_msg = 'len(x) {symbol} {min_length} does not hold for x={wrong_value}'
        super(TooShort, self).__init__(wrong_value=wrong_value, min_length=min_length, symbol=symbol, help_msg=help_msg)


def minlen(min_length, strict: bool = False):
    """
    'Minimum length' validation_function generator.
    Returns a validation_function to check that len(x) >= min_length (strict=False, default)
    or len(x) > min_length (strict=True)

    :param min_length: minimum length for x
    :param strict: Boolean flag to switch between len(x) >= min_length (strict=False) and len(x) > min_length
    (strict=True)
    :return:
    """
    if strict:
        def minlen_(x):
            if len(x) > min_length:
                return True
            else:
                # raise Failure('minlen: len(x) > ' + str(min_length) + ' does not hold for x=' + str(x))
                raise TooShort(wrong_value=x, min_length=min_length, strict=True)
    else:
        def minlen_(x):
            if len(x) >= min_length:
                return True
            else:
                # raise Failure('minlen: len(x) >= ' + str(min_length) + ' does not hold for x=' + str(x))
                raise TooShort(wrong_value=x, min_length=min_length, strict=False)

    minlen_.__name__ = 'length_{}greater_than_{}'.format('strictly_' if strict else '', min_length)
    return minlen_


def minlens(min_length_strict):
    """ Alias for 'Minimum length' validation_function generator in strict mode """
    return minlen(min_length_strict, True)


class TooLong(Failure, ValueError):
    """ Custom Failure raised by maxlen """
    def __init__(self, wrong_value, max_length, strict):
        symbol = '<' if strict else '<='
        help_msg = 'len(x) {symbol} {max_length} does not hold for x={wrong_value}'
        super(TooLong, self).__init__(wrong_value=wrong_value, max_length=max_length, symbol=symbol, help_msg=help_msg)


def maxlen(max_length, strict: bool = False):
    """
    'Maximum length' validation_function generator.
    Returns a validation_function to check that len(x) <= max_length (strict=False, default) or len(x) < max_length (strict=True)

    :param max_length: maximum length for x
    :param strict: Boolean flag to switch between len(x) <= max_length (strict=False) and len(x) < max_length
    (strict=True)
    :return:
    """
    if strict:
        def maxlen_(x):
            if len(x) < max_length:
                return True
            else:
                # raise Failure('maxlen: len(x) < ' + str(max_length) + ' does not hold for x=' + str(x))
                raise TooLong(wrong_value=x, max_length=max_length, strict=True)
    else:
        def maxlen_(x):
            if len(x) <= max_length:
                return True
            else:
                # raise Failure('maxlen: len(x) <= ' + str(max_length) + ' does not hold for x=' + str(x))
                raise TooLong(wrong_value=x, max_length=max_length, strict=False)

    maxlen_.__name__ = 'length_{}lesser_than_{}'.format('strictly_' if strict else '', max_length)
    return maxlen_


def maxlens(max_length_strict):
    """ Alias for 'Maximum length' validation_function generator in strict mode """
    return maxlen(max_length_strict, True)


class WrongLength(Failure, ValueError):
    """ Custom failure raised by has_length """
    def __init__(self, wrong_value, ref_length):
        help_msg = 'len(x) == {ref_length} does not hold for x={wrong_value}'
        super(WrongLength, self).__init__(wrong_value=wrong_value, ref_length=ref_length, help_msg=help_msg)


def has_length(ref_length):
    """
    'length equals' validation function generator.
    Returns a validation_function to check that `len(x) == ref_length`

    :param ref_length:
    :return:
    """
    def has_length_(x):
        if len(x) == ref_length:
            return True
        else:
            raise WrongLength(wrong_value=x, ref_length=ref_length)

    has_length_.__name__ = 'length_equals_{}'.format(ref_length)
    return has_length_


class LengthNotInRange(Failure, ValueError):
    """ Custom Failure raised by length_between """
    def __init__(self, wrong_value, min_length, left_strict, max_length, right_strict):
        left_symbol = '<' if left_strict else '<='
        right_symbol = '<' if right_strict else '<='
        help_msg = '{min_length} {left_symbol} len(x) {right_symbol} {max_length} does not hold for x={wrong_value}'
        super(LengthNotInRange, self).__init__(wrong_value=wrong_value, min_length=min_length, left_symbol=left_symbol,
                                               max_length=max_length, right_symbol=right_symbol, help_msg=help_msg)


def length_between(min_len, max_len, open_left: bool = False, open_right: bool = False):
    """
    'Is length between' validation_function generator.
    Returns a validation_function to check that `min_len <= len(x) <= max_len (default)`. `open_right` and `open_left`
    flags allow to transform each side into strict mode. For example setting `open_left=True` will enforce
    `min_len < len(x) <= max_len`.

    :param min_len: minimum length for x
    :param max_len: maximum length for x
    :param open_left: Boolean flag to turn the left inequality to strict mode
    :param open_right: Boolean flag to turn the right inequality to strict mode
    :return:
    """
    if open_left and open_right:
        def length_between_(x):
            if (min_len < len(x)) and (len(x) < max_len):
                return True
            else:
                # raise Failure('length between: {} < len(x) < {} does not hold for x={}'.format(min_len, max_len,
                # x))
                raise LengthNotInRange(wrong_value=x, min_length=min_len, left_strict=True, max_length=max_len,
                                       right_strict=True)
    elif open_left:
        def length_between_(x):
            if (min_len < len(x)) and (len(x) <= max_len):
                return True
            else:
                # raise Failure('length between: {} < len(x) <= {} does not hold for x={}'.format(min_len, max_len,
                # x))
                raise LengthNotInRange(wrong_value=x, min_length=min_len, left_strict=True, max_length=max_len,
                                       right_strict=False)
    elif open_right:
        def length_between_(x):
            if (min_len <= len(x)) and (len(x) < max_len):
                return True
            else:
                # raise Failure('length between: {} <= len(x) < {} does not hold for x={}'.format(min_len, max_len,
                #  x))
                raise LengthNotInRange(wrong_value=x, min_length=min_len, left_strict=False, max_length=max_len,
                                       right_strict=True)
    else:
        def length_between_(x):
            if (min_len <= len(x)) and (len(x) <= max_len):
                return True
            else:
                # raise Failure('length between: {} <= len(x) <= {} does not hold for x={}'.format(min_len,
                #  max_len, x))
                raise LengthNotInRange(wrong_value=x, min_length=min_len, left_strict=False, max_length=max_len,
                                       right_strict=False)

    length_between_.__name__ = 'length_between_{}_and_{}'.format(min_len, max_len)
    return length_between_


class NotInAllowedValues(Failure, ValueError):
    """ Custom Failure raised by is_in """
    def __init__(self, wrong_value, allowed_values):
        help_msg = 'x in {allowed_values} does not hold for x={wrong_value}'
        super(NotInAllowedValues, self).__init__(wrong_value=wrong_value, allowed_values=allowed_values,
                                                 help_msg=help_msg)


def is_in(allowed_values: Set):
    """
    'Values in' validation_function generator.
    Returns a validation_function to check that x is in the provided set of allowed values

    :param allowed_values: a set of allowed values
    :return:
    """
    def is_in_allowed_values(x):
        if x in allowed_values:
            return True
        else:
            # raise Failure('is_in: x in ' + str(allowed_values) + ' does not hold for x=' + str(x))
            raise NotInAllowedValues(wrong_value=x, allowed_values=allowed_values)

    is_in_allowed_values.__name__ = 'is_in_{}'.format(allowed_values)
    return is_in_allowed_values


class NotSubset(Failure, ValueError):
    """ Custom Failure raised by is_subset """
    def __init__(self, wrong_value, reference_set, unsupported):
        help_msg = 'x subset of {reference_set} does not hold for x={wrong_value}. Unsupported elements: {unsupported}'
        super(NotSubset, self).__init__(wrong_value=wrong_value, reference_set=reference_set, unsupported=unsupported,
                                        help_msg=help_msg)


def is_subset(reference_set: Set):
    """
    'Is subset' validation_function generator.
    Returns a validation_function to check that x is a subset of reference_set

    :param reference_set: the reference set
    :return:
    """
    def is_subset_of(x):
        missing = x - reference_set
        if len(missing) == 0:
            return True
        else:
            # raise Failure('is_subset: len(x - reference_set) == 0 does not hold for x=' + str(x)
            #                   + ' and reference_set=' + str(reference_set) + '. x contains unsupported '
            #                      'elements ' + str(missing))
            raise NotSubset(wrong_value=x, reference_set=reference_set, unsupported=missing)

    is_subset_of.__name__ = 'is_subset_of_{}'.format(reference_set)
    return is_subset_of


class DoesNotContainValue(Failure, ValueError):
    """ Custom Failure raised by contains """
    def __init__(self, wrong_value, ref_value):
        help_msg = '{ref_value} in x does not hold for x={wrong_value}'
        super(DoesNotContainValue, self).__init__(wrong_value=wrong_value, ref_value=ref_value,
                                                  help_msg=help_msg)


def contains(ref_value):
    """
    'Contains' validation_function generator.
    Returns a validation_function to check that `ref_value in x`

    :param ref_value: a value that must be present in x
    :return:
    """
    def contains_ref_value(x):
        if ref_value in x:
            return True
        else:
            raise DoesNotContainValue(wrong_value=x, ref_value=ref_value)

    contains_ref_value.__name__ = 'contains_{}'.format(ref_value)
    return contains_ref_value


class NotSuperset(Failure, ValueError):
    """ Custom Failure raised by is_superset """
    def __init__(self, wrong_value, reference_set, missing):
        help_msg = 'x superset of {reference_set} does not hold for x={wrong_value}. Missing elements: {missing}'
        super(NotSuperset, self).__init__(wrong_value=wrong_value, reference_set=reference_set, missing=missing,
                                          help_msg=help_msg)


def is_superset(reference_set: Set):
    """
    'Is superset' validation_function generator.
    Returns a validation_function to check that x is a superset of reference_set

    :param reference_set: the reference set
    :return:
    """
    def is_superset_of(x):
        missing = reference_set - x
        if len(missing) == 0:
            return True
        else:
            # raise Failure('is_superset: len(reference_set - x) == 0 does not hold for x=' + str(x)
            #               + ' and reference_set=' + str(reference_set) + '. x does not contain required '
            #                       'elements ' + str(missing))
            raise NotSuperset(wrong_value=x, reference_set=reference_set, missing=missing)

    is_superset_of.__name__ = 'is_superset_of_{}'.format(reference_set)
    return is_superset_of


class InvalidItemInSequence(WrappingFailure, ValueError):
    """ Custom Failure raised by on_all_ and on_each_ """
    help_msg = 'Provided sequence contains one value that is invalid.'


# TODO rename 'all_on_each'
def on_all_(*validation_func):
    """
    Generates a validation_function for collection inputs where each element of the input will be validated against the
    validation_functions provided. For convenience, a list of validation_functions can be provided and will be replaced
    with an 'and_'.

    Note that if you want to apply DIFFERENT validation_functions for each element in the input, you should rather use
    on_each_.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """
    # create the validation functions
    validation_function_func = _process_validation_function_s(list(validation_func))

    def on_all_val(x):
        # validate all elements in x in turn
        for idx, x_elt in enumerate(x):
            try:
                res = validation_function_func(x_elt)
            except Exception as e:
                raise InvalidItemInSequence(wrong_value=x_elt, wrapped_func=validation_function_func, validation_outcome=e)

            if not result_is_success(res):
                # one element of x was not valid > raise
                # raise Failure('on_all_(' + str(validation_func) + '): failed validation for input '
                #                       'element [' + str(idx) + ']: ' + str(x_elt))
                raise InvalidItemInSequence(wrong_value=x_elt, wrapped_func=validation_function_func, validation_outcome=res)
        return True

    on_all_val.__name__ = 'apply_<{}>_on_all_elts'.format(validation_function_func.__name__)
    return on_all_val


# TODO rename one_for_each
def on_each_(*validation_functions_collection):
    """
    Generates a validation_function for collection inputs where each element of the input will be validated against the
    corresponding validation_function(s) in the validation_functions_collection. Validators inside the tuple can be
    provided as a list for convenience, this will be replaced with an 'and_' operator if the list has more than one
    element.

    Note that if you want to apply the SAME validation_functions to all elements in the input, you should rather use
    on_all_.

    :param validation_functions_collection: a sequence of (base validation function or list of base validation functions
    to use).
    A base validation function may be a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type), or
    a list of several such elements. Nested lists are supported and indicate an implicit `and_` (such as the main list).
    Tuples indicate an implicit `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/)
    expressions can be used instead of callables, they will be transformed to functions automatically.
    :return:
    """
    # create a tuple of validation functions.
    validation_function_funcs = tuple(_process_validation_function_s(validation_func)
                                      for validation_func in validation_functions_collection)

    # generate a validation function based on the tuple of validation_functions lists
    def on_each_val(x: Tuple):
        if len(validation_function_funcs) != len(x):
            raise Failure('on_each_: x does not have the same number of elements than validation_functions_collection.')
        else:
            # apply each validation_function on the input with the same position in the collection
            idx = -1
            for elt, validation_function_func in zip(x, validation_function_funcs):
                idx += 1
                try:
                    res = validation_function_func(elt)
                except Exception as e:
                    raise InvalidItemInSequence(wrong_value=elt, wrapped_func=validation_function_func, validation_outcome=e)

                if not result_is_success(res):
                    # one validation_function was unhappy > raise
                    # raise Failure('on_each_(' + str(validation_functions_collection) + '): _validation_function [' + str(idx)
                    #               + '] (' + str(validation_functions_collection[idx]) + ') failed validation for '
                    #                       'input ' + str(x[idx]))
                    raise InvalidItemInSequence(wrong_value=elt, wrapped_func=validation_function_func, validation_outcome=res)
            return True

    on_each_val.__name__ = 'map_<{}>_on_elts' \
                           ''.format('(' + ', '.join([f.__name__ for f in validation_function_funcs]) + ')')
    return on_each_val
