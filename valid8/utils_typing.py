from abc import abstractmethod, ABCMeta

from typing import Tuple, Any

# for compliance with older versions we cant rely on typing_inspect
from valid8._typing_inspect import is_typevar, is_union_type, get_args


class Boolean(metaclass=ABCMeta):
    """
    An abstract base class for booleans, similar to what is available in numbers
    see https://docs.python.org/3.5/library/numbers.html
    """
    __slots__ = ()

    @abstractmethod
    def __bool__(self):
        """Return a builtin bool instance. Called for bool(self)."""

    @abstractmethod
    def __and__(self, other):
        """self & other"""

    @abstractmethod
    def __rand__(self, other):
        """other & self"""

    @abstractmethod
    def __xor__(self, other):
        """self ^ other"""

    @abstractmethod
    def __rxor__(self, other):
        """other ^ self"""

    @abstractmethod
    def __or__(self, other):
        """self | other"""

    @abstractmethod
    def __ror__(self, other):
        """other | self"""

    @abstractmethod
    def __invert__(self):
        """~self"""


# register bool and numpy bool_ as virtual subclasses
# so that issubclass(bool, Boolean) = issubclass(np.bool_, Boolean) = True
Boolean.register(bool)

try:
    import numpy as np
    Boolean.register(np.bool_)
except ImportError:
    # silently escape
    pass


# def is_pep484_none_type(type_hint):
#     """ Returns True if the provided PEP484 type hint is the None type """
#     return (type_hint is type(None)) or (str(type_hint) == type(None).__name__)


# def is_pep484_union_type(type_hint):
#     """ Returns True if the provided PEP484 type hint is the Union type """
#     return str(type_hint).startswith('typing.Union')


def resolve_union_and_typevar(typ) -> Tuple[Any, ...]:
    """
    If typ is a TypeVar,
     * if the typevar is bound, return resolve_union_and_typevar(bound)
     * if the typevar has constraints, return a tuple containing all the types listed in the constraints (with
     appropriate recursive call to resolve_union_and_typevar for each of them)
     * otherwise return (object, )

    If typ is a Union, return a tuple containing all the types listed in the union (with
     appropriate recursive call to resolve_union_and_typevar for each of them)

    Otherwise return (typ, )

    :param typ:
    :return:
    """
    if is_typevar(typ):
        if hasattr(typ, '__bound__') and typ.__bound__ is not None:
            return resolve_union_and_typevar(typ.__bound__)
        elif hasattr(typ, '__constraints__') and typ.__constraints__ is not None:
            return tuple(typpp for c in typ.__constraints__ for typpp in resolve_union_and_typevar(c))
        else:
            return object,
    elif is_union_type(typ):
        # do not use typ.__args__, it may be wrong
        # the solution below works even in typevar+config cases such as u = Union[T, str][Optional[int]]
        return get_args(typ, evaluate=True)
    else:
        return typ,


def is_pep484_nonable(typ):
    """
    Checks if a given type is nonable, meaning that it explicitly or implicitly declares a Union with NoneType.
    Nested TypeVars and Unions are supported.

    :param typ:
    :return:
    """
    # TODO rely on typing_inspect if there is an answer to https://github.com/ilevkivskyi/typing_inspect/issues/14
    if typ is type(None):
        return True
    elif is_typevar(typ) or is_union_type(typ):
        return any(is_pep484_nonable(tt) for tt in resolve_union_and_typevar(typ))
    else:
        return False
