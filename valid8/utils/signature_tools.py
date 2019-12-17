#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2019. All right reserved.
from functools import partial
from types import BuiltinFunctionType

# needed below. from inspect and funcsigs
_WrapperDescriptor = type(type.__call__)
_MethodWrapper = type(all.__call__)


class IsBuiltInError(TypeError):
    """note "built-in" means "C built-in"""
    pass


try:
    from inspect import signature, FullArgSpec

    try:
        from inspect import _signature_is_builtin
    except ImportError:
        from inspect import isbuiltin, ismethoddescriptor

        # from inspect
        _ClassMethodWrapper = type(int.__dict__['from_bytes'])
        _NonUserDefinedCallables = (_WrapperDescriptor,
                                    _MethodWrapper,
                                    _ClassMethodWrapper,
                                    BuiltinFunctionType)

        def _signature_is_builtin(obj):
            """ From inspect"""
            return (isbuiltin(obj) or
                    ismethoddescriptor(obj) or
                    isinstance(obj, _NonUserDefinedCallables) or
                    # Can't test 'isinstance(type)' here, as it would
                    # also be True for regular python classes
                    obj in (type, object))

    def _is_builtin_value_error(e):
        try:
            return (e.__class__ is ValueError) and ('builtin' in e.args[0])
        except:
            return False

    def getfullargspec(f, skip_bound_arg=False, follow_wrapped=True):
        """
        This method adds `skip_bound_arg` argument to `getfullargspec` so that it is capable of skipping the 'self'
        parameter of bound methods, like `signature` does.

        This is the version for python 3. It is mostly the same code than in `inspect.getfullargspec`, except that
         - `skip_bound_arg` is not forced to `False`
         - Errors are improved if possible: if the function is a built-in the error raised is an explicit
           `IsBuiltInError`.

        :param f:
        :param skip_bound_arg:
        :param follow_wrapped:
        :return:
        """
        if skip_bound_arg:
            try:
                sig = signature(f, follow_wrapped=follow_wrapped)
            except ValueError as e:
                if _signature_is_builtin(f):
                    raise IsBuiltInError(f)
                elif isinstance(f, partial) and _signature_is_builtin(f.func):
                    raise IsBuiltInError(f)
                elif _is_builtin_value_error(e):
                    raise IsBuiltInError(f)
                else:
                    raise

            args = []
            varargs = None
            varkw = None
            kwonlyargs = []
            annotations = {}
            defaults = ()
            kwdefaults = {}

            if sig.return_annotation is not sig.empty:
                annotations['return'] = sig.return_annotation

            for p in sig.parameters.values():
                kind = p.kind
                name = p.name

                if kind is p.POSITIONAL_ONLY:
                    args.append(name)
                elif kind is p.POSITIONAL_OR_KEYWORD:
                    args.append(name)
                    if p.default is not p.empty:
                        defaults += (p.default,)
                elif kind is p.VAR_POSITIONAL:
                    varargs = name
                elif kind is p.KEYWORD_ONLY:
                    kwonlyargs.append(name)
                    if p.default is not p.empty:
                        kwdefaults[name] = p.default
                elif kind is p.VAR_KEYWORD:
                    varkw = name

                if p.annotation is not p.empty:
                    annotations[name] = p.annotation

            if not kwdefaults:
                # compatibility with 'func.__kwdefaults__'
                kwdefaults = None

            if not defaults:
                # compatibility with 'func.__defaults__'
                defaults = None

            return FullArgSpec(args, varargs, varkw, defaults,
                               kwonlyargs, kwdefaults, annotations)

        else:
            # use getfullargspec
            raise NotImplementedError()

except ImportError:
    # python 2
    from inspect import getargspec
    from funcsigs import signature

    from collections import namedtuple
    FullArgSpec = namedtuple('FullArgSpec',
                             'args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations')

    # from https://github.com/aliles/funcsigs/blob/master/funcsigs/__init__.py#L85
    _NonUserDefinedCallables = (_WrapperDescriptor,
                                _MethodWrapper,
                                BuiltinFunctionType)

    def getfullargspec(f, skip_bound_arg=False, follow_wrapped=True):
        """
        This method adds `skip_bound_arg` argument to `getfullargspec` so that it is capable of skipping the 'self'
        parameter of bound methods, like `signature` does.

        This version is for python 2. It is based on `getargspec`.

        It is also enhanced to support `partial` objects because before Python 3.4, getargspec() did't work for
        functools.partial, so it needs to be handled separately.

        Finally when some signatures cant be found, if the function is a built-in the error raised is an explicit
        `IsBuiltInError`.

        :param f:
        :param skip_bound_arg:
        :param follow_wrapped:
        :return:
        """
        if follow_wrapped:
            try:
                # Was this function wrapped by a decorator?
                wrapped = f.__wrapped__
            except AttributeError:
                pass
            else:
                return getfullargspec(wrapped, skip_bound_arg=skip_bound_arg, follow_wrapped=follow_wrapped)

        try:
            if isinstance(f, partial):
                # (1) partial
                # from https://github.com/dsacre/pyliblo/commit/e897f9987dc97fc678d61ac0e16fe79c6a7dffc0#diff-2be46de1531c648b0e936ccfa59f1692R262
                # before Python 3.4, getargspec() did't work for functools.partial, so it needs to be handled separately
                p = f
                f = f.func
                args, varpos, varkw, defaults = getargspec(f)
                nb_args_before = len(args)
                nb_pos_removed = len(p.args)
                args = args[nb_pos_removed:]
                if defaults is None:
                    if p.keywords is not None and len(p.keywords) > 0:
                        nb_args_after = nb_args_before - nb_pos_removed
                        args = list(args)
                        end = nb_args_after
                        i = 0
                        while i < end:
                            if args[i] in p.keywords:
                                del args[i]
                                end -= 1
                            else:
                                i += 1
                else:
                    nb_without_default_before = nb_args_before - len(defaults)
                    _diff = nb_pos_removed - nb_without_default_before
                    nb_pos_defaults_removed = max(0, _diff)
                    defaults = defaults[nb_pos_defaults_removed:]
                    if p.keywords is not None and len(p.keywords) > 0:
                        nb_args_after = nb_args_before - nb_pos_removed
                        nb_without_defaults_after = max(0, -_diff)
                        args = list(args)
                        defaults = list(defaults)
                        end = nb_args_after
                        i = 0
                        while i < end:
                            if args[i] in p.keywords:
                                del args[i]
                                del defaults[i - nb_without_defaults_after]
                                end -= 1
                            else:
                                i += 1

                return FullArgSpec(args, varpos, varkw, defaults, None, None, None)

            else:
                # (2) nominal case
                args, varpos, varkw, defaults = getargspec(f)
                try:
                    # if bound instance or class method
                    if skip_bound_arg and f.__self__ is not None:
                        args = args[1:]
                except AttributeError:
                    pass
                return FullArgSpec(args, varpos, varkw, defaults, None, None, None)

        except TypeError as e:
            # built-ins...
            if isinstance(f, _NonUserDefinedCallables):
                # see https://docs.python.org/2/library/types.html#types.BuiltinFunctionType
                # note "built-in" means "C built-in"
                raise IsBuiltInError(f)
            else:
                # try:
                #     declaring_class = f.__objclass__
                #     # this does not make us make any progress... skip
                # except AttributeError:
                if e.args[0].endswith("> is not a Python function"):
                    raise IsBuiltInError(f)
                else:
                    raise ValueError("unknown case")
