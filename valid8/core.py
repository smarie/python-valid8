from abc import abstractmethod
from typing import Callable, Any

from mini_lambda.main import _LambdaExpression


def _create_main_validation_function(att_validators, allow_not_none: bool):
    """
    Creates the main validation function to be used for a specific input.
    * if att_validators is not a list, it transforms it into a list
    * if 'not_none' validator is present in the list, it should be the first in the list.

    The function generates a validation function that will
    * either raise an error on None or ignore None values silently, depending respectively on if the user included
    `not_none` in the validators list or not
    * combine all validators from the list (except 'not_none') in an 'and_' validator if more than one validator

    :param att_validators: a validator function or a list of validators
    :param allow_not_none: True to allow 'not_none' to be present in the list of validators
    :return:
    """
    att_validators = _assert_list_and_protect_not_none(att_validators, allow_not_none=allow_not_none)

    if att_validators[0] != not_none:
        ignore_nones_silently = True
        remaining_validators = att_validators
    else:
        # the first element is not_none, it will be removed and replaced with _not_none_checker
        ignore_nones_silently = False
        remaining_validators = att_validators[1:]

    if len(remaining_validators) >= 1:
        # note that and_ automatically reduces to contents when contents is a single element
        main_validation_function = _not_none_checker(and_(remaining_validators),
                                                     ignore_none_silently=ignore_nones_silently)
    else:
        # there is only one validator here
        if ignore_nones_silently:
            main_validation_function = _not_none_checker(remaining_validators[0],
                                                         ignore_none_silently=ignore_nones_silently)
        else:
            # there is a single validator here and it is 'not_none'. We cant replace it with
            main_validation_function = not_none

    return main_validation_function


def get_validator_display_name(validator: Callable):
    """
    Used internally to get the name to display concerning a validator, in error messages for example.

    :param validator:
    :return:
    """
    return validator.__name__ if hasattr(validator, '__name__') else str(validator)


def _not_none_checker(validator, ignore_none_silently: bool = True):
    """
    Generates a checker handling None values. When a None value is received, it is not passed to the validator.
    Instead this operator will either drop silently (ignore_none_silently = True) or return a False
    (ignore_none_silently=False)

    :param validator:
    :param ignore_none_silently:
    :return:
    """
    if ignore_none_silently:
        def drop_none_silently(x):
            if x is not None:
                return validator(x)
            else:
                # value is None: skip validation (users should explicitly include 'not_none' as the first validator to
                # change this behaviour)
                return True

        # set a name so that the error messages are correct
        drop_none_silently.__name__ = get_validator_display_name(validator)
        return drop_none_silently

        # use the `decorate` helper method to preserve name and signature of the inner object
        # ==> NO, we want to support also non-function callable objects
        # def drop_none_silently_wrapper(validator, x):
        #     if x is not None:
        #         return validator(x)
        #     else:
        #         # value is None : skip validation (users should explicitly include 'not_none' as the first validator to
        #         # change this behaviour)
        #         return True
        # drop_none_silently = decorate(validator, drop_none_silently_wrapper)
        # return drop_none_silently

    else:
        def check_not_none(x):
            # not_none will perform the Exception raising
            if not_none(x):
                return validator(x)
            else:
                # this should never happen, except if not_none changed behaviour and we forgot to align everything..
                raise Exception('Internal error - please create an issue on the project page')
        return check_not_none


class Failure(ValueError):
    """
    A utility class to represent base validation functions failures. It is a subclass of ValueError for consistency with
    python best practices. It is recommended that base validation functions subclass this exception type in order to
    provide a unique exception identifier for each base validation failure.
    """
    pass


class WrappedFailure(Failure):
    """ Represents a validation failure due to another base validation function """

    def __init__(self, failing_base_validation_func, var_value, validation_outcome: Any = None):
        """
        Creates a validation Failure associated with validation of var_value using `base_validation_func`.
        Additional details about the validation_outcome (result or exception) can be provided

        :param failing_base_validation_func:
        :param var_value:
        :param validation_outcome:
        """

        # store details in the object for future access if needed
        self.failing_base_validation_func = failing_base_validation_func
        self.var_value = var_value
        self.validation_outcome = validation_outcome

        # create the exception main message according to the type of result
        if isinstance(validation_outcome, Exception):
            contents = 'base validator [{val}] raised [{exc}: {det}]' \
                       ''.format(val=get_validator_display_name(failing_base_validation_func),
                                 exc=type(validation_outcome).__name__, det=validation_outcome)
            # exception: also link the traceback
            self.__traceback__ = validation_outcome.__traceback__
        else:
            contents = 'base validator [{val}] returned [{res}].' \
                       ''.format(val=get_validator_display_name(failing_base_validation_func), res=validation_outcome)

        # call super constructor with the message
        super(Failure, self).__init__(contents)


