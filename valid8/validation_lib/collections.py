try:  # python 3.5+
    # noinspection PyUnresolvedReferences
    from typing import Set, Tuple, Container
except ImportError:
    pass

from valid8.composition import and_
from valid8.base import ValidationFailure, get_callable_name, NP_TRUE


class Empty(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by non_empty """
    help_msg = 'len(x) > 0 does not hold for x={wrong_value}'


def non_empty(x):
    """
    'non empty' validation function. Raises a `Empty` error in case of failure.
    """
    if len(x) > 0:
        return True
    else:
        raise Empty(wrong_value=x)


class NotEmpty(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by non_empty """
    help_msg = 'len(x) == 0 does not hold for x={wrong_value}'


def empty(x):
    """
    'is empty' validation function. Raises a `NotEmpty` error in case of failure.
    """
    if len(x) == 0:
        return True
    else:
        raise NotEmpty(wrong_value=x)


class TooShort(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by minlen """
    help_msg = 'len(x) >= {min_length} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, min_length, **kwargs):
        super(TooShort, self).__init__(wrong_value=wrong_value, min_length=min_length, **kwargs)


def minlen(min_length
           ):
    """
    'Minimum length' validation_function generator.
    Returns a validation_function to check that len(x) >= min_length

    :param min_length: minimum length for x
    :return:
    """
    def minlen_(x):
        if len(x) >= min_length:
            return True
        else:
            raise TooShort(wrong_value=x, min_length=min_length)

    minlen_.__name__ = 'length_greater_than_%s' % min_length
    return minlen_


class TooLong(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by maxlen """
    help_msg = 'len(x) <= {max_length} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, max_length, **kwargs):
        super(TooLong, self).__init__(wrong_value=wrong_value, max_length=max_length, **kwargs)


def maxlen(max_length,
           ):
    """
    'Maximum length' validation_function generator.
    Returns a validation_function to check that len(x) <= max_length

    :param max_length: maximum length for x
    :return:
    """
    def maxlen_(x):
        if len(x) <= max_length:
            return True
        else:
            # raise ValidationFailure('maxlen: len(x) <= ' + str(max_length) + ' does not hold for x=' + str(x))
            raise TooLong(wrong_value=x, max_length=max_length)

    maxlen_.__name__ = 'length_lesser_than_%s' % max_length
    return maxlen_


class WrongLength(ValidationFailure, ValueError):
    """ Custom failure raised by has_length """
    help_msg = 'len(x) == {ref_length} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, ref_length, **kwargs):
        super(WrongLength, self).__init__(wrong_value=wrong_value, ref_length=ref_length, **kwargs)


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

    has_length_.__name__ = 'length_equals_%s' % ref_length
    return has_length_


class LengthNotInRange(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by length_between """
    help_msg = '{min_length} <= len(x) <= {max_length} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, min_length, max_length, **kwargs):
        super(LengthNotInRange, self).__init__(wrong_value=wrong_value, min_length=min_length, max_length=max_length,
                                               **kwargs)


def length_between(min_len,
                   max_len,
                   ):
    """
    'Is length between' validation_function generator.
    Returns a validation_function to check that `min_len <= len(x) <= max_len (default)`.

    :param min_len: minimum length for x
    :param max_len: maximum length for x
    :return:
    """
    def length_between_(x):
        if (min_len <= len(x)) and (len(x) <= max_len):
            return True
        else:
            raise LengthNotInRange(wrong_value=x, min_length=min_len, max_length=max_len)

    length_between_.__name__ = 'length_between_%s_and_%s' % (min_len, max_len)
    return length_between_


class NotInAllowedValues(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by is_in """
    help_msg = 'x in {allowed_values} does not hold for x={wrong_value}'

    def __init__(self, wrong_value, allowed_values, **kwargs):
        super(NotInAllowedValues, self).__init__(wrong_value=wrong_value, allowed_values=allowed_values,
                                                 **kwargs)


def is_in(allowed_values  # type: Container
          ):
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
            # raise ValidationFailure('is_in: x in ' + str(allowed_values) + ' does not hold for x=' + str(x))
            raise NotInAllowedValues(wrong_value=x, allowed_values=allowed_values)

    is_in_allowed_values.__name__ = 'is_in_%s' % (allowed_values, )
    return is_in_allowed_values


class NotSubset(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by is_subset """
    help_msg = 'x subset of {reference_set} does not hold for x={wrong_value}. Unsupported elements: {unsupported}'

    def __init__(self, wrong_value, reference_set, unsupported, **kwargs):
        super(NotSubset, self).__init__(wrong_value=wrong_value, reference_set=reference_set, unsupported=unsupported,
                                        **kwargs)


def is_subset(reference_set  # type: Set
              ):
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
            # raise ValidationFailure('is_subset: len(x - reference_set) == 0 does not hold for x=' + str(x)
            #                   + ' and reference_set=' + str(reference_set) + '. x contains unsupported '
            #                      'elements ' + str(missing))
            raise NotSubset(wrong_value=x, reference_set=reference_set, unsupported=missing)

    is_subset_of.__name__ = 'is_subset_of_%s' % reference_set
    return is_subset_of


class DoesNotContainValue(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by contains """
    help_msg = '{ref_value} in x does not hold for x={wrong_value}'

    def __init__(self, wrong_value, ref_value, **kwargs):
        super(DoesNotContainValue, self).__init__(wrong_value=wrong_value, ref_value=ref_value, **kwargs)


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

    contains_ref_value.__name__ = 'contains_%s' % ref_value
    return contains_ref_value


class NotSuperset(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by is_superset """
    help_msg = 'x superset of {reference_set} does not hold for x={wrong_value}. Missing elements: {missing}'

    def __init__(self, wrong_value, reference_set, missing, **kwargs):
        super(NotSuperset, self).__init__(wrong_value=wrong_value, reference_set=reference_set, missing=missing,
                                          **kwargs)


def is_superset(reference_set  # type: Set
                ):
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
            # raise ValidationFailure('is_superset: len(reference_set - x) == 0 does not hold for x=' + str(x)
            #               + ' and reference_set=' + str(reference_set) + '. x does not contain required '
            #                       'elements ' + str(missing))
            raise NotSuperset(wrong_value=x, reference_set=reference_set, missing=missing)

    is_superset_of.__name__ = 'is_superset_of_%s' % reference_set
    return is_superset_of


class InvalidItemInSequence(ValidationFailure, ValueError):
    """ Custom ValidationFailure raised by on_all_ and on_each_ """
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
        tuple(callable, help_msg_str), a tuple(callable, failure_type), a tuple(callable, help_msg, failure_type)
        or a list of several such elements. Tuples indicate an implicit `failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of callables,
        they will be transformed to functions automatically.
    :return:
    """
    # create the validation functions
    validation_function_func = and_(*validation_func)

    def on_all_val(x):
        # validate all elements in x in turn
        for idx, x_elt in enumerate(x):
            try:
                res = validation_function_func(x_elt)
            except Exception as e:
                raise InvalidItemInSequence(wrong_value=x_elt, validation_func=validation_function_func,
                                            validation_outcome=e)

            # if not result_is_success(res): <= DO NOT REMOVE THIS COMMENT
            if (res is not None) and (res is not True) and (res is not NP_TRUE):
                # one element of x was not valid > raise
                # raise ValidationFailure('on_all_(' + str(validation_func) + '): failed for input '
                #                       'element [' + str(idx) + ']: ' + str(x_elt))
                raise InvalidItemInSequence(wrong_value=x_elt, validation_func=validation_function_func,
                                            validation_outcome=res)
        return True

    on_all_val.__name__ = 'apply_<%s>_on_all_elts' % get_callable_name(validation_function_func)
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
        A base validation function may be a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type),
        tuple(callable, help_msg_str, failure_type) or a list of several such elements. Tuples indicate an implicit
        `failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of callables,
        they will be transformed to functions automatically.
    :return:
    """
    # create a tuple of validation functions.
    validation_function_funcs = tuple(and_(validation_func) for validation_func in validation_functions_collection)

    # generate a validation function based on the tuple of validation_functions lists
    def on_each_val(x  # type: Tuple
                    ):
        if len(validation_function_funcs) != len(x):
            raise ValidationFailure(x, 'on_each_: x does not have the same number of elements than '
                             '`validation_functions_collection`.')
        else:
            # apply each validation_function on the input with the same position in the collection
            idx = -1
            for elt, validation_function_func in zip(x, validation_function_funcs):
                idx += 1
                try:
                    res = validation_function_func(elt)
                except Exception as e:
                    raise InvalidItemInSequence(wrong_value=elt,
                                                validation_func=validation_function_func,
                                                validation_outcome=e)

                # if not result_is_success(res): <= DO NOT REMOVE THIS COMMENT
                if (res is not None) and (res is not True) and (res is not NP_TRUE):
                    # one validation_function was unhappy > raise
                    raise InvalidItemInSequence(wrong_value=elt,
                                                validation_func=validation_function_func,
                                                validation_outcome=res)
            return True

    on_each_val.__name__ = 'map_<(%s)>_on_elts' % ', '.join([get_callable_name(f) for f in validation_function_funcs])
    return on_each_val
