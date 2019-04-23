import sys
from inspect import isclass
from warnings import warn

from linecache import getline

from valid8.base import ValueIsNone, raise_
from valid8.entry_points import Validator, ValidationError, NonePolicy, assert_valid
from valid8.validation_lib.types import HasWrongType, IsWrongType
from valid8.validation_lib.collections import NotInAllowedValues, TooLong, TooShort, WrongLength, DoesNotContainValue, \
    NotSubset, NotSuperset
from valid8.validation_lib.comparables import TooSmall, TooBig, NotEqual

try:  # python 3.5+
    # noinspection PyUnresolvedReferences
    from typing import Any, Union, Set, Iterable, Callable, Container, Tuple
    try:  # python 3.5.3-
        from typing import Type
    except ImportError:
        pass
except ImportError:
    pass


def assert_instance_of(value,
                       allowed_types  # type: Union[Type, Tuple[Type]]
                       ):
    """
    An inlined version of instance_of(var_types)(value) without 'return True': it does not return anything in case of
    success, and raises a HasWrongType exception in case of failure.

    Used in validate and validation/validator

    :param value: the value to check
    :param allowed_types: the type(s) to enforce. If a tuple of types is provided it is considered alternate types: one
        match is enough to succeed. If None, type will not be enforced
    :return:
    """
    if not isinstance(value, allowed_types):
        try:
            # more than 1 ?
            allowed_types[1]
            raise HasWrongType(wrong_value=value, ref_type=allowed_types,
                               help_msg='Value should be an instance of any of {ref_type}')
        except IndexError:
            # 1
            allowed_types = allowed_types[0]
        except TypeError:
            # 1
            pass
        raise HasWrongType(wrong_value=value, ref_type=allowed_types)


def assert_subclass_of(typ,
                       allowed_types  # type: Union[Type, Tuple[Type]]
                       ):
    """
    An inlined version of subclass_of(var_types)(value) without 'return True': it does not return anything in case of
    success, and raises a IsWrongType exception in case of failure.

    Used in validate and validation/validator

    :param typ: the type to check
    :param allowed_types: the type(s) to enforce. If a tuple of types is provided it is considered alternate types:
        one match is enough to succeed. If None, type will not be enforced
    :return:
    """
    if not issubclass(typ, allowed_types):
        try:
            # more than 1 ?
            allowed_types[1]
            raise IsWrongType(wrong_value=typ, ref_type=allowed_types,
                              help_msg='Value should be a subclass of any of {ref_type}')
        except IndexError:
            # 1
            allowed_types = allowed_types[0]
        except TypeError:
            # 1
            pass
        raise IsWrongType(wrong_value=typ, ref_type=allowed_types)


class _QuickValidator(Validator):
    """
    Represents the Validator behind the `validate` function.
    """

    def __init__(self):
        super(_QuickValidator, self).__init__(validate)

    def _create_validation_error(self,
                                 name,                     # type: str
                                 value,                    # type: Any
                                 validation_outcome=None,  # type: Any
                                 error_type=None,          # type: Type[ValidationError]
                                 help_msg=None,            # type: str
                                 **kw_context_args):
        err = super(_QuickValidator, self)._create_validation_error(name=name, value=value,
                                                                    validation_outcome=validation_outcome,
                                                                    error_type=error_type, help_msg=help_msg,
                                                                    **kw_context_args)

        # remove all causes - this is a quick validator
        err.__cause__ = None

        # disable displaying the annoying prefix
        err.display_prefix_for_exc_outcomes = False
        return err

    def assert_valid(self,
                     name,             # type: str
                     value,            # type: Any
                     error_type=None,  # type: Type[ValidationError]
                     help_msg=None,    # type: str
                     **kw_context_args):
        raise NotImplementedError('This is a special validator object that is not able to perform validation')

    def is_valid(self,
                 value  # type: Any
                 ):
        raise NotImplementedError('This is a special validator object that is not able to perform validation')