def get_names(validators):
    return ', '.join([get_validator_display_name(val) for val in validators])


# this validator is too tied to the above to be moved elsewhere
def not_none(x: Any):
    """ 'Is not None' validator """
    if x is None:
        raise Failure('not_none: failure, x is None')
    else:
        return True


def _assert_list_and_protect_not_none(validators, allow_not_none: bool = False):
    """
     * if validators is an empty list, throw error
     * If validators is a singleton, turns it into a list.
     * If validators contains not_none and allow_not_none is set to True, asserts that not_none is first in the list
     * If validators contains not_none and allow_not_none is set to False, asserts that not_none is not present at all
     in the list
     * all validators that are instances of _LambdaExpression are transformed to functions automatically

    :param validators:
    :param allow_not_none:
    :return:
    """
    i = -1
    if isinstance(validators, _LambdaExpression):
        # special case of a _LambdaExpression: automatically convert to a function here,
        # Indeed the try/except below wont work because .index() will always return something (a new _LambdaExpression).
        validators = [validators.as_function()]
    else:
        try:
            # special case of a _LambdaExpression: automatically convert to a function
            # note: we have to do it before even performing the .index() below otherwise we get failures
            validators = [v.as_function() if isinstance(v, _LambdaExpression) else v for v in validators]

            # find 'not_none' in the list?
            i = validators.index(not_none)

        except ValueError:
            # not_none not found in validators list : ok
            pass
        except (AttributeError, TypeError):
            # validators is not a list (not iterable, no attribute 'index'): turn it into a list
            validators = [validators]

    # not_none ?
    # obviously this does not prevent users to embed a not_none inside an 'and_' or something else... but we cant
    # prevent all mistakes :)
    if i > 0 or (i == 0 and not allow_not_none):
        raise ValueError('not_none is a special validator that can only be provided at the beginning of the'
                         ' global validators list')
    # empty list ?
    if len(validators) == 0:
        raise ValueError('provided validators list is empty')

    return validators


# ----------- negation
class DidNotFail(Failure):
    """ Raised by the not_ operator when the inner validator did not fail."""
    def __init__(self, validator, value):
        """
        Constructor from the inner validator name and the value that caused validation

        :param validator:
        :param value:
        """
        msg = '{validator} validated value {value} with success, therefore the not() is a failure' \
              ''.format(validator=get_validator_display_name(validator), value=value)
        super(DidNotFail, self).__init__(msg)


def not_(validator, catch_all: bool = False):
    """
    Generates the inverse of the provided validator: when the validator returns `False` or raises a `ValidationError`,
    this validator returns `True`. Otherwise it returns `False`.

    By default, `Expection` other than `ValidationError` are not caught and therefore fail the validation
    (`catch_all=False`). To change this behaviour you can turn the `catch_all` parameter to `True`, in which case all
    exceptions will be caught instead of just `ValidationError`s.

    Note that you may provide a list of validators to `not_()`. It will be interpreted as `not_(and_(<valiators_list>))`

    :param validator:
    :param catch_all: an optional boolean flag. By default, only ValidationError are silently catched and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be catched and turned to a
    'ok' result
    :return:
    """

    # in case this is a validator list, create a 'and_' around it (otherwise this returns the validator)
    # not any more, this is not very intuitive
    # validator = and_(validator)

    def not_v_(x):
        try:
            res = validator(x)
            if not result_is_success(res):  # inverse the result
                return True

        except Failure:
            return True  # caught exception: return True

        except Exception as e:
            if not catch_all:
                raise e
            else:
                return True  # caught exception: return True

        # if we're here that's a failure
        raise DidNotFail(validator, x)

    not_v_.__name__ = 'not({})'.format(get_validator_display_name(validator))
    return not_v_


