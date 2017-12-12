from abc import abstractmethod
from typing import Callable, Any, Union, Tuple, List, Type, Sequence

from mini_lambda.main import _LambdaExpression


class BasicFailure(ValueError):
    """
    A utility class to represent base validation functions failures. It is a subclass of ValueError for consistency with
    python best practices.

    It is however recommended that exceptions raised by base validation functions be specific subtypes instead of that
    generic one, in order to provide a unique exception identifier for each failure mode.

    For example

    ```python
    class ConditionWasNotMet(BasicFailure):
        pass

    def my_validator(x):
        if <condition>:
            return True
        else:
            raise ConditionWasNotMet("x={val} does not meet <condition>".format(val=x))
    ```

    Note: in order to get more consistent error messages as well as error contents, applications may wish to subclass
    the `Failure` type instead of `BasicFailure`. See `Failure` for details.
    """
    pass


class Failure(BasicFailure):
    """
    Represents a validation failure with details (as opposed to `BasicFailure` that is basically a blank exception
    type subclassing `ValueError`).

    Users may typically extend this class to define their
    """

    help_msg = 'No additional diagnostic information is available'
    """ This class attribute holds the default help message used when no `help_msg` attribute is set at instance level 
    (for example through the constructor). Subclasses may wish to override this class attribute, or to define a 
    different behaviour by overriding `get_diagnostics_msg` """

    def __init__(self, validation_function, validated_value, validation_outcome, help_msg: str = None):
        """
        Creates a Failure associated with validation of validated_value using `base_validation_func`.
        Additional details about the validation_outcome (result or exception) can be provided

        :param validation_function: the validation function that failed validation
        :param validated_value: the value that was validated
        :param validation_outcome: the result (either a caught exception or a variable different than `True` or `None`)
        :param help_msg: an optional help message specific to this failure. If not provided, the class attribute
        `help_msg` will be used. This behaviour may be redefined by subclasses by overriding `get_diagnostics_msg`
        """

        # store details in the object for future access if needed
        self.validation_function = validation_function
        self.validated_value = validated_value
        self.validation_outcome = validation_outcome

        # store this one ONLY if non-None, otherwise the class attribute should be left visible
        if help_msg is not None:
            self.help_msg = help_msg

        # create the exception main message according to the type of result
        if isinstance(validation_outcome, Exception):
            contents = self.get_msg_for_caught_exception(validation_function, validated_value, validation_outcome)
            # exception: also link the traceback
            self.__traceback__ = validation_outcome.__traceback__
        else:
            contents = self.get_msg_for_wrong_result(validation_function, validated_value, validation_outcome)

        # call super constructor with the message
        super(BasicFailure, self).__init__(contents)

    def get_msg_for_wrong_result(self, failing_base_validation_func, value, validation_outcome):
        """

        :param failing_base_validation_func:
        :param value:
        :param validation_outcome:
        :return:
        """
        contents = 'base validator [{val}] failed validating [{value}] and returned [{res}]. {diag}' \
                   ''.format(val=get_validator_display_name(failing_base_validation_func), res=validation_outcome,
                             value=value, diag=self.get_diagnostics_msg(value))
        return contents

    def get_msg_for_caught_exception(self, failing_base_validation_func, value, validation_outcome):
        """

        :param failing_base_validation_func:
        :param value:
        :param validation_outcome:
        :return:
        """
        contents = 'base validator [{val}] failed validating [{value}] and raised [{exc}: {det}].' \
                   ''.format(val=get_validator_display_name(failing_base_validation_func),
                             exc=type(validation_outcome).__name__, det=validation_outcome,
                             value=value, diag=self.get_diagnostics_msg())
        return contents

    def get_diagnostics_msg(self):
        """
        The method used to get the diagnostics message associated with a failure. By default it returns the 'help_msg'
        attribute, whether it is defined at the instance level (for example by passing help_msg to the constructor) or
        at the class level (default).

        Subclasses may wish to override this behaviour to provide more fine-grain diagnosis adapted to the validator
        function and the value that was validated and failed validation. All contextual information is available in
        `self`.
        :return: the diagnostics message, explaining for example why this failure happened, and/or recommendations to
        make sure that it does not happen again
        """
        return self.help_msg


CallableAndFailureTuple = Tuple[Callable, Union[str, Type[BasicFailure]]]
""" Represents the allowed construct to define a failure raiser from a validator function: a tuple """

