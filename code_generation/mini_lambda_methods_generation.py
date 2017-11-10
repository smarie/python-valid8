from sys import getsizeof
from typing import Tuple, Set, Optional, Any

import os

# from quik import Template
from mako import exceptions
from mako.template import Template

# from sortedcontainers import SortedSet
from ordered_set import OrderedSet

from autoclass import autoclass
from enforce import runtime_validation


@runtime_validation
@autoclass
class Override:
    def __init__(self, method_name: str,
                 # we cannot use Callable, see https://github.com/RussBaz/enforce/issues/58
                 unbound_method: Optional[Any] = None,
                 operator: Optional[str] = None, is_operator_left: bool = True,
                 self_operator: Optional[str] = None):
        """
        A descriptor for a method to override in _InputEvaluatorGenerated.
        * If only method_name is provided, the overriden method adds itself to the stack
        (see StackableFunctionEvaluator)
        * If unbound_method is provided, the overriden method adds the provided unbound method to the stack
        * If operator and is_operator_left are provided, the overriden method adds a method performing
        (args <operator> x) if is_operator_left=False or (x <operator> args) if is_operator_left=True
        * If self_operator is provided,  the overriden method adds a method performing <operator> x

        :param method_name: the method name
        :param unbound_method:
        :param operator: for pairwise operators e.g. a * b
        :param is_operator_left:
        :param self_operator: for self-operator e.g. -x
        """
        pass

    def __hash__(self):
        return hash(self.method_name)

    def __str__(self):
        if self.self_operator:
            return '{}: Self operator {}'.format(self.method_name, self.self_operator)
        elif self.operator:
            return '{}: Pairwise operator {} {}'.format(self.method_name, self.operator,
                                                        'left' if self.is_operator_left else 'right')
        elif self.unbound_method:
            return '{}: Unbound method {}'.format(self.method_name, self.unbound_method.__name__)
        else:
            return '{}: Standard default'.format(self.method_name)


@runtime_validation
@autoclass
class OverExc:
    def __init__(self, method_name: str,
                 module_method_name: Optional[str] = None,
                 # we cannot use Callable, see https://github.com/RussBaz/enforce/issues/58
                 unbound_method: Optional[Any] = None):
        """
        A descriptor for a method to override with exception in _InputEvaluatorGenerated, and for which a module-level
        replacement method needs to be provided.

        The method_name will raise an exception and indicate that module_method_name is the replacement method. The
        latter will implement by adding method_name to the stack (see StackableFunctionEvaluator). If unbound_method is
        provided, the module method will add unbound_method to the stack instead of method_name.

        By default module_method_name is equal to a capitalized, underscores-removed, version of the method name.
        For example __bytes__ become Bytes

        :param method_name: the method name
        :param module_method_name:
        :param unbound_method:
        """
        # this is executed AFTER @autoargs
        self.module_method_name = module_method_name or method_name.replace('__', '').capitalize()

    def __hash__(self):
        return hash(self.method_name)

    def __str__(self):
        return 'Exception {} replaced by module method {}'.format(self.method_name, self.module_method_name)


def generate_code():
    """
    This method reads the template file, fills it with the appropriate contents, and writes the result in the
    mini_lambda_generated.py file. All contents of the destination file are overriden by this operation.
    :return:
    """

    # generate the to-do list
    to_override, to_override_with_exception = define_what_needs_to_be_written()
    # check outside of the template that it works:
    for o in to_override:
        print(o)
    for o in to_override_with_exception:
        print(o)

    # open the mako template file
    THIS_DIR = os.path.dirname(__file__)
    template_file = os.path.join(THIS_DIR, 'mini_lambda_template.mako')
    with open(template_file) as f:
        body = f.read()

    try:
        # create the template
        temp = Template(text=body)  # , module_directory=os.path.join(THIS_DIR, 'tmp'))

        # fill it with the variables contents
        res = temp.render(to_override=to_override, to_override_with_exception=to_override_with_exception)

        # write the result to the destination file
        dest_file = os.path.join(THIS_DIR, os.pardir, 'valid8', 'mini_lambda_generated.py')
        with open(dest_file, 'wt') as f:
            f.write(res)
    except:
        # mako user-friendly exception display
        print(exceptions.text_error_template().render())


