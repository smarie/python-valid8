from numbers import Integral
from typing import Iterator, Generator, Reversible, Mapping

import os


def __get_all_magic_methods(*classes):
    """
    Helper method to return all magic methods in a given type
    :param classes:
    :return:
    """
    return {name for clazz in classes for name in dir(clazz) if name.startswith('__')}

# init
method_names_to_override = set()
methods_that_should_not_be_overriden = set()
methods_impossible_to_override = set()

# Base
# .__class__, .__mro__
# .__doc__, .__name__, __module__, .__dict__
methods_that_should_not_be_overriden.update({'__class__', '__mro__', '__doc__', '__name__', '__module__', '__dict__'})

# Iterable
# .__iter__
# method_names_to_override.update(__get_all_magic_methods(Iterable))
# Actually this COULD work but creates infinite loops when a list comprehension is used in the expression [i for i in x]
# so we prefer to raise an exception and tell users that list comprehensions are forbidden
# methods_that_should_not_be_overriden.update({'__iter__'})
methods_impossible_to_override.update({('Iter', '__iter__', None)})

# Iterator and Generator
# .__next__
method_names_to_override.update(__get_all_magic_methods(Iterator, Generator))

# Initializable Object
# .__new__, .__init__, .__del__
methods_that_should_not_be_overriden.update({'__new__', '__init__', '__del__'})

# Representable Object
# .__repr__, .__str__, .__bytes__, .__format__,
# __sizeof__
methods_impossible_to_override.update({('Str', '__str__', None),
                                       ('Repr', '__repr__', None),
                                       ('Bytes', '__bytes__', 'bytes'),
                                       ('Format', '__format__', None),
                                       ('Getsizeof', '__sizeof__', None)})

# Comparable Objects >> we will get them from Set
# .__lt__, .__le__, .__eq__, .__ne__, .__gt__, .__ge__
method_names_to_override.update({'__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__'})

# Hashable Object
# .__hash__
# method_names_to_override.update(__get_all_magic_methods(Hashable))
methods_impossible_to_override.update({('Hash', '__hash__', None)})

# Truth-testable Object
# .__bool__
methods_impossible_to_override.update({('Bool', '__bool__', None)})

# Object = Field container
#  .__getattribute__ (to avoid)
# .__getattr__,.__setattr__, .__delattr__
# .__dir__
# .__slots__
# method_names_to_override.update({'__getattr__'}) >> WE ACTUALLY DO IT MANUALLY
methods_that_should_not_be_overriden.update({'__getattr__', '__getattribute__', '__setattr__', '__delattr__', '__dir__', '__slots__'})

# Object Descriptors
# .__get__ , .__set__, .__delete__, .__set_name__
# method_names_to_override.update({'__get__'})
methods_that_should_not_be_overriden.update({'__get__', '__set__', '__delete__', '__set_name__'})

# Callable
# .__call__
method_names_to_override.update({'__call__'})

# Class
# .__instancecheck__, .__subclasscheck__
# .__init_subclass__
# .__subclasshook__, .__abstractmethods__
#
# PROBLEM: these 2 methods are CLASS methods, carried by the SECOND argument, not the first.
# so isintance(x, int) calls __instancecheck__ on int, not on x !
methods_that_should_not_be_overriden.update({'__instancecheck__', '__subclasscheck__'})
methods_that_should_not_be_overriden.update({'__init_subclass__', '__subclasshook__', '__abstractmethods__'})

# Container
# .__contains__
# method_names_to_override.update(__get_all_magic_methods(Container))
methods_that_should_not_be_overriden.update({'__contains__'})

# Sized Container
# .__len__, .__length_hint__
methods_impossible_to_override.update({('Len', '__len__', None)})

# Iterable Container : see Iterable
# Reversible Container
# .__reversed__,
method_names_to_override.update(__get_all_magic_methods(Reversible))

# Subscriptable / Mapping Container
# .__getitem__, .__missing__, .__setitem__, .__delitem__,
method_names_to_override.update(__get_all_magic_methods(Mapping))
methods_that_should_not_be_overriden.update({'__setitem__', '__delitem__'})

# Numeric types
#  .__add__, .__radd__, .__sub__, .__rsub__, .__mul__, .__rmul__, .__truediv__, .__rtruediv__,
# .__mod__, .__rmod__, .__divmod__, .__rdivmod__, .__pow__, .__rpow__
# .__matmul__, .__floordiv__, .__rfloordiv__
# .__lshift__, .__rshift__, __rlshift__, __rrshift__
# .__neg__, .__pos__, .__abs__, .__invert__
method_names_to_override.update(__get_all_magic_methods(Integral))
# Boolean types
# .__and__, .__xor__, .__or__, __rand__, __rxor__, __ror__
methods_that_should_not_be_overriden.update({'__and__', '__xor__', '__or__', '__rand__', '__rxor__', '__ror__'})