BaseValidator = Union[Callable, CallableAndFailureTuple]
""" Represents the 'typing' type for 'base validator' """

BaseValidators = Union[BaseValidator, List['BaseValidators']]  # recursion is used here ('forward reference')
""" Represents the 'typing' type for 'base validators' arguments in the various methods """

supported_syntax = 'a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type), or a list of ' \
                   'several such elements in which not_none if present shall be first. Nested lists are supported ' \
                   'and indicate an implicit `and_` (such as the main list). Tuples indicate an implicit ' \
                   '`failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be ' \
                   'used instead of callables, they will be transformed to functions automatically.'


def get_validator_display_name(validator: Callable):
    """
    Used internally to get the name to display concerning a validator, in error messages for example.

    :param validator:
    :return:
    """
    return validator.__name__ if hasattr(validator, '__name__') else str(validator)


def get_names(validators: Sequence[Callable]):
    return ', '.join([get_validator_display_name(val) for val in validators])


def _none_handling_wrapper(validator: Callable, ignore_none_silently: bool = True) -> Callable:
    """
    Wraps the given validation function to handle None values. When a None value is received by the wrapper, it is not
    passed to the validator. Instead this operator will either drop silently (ignore_none_silently = True) or return a
    False (ignore_none_silently=False)

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


def failure_raiser(validation_function: Callable, failure_type_or_help_msg: Union[str, Type[Failure]] = None):
    """
    Wraps the provided validator so that in case of failure it raises the given failure_type or a Failure with the
    given help message.

    :param validation_function:
    :param failure_type_or_help_msg: a subclass of BasicFailure or None (default, means Failure)
    :return:
    """

    if validation_function is not_none:
        raise ValueError('not_none is a special validator that should only ')

    # convert mini-lambdas to functions if needed
    if isinstance(validation_function, _LambdaExpression):
        validation_function = validation_function.as_function()

    failure_type_or_help_msg = failure_type_or_help_msg or Failure
    if not issubclass(failure_type_or_help_msg, Failure) and not isinstance(failure_type_or_help_msg, str):
        raise ValueError('failure_type_or_help_msg should be a subclass of Failure or a text, found: {}'
                         ''.format(str(failure_type_or_help_msg)))

    def raiser(x):
        """ Wraps validation_function to raise a failure_type_or_help_msg in case of failure """

        try:
            # perform validation
            res = validation_function(x)

        except Exception as e:
            # caught any exception: raise the provided failure type with that exception in the details
            if isinstance(failure_type_or_help_msg, str):
                exc = Failure(validation_function=validation_function, validated_value=x,
                              validation_outcome=e, help_msg=failure_type_or_help_msg)
            else:
                exc = failure_type_or_help_msg(failing_base_validation_func=validation_function, var_value=x,
                                               validation_outcome=e)
            raise exc.with_traceback(e.__traceback__)

        if not result_is_success(res):
            # failure without exception: raise the provided failure type
            if isinstance(failure_type_or_help_msg, str):
                exc = Failure(validation_function=validation_function, validated_value=x,
                              validation_outcome=res, help_msg=failure_type_or_help_msg)
            else:
                exc = failure_type_or_help_msg(failing_base_validation_func=validation_function, var_value=x,
                                               validation_outcome=res)
            raise exc

    # set a name so that the error messages are correct
    raiser.__name__ = get_validator_display_name(validation_function)
    return raiser


def _make_proper_validators_list(validators: BaseValidators, allow_not_none: bool = False):
    """
    This function handles the various ways that users may enter 'validators', so as to output a list of callable
    methods.

    valid8 supports the following expressions for 'validators'
     * <BaseValidator>
     * List[<BaseValidator>(s)]. The list must not be empty. If not_none is used in the list it must be first.

    <BaseValidator> may either be
     * a callable or a mini-lambda expression (instance of _LambdaExpression - in which case it is automatically
     'closed').
     * a Tuple[callable or mini-lambda expression ; failure_type]. Where failure type should be a subclass of
     valid8.BasicFailure. In which case the tuple will be replaced with a failure_raiser(callable, failure_type)

    When the contents provided does not match the above, this function raises ValueError.
    Otherwise it produces a list of callables.

    :param validators:
    :param allow_not_none:
    :return:
    """

    # handle the case where validators is not yet a list or is empty or none
    if validators is None:
        raise ValueError('mandatory validators is none')

    elif not isinstance(validators, list):
        validators = [validators]

    elif len(validators) == 0:
        raise ValueError('provided validators list is empty')

    # now validators is a non-empty list
    final_list = []
    for v in validators:
        if isinstance(v, _LambdaExpression):
            # special case of a _LambdaExpression: automatically convert to a function
            # note: we have to do it before anything else (such as .index) otherwise we may get failures
            final_list.append(v.as_function())

        elif isinstance(v, tuple):
            # convert all the tuples to failure raisers
            final_list.append(failure_raiser(*v))

        elif callable(v):
            # use the validator directly
            final_list.append(v)

        elif isinstance(v, list):
            # a list is an implicit and_, make it explicit
            final_list.append(and_(*v))

        else:
            raise TypeError('base validation function(s) not compliant with the allowed syntax. Base validation'
                            ' function(s) can be {}. Found [{}].'.format(supported_syntax, str(v)))

    i = -1
    try:
        # find 'not_none' in the list?
        i = final_list.index(not_none)
    except ValueError:
        # `not_none` not found in validators list : ok
        pass

    # obviously this does not prevent users to embed a not_none inside an 'and_' or something else... but we cant
    # prevent all mistakes :)
    if i > 0 or (i == 0 and not allow_not_none):
        raise ValueError('not_none is a special validator that can only be provided at the beginning of the'
                         ' global validators list')

    return final_list


def _create_main_validation_function(att_validators: BaseValidators, allow_not_none: bool):
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
    att_validators = _make_proper_validators_list(att_validators,
                                                  allow_not_none=allow_not_none)

    if att_validators[0] != not_none:
        ignore_nones_silently = True
        remaining_validators = att_validators
    else:
        # the first element is not_none, it will be removed and replaced with _none_handling_wrapper
        ignore_nones_silently = False
        remaining_validators = att_validators[1:]

    if len(remaining_validators) >= 1:
        # note that and_ automatically reduces to contents when contents is a single element
        main_validation_function = _none_handling_wrapper(and_(*remaining_validators),
                                                          ignore_none_silently=ignore_nones_silently)
    else:
        # there is only one validator here
        if ignore_nones_silently:
            main_validation_function = _none_handling_wrapper(remaining_validators[0],
                                                              ignore_none_silently=ignore_nones_silently)
        else:
            # there is a single validator here and it is 'not_none'. We cant replace it with
            main_validation_function = not_none

    return main_validation_function


# ------------ Not none -----------
# this validator is too tied to the above to be moved elsewhere
def not_none(x: Any):
    """
    'Is not None' validator. Since by default None values are ignored by validation, users have to explicitly
    :param x:
    :return:
    """
    if x is None:
        raise BasicFailure('not_none: failure, x is None')
    else:
        return True


# ----------- negation
class DidNotFail(BasicFailure):
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

        except BasicFailure:
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
class CompositionFailure(BasicFailure):
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


def and_(*validators):
    """
    An 'and' validator: it returns `True` if all of the provided validators return `True`, or raises a
    `ValidationException` on the first `False` received or `Exception` caught.

    Note that an implicit `and_` is performed if you provide a list of validators to any of the entry points
    (`@validate`, `@validate_arg`, `assert_valid`, `is_valid`, `Validator`)

    :param validators:
    :return:
    """

    validators = _make_proper_validators_list(list(validators))

    if len(validators) == 1:
        return validators[0]  # simplification for single validator case: no wrapper
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


class AllValidatorsFailed(BasicFailure):
    """ Raised by the or_ and xor_ operator when all inner validators failed validation """

    def get_what(self):
        return 'No validator succeeded'


def or_(*validators):
    """
    An 'or' validator: returns `True` if at least one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught
    exception's message if any.

    :param validators:
    :return:
    """

    validators = _make_proper_validators_list(list(validators))

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


class XorTooManySuccess(BasicFailure):
    """ Raised by the xor_ operator when more than one validator succeeded """

    def get_what(self):
        return 'Too many validators (more than 1) succeeded'


def xor_(*validators):
    """
    A 'xor' validator: returns `True` if exactly one of the provided validators returns `True`. All exceptions will be
    silently caught. In case of failure, a global `ValidationException` will be raised, together with the first caught
    exception's message if any.

    :param validators:
    :return:
    """

    validators = _make_proper_validators_list(list(validators))

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

    # in case this is a list, create a 'and_' around it (otherwise and_ will return the validator without wrapping it)
    main_validator = and_(validators)
    return not_(main_validator, catch_all=catch_all)


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