# TODO same none_policy than the rest of valid8 ? Probably not, it would slightly decrease performance no?
def validate(name,                   # type: str
             value,                  # type: Any
             enforce_not_none=True,  # type: bool
             equals=None,            # type: Any
             instance_of=None,       # type: Union[Type, Tuple[Type]]
             subclass_of=None,       # type: Union[Type, Tuple[Type]]
             is_in=None,             # type: Container
             subset_of=None,         # type: Set
             contains = None,        # type: Union[Any, Iterable]
             superset_of=None,       # type: Set
             min_value=None,         # type: Any
             min_strict=False,       # type: bool
             max_value=None,         # type: Any
             max_strict=False,       # type: bool
             length=None,            # type: int
             min_len=None,           # type: int
             min_len_strict=False,   # type: bool
             max_len=None,           # type: int
             max_len_strict=False,   # type: bool
             custom=None,            # type: Callable[[Any], Any]
             error_type=None,        # type: Type[ValidationError]
             help_msg=None,          # type: str
             **kw_context_args):
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
    :param enforce_not_none: boolean, default True. Whether to enforce that `value` is not None.
    :param equals: an optional value to enforce.
    :param instance_of: optional type(s) to enforce. If a tuple of types is provided it is considered alternate types: one
        match is enough to succeed. If None, type will not be enforced
    :param subclass_of: optional type(s) to enforce. If a tuple of types is provided it is considered alternate types: one
        match is enough to succeed. If None, type will not be enforced
    :param is_in: an optional set of allowed values.
    :param subset_of: an optional superset for the variable
    :param contains: an optional value that the variable should contain (value in variable == True)
    :param superset_of: an optional subset for the variable
    :param min_value: an optional minimum value
    :param min_strict: if True, only values strictly greater than `min_value` will be accepted
    :param max_value: an optional maximum value
    :param max_strict: if True, only values strictly lesser than `max_value` will be accepted
    :param length: an optional strict length
    :param min_len: an optional minimum length
    :param min_len_strict: if True, only values with length strictly greater than `min_len` will be accepted
    :param max_len: an optional maximum length
    :param max_len_strict: if True, only values with length strictly lesser than `max_len` will be accepted
    :param custom: a custom base validation function or list of base validation functions to use. This is the same
        syntax than for valid8 decorators. A callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type),
        or a list of several such elements. Nested lists are supported and indicate an implicit `and_`. Tuples indicate
        an implicit `_failure_raiser`. [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be
        used instead of callables, they will be transformed to functions automatically.
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
        # - is_in/contains/subset_of/superset_of/has_length/minlen/maxlen/is_in in collections.py
        # - instance_of/subclass_of in types.py

        # try (https://github.com/orf/inliner) to perform the inlining below automatically without code duplication ?
        # > maybe not because quite dangerous (AST mod) and below we skip the "return True" everywhere for performance
        #
        # Another alternative: easy Cython compiling https://github.com/AlanCristhian/statically
        # > but this is not py2 compliant

        if value is None:
            # inlined version of _none_rejecter in base.py
            if enforce_not_none:
                raise ValueIsNone(wrong_value=value)
                # raise MissingMandatoryParameterException('Error, ' + name + '" is mandatory, it should be non-None')

            # else do nothing and return

        else:
            if equals is not None:
                if value != equals:
                    raise NotEqual(wrong_value=value, ref_value=equals)

            if instance_of is not None:
                assert_instance_of(value, instance_of)

            if subclass_of is not None:
                assert_subclass_of(value, subclass_of)

            if is_in is not None:
                # inlined version of is_in(allowed_values=allowed_values)(value) without 'return True'
                if value not in is_in:
                    raise NotInAllowedValues(wrong_value=value, allowed_values=is_in)

            if contains is not None:
                # inlined version of contains(ref_value=contains)(value) without 'return True'
                if contains not in value:
                    raise DoesNotContainValue(wrong_value=value, ref_value=contains)

            if subset_of is not None:
                # inlined version of is_subset(reference_set=subset_of)(value)
                missing = value - subset_of
                if len(missing) != 0:
                    raise NotSubset(wrong_value=value, reference_set=subset_of, unsupported=missing)

            if superset_of is not None:
                # inlined version of is_superset(reference_set=superset_of)(value)
                missing = superset_of - value
                if len(missing) != 0:
                    raise NotSuperset(wrong_value=value, reference_set=superset_of, missing=missing)

            if min_value is not None:
                # inlined version of gt(min_value=min_value, strict=min_strict)(value) without 'return True'
                if min_strict:
                    if not value > min_value:
                        raise TooSmall(wrong_value=value, min_value=min_value, strict=True)
                else:
                    if not value >= min_value:
                        raise TooSmall(wrong_value=value, min_value=min_value, strict=False)

            if max_value is not None:
                # inlined version of lt(max_value=max_value, strict=max_strict)(value) without 'return True'
                if max_strict:
                    if not value < max_value:
                        raise TooBig(wrong_value=value, max_value=max_value, strict=True)
                else:
                    if not value <= max_value:
                        raise TooBig(wrong_value=value, max_value=max_value, strict=False)

            if length is not None:
                # inlined version of has_length() without 'return True'
                if len(value) != length:
                    raise WrongLength(wrong_value=value, ref_length=length)

            if min_len is not None:
                # inlined version of minlen(min_length=min_len, strict=min_len_strict)(value) without 'return True'
                if min_len_strict:
                    if not len(value) > min_len:
                        raise TooShort(wrong_value=value, min_length=min_len, strict=True)
                else:
                    if not len(value) >= min_len:
                        raise TooShort(wrong_value=value, min_length=min_len, strict=False)

            if max_len is not None:
                # inlined version of maxlen(max_length=max_len, strict=max_len_strict)(value) without 'return True'
                if max_len_strict:
                    if not len(value) < max_len:
                        raise TooLong(wrong_value=value, max_length=max_len, strict=True)
                else:
                    if not len(value) <= max_len:
                        raise TooLong(wrong_value=value, max_length=max_len, strict=False)

    except Exception as e:
        err = _QUICK_VALIDATOR._create_validation_error(name, value, validation_outcome=e, error_type=error_type,
                                                        help_msg=help_msg, **kw_context_args)
        raise_(err)

    if custom is not None:
        # traditional custom validator
        assert_valid(name, value, custom, error_type=error_type, help_msg=help_msg, **kw_context_args)
    else:
        # basic (and not enough) check to verify that there was no typo leading an argument to be put in kw_context_args
        if error_type is None and help_msg is None and len(kw_context_args) > 0:
            raise ValueError("Keyword context arguments have been provided but help_msg and error_type are not: {}"
                             "".format(kw_context_args))


_QUICK_VALIDATOR = _QuickValidator()


class WrappingValidatorEye(object):
    """ Represents the object where users may put the validation outcome inside a validation context manager.
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


class _Dummy_Callable_(object):
    """ A dummy callable whose name can be configured """
    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        pass

    def __str__(self):
        return self.name


class validator(Validator):
    """
    A context manager to wrap validation tasks.
    Any exception caught within this context will be wrapped by a ValidationError and raised.

    ```python
    from valid8 import validation
    with validation('df', df, instance_of=pd.DataFrame):
        check_uniform_sampling(df)
    ```

    You can also use the returned object to store a boolean value indicating success or failure. In that case using the
    'validator' alias might be more readable. For example

    ```python
    from valid8 import validation
    with validator('surface', surf) as v:
        v.alid = surf > 0 and isfinite(surf)
    ```

    """
    def __init__(self,
                 name,              # type: str
                 value,             # type: Any
                 instance_of=None,  # type: Union[Type, Tuple[Type]]
                 subclass_of=None,  # type: Union[Type, Tuple[Type]]
                 error_type=None,   # type: Type[ValidationError]
                 help_msg=None,     # type: str
                 **kw_context_args):
        """
        Creates a context manager to wrap validation tasks. Any exception caught within this context will be wrapped
        by a ValidationError and raised.

        You can also use the returned object to store a boolean value indicating success or failure. For example

        ```python
        from valid8 import validation
        with validation('surface', surf) as v:
            v.alid = surf > 0 and isfinite(surf)
        ```

        :param name: the name of the variable being validated
        :param value: the value being validated
        :param instance_of: the type(s) to enforce. If a tuple of types is provided it is considered alternate types:
            one match is enough to succeed. If None, type will not be enforced
        :param subclass_of: the type(s) to enforce. If a tuple of types is provided it is considered alternate types: one
            match is enough to succeed. If None, type will not be enforced
        :param error_type: a subclass of `ValidationError` to raise in case of validation failure. By default a
            `ValidationError` will be raised with the provided `help_msg`
        :param help_msg: an optional help message to be used in the raised error in case of validation failure.
        :param kw_context_args: optional contextual information to store in the exception, and that may be also used
            to format the help message
        """
        # First perform the type check if needed
        if instance_of is not None:
            validate(name=name, value=value, instance_of=instance_of)

        if subclass_of is not None:
            assert_subclass_of(value, subclass_of)

        validation_function = _Dummy_Callable_('<wrap_valid_contents>')
        super(validator, self).__init__(validation_function, error_type=error_type, help_msg=help_msg,
                                         none_policy=NonePolicy.VALIDATE, **kw_context_args)
        self.name = name
        self.value = value
        self.eye = WrappingValidatorEye()

    def __enter__(self):
        # extract the source file and line number where the calling 'with validator()' line is
        # inspect.stack is extremely slow, the fastest is sys._getframe or inspect.currentframe().
        # See https://gist.github.com/JettJones/c236494013f22723c1822126df944b12
        # stack = traceback.extract_stack()
        # self.src_file_path = stack[-2][0]
        # self.src_file_line_nb = stack[-2][1]
        entry_frame = sys._getframe(1)
        self.entry_file_path = entry_frame.f_code.co_filename
        self.entry_line_nb = entry_frame.f_lineno

        # return the object to collect validation results
        return self.eye

    def __exit__(self, exc_type, exc_val, exc_tb):

        result = exc_val or self.eye.outcome

        if result is not None and result is not True:
            # *** We should raise a Validation Error ***

            # and where the exit happened
            # stack = traceback.extract_stack(limit=2)
            # exit_line_nb = stack[-2][1]
            exit_frame = sys._getframe(1)
            exit_file_path = exit_frame.f_code.co_filename
            exit_line_nb = exit_frame.f_lineno

            if exit_file_path != self.entry_file_path:
                warn('Error identifying the source file where validator/validation was used - no string '
                     'representation will be available')
            else:
                # read the lines in the source corresponding to the contents
                try:
                    if self.entry_file_path.startswith('<'):
                        # interactive interpreter...

                        # `inspect` does not work yet for interactive interpreters see https://bugs.python.org/issue12920
                        # from inspect import getsourcelines
                        # lines = getsourcelines(exit_frame.f_code)[0]
                        # wrapped_block_lines = [l.strip() for l in
                        #                        lines[(self.entry_line_nb - exit_frame.f_code.co_firstlineno):
                        #                              (exit_frame.f_lineno - exit_frame.f_code.co_firstlineno + 1)]]

                        # In PyCharm it seems to be a specific console, no idea on how to get it
                        # from code import InteractiveConsole

                        # On iPython/jupyter there is something...
                        # try:
                        #     from IPython.core.history import HistoryAccessor
                        #     h = HistoryAccessor(profile='default')
                        #     # lines = h.get_range_by_str("%s-%s" % )
                        #     print("TO DO %s" % h.get_range_by_str(""))
                        # except ImportError:
                        #     pass
                        # this is supposed to work too on iPython
                        # code inspired from 'findsource' function in
                        #    https://github.com/uqfoundation/dill/blob/master/dill/source.py
                        try:
                            import readline
                        except ImportError:
                            err = sys.exc_info()[1].args[0]
                            if sys.platform[:3] == 'win':
                                err += ", please install 'pyreadline'"
                            raise IOError(err)
                        lbuf = readline.get_current_history_length()
                        lines = [readline.get_history_item(i) + '\n' for i in range(1, lbuf)]
                        # print('history! yes {} {}'.format(self.entry_line_nb, lbuf))
                        # for line in lines:
                        #     print(line)
                        exit_line_nb = len(lines)

                        # retrieve the lines wrapped by the context manager, until the line that raises the exception.
                        # note: it might not be the last line in the block of code wrapped by the context manager
                        wrapped_block_lines = [line.strip()
                                               for line in lines[self.entry_line_nb:exit_line_nb]]
                    else:
                        # -- that's a normal code file
                        # with open(self.entry_file_path) as src:
                        #     lines = list(src)

                        # faster: use linecache https://docs.python.org/3/library/linecache.html
                        wrapped_block_lines = [getline(self.entry_file_path, i + 1).strip()
                                               for i in range(self.entry_line_nb, exit_line_nb)]

                    if exc_val is not None:
                        # -- There was an exception, we dont know where: output the full code in self.main_function.name
                        self.main_function.name = ' ; '.join(wrapped_block_lines)

                    else:
                        # We can put this back ONLY if we find a way to also work properly when the line is a multiline
                        # Otherwise it is better not to try to be too smart here
                        #
                        # -- There was no exception so we just output the line where self.eye.outcome is computed
                        # found = None
                        # for idx, line in enumerate(wrapped_block_lines[::-1]):
                        #     if ('.' + self.eye.last_field_name_used) in line:
                        #         found = line
                        #         break
                        # if found is not None:
                        #     self.main_function.name = found
                        # else:
                        #     # not able to identify... dump the whole block
                        self.main_function.name = ' ; '.join(wrapped_block_lines)

                except Exception as e:
                    warn('Error while inspecting source code at {}. No details will be added to the resulting '
                         'exception. Caught {}'.format(self.entry_file_path, e))

            raise_(self._create_validation_error(self.name, self.value, validation_outcome=result))


validation = validator
""" Alias for validation, more readable when using the returned object to store boolean results """
