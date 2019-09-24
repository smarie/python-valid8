from valid8.utils.typing_tools import Boolean, is_pep484_nonable

from valid8.base import ValidationFailure, failure_raiser, as_failure_raiser, Invalid
from valid8.composition import CompositionFailure, AtLeastOneFailed, and_, DidNotFail, not_, AllValidatorsFailed, or_, \
    XorTooManySuccess, xor_, not_all, fail_on_none, skip_on_none

from valid8.entry_points import NonePolicy, NoneArgPolicy, ValidationError, Validator, assert_valid, is_valid
from valid8.entry_points_annotations import InvalidNameError, InputValidationError, InputValidator, \
    OutputValidationError, ClassFieldValidationError, validate_arg, validate_field, validate_io, validate_out, \
    decorate_with_validation, decorate_with_validators
from valid8.entry_points_inline import validate, validation, validator, assert_instance_of

# import all symbols explicitly declared in the validation lib `__all__` list
# from valid8.validation_lib import *

try:
    # Distribution mode : import from _version.py generated by setuptools_scm during release
    from ._version import version as __version__
except ImportError:
    # Source mode : use setuptools_scm to get the current version from src using git
    from setuptools_scm import get_version as _gv
    from os import path as _path
    __version__ = _gv(_path.join(_path.dirname(__file__), _path.pardir))

__all__ = [
    '__version__',

    # submodules
    'base', 'common_syntax', 'composition', 'entry_points', 'entry_points_annotations', 'entry_points_inline',
    'validation_lib', 'utils',

    # symbols
    # -- utils_typing
    'Boolean', 'is_pep484_nonable',
    # -- base
    'ValidationFailure', 'Invalid', 'failure_raiser', 'as_failure_raiser',
    # -- composition
    'CompositionFailure', 'AtLeastOneFailed', 'and_', 'DidNotFail', 'not_', 'AllValidatorsFailed', 'or_',
    'XorTooManySuccess', 'xor_', 'not_all', 'fail_on_none', 'skip_on_none',
    # -- entry_points
    'NonePolicy', 'NoneArgPolicy', 'ValidationError', 'Validator', 'assert_valid', 'is_valid',
    # -- entry_points_annotations
    'InvalidNameError', 'InputValidationError', 'InputValidator', 'OutputValidationError', 'ClassFieldValidationError',
    'validate_arg', 'validate_field', 'validate_io', 'validate_out', 'decorate_with_validation',
    'decorate_with_validators',
    # -- entry_points_inline
    'validate', 'validation', 'validator', 'assert_instance_of'
]

# from valid8.validation_lib import __all__ as __vlib_all__
# __all__ += __vlib_all__
