from valid8.utils_init import __remove_all_external_symbols, __get_all_submodules_symbols

__PACKAGE_NAME = 'valid8'
__SUBMODULES_TO_EXPORT = ['base',  'composition', 'entry_points', 'entry_points_annotations', 'entry_points_inline',
                          'validation_lib', 'utils_string', 'utils_typing']


# (1) allow users to do
#     import <package> as p and then p.<symbol>
__all__ = __get_all_submodules_symbols(__PACKAGE_NAME, __SUBMODULES_TO_EXPORT)
# Note: this is one way to do it, but it would be simpler to check the names in globals() at the end of this file.

# (2) allow users to do
#     from <package> import <symbol>
#
# The following works, but unfortunately IDE like pycharm do not understand
from valid8.utils_string import *
from valid8.utils_typing import *

from valid8.base import *
from valid8.composition import *

from valid8.validation_lib.types import *
from valid8.validation_lib.collections import *
from valid8.validation_lib.comparables import *
from valid8.validation_lib.numbers import *

from valid8.entry_points import *
from valid8.entry_points_annotations import *
from valid8.entry_points_inline import *

# remove all symbols that were imported above but do not belong in this package
__remove_all_external_symbols(__PACKAGE_NAME, globals())

# Otherwise exhaustive list would be required, which is sad
# ...

# print(__all__)
# print(globals().keys())
# print('Done')
