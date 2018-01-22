import traceback
from typing import Any, Union, Set
from warnings import warn

from valid8.entry_points import Validator, ValidationError, NonePolicy
from valid8.validation_lib.types import HasWrongType
from valid8.validation_lib.collections import NotInAllowedValues, TooLong, TooShort
from valid8.validation_lib.comparables import TooSmall, TooBig
from valid8.base import ValueIsNone

try:
    # noinspection PyUnresolvedReferences
    from typing import Type
except ImportError:
    pass


def assert_instance_of(value, allowed_types: Union[type, Set[type]]):
    """
    An inlined version of instance_of(var_types)(value) without 'return True': it does not return anything in case of
    success, and raises a HasWrongType exception in case of failure.

    Used in quick_valid and wrap_valid

    :param value: the value to check
    :param allowed_types: the type(s) to enforce. If a set of types is provided it is considered alternate types: one
    match is enough to succeed. If None, type will not be enforced
    :return:
    """
    if not isinstance(allowed_types, set):
        # ref_type is a single type
        if not isinstance(value, allowed_types):
            raise HasWrongType(wrong_value=value, ref_type=allowed_types)
    else:
        # ref_type is a set
        match = False
        # test against each of the provided types
        for ref in allowed_types:
            if isinstance(value, ref):
                match = True
                break
        if not match:
            raise HasWrongType(wrong_value=value, ref_type=allowed_types,
                               help_msg='Value should be an instance of any of {ref_type}')


class _QuickValidator(Validator):
    """
    Represents the validator behind the `quick_valid` function.
    """

    def __init__(self):
        super(_QuickValidator, self).__init__(quick_valid)

    def _create_validation_error(self, name: str, value: Any, validation_outcome: Any = None,
                                 error_type: 'Type[ValidationError]' = None, help_msg: str = None, **kw_context_args):
        err = super(_QuickValidator, self)._create_validation_error(name=name, value=value,
                                                                    validation_outcome=validation_outcome,
                                                                    error_type=error_type, help_msg=help_msg,
                                                                    **kw_context_args)
        # disable displaying the annoying prefix
        err.display_prefix_for_exc_outcomes = False
        raise err

    def assert_valid(self, name: str, value: Any, error_type: 'Type[ValidationError]' = None,
                     help_msg: str = None, **kw_context_args):
        raise NotImplementedError('This is a special validator object that is not able to perform validation')

    def is_valid(self, value: Any):
        raise NotImplementedError('This is a special validator object that is not able to perform validation')


