from itertools import chain
from sys import version_info

from valid8.base import _failure_raiser, WrappingFailure, as_function

try:  # python 3.5+
    from typing import Callable, Union, List, Tuple, Iterable, Mapping, Any
    try:  # python 3.5.3-
        from typing import Type
    except ImportError:
        use_typing = False
    else:
        # 1. the lowest-level user or 3d party-provided validation functions
        CheckerCallable = Callable[[Any], Any]
        try:
            from mini_lambda import x
            CheckerCallableOrLambda = Union[CheckerCallable, type(x)]
            """A base checker function is a callable with signature (val), returning `True` or `None` in case of 
            success. Mini-lambda expressions are supported too."""
        except ImportError:
            CheckerCallableOrLambda = CheckerCallable
            """A base checker function is a callable with signature (val), returning `True` or `None` in case of 
            success"""

        # 2. the syntax to optionally transform them into failure raisers by providing a tuple
        CheckerDefinition = Union[CheckerCallableOrLambda,
                                  Tuple[CheckerCallableOrLambda, str],
                                  Tuple[CheckerCallableOrLambda, Type[WrappingFailure]],
                                  Tuple[CheckerCallableOrLambda, str, Type[WrappingFailure]]
        ]
        """Defines a checker from a base checker function together with optional error message and failure type 
        (in which case a failure raiser is created to wrap that function)"""

        # 3. the syntax to describe several validation functions at once
        CheckerDefinitionElement = Union[str, Type[WrappingFailure], CheckerCallableOrLambda]
        """This type represents one of the elements that can define a checker"""

        OneOrSeveralCheckerDefinitions = Union[CheckerDefinition,
                                               Iterable[CheckerDefinition],
                                               Mapping[CheckerDefinitionElement, Union[CheckerDefinitionElement,
                                                                                Tuple[CheckerDefinitionElement, ...]]]]
        """Several validators can be provided as a singleton, iterable, or dict-like. In that case the value can be a 
        single variable or a tuple, and it will be combined with the key to form the validator. So you can use any of the 
        elements defining a validators as the key."""

        # shortcut name used everywhere. Less explicit
        ValidationFuncs = OneOrSeveralCheckerDefinitions

        use_typing = version_info > (3, 0)

except TypeError:
    # this happens with python 3.5.2: typing has an issue.
    use_typing = False

except ImportError:
    use_typing = False


try:
    from mini_lambda import FunctionDefinitionError
except ImportError:
    # create a dummy one
    class FunctionDefinitionError(Exception):
        pass


supported_syntax = 'a callable, a tuple(callable, help_msg_str), a tuple(callable, failure_type), ' \
                   'tuple(callable, help_msg_str, failure_type), or a list of ' \
                   'several such elements. Tuples indicate an implicit `_failure_raiser`. ' \
                   '[mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of ' \
                   'callables, they will be transformed to functions automatically.'


def _make_checker_callable(checker_def  # type: CheckerDefinition
                           ):
    # type: (...) -> CheckerCallable
    """
    Creates a callable for usage in valid8, from a "validation function" or m together with optional error message
    and failure type.

     - if `checker_def` is a <validation_func> callable it is used directly (no wrapping)
     - if `checker_def` is a tuple such as (<validation_func>, <err_msg>), (<validation_func>, <err_type>),
     or (<validation_func>, <err_msg>, <err_type>), a `failure_raiser` is created.

    Note: `<validation_func>` should be a `callable` with one argument: `f(val)`. It should  return `True` or `None`
    in case of success. If it is a mini-lambda expression it will automatically be transformed into a function using
    `mini_lambda.as_function`. See `ValidationCallable` type hint.

    :param checker_def: the definition for a checker. One of <validation_func>, (<validation_func>, <err_msg>),
        (<validation_func>, <err_type>), or (<validation_func>, <err_msg>, <err_type>) where <validation_func> is a
        callable taking a single input and returning `True` or `None` in case of success. mini-lambda expressions are
        supported too and automatically converted into callables.
    :return: a checker callable that is either directly the provided callable, or a `failure_raiser` wrapping this
        callable using the additional details provided.
    """
    try:
        nb_elts = len(checker_def)
    except (TypeError, FunctionDefinitionError):
        # -- single element
        # handle the special case of a LambdaExpression: automatically convert to a function
        return as_function(checker_def)
    else:
        # -- a tuple
        if nb_elts == 1:
            validation_func, help_msg, failure_type = checker_def[0], None, None
        elif nb_elts == 2:
            if isinstance(checker_def[1], str):
                validation_func, help_msg, failure_type = checker_def[0], checker_def[1], None
            else:
                validation_func, help_msg, failure_type = checker_def[0], None, checker_def[1]
        elif nb_elts == 3:
            validation_func, help_msg, failure_type = checker_def[:]
        else:
            raise ValueError('tuple in validator definition should have length 1, 2, or 3. Found: %s' % (checker_def,))

        # check help msg and failure type
        if failure_type is not None:
            failure_type_ok = False
            try:
                if issubclass(failure_type, WrappingFailure):
                    failure_type_ok = True
            except:
                pass
        else:
            failure_type_ok = True

        if help_msg is not None:
            help_msg_ok = False
            try:
                if isinstance(help_msg, str):
                    help_msg_ok = True
            except:
                pass
        else:
            help_msg_ok = True

        if (not failure_type_ok) or (not help_msg_ok):
            raise ValueError('base validation function(s) not compliant with the allowed syntax. Base validation'
                             ' function(s) can be %s. Found %s.' % (supported_syntax, checker_def))

        # handle the special case of a LambdaExpression: automatically convert to a function
        validation_func = as_function(validation_func)

        # finally create the failure raising callable
        return _failure_raiser(validation_func, help_msg=help_msg, failure_type=failure_type)


