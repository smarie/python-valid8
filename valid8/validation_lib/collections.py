from typing import Set, Tuple

from composition import _process_validation_function_s
from valid8.base import Failure, WrappingFailure, result_is_success


class TooShort(Failure):
    def __init__(self, wrong_value, min_length, strict):
        symbol = '>' if strict else '>='
        help_msg = 'len(x) {symbol} {min_length} does not hold for x={{wrong_value}}'
        super(TooShort, self).__init__(wrong_value=wrong_value, min_length=min_length, symbol=symbol, help_msg=help_msg)


def minlen(min_length, strict: bool = False):
    """
    'Minimum length' validator generator.
    Returns a validator to check that len(x) >= min_length (strict=False, default) or len(x) > min_length (strict=True)

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
    """ Alias for 'Minimum length' validator generator in strict mode """
    return minlen(min_length_strict, True)


class TooLong(Failure):
    def __init__(self, wrong_value, max_length, strict):
        symbol = '<' if strict else '<='
        help_msg = 'len(x) {symbol} {max_length} does not hold for x={{wrong_value}}'
        super(TooLong, self).__init__(wrong_value=wrong_value, max_length=max_length, symbol=symbol, help_msg=help_msg)


def maxlen(max_length, strict: bool = False):
    """
    'Maximum length' validator generator.
    Returns a validator to check that len(x) <= max_length (strict=False, default) or len(x) < max_length (strict=True)

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
    """ Alias for 'Maximum length' validator generator in strict mode """
    return maxlen(max_length_strict, True)


class LengthNotInRange(Failure):
    def __init__(self, wrong_value, min_length, left_strict, max_length, right_strict):
        left_symbol = '<' if left_strict else '<='
        right_symbol = '<' if right_strict else '<='
        help_msg = '{min_length} {left_symbol} len(x) {right_symbol} {max_length} does not hold for x={wrong_value}'
        super(LengthNotInRange, self).__init__(wrong_value=wrong_value, min_length=min_length, left_symbol=left_symbol,
                                               max_length=max_length, right_symbol=right_symbol, help_msg=help_msg)


def length_between(min_len, max_len, open_left: bool = False, open_right: bool = False):
    """
    'Is length between' validator generator.
    Returns a validator to check that min_len <= len(x) <= max_len (default). open_right and open_left flags allow to
    transform each side into strict mode. For example setting open_left=True will enforce min_len < len(x) <= max_len

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


class NotInAllowedValues(Failure):
    def __init__(self, wrong_value, allowed_values):
        help_msg = 'x in {allowed_values} does not hold for x={wrong_value}'
        super(NotInAllowedValues, self).__init__(wrong_value=wrong_value, allowed_values=allowed_values,
                                                 help_msg=help_msg)


def is_in(allowed_values: Set):
    """
    'Values in' validator generator.
    Returns a validator to check that x is in the provided set of allowed values

    :param allowed_values: a set of allowed values
    :return:
    """
    def is_in_allowed_values(x):
        if x in allowed_values:
            return True
        else:
            # raise Failure('is_in: x in ' + str(allowed_values) + ' does not hold for x=' + str(x))
            raise NotInAllowedValues(wrong_value=x, allowed_values=allowed_values)

    return is_in_allowed_values


class NotSubset(Failure):
    def __init__(self, wrong_value, reference_set, unsupported):
        help_msg = 'x subset of {reference_set} does not hold for x={wrong_value}. Unsupported elements: {unsupported}'
        super(NotSubset, self).__init__(wrong_value=wrong_value, reference_set=reference_set, unsupported=unsupported,
                                        help_msg=help_msg)


def is_subset(reference_set: Set):
    """
    'Is subset' validator generator.
    Returns a validator to check that x is a subset of reference_set

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

    return is_subset_of


class NotSuperset(Failure):
    def __init__(self, wrong_value, reference_set, missing):
        help_msg = 'x superset of {reference_set} does not hold for x={wrong_value}. Missing elements: {missing}'
        super(NotSuperset, self).__init__(wrong_value=wrong_value, reference_set=reference_set, missing=missing,
                                          help_msg=help_msg)


def is_superset(reference_set: Set):
    """
    'Is superset' validator generator.
    Returns a validator to check that x is a superset of reference_set

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

    return is_superset_of


class InvalidItemInSequence(WrappingFailure):
    help_msg = 'Provided sequence contains one value that is invalid.'


# TODO rename 'all_on_each'
def on_all_(*validation_func):
    """
    Generates a validator for collection inputs where each element of the input will be validated against the validators
    provided. For convenience, a list of validators can be provided and will be replaced with an 'and_'.

    Note that if you want to apply DIFFERENT validators for each element in the input, you should rather use on_each_.

    :param validation_func: the base validation function or list of base validation functions to use. A callable, a
    tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of several such elements. Nested lists
    are supported and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit
    `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
    of callables, they will be transformed to functions automatically.
    :return:
    """
    # create the validation functions
    validator_func = _process_validation_function_s(list(validation_func))

    def on_all_val(x):
        # validate all elements in x in turn
        idx = -1
        for x_elt in x:
            idx += 1
            try:
                res = validator_func(x_elt)
            except Exception as e:
                raise InvalidItemInSequence(wrong_value=x_elt, wrapped_func=validator_func, validation_outcome=e)

            if not result_is_success(res):
                # one element of x was not valid > raise
                # raise Failure('on_all_(' + str(validation_func) + '): failed validation for input '
                #                       'element [' + str(idx) + ']: ' + str(x_elt))
                raise InvalidItemInSequence(wrong_value=x_elt, wrapped_func=validator_func, validation_outcome=res)
        return True

    return on_all_val


# TODO rename one_for_each
def on_each_(*validators_collection):
    """
    Generates a validator for collection inputs where each element of the input will be validated against the
    corresponding validator(s) in the validators_collection. Validators inside the tuple can be provided as a list for
    convenience, this will be replaced with an 'and_' operator if the list has more than one element.

    Note that if you want to apply the SAME validators to all elements in the input, you should rather use on_all_.

    :param validators_collection: a sequence of (base validation function or list of base validation functions to use).
    A base validation function may be a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type), or
    a list of several such elements. Nested lists are supported and indicate an implicit `and_` (such as the main list).
    Tuples indicate an implicit `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/)
    expressions can be used instead of callables, they will be transformed to functions automatically.
    :return:
    """
    # create a tuple of validation functions.
    validator_funcs = tuple(_process_validation_function_s(validation_func)
                            for validation_func in validators_collection)

    # generate a validation function based on the tuple of validators lists
    def on_each_val(x: Tuple):
        if len(validator_funcs) != len(x):
            raise Failure('on_each_: x does not have the same number of elements than validators_collection.')
        else:
            # apply each validator on the input with the same position in the collection
            idx = -1
            for elt, validator_func in zip(x, validator_funcs):
                idx += 1
                try:
                    res = validator_func(elt)
                except Exception as e:
                    raise InvalidItemInSequence(wrong_value=elt, wrapped_func=validator_func, validation_outcome=e)

                if not result_is_success(res):
                    # one validator was unhappy > raise
                    # raise Failure('on_each_(' + str(validators_collection) + '): _validator [' + str(idx)
                    #               + '] (' + str(validators_collection[idx]) + ') failed validation for '
                    #                       'input ' + str(x[idx]))
                    raise InvalidItemInSequence(wrong_value=elt, wrapped_func=validator_func, validation_outcome=res)
            return True

    return on_each_val
