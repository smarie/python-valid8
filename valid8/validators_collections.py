from numbers import Integral
from typing import Set, Tuple

from valid8.core import BasicFailure, _create_main_validation_function


def minlen(min_length: Integral, strict: bool = False):
    """
    'Minimum length' validator generator.
    Returns a validator to check that len(x) >= min_length (strict=False, default) or len(x) > min_length (strict=True)

    :param min_length: minimum length for x
    :param strict: Boolean flag to switch between len(x) >= min_length (strict=False) and len(x) > min_length
    (strict=True)
    :return:
    """
    if strict:
        def minlen(x):
            if len(x) > min_length:
                return True
            else:
                raise BasicFailure('minlen: len(x) > ' + str(min_length) + ' does not hold for x=' + str(x))
    else:
        def minlen(x):
            if len(x) >= min_length:
                return True
            else:
                raise BasicFailure('minlen: len(x) >= ' + str(min_length) + ' does not hold for x=' + str(x))

    minlen.__name__ = 'length_{}greater_than_{}'.format('strictly_' if strict else '', min_length)
    return minlen


def minlens(min_length_strict: Integral):
    """ Alias for 'Minimum length' validator generator in strict mode """
    return minlen(min_length_strict, True)


def maxlen(max_length: Integral, strict: bool = False):
    """
    'Maximum length' validator generator.
    Returns a validator to check that len(x) <= max_length (strict=False, default) or len(x) < max_length (strict=True)

    :param max_length: maximum length for x
    :param strict: Boolean flag to switch between len(x) <= max_length (strict=False) and len(x) < max_length
    (strict=True)
    :return:
    """
    if strict:
        def maxlen(x):
            if len(x) < max_length:
                return True
            else:
                raise BasicFailure('maxlen: len(x) < ' + str(max_length) + ' does not hold for x=' + str(x))
    else:
        def maxlen(x):
            if len(x) <= max_length:
                return True
            else:
                raise BasicFailure('maxlen: len(x) <= ' + str(max_length) + ' does not hold for x=' + str(x))

    maxlen.__name__ = 'length_{}lesser_than_{}'.format('strictly_' if strict else '', max_length)
    return maxlen


def maxlens(max_length_strict: Integral):
    """ Alias for 'Maximum length' validator generator in strict mode """
    return maxlen(max_length_strict, True)


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
        def length_between(x):
            if (min_len < len(x)) and (len(x) < max_len):
                return True
            else:
                raise BasicFailure('length between: {} < len(x) < {} does not hold for x={}'.format(min_len, max_len, x))
    elif open_left:
        def length_between(x):
            if (min_len < len(x)) and (len(x) <= max_len):
                return True
            else:
                raise BasicFailure('length between: {} < len(x) <= {} does not hold for x={}'.format(min_len, max_len, x))
    elif open_right:
        def length_between(x):
            if (min_len <= len(x)) and (len(x) < max_len):
                return True
            else:
                raise BasicFailure('length between: {} <= len(x) < {} does not hold for x={}'.format(min_len, max_len, x))
    else:
        def length_between(x):
            if (min_len <= len(x)) and (len(x) <= max_len):
                return True
            else:
                raise BasicFailure('length between: {} <= len(x) <= {} does not hold for x={}'.format(min_len, max_len, x))

    length_between.__name__ = 'length_between_{}_and_{}'.format(min_len, max_len)
    return length_between


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
            raise BasicFailure('is_in: x in ' + str(allowed_values) + ' does not hold for x=' + str(x))

    return is_in_allowed_values


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
            raise BasicFailure('is_subset: len(x - reference_set) == 0 does not hold for x=' + str(x)
                               + ' and reference_set=' + str(reference_set) + '. x contains unsupported '
                                  'elements ' + str(missing))
    return is_subset_of


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
            raise BasicFailure('is_superset: len(reference_set - x) == 0 does not hold for x=' + str(x)
                               + ' and reference_set=' + str(reference_set) + '. x does not contain required '
                                  'elements ' + str(missing))
    return is_superset_of


# TODO rename 'all_on_each'
def on_all_(*validators_for_all_elts):
    """
    Generates a validator for collection inputs where each element of the input will be validated against the validators
    provided. For convenience, a list of validators can be provided and will be replaced with an 'and_'.

    Note that if you want to apply DIFFERENT validators for each element in the input, you should rather use on_each_.

    :param validators_for_all_elts:
    :return:
    """
    # create the validation function
    validator_funcs = _create_main_validation_function(list(validators_for_all_elts), allow_not_none=True)

    def on_all_val(x):
        # validate all elements in x in turn
        idx = -1
        for x_elt in x:
            idx += 1
            res = validator_funcs(x_elt)
            if res not in {None, True}:
                # one element of x was not valid > raise
                raise BasicFailure('on_all_(' + str(validators_for_all_elts) + '): failed validation for input '
                                      'element [' + str(idx) + ']: ' + str(x_elt))
        return True

    return on_all_val


# TODO rename one_for_each
def on_each_(*validators_collection):
    """
    Generates a validator for collection inputs where each element of the input will be validated against the
    corresponding validator(s) in the validators_collection. Validators inside the tuple can be provided as a list for
    convenience, this will be replaced with an 'and_' operator if the list has more than one element.

    Note that if you want to apply the SAME validators to all elements in the input, you should rather use on_all_.

    :param validators_collection:
    :return:
    """
    # create a tuple of validation functions.
    validator_funcs = tuple(_create_main_validation_function(validators, allow_not_none=True)
                            for validators in validators_collection)

    # generate a validation function based on the tuple of validators lists
    def on_each_val(x: Tuple):
        if len(validator_funcs) != len(x):
            raise BasicFailure('on_each_: x does not have the same number of elements than validators_collection.')
        else:
            # apply each validator on the input with the same position in the collection
            idx = -1
            for elt, validator_func in zip(x, validator_funcs):
                idx += 1
                res = validator_func(elt)
                if res not in {None, True}:
                    # one validator was unhappy > raise
                    raise BasicFailure('on_each_(' + str(validators_collection) + '): _validator [' + str(idx)
                                       + '] (' + str(validators_collection[idx]) + ') failed validation for '
                                          'input ' + str(x[idx]))
            return True

    return on_each_val
