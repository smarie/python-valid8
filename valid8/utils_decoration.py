import sys
from collections import OrderedDict

try:  # python 3.5+
    from typing import Callable
except ImportError:
    pass

try:
    from inspect import Signature
except ImportError:
    from funcsigs import Signature


def apply_on_each_func_args_sig(func,
                                cur_args,
                                cur_kwargs,
                                sig,  # type: Signature
                                func_to_apply,
                                func_to_apply_params_dict):
    """
    Applies func_to_apply on each argument of func according to what's received in current call (cur_args, cur_kwargs).
    For each argument of func named 'att' in its signature, the following method is called:

    `func_to_apply(cur_att_value, func_to_apply_paramers_dict[att], func, att_name)`

    :param func:
    :param cur_args:
    :param cur_kwargs:
    :param sig:
    :param func_to_apply:
    :param func_to_apply_params_dict:
    :return:
    """

    # match the received arguments with the signature to know who is who
    bound_values = sig.bind(*cur_args, **cur_kwargs)

    # add the default values in here to get a full list
    apply_defaults(bound_values)

    for att_name, att_value in bound_values.arguments.items():
        if att_name in func_to_apply_params_dict.keys():
            # value = a normal value, or cur_kwargs as a whole
            func_to_apply(att_value, func_to_apply_params_dict[att_name], func, att_name)

        # The behaviour below is removed as it is too complex to explain
        # else:
        #     if sig.parameters[att_name].kind == Parameter.VAR_KEYWORD:
        #         # if the attribute is variable-length keyword argument we can try to find a matching key inside it
        #         # each item is handled independently (if func signature contains the kw args names such as a, b)
        #         for name, value in att_value.items():
        #             if name in func_to_apply_params_dict.keys():
        #                 func_to_apply(value, func_to_apply_params_dict[name], func, name)


if sys.version_info >= (3, 0):
    def apply_defaults(bound_values):
        bound_values.apply_defaults()
else:
    # TODO when funcsigs implements PR https://github.com/aliles/funcsigs/pull/30 remove this
    def apply_defaults(bound_values):
        arguments = bound_values.arguments

        # Creating a new one and not modifying in-place for thread safety.
        new_arguments = []

        for name, param in bound_values._signature.parameters.items():
            try:
                new_arguments.append((name, arguments[name]))
            except KeyError:
                if param.default is not param._empty:
                    val = param.default
                elif param.kind is param._VAR_POSITIONAL:
                    val = ()
                elif param.kind is param._VAR_KEYWORD:
                    val = {}
                else:
                    # BoundArguments was likely created by bind_partial
                    continue
                new_arguments.append((name, val))

        bound_values.arguments = OrderedDict(new_arguments)
