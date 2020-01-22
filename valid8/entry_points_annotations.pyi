from typing import Callable, List, Union, Any, Type, TypeVar

try:
    from inspect import signature, Signature
except ImportError:
    from funcsigs import signature, Signature

from valid8.composition import ValidationFuncs
from valid8.entry_points import ValidationError, Validator


class InputValidationError(ValidationError):
    ...


class OutputValidationError(ValidationError):
    ...


class ClassFieldValidationError(ValidationError):
    ...


class FuncValidator(Validator):
    def __init__(self,
                 validated_func: Callable,
                 *validation_func: ValidationFuncs,
                 error_type: Type[ValidationError] = None,
                 help_msg: str = None,
                 none_policy: int = None,
                 **kw_context_args):
        ...

    def get_validated_func_display_name(self):
        ...


class InputValidator(FuncValidator):
    ...


class OutputValidator(FuncValidator):
    ...


class ClassFieldValidator(Validator):
    ...

    def get_validated_class_display_name(self):
        ...


DecoratedClass = TypeVar("DecoratedClass", bound=Type[Any])


def validate_field(field_name,
                   *validation_func: ValidationFuncs,
                   help_msg: str = None,
                   error_type: Type[InputValidationError] = None,
                   none_policy: int = None,
                   **kw_context_args) -> Callable[[DecoratedClass], DecoratedClass]:
    ...


DecoratedFunc = TypeVar("DecoratedFunc", bound=Callable)


def validate_io(none_policy: int=None,
                _out_: ValidationFuncs=None,
                **kw_validation_funcs: ValidationFuncs
                ) -> Callable[[DecoratedFunc], DecoratedFunc]:
    ...


def validate_arg(arg_name,
                 *validation_func: ValidationFuncs,
                 help_msg: str = None,
                 error_type: Type[InputValidationError] = None,
                 none_policy: int = None,
                 **kw_context_args) -> Callable[[DecoratedFunc], DecoratedFunc]:
    ...


def validate_out(*validation_func: ValidationFuncs,
                 help_msg: str = None,
                 error_type: Type[OutputValidationError] = None,
                 none_policy: int = None,
                 **kw_context_args) -> Callable[[DecoratedFunc], DecoratedFunc]:
    ...


def decorate_cls_with_validation(cls: DecoratedClass,
                                 field_name: str,
                                 *validation_func: ValidationFuncs,
                                 help_msg: str = None,
                                 error_type: 'Union[Type[InputValidationError], Type[OutputValidationError]]' = None,
                                 none_policy: int = None,
                                 **kw_context_args) -> DecoratedClass:
    ...


def decorate_several_with_validation(func: DecoratedFunc,
                                     _out_: ValidationFuncs = None,
                                     none_policy: int = None,
                                     **validation_funcs: ValidationFuncs
                                     ) -> DecoratedFunc:
    ...


def decorate_with_validation(func: DecoratedFunc,
                             arg_name: str,
                             *validation_func: ValidationFuncs,
                             help_msg: str = None,
                             error_type: Union[Type[InputValidationError], Type[OutputValidationError]] = None,
                             none_policy: int = None,
                             _constructor_of_cls_: Type=None,
                             **kw_context_args) -> DecoratedFunc:
    ...


class InvalidNameError(ValueError):
    ...


def _create_function_validator(validated_func: Callable,
                               s: Signature,
                               arg_name: str,
                               *validation_func: ValidationFuncs,
                               help_msg: str = None,
                               error_type: Type[InputValidationError] = None,
                               none_policy: int = None,
                               validated_class: Type=None,
                               validated_class_field_name: str=None,
                               **kw_context_args) -> Union[ClassFieldValidator, InputValidator, OutputValidator]:
    ...


def decorate_with_validators(func: DecoratedFunc,
                             func_signature: Signature = None,
                             **validators: Union[Validator, List[Validator]]
                             ) -> DecoratedFunc:
    ...