# ----------- composition (we cant move these in another file since and_() is quite tight to the core)
class CompositionFailure(Failure):
    """ Root failure of all composition operators """

    def __init__(self, validators, value):
        """
        Constructor from a list of validators and a value.
        The constructor will replay the validation process in order to get all the results and attach them in
        the message

        :param validators:
        :param value:
        """
        successes = list()
        failures = dict()
        failures_for_print = dict()

        for validator in validators:
            name = get_validator_display_name(validator)
            try:
                res = validator(value)
                if result_is_success(res):
                    successes.append(name)
                else:
                    failures[validator] = res
                    failures_for_print[name] = str(res)

            except Exception as exc:
                failures[validator] = exc
                failures_for_print[name] = '[{exc_type}] {msg}'.format(exc_type=type(exc).__name__, msg=str(exc))

        msg = '{what} validation for value [{val}]. Successes: {succ} / Failures: {fails} ' \
              ''.format(what=self.get_what(), val=value, succ=successes, fails=failures_for_print)

        super(CompositionFailure, self).__init__(msg)

        # additional information
        self.validators = validators
        self.value = value
        self.success = successes
        self.failures = failures

    @abstractmethod
    def get_what(self):
        pass


class AtLeastOneFailed(CompositionFailure):
    """ Raised by the and_ operator when at least one of the inner validators failed validation """

    def get_what(self):
        return 'At least one validator failed'


def and_(validators):
    """
    An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a
    `ValidationException` on the first `False` received or `Exception` caught.

    Note that an implicit `and_` is performed if you provide a list of validators to `@validate`.

    :param validators:
    :return:
    """

    validators = _assert_list_and_protect_not_none(validators)

    if len(validators) == 1:
        return validators[0]  # simplification for single validator case
    else:
        def and_v_(x):
            for validator in validators:
                try:
                    res = validator(x)
                    if not result_is_success(res):
                        # one validator was unhappy > raise
                        raise AtLeastOneFailed(validators, x)

                except Exception as e:
                    # one validator was unhappy > raise
                    raise AtLeastOneFailed(validators, x).with_traceback(e.__traceback__)

            return True

        and_v_.__name__ = 'and({})'.format(get_names(validators))
        return and_v_


class AllValidatorsFailed(Failure):
    """ Raised by the or_ and xor_ operator when all inner validators failed validation """

    def get_what(self):
        return 'No validator succeeded'


def or_(validators):
    """
    An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught
    exception's message if any.

    :param validators:
    :return:
    """

    validators = _assert_list_and_protect_not_none(validators)

    if len(validators) == 1:
        return validators[0]  # simplification for single validator case
    else:
        def or_v_(x):
            for validator in validators:
                try:
                    res = validator(x)
                    if result_is_success(res):
                        # we can return : one validator was happy
                        return True
                except Exception:
                    # catch all silently
                    pass

            # no validator accepted: gather details and raise
            raise AllValidatorsFailed(validators, x)

        or_v_.__name__ = 'or({})'.format(get_names(validators))
        return or_v_


class XorTooManySuccess(Failure):
    """ Raised by the xor_ operator when more than one validator succeeded """

    def get_what(self):
        return 'Too many validators (more than 1) succeeded'


def xor_(validators):
    """
    A 'xor' validator: returns `True` if exactly one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught
    exception's message if any.

    :param validators:
    :return:
    """

    validators = _assert_list_and_protect_not_none(validators)

    if len(validators) == 1:
        return validators[0]  # simplification for single validator case
    else:
        def xor_v_(x):
            ok_validators = []
            for validator in validators:
                try:
                    res = validator(x)
                    if result_is_success(res):
                        ok_validators.append(validator)
                except Exception:
                    pass

            # return if were happy or not
            if len(ok_validators) == 1:
                # one unique validator happy: success
                return True

            elif len(ok_validators) > 1:
                # several validators happy : fail
                raise XorTooManySuccess(validators, x)

            else:
                # no validator happy, fail
                raise AllValidatorsFailed(validators, x)

        xor_v_.__name__ = 'xor({})'.format(get_names(validators))
        return xor_v_


def not_all(validators, catch_all: bool = False):
    """
    An alias for not_(and_(validators)).

    :param validators: a validators list or a single validator
    :param catch_all: an optional boolean flag. By default, only ValidationError are silently catched and turned into
    a 'ok' result. Turning this flag to True will assume that all exceptions should be catched and turned to a
    'ok' result
    :return:
    """

    # in case this is a validator list, create a 'and_' around it (otherwise this returns the validator)
    validators = and_(validators)
    return not_(validators, catch_all=catch_all)


SUCCESS_CONDITIONS = 'in {None, True}'  # used in some error messages


def result_is_success(validation_result):
    """
    Helper function to check if some results returned by a validation function mean success or failure.

    The result should be True or None for a validation to be considered valid. Note that this is
    quite different from the standard python truth value test (where None is equivalent to False), but it seems
    more adapted to an intuitive usage, where a function that returns silently without any output means a
    successful validation.

    :param validation_result:
    :return:
    """
    return validation_result in {None, True}