# TODO same none_policy than the rest of valid8 ? Probably not, it would slightly decrease performance no?
def quick_valid(name: str, value: Any,
                instance_of: Union[type, Set[type]] = None, enforce_not_none: bool = True,
                is_in: Set = None,
                min_value: Any = None, min_strict: bool = False, max_value: Any = None, max_strict: bool = False,
                min_len: int = None, min_len_strict: bool = False, max_len: int = None, max_len_strict: bool = False,
                error_type: 'Type[ValidationError]' = None,
                help_msg: str = None, **kw_context_args):
    """
    A validation function for quick inline validation of `value`, with minimal capabilities:

    * None handling: reject None (enforce_not_none=True, default), or accept None silently (enforce_not_none=False)
    * Type validation: `value` should be an instance of any of `var_types` if provided
    * Value validation:
       * if `allowed_values` is provided, `value` should be in that set
       * if `min_value` (resp. `max_value`) is provided, `value` should be greater than it. Comparison is not strict by
       default and can be set to strict by setting `min_strict`, resp. `max_strict`, to `True`
       * if `min_len` (resp. `max_len`) is provided, `len(value)` should be greater than it. Comparison is not strict by
       default and can be set to strict by setting `min_len_strict`, resp. `max_len_strict`, to `True`

    :param name: the applicative name of the checked value, that will be used in error messages
    :param value: the value to check
    :param instance_of: the type(s) to enforce. If a set of types is provided it is considered alternate types: one
    match is enough to succeed. If None, type will not be enforced
    :param enforce_not_none: boolean, default True. Whether to enforce that var is not None.
    :param is_in: an optional set of allowed values
    :param min_value: an optional minimum value
    :param min_strict: if True, only values strictly greater than `min_value` will be accepted
    :param max_value: an optional maximum value
    :param max_strict: if True, only values strictly lesser than `max_value` will be accepted
    :param min_len: an optional minimum length
    :param min_len_strict: if True, only values with length strictly greater than `min_len` will be accepted
    :param max_len: an optional maximum length
    :param max_len_strict: if True, only values with length strictly lesser than `max_len` will be accepted
    :param error_type: a subclass of `ValidationError` to raise in case of validation failure. By default a
    `ValidationError` will be raised with the provided `help_msg`
    :param help_msg: an optional help message to be used in the raised error in case of validation failure.
    :param kw_context_args: optional contextual information to store in the exception, and that may be also used
    to format the help message
    :return: nothing in case of success. Otherwise, raises a ValidationError
    """

    # backwards compatibility
    instance_of = instance_of or (kw_context_args.pop('allowed_types') if 'allowed_types' in kw_context_args else None)
    is_in = is_in or (kw_context_args.pop('allowed_values') if 'allowed_values' in kw_context_args else None)

    try:

        # the following corresponds to an inline version of
        # - _none_rejecter in base.py
        # - gt/lt in comparables.py
        # - minlen/maxlen/is_in in collections.py
        # - instance_of in types.py

        # TODO try (https://github.com/orf/inliner) to perform the inlining below automatically without code duplication
        # maybe not because below we skip the "return True" everywhere for performance

        if value is None:
            # inlined version of _none_rejecter in base.py
            if enforce_not_none:
                raise ValueIsNone(wrong_value=value)
                # raise MissingMandatoryParameterException('Error, ' + name + '" is mandatory, it should be non-None')

            # else do nothing and return

        else:
            if instance_of is not None:
                assert_instance_of(value, instance_of)

            if is_in is not None:
                # inlined version of is_in(allowed_values=allowed_values)(value) without 'return True'
                if value not in is_in:
                    raise NotInAllowedValues(wrong_value=value, allowed_values=is_in)

            if min_value is not None:
                # inlined version of gt(min_value=min_value, strict=min_strict)(value) without 'return True'
                if min_strict:
                    if value <= min_value:
                        raise TooSmall(wrong_value=value, min_value=min_value, strict=True)
                else:
                    if value < min_value:
                        raise TooSmall(wrong_value=value, min_value=min_value, strict=False)

            if max_value is not None:
                # inlined version of lt(max_value=max_value, strict=max_strict)(value) without 'return True'
                if max_strict:
                    if value >= max_value:
                        raise TooBig(wrong_value=value, max_value=max_value, strict=True)
                else:
                    if value > max_value:
                        raise TooBig(wrong_value=value, max_value=max_value, strict=False)

            if min_len is not None:
                # inlined version of minlen(min_length=min_len, strict=min_len_strict)(value) without 'return True'
                if min_len_strict:
                    if len(value) <= min_len:
                        raise TooShort(wrong_value=value, min_length=min_len, strict=True)
                else:
                    if len(value) < min_len:
                        raise TooShort(wrong_value=value, min_length=min_len, strict=False)

            if max_len is not None:
                # inlined version of maxlen(max_length=max_len, strict=max_len_strict)(value) without 'return True'
                if max_len_strict:
                    if len(value) >= max_len:
                        raise TooLong(wrong_value=value, max_length=max_len, strict=True)
                else:
                    if len(value) > max_len:
                        raise TooLong(wrong_value=value, max_length=max_len, strict=False)

    except Exception as e:
        raise _QUICK_VALIDATOR._create_validation_error(name, value, validation_outcome=e, error_type=error_type,
                                                        help_msg=help_msg, **kw_context_args)


_QUICK_VALIDATOR = _QuickValidator()


class WrappingValidatorEye:
    """ Represents the object where users may put the validation outcome inside a wrap_valid context manager.
    You may set any field on this object, it will be put in the 'outcome' field """

    __slots__ = ['outcome', 'last_field_name_used']

    def __init__(self):
        self.outcome = None
        self.last_field_name_used = 'outcome'

    def __setattr__(self, key, value):
        """
        You may set any field on this object, it will be put in the 'outcome' field

        :param key: not used
        :param value:
        :return:
        """
        if key == 'last_field_name_used':
            super(WrappingValidatorEye, self).__setattr__('last_field_name_used', value)
        else:
            # remember the key
            super(WrappingValidatorEye, self).__setattr__('last_field_name_used', key)
            super(WrappingValidatorEye, self).__setattr__('outcome', value)


class _Dummy_Callable_:
    """ A dummy callable whose name can be configured """
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        pass

    def __str__(self):
        return self.name


