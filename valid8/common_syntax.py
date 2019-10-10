from itertools import chain
from sys import version_info

from makefun import with_signature

from valid8.base import failure_raiser, ValidationFailure, is_mini_lambda, pop_kwargs

try:  # python 3.5+
    # noinspection PyUnresolvedReferences
    from typing import Callable, Union, List, Tuple, Iterable, Mapping, Any
    try:  # python 3.5.3-
        # noinspection PyUnresolvedReferences
        from typing import Type
    except ImportError:
        use_typing = False
    else:
        # noinspection PyUnresolvedReferences
        from valid8.base import ValidationCallable, ValidationCallableOrLambda

        # 2. the syntax to optionally transform them into failure raisers by providing a tuple
        ValidationFuncDefinition = Union[ValidationCallableOrLambda,
                                         Tuple[ValidationCallableOrLambda, str],
                                         Tuple[ValidationCallableOrLambda, Type[ValidationFailure]],
                                         Tuple[ValidationCallableOrLambda, str, Type[ValidationFailure]]
                                         ]
        """Defines a checker from a base checker function together with optional error message and failure type 
        (in which case a failure raiser is created to wrap that function)"""

        # 3. the syntax to describe several validation functions at once
        VFDefinitionElement = Union[str, Type[ValidationFailure], ValidationCallableOrLambda]
        """This type represents one of the elements that can define a checker: help msg, failure type, callable"""

        OneOrSeveralVFDefinitions = Union[ValidationFuncDefinition,
                                          Iterable[ValidationFuncDefinition],
                                          Mapping[VFDefinitionElement, Union[VFDefinitionElement,
                                                                             Tuple[VFDefinitionElement, ...]]]]
        """Several validators can be provided as a singleton, iterable, or dict-like. In that case the value can be a 
        single variable or a tuple, and it will be combined with the key to form the validator. So you can use any of 
        the elements defining a validators as the key."""

        # shortcut name used everywhere. Less explicit
        ValidationFuncs = OneOrSeveralVFDefinitions

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
                   'several such elements. Dicts are supported too. Tuples indicate an implicit `failure_raiser`. ' \
                   '[mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead of ' \
                   'callables, they will be transformed to functions automatically.'


def make_validation_func_callable(vf_definition,                   # type: ValidationFuncDefinition
                                  callable_creator=failure_raiser  # type: Callable
                                  ):
    # type: (...) -> ValidationCallable
    """
    Creates a validation callable for usage in valid8, from a "validation function" callable optionally completed with
    an associated error message and failure type to be used in case validation fails.

    If `vf_definition` is a single <validation_func> callable, a failure raiser is created around it

    >>> import sys, pytest
    >>> if sys.version_info < (3, 0):
    ...     pytest.skip('doctest skipped in python 2 because exception namespace is different but details matter')

    >>> def vf(x): return x + 1 == 0
    >>> assert make_validation_func_callable(vf) is not vf  # TODO better assert here ?

    If `vf_definition` is a tuple such as (<validation_func>, <err_msg>), (<validation_func>, <failure_type>),
    or (<validation_func>, <err_msg>, <failure_type>), a `failure_raiser` is created.

    >>> class MyFailure(ValidationFailure):
    ...     pass
    >>> vf_with_details = make_validation_func_callable((vf, 'blah', MyFailure))
    >>> vf_with_details('hello')
    Traceback (most recent call last):
    ...
    valid8.common_syntax.MyFailure: blah. Function [vf] raised TypeError: ...

    Notes:

     - `<validation_func>` should be a `callable` with one argument: `f(val)`. It should return `True` or `None`
       in case of success. If it is a mini-lambda expression it will automatically be transformed into a function using
       `mini_lambda.as_function`. See `ValidationCallable` type hint.
     - `<err_msg>` should be a string
     - `<failure_type>` should be a subclass of `ValidationFailure`

    :param vf_definition: the definition for a validation function. One of <validation_func>,
        (<validation_func>, <err_msg>), (<validation_func>, <err_type>), or (<validation_func>, <err_msg>, <err_type>)
        where <validation_func> is a callable taking a single input and returning `True` or `None` in case of success.
        mini-lambda expressions are supported too and automatically converted into callables.
    :param callable_creator: method to be called to finally create the callable. Can be used by extensions to specify
        a custom way to create callables. Default is `failure_raiser`.
    :return: a validation callable that is either directly the provided callable, or a `failure_raiser` wrapping this
        callable using the additional details (err_msg, failure_type) provided.
    """
    try:
        nb_elts = len(vf_definition)
    except (TypeError, FunctionDefinitionError):
        # -- single element
        # handle the special case of a LambdaExpression: automatically convert to a function
        if not is_mini_lambda(vf_definition) and not callable(vf_definition):
            raise ValueError('base validation function(s) not compliant with the allowed syntax. Base validation'
                             ' function(s) can be %s Found %s.' % (supported_syntax, vf_definition))
        else:
            # single element.
            return callable_creator(vf_definition)
    else:
        # -- a tuple
        if nb_elts == 1:
            validation_func, help_msg, failure_type = vf_definition[0], None, None
        elif nb_elts == 2:
            if isinstance(vf_definition[1], str):
                validation_func, help_msg, failure_type = vf_definition[0], vf_definition[1], None
            else:
                validation_func, help_msg, failure_type = vf_definition[0], None, vf_definition[1]
        elif nb_elts == 3:
            validation_func, help_msg, failure_type = vf_definition[:]
        else:
            raise ValueError('tuple in validator definition should have length 1, 2, or 3. Found: %s' % (vf_definition,))

        # check help msg and failure type
        if failure_type is not None:
            failure_type_ok = False
            # noinspection PyBroadException
            try:
                # noinspection PyTypeChecker
                if issubclass(failure_type, ValidationFailure):
                    failure_type_ok = True
            except:  # noqa: E722
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

        # check that the definition is valid
        if (not failure_type_ok) or (not help_msg_ok) or (not is_mini_lambda(validation_func)
                                                          and not callable(validation_func)):
            raise ValueError('base validation function(s) not compliant with the allowed syntax. Base validation'
                             ' function(s) can be %s Found %s.' % (supported_syntax, vf_definition))

        # finally create the failure raising callable
        return callable_creator(validation_func, help_msg=help_msg, failure_type=failure_type)


