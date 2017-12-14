from abc import abstractmethod, ABCMeta


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


def is_pep484_none_type(type_hint):
    """ Returns True if the provided PEP484 type hint is the None type """
    return (type_hint is type(None)) or (str(type_hint) == type(None).__name__)


def is_pep484_union_type(type_hint):
    """ Returns True if the provided PEP484 type hint is the Union type """
    return str(type_hint).startswith('typing.Union')


def is_pep484_nonable(type_hint):
    """
    Returns True if the provided PEP484 type hint is Nonable, meaning that it is either the None type or a union
    containing the none type (recursive).

    The idea here is not to rely on a full pep484 type validation library but to do the minimum checks for Nonable
    indeed we do not want to add a dependency, and we cannot do try/except to find which validation library is
    available, that would lead to inconsistent behaviour according to targets

    :param type_hint:
    :return:
    """

    # For reference - with enforce type checker that would be:
    # --------------------------------------------------------
    # from enforce.settings import Settings
    # from enforce.validator import init_validator
    # # use enforce to check if the type hint
    # validator = init_validator(dict(foo=type_hint))
    # validator.settings = Settings(enabled=True, group=None)
    # return validator.validate(None, 'foo')

    if type_hint is None:
        # no type hint - we cannot say anything
        return False

    elif is_pep484_none_type(type_hint):
        return True

    elif is_pep484_union_type(type_hint):
        try:
            union_params = type_hint.__union_params__
        except AttributeError:
            union_params = type_hint.__args__
        for element in union_params:
            if is_pep484_nonable(element):
                return True

    # fallback
    return False