class wrap_valid(Validator):
    """
    A context manager to wrap validation tasks.
    Any exception caught within this context will be wrapped by a ValidationError and raised.

    You can also use the returned object to store a boolean value indicating success or failure. For example

    ```python
    from valid8 import wrap_valid
    with wrap_valid('surface', surf) as v:
        v.alid = surf > 0 and isfinite(surf)
    ```
    """
    def __init__(self, name: str, value: Any, instance_of: Union[type, Set[type]] = None,
                 error_type: 'Type[ValidationError]' = None, help_msg: str = None, **kw_context_args):
        """
        Creates a context manager to wrap validation tasks. Any exception caught within this context will be wrapped
        by a ValidationError and raised.

        You can also use the returned object to store a boolean value indicating success or failure. For example

        ```python
        from valid8 import wrap_valid
        with wrap_valid('surface', surf) as v:
            v.alid = surf > 0 and isfinite(surf)
        ```

        :param name: the name of the variable being validated
        :param value: the value being validated
        :param instance_of: the type(s) to enforce. If a set of types is provided it is considered alternate types:
        one match is enough to succeed. If None, type will not be enforced
        :param error_type: a subclass of `ValidationError` to raise in case of validation failure. By default a
        `ValidationError` will be raised with the provided `help_msg`
        :param help_msg: an optional help message to be used in the raised error in case of validation failure.
        :param kw_context_args: optional contextual information to store in the exception, and that may be also used
        to format the help message
        """
        # First perform the type check if needed
        if instance_of is not None:
            quick_valid(name=name, value=value, instance_of=instance_of)

        validation_function = _Dummy_Callable_('<wrap_valid_contents>')
        super(wrap_valid, self).__init__(validation_function, error_type=error_type, help_msg=help_msg,
                                         none_policy=NonePolicy.VALIDATE, **kw_context_args)
        self.name = name
        self.value = value
        self.eye = WrappingValidatorEye()

    def __enter__(self):
        # extract the source file and line number where the calling 'with wrap_valid()' line is
        stack = traceback.extract_stack()
        self.src_file_path, self.src_file_line_nb, *_ = stack[-2]

        # return the object to collect validation results
        return self.eye

    def __exit__(self, exc_type, exc_val, exc_tb):

        result = exc_val or self.eye.outcome

        if result is not None and result is not True:
            # *** We should raise a Validation Error ***

            # extract the source file and line number where the calling 'with wrap_valid()' line is
            stack = traceback.extract_stack()
            src_file_path, src_file_line_nb_end, *_ = stack[-2]

            if src_file_path != self.src_file_path:
                warn('Error identifying the source file where wrap_valid was used - no string representation will '
                     'be available')
            else:
                # read the lines in the source corresponding to the contents
                try:
                    if self.src_file_path == '<input>':
                        # -- that's the interpreter history
                        # code inspired from 'findsource' function in
                        #    https://github.com/uqfoundation/dill/blob/master/dill/source.py
                        # TODO test it and make it work on windows as it doesn't (even with pyreadline installed)
                        import readline
                        lbuf = readline.get_current_history_length()
                        lines = [readline.get_history_item(i) + '\n' for i in range(1, lbuf)]
                        # print('history! yes {} {}'.format(self.src_file_line_nb, lbuf))
                        # for line in lines:
                        #     print(line)
                        src_file_line_nb_end = len(lines)
                    else:
                        # -- that's a file
                        with open(self.src_file_path) as src:
                            lines = list(src)
                    wrapped_block_lines = [line.strip() for line in lines[self.src_file_line_nb:src_file_line_nb_end]]

                    if exc_val is not None:
                        # -- There was an exception, we dont know where: output the full code in self.main_function.name
                        self.main_function.name = ' ; '.join(wrapped_block_lines)

                    else:
                        # -- There was no exception so we just output the line where self.eye.outcome is computed
                        found = None
                        for idx, line in enumerate(wrapped_block_lines[::-1]):
                            if ('.' + self.eye.last_field_name_used) in line:
                                found = line
                                break
                        if found is not None:
                            self.main_function.name = found
                        else:
                            # not able to identify... dump the whole block
                            self.main_function.name = ' ; '.join(wrapped_block_lines)

                except Exception as e:
                    warn('Error while inspecting source code at {}. No details will be added to the resulting '
                         'exception. Caught {}'.format(self.src_file_path, e))

            raise self._create_validation_error(self.name, self.value, validation_outcome=result)