# Python 3+: load the 'more explicit api'
if use_typing:
    new_sig = """(*vf_definition: OneOrSeveralVFDefinitions,
                  callable_creator: Callable = failure_raiser
                  )"""
else:
    new_sig = None


@with_signature(new_sig)
def make_validation_func_callables(*vf_definition,                  # type: OneOrSeveralVFDefinitions
                                   **kwargs
                                   ):
    # type: (...) -> Tuple[ValidationCallable, ...]
    """
    Creates one or several validation callables for usage in valid8, from one or several "validation function"
    callables, optionally completed with associated error messages and failure types to be used in case validation
    fails.

    If several `vf_definition` are provided, `make_validation_func_callable` will be called for each `vf_definition`,
    and a tuple containing the results will be returned. See `make_validation_func_callable` for details on the
    supported tuples to use.

    >>> import sys, pytest
    >>> if sys.version_info < (3, 6):
    ...     pytest.skip('doctest skipped for old python versions')

    >>> # two dummy validation callables
    >>> def is_big(x): return x > 10
    >>> def is_minus_1(x, **ctx): return x + 1 == 0

    >>> # a custom failure we would like to be raised
    >>> class MyFailure(ValidationFailure):
    ...     pass

    >>> # process both vf1 and v2, reusing vf1 'as is' and enriching vf2 with a custom failure type and error message
    >>> several_vfs = make_validation_func_callables([is_big, (is_minus_1, 'not minus 1!', MyFailure)])
    >>> assert len(several_vfs) == 2
    >>> assert several_vfs[0] is not is_big  # TODO better assert here ?
    >>> several_vfs[1]('hello')
    Traceback (most recent call last):
    ...
    valid8.common_syntax.MyFailure: not minus 1!. Function [is_minus_1] raised TypeError: ...

    If a single `vf_definition` is provided AND it is a non-tuple iterable (typically a list),
    `make_validation_func_callables(vf_definition)` is equivalent to `make_validation_func_callables(*vf_definition)`

    # >>> assert make_validation_func_callables([is_big]) == make_validation_func_callables(is_big) TODO re-enable when equality operator works

    Finally, if a single `vf_definition` is provided AND it is a dict-like mapping, a special syntax is enabled where
    you can put *any* part of the definition in the key and in the value. `make_validation_func_callable` will still
    then be called for each item in the dictionary, and a tuple with the results will be returned.

    Examples:

    >>> vfs = make_validation_func_callables({'x should be big': is_big,
    ...                                        'x should be minus 1': (is_minus_1, MyFailure)})
    >>> vfs[0](2)
    Traceback (most recent call last):
    ...
    valid8.base.InvalidValue: x should be big. Function [is_big] returned [False] for value 2.

    :param vf_definition: the base validation function or list of base validation functions to use. A callable, a
        tuple(callable, help_msg_str), a tuple(callable, failure_type), tuple(callable, help_msg_str, failure_type)
        or a list of several such elements. A dict can also be used (see doc).
        Tuples indicate an implicit `failure_raiser`.
        [mini_lambda](https://smarie.github.io/python-mini-lambda/) expressions can be used instead
        of callables, they will be transformed to functions automatically.
    :param callable_creator: method to be called to finally create the callable. Can be used by extensions to specify
        a custom way to create callables. Default is `failure_raiser`.
    :return: a tuple of callables
    """
    # python <3.5 compliance: pop the kwargs following the varargs
    callable_creator = pop_kwargs(kwargs, [('callable_creator', failure_raiser)], allow_others=False)

    # handle the case where vf_definition is not yet a list or is empty or none
    if len(vf_definition) == 0:
        raise ValueError('No validation function definition was provided')
    elif len(vf_definition) == 1:
        # a single item has been received. If it is not a tuple, use it: it might be a list or dict
        single_entry = vf_definition[0]
        if not isinstance(single_entry, tuple):
            vf_definition = single_entry

    try:
        # mapping ?
        v_items = iter(vf_definition.items())
    except (AttributeError, FunctionDefinitionError):
        try:
            # iterable ?
            v_iter = iter(vf_definition)
        except (TypeError, FunctionDefinitionError):
            # single validator: create a tuple manually
            all_validators = (make_validation_func_callable(vf_definition, callable_creator=callable_creator),)
        else:
            # iterable
            all_validators = tuple(make_validation_func_callable(v, callable_creator=callable_creator) for v in v_iter)
    else:
        # mapping: be 'smart'
        def _mapping_entry_to_vf(k, v):
            # type: (...) -> ValidationCallable
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
                        if issubclass(_elt, Exception):  # broad: Exception, check for ValidationFailure subclass is made below
                            err_type = _elt
                        else:
                            callabl = _elt
                    except TypeError:
                        callabl = _elt

            return make_validation_func_callable((callabl, err_msg, err_type), callable_creator=callable_creator)

        all_validators = tuple(_mapping_entry_to_vf(k, v) for k, v in v_items)

    if len(all_validators) == 0:
        raise ValueError("No validators provided")
    else:
        return all_validators