def __get_all_magic_methods(*classes):
    """
    Helper method to return all magic methods in a given type. We do not use it anymore in the final code, but good for
    debug
    :param classes:
    :return:
    """
    return {name for clazz in classes for name in dir(clazz) if name.startswith('__')}


def define_what_needs_to_be_written() -> Tuple[Set[Override], Set[OverExc]]:
    """
    Creates three sets containing the definition of what we want to write as methods in the generated class.
    :return: a tuple of two sorted sets. The first set contains Override definitions, the second one OverExc
    definitions
    """

    # init containers
    to_override = OrderedSet()
    to_override_with_exception = OrderedSet()
    to_skip = set()

    # ** Base **
    # .__class__, .__mro__
    # .__doc__, .__name__, __module__, .__dict__
    to_skip.update({'__class__', '__mro__', '__doc__', '__name__', '__module__', '__dict__'})

    # ** Iterable **
    # .__iter__
    # to_override.update(__get_all_magic_methods(Iterable))
    # Actually this COULD work but creates infinite loops when a list comprehension is used in the expression [i for i in x]
    # so we prefer to raise an exception and tell users that list comprehensions are forbidden
    # to_skip.update({'__iter__'})
    to_override_with_exception.update({OverExc('__iter__')})

    # ** Iterator and Generator **
    # .__next__
    # to_override.update(__get_all_magic_methods(Iterator, Generator))
    to_override.add(Override('__next__', unbound_method=next))

    # ** Initializable Object **
    # .__new__, .__init__, .__del__
    to_skip.update({'__new__', '__init__', '__del__'})

    # ** Representable Object **
    # .__repr__, .__str__, .__bytes__, .__format__,
    # __sizeof__
    to_override_with_exception.update({OverExc('__str__', unbound_method=str),
                                       OverExc('__repr__', unbound_method=repr),
                                       OverExc('__bytes__', unbound_method=bytes),
                                       OverExc('__format__', unbound_method=format),
                                       OverExc('__sizeof__', unbound_method=getsizeof)})

    # ** Comparable Objects **
    # .__lt__, .__le__, .__eq__, .__ne__, .__gt__, .__ge__
    # to_override.update(__get_all_magic_methods(Set))
    to_override.update({Override('__lt__', operator='<'),
                        Override('__le__', operator='<='),
                        Override('__eq__', operator='=='),
                        Override('__ne__', operator='!='),
                        Override('__gt__', operator='>'),
                        Override('__ge__', operator='>=')})

    # ** Hashable Object **
    # .__hash__
    # to_override.update(__get_all_magic_methods(Hashable))
    to_override_with_exception.update({OverExc('__hash__')})

    # ** Truth-testable Object **
    # .__bool__
    to_override_with_exception.update({OverExc('__bool__')})

    # ** Object = Field container **
    #  .__getattribute__ (to avoid)
    # .__getattr__,.__setattr__, .__delattr__
    # .__dir__
    # .__slots__
    to_skip.update({'__getattribute__', '__setattr__', '__delattr__', '__dir__', '__slots__'})
    to_override.add(Override('__getattr__', unbound_method=getattr))

    # ** Object Descriptors **
    # .__get__ , .__set__, .__delete__, .__set_name__
    # to_override.update({'__get__'})
    to_skip.update({'__get__', '__set__', '__delete__', '__set_name__'})

    # ** Callable **
    # .__call__
    # to_override.update(__get_all_magic_methods(Callable))
    to_override.add(Override('__call__'))

    # ** Class **
    # .__instancecheck__, .__subclasscheck__
    # .__init_subclass__
    # .__subclasshook__, .__abstractmethods__
    # IMPOSSIBLE TO OVERRIDE: these 2 methods are CLASS methods, carried by the SECOND argument, not the first.
    # so isintance(x, int) calls __instancecheck__ on int, not on x !
    to_skip.update({'__instancecheck__', '__subclasscheck__'})
    to_skip.update({'__init_subclass__', '__subclasshook__', '__abstractmethods__'})

    # ** Container **
    # .__contains__
    # to_override.update(__get_all_magic_methods(Container))
    to_skip.update({'__contains__'})

    # ** Sized Container **
    # .__len__, .__length_hint__
    to_override_with_exception.add(OverExc('__len__'))

    # ** Iterable Container : see Iterable **
    # ** Reversible Container **
    # .__reversed__,
    # to_override.update(__get_all_magic_methods(Reversible))
    to_override.add(Override('__reversed__', unbound_method=reversed))

    # ** Subscriptable / Mapping Container **
    # .__getitem__, .__missing__, .__setitem__, .__delitem__,
    # to_override.update(__get_all_magic_methods(Mapping))
    to_override.update({Override('__getitem__'),
                        Override('__missing__')})
    to_skip.update({'__setitem__', '__delitem__'})

    # ** Numeric types **
    #  .__add__, .__radd__, .__sub__, .__rsub__, .__mul__, .__rmul__, .__truediv__, .__rtruediv__,
    # .__mod__, .__rmod__, .__divmod__, .__rdivmod__, .__pow__, .__rpow__
    # .__matmul__, .__floordiv__, .__rfloordiv__
    # .__lshift__, .__rshift__, __rlshift__, __rrshift__
    # .__neg__, .__pos__, .__abs__, .__invert__
    # to_override.update(__get_all_magic_methods(Integral))
    to_override.update({Override('__add__', operator='+'),
                        Override('__radd__', operator='+', is_operator_left=False),
                        Override('__sub__', operator='-'),
                        Override('__rsub__', operator='-', is_operator_left=False),
                        Override('__mul__', operator='*'),
                        Override('__rmul__', operator='*', is_operator_left=False),
                        Override('__truediv__', operator='/'),
                        Override('__rtruediv__', operator='/', is_operator_left=False),
                        Override('__mod__', operator='%'),
                        Override('__rmod__', operator='%', is_operator_left=False),
                        Override('__divmod__'),  # TODO , unbound_method=divmod but how
                        Override('__rdivmod__'),
                        Override('__pow__', operator='**'),
                        Override('__rpow__', operator='**', is_operator_left=False),
                        Override('__matmul__', operator='@'),
                        # Override('__rmatmul__', operator='@', is_operator_left=False),
                        Override('__floordiv__', operator='//'),
                        Override('__rfloordiv__', operator='//', is_operator_left=False),
                        Override('__lshift__', operator='<<'),
                        Override('__rlshift__', operator='<<', is_operator_left=False),
                        Override('__rshift__', operator='>>'),
                        Override('__rrshift__', operator='>>', is_operator_left=False),
                        Override('__rshift__', operator='>>'),
                        Override('__rshift__', operator='>>'),
                        Override('__neg__', self_operator='-'),
                        Override('__pos__', self_operator='+'),
                        Override('__abs__', unbound_method=abs),
                        Override('__invert__', self_operator='~'),
                        })


    # ** Boolean types **
    # .__and__, .__xor__, .__or__, __rand__, __rxor__, __ror__
    to_skip.update({'__and__', '__xor__', '__or__', '__rand__', '__rxor__', '__ror__'})

    # ** Type conversion **
    # __int__, __long__, __float__, __complex__, __oct__, __hex__, __index__, __trunc__, __coerce__
    to_override.update({Override('__trunc__'),
                        Override('__coerce__')})
    to_skip.update({'__index__'})
    to_override_with_exception.update({OverExc('__int__', unbound_method=int),
                                       # OverExc('__long__', unbound_method=long),
                                       OverExc('__float__', unbound_method=float),
                                       OverExc('__complex__', unbound_method=complex),
                                       OverExc('__oct__', unbound_method=oct),
                                       OverExc('__hex__', unbound_method=hex),
                                       # ('Index', '__index__', None)
                                       })
    # ** Pickle **
    # __reduce__, __reduce_ex__
    to_skip.update({'__reduce__', '__reduce_ex__'})

    # make sure that the ones noted 'to skip' are not in the other sets to return
    to_override_2 = OrderedSet()
    for overriden in to_override:
        if overriden not in to_skip and overriden not in to_override_with_exception:
            assert type(overriden) == Override
            to_override_2.add(overriden)

    to_override_with_exception_2 = OrderedSet()
    for overriden_with_e in to_override_with_exception:
        if overriden_with_e not in to_skip:
            assert type(overriden_with_e) == OverExc
            to_override_with_exception_2.add(overriden_with_e)

    return to_override_2, to_override_with_exception_2


if __name__ == '__main__':
    generate_code()