def _make_checker_callables(*validation_func  # type: OneOrSeveralCheckerDefinitions
                            ):
    # type: (...) -> Tuple[CheckerCallable]
    """
    Converts the provided checker definitions into checkers.

     - `validation_func` a single `Validator`, an iterable of `Validator`s, or a dictionary of
       validators (in which case many syntaxes are allowed, see below). See `Validators` type hint.

     - A `Validator` is a validation function together with optional error messages and optional error types. See
       `make_validator(validator)` for details.

    TODO Dict syntax

    This function handles the various ways that users may enter 'validation functions'.

    valid8 supports the following expressions for 'validation functions'
     * <ValidationFunc>
     * List[<ValidationFunc>(s)]. The list must not be empty.

    <ValidationFunc> may either be
     * a callable or a mini-lambda expression (instance of LambdaExpression - in which case it is automatically
     'closed').
     * a Tuple[callable or mini-lambda expression ; failure_type]. Where failure type should be a subclass of
     valid8.Failure. In which case the tuple will be replaced with a _failure_raiser(callable, failure_type)

    When the contents provided does not match the above, this function raises a ValueError. Otherwise it produces a
    list of callables, that will typically be turned into a `and_` in the nominal case except if this is called inside
    `or_` or `xor_`.

    :param validation_funcs: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements.
        Tuples indicate an implicit `_failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :return:
    """
    # handle the case where validation_func is not yet a list or is empty or none
    if len(validation_func) == 0:
        raise ValueError('mandatory validation_func is None')
    elif len(validation_func) == 1:
        # a single item has been received. If it is not a tuple, unpack it
        single_entry = validation_func[0]
        if not isinstance(single_entry, tuple):
            validation_func = single_entry

    try:
        # mapping ?
        v_items = iter(validation_func.items())
    except (AttributeError, FunctionDefinitionError):
        try:
            # iterable ?
            v_iter = iter(validation_func)
        except (TypeError, FunctionDefinitionError):
            # single validator: create a tuple manually
            all_validators = (_make_checker_callable(validation_func),)
        else:
            # iterable
            all_validators = tuple(_make_checker_callable(v) for v in v_iter)
    else:
        # mapping: be 'smart'
        def _mapping_entry_to_checker(k, v):
            # type: (...) -> CheckerCallable
            try:
                # tuple?
                iter(v)
            except (TypeError, FunctionDefinitionError):
                # single value: make a tuple with the key
                vals = (k, v)
            else:
                # tuple: chain with key
                vals = chain((k, ), v)

            # find the various elements from the key and value
            callabl, err_msg, err_type = None, None, None
            for _elt in vals:
                if isinstance(_elt, str):
                    err_msg = _elt
                else:
                    try:
                        if issubclass(_elt, Exception):
                            err_type = _elt
                        else:
                            callabl = _elt
                    except TypeError:
                        callabl = _elt

            return _make_checker_callable((callabl, err_msg, err_type))

        all_validators = tuple(_mapping_entry_to_checker(k, v) for k, v in v_items)

    if len(all_validators) == 0:
        raise ValueError("No validators provided")
    else:
        return all_validators