# Type conversion
# __int__, __long__, __float__, __complex__, __oct__, __hex__, __index__, __trunc__, __coerce__
method_names_to_override.update({'__trunc__', '__coerce__'})
methods_that_should_not_be_overriden.update({'__index__'})
methods_impossible_to_override.update({('Int', '__int__', None),
                                       ('Long', '__long__', None),
                                       ('Float', '__float__', None),
                                       ('Complex_', '__complex__', 'complex'),  # overriden: int does not implement __complex__
                                       ('Oct', '__oct__', 'oct'), # overriden: int does not implement __oct__
                                       ('Hex', '__hex__', 'hex'), # overriden: int does not implement __hex__
                                       # ('Index', '__index__', None)
                                      })

# Pickle
# __reduce__, __reduce_ex__
methods_that_should_not_be_overriden.update({'__reduce__', '__reduce_ex__'})


# open the template file
THIS_DIR = os.path.dirname(__file__)
template_file = os.path.join(THIS_DIR, 'mini_lambda_base_template.py')
with open(template_file) as f:
    body = f.read()

# prepare it to become a template
body = body.replace('    pass', '{}\n\n{}\n\n{}')


# Standard case 1:
# all magic methods that 'just' need to be implemented, or remapped to the original method calling them because on
# some built-in data types the magic method does not exist
case_1 = '    # *** CASE 1 : magic methods that add themselves to the stack ***\n'
for name in method_names_to_override:
    if name not in methods_that_should_not_be_overriden \
            and name not in [nam[1] for nam in methods_impossible_to_override]:
        # print('Overriding ' + name)
        # _InputEvaluator.add_magic_method(name)
        msg = '    def {}(self, *args):\n' \
              '        """ Returns a new _InputEvaluator performing \'{}(x, *args)\' on the result of this evaluator\'s evaluation """\n' \
              '        return self.add_bound_method_to_stack(\'{}\', *args)\n\n'
        case_1 += msg.format(name, name, name)
        # print(case_1)

# Standard case 2:
# all magic methods that do not work because the python framework does not allow them to return another type than
# the expected one. For all of them there are two methods: one here throwing an exception, and one at package-level
# to provide a replacement.
case_2 = '    # *** CASE 2 : magic methods that should raise an error and should be replaced with a module-level one ***\n'
case_2_2 = '# *** CASE 2 second part: the package-level replacement methods\n'
for new_method_name, magic_method_name, method_to_call in methods_impossible_to_override:
    # print('Cannot Override ' + magic_method_name + ' because python checks the return type, creating module-level '
    #       'equivalent function ' + new_method_name + ' instead, calling '
    #       + (str(method_to_call) if method_to_call else magic_method_name))
    # add_module_method_and_local_exception(new_method_name, magic_method_name, method_to_call)
    msg = '    def {}(self, *args):\n' \
          '        """\n' \
          '        This magic method can not be used on an _InputEvaluator, because unfortunately python checks the\n' \
          '        result type and does not allow it to be a custom type.\n' \
          '        """\n' \
          '        raise NotImplementedError(\'{} is not supported by _InputEvaluator, since python raises an\'\n' \
          '                                  \'error when its output is not directly an object of the type it expects.\'\n' \
          '                                  \'Please use the {}() method provided at valid8 package level instead\')\n\n'
    case_2 += msg.format(magic_method_name, magic_method_name, new_method_name)
    # print(case_2)
    msg2 = 'def {}(evaluator: _InputEvaluatorGenerated):\n' \
           '    """ This is a replacement method for _InputEvaluator \'{}\' magic method """\n' \
           '    return evaluator.{}({})\n\n\n'
    case_2_2 += msg2.format(new_method_name, magic_method_name,
                            'add_bound_method_to_stack' if method_to_call is None else 'add_unbound_method_to_stack',
                            (str(method_to_call) if method_to_call else ('\'' + magic_method_name + '\'')))
    # print(case_2_2)


body = body.format(case_1, case_2, case_2_2)

dest_file = os.path.join(THIS_DIR, os.pardir, 'valid8', 'mini_lambda_generated.py')
with open(dest_file, 'wt') as f:
    f.write(body)
