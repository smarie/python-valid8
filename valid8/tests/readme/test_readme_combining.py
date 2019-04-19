import sys

import pytest

from valid8 import ValidationError, InputValidationError


@pytest.mark.skipif(sys.version_info < (3, 0), reason="no type hints in python 2")
@pytest.mark.skipif(sys.version_info >= (3, 7), reason="enforce does not work with python 3.7")
def test_readme_index_combining_enforce():
    """ Tests that the examples provided in the index page under Combining/Enforce are correct """

    from ._tests_pep484 import test_readme_combining_enforce
    test_readme_combining_enforce()


def test_readme_index_combining_autoclass():
    """ Tests that the examples provided in the index page under Combining/autoclass are correct """

    from autoclass import autoclass
    from mini_lambda import s, x, Len
    from valid8 import validate_field, instance_of, is_multiple_of, ClassFieldValidationError

    class InvalidNameError(ClassFieldValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(ClassFieldValidationError):
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000.'

    @validate_field('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
    @validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                    error_type=InvalidSurfaceError)
    @autoclass
    class House(object):
        def __init__(self, name, surface=None):
            pass

    h = House('sweet home', 200)

    h.surface = None  # Valid (surface is nonable by signature)

    with pytest.raises(InvalidNameError):
        h.name = ''  # InvalidNameError

    with pytest.raises(InvalidSurfaceError):
        h.surface = 10000  # InvalidSurfaceError


def test_readme_index_combining_autoclass_2():
    """ Tests that the examples provided in the index page under Combining/autoclass are correct (2) """

    from autoclass import autoclass
    from mini_lambda import s, x, Len
    from valid8 import validate_arg, instance_of, is_multiple_of

    class InvalidNameError(InputValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(InputValidationError):
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000.'

    @autoclass
    class House(object):

        @validate_arg('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
        @validate_arg('surface', (x >= 0) & (x < 10000), is_multiple_of(100), error_type=InvalidSurfaceError)
        def __init__(self, name, surface=None):
            pass

    h = House('sweet home', 200)
    h.surface = None  # Valid

    with pytest.raises(InvalidNameError):
        h.name = ''

    with pytest.raises(InvalidSurfaceError):
        h.surface = 10000


def test_readme_index_combining_attrs():
    """ Tests that the examples provided in the index page under Combining/autoclass are correct """

    import attr
    from mini_lambda import s, x, Len
    from valid8 import validate_field, instance_of, is_multiple_of, ClassFieldValidationError

    class InvalidNameError(ClassFieldValidationError):
        help_msg = 'name should be a non-empty string'

    class InvalidSurfaceError(ClassFieldValidationError):
        help_msg = 'Surface should be a multiple of 100 between 0 and 10000.'

    @validate_field('name', instance_of(str), Len(s) > 0, error_type=InvalidNameError)
    @validate_field('surface', (x >= 0) & (x < 10000), is_multiple_of(100),
                    error_type=InvalidSurfaceError)
    @attr.s
    class House(object):
        name = attr.ib()
        surface = attr.ib(default=None)

    h = House('sweet home')  # Valid (surface is nonable by generated signature)

    h.name = ''       # DOES NOT RAISE InvalidNameError (no setter!)

    with pytest.raises(InvalidNameError):
        House('', 10000)  # InvalidNameError

    with pytest.raises(InvalidSurfaceError):
        House('sweet home', 10000)  # InvalidSurfaceError


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints are not supported in this version")
def test_unused_pytypes():
    """ Tests that pytypes and valid8 can work together too """

    # for type checking
    from pytypes import typechecked, InputTypeError

    # for value checking
    from valid8 import validate_io, minlens, gt

    from ._tests_pep484 import create_for_test_unused_pytypes
    build_house = create_for_test_unused_pytypes()
    build_house = validate_io(name=minlens(0), surface=gt(0))(build_house)
    build_house = typechecked(build_house)

    build_house('test', 12, 2)  # validation OK

    with pytest.raises(InputTypeError):
        build_house('test', 12, 2.2)  # Type validation: @typechecked raises a InputTypeError

    build_house('test', 12, None)  # Mandatory/Optional validation: Declared 'Optional' with PEP484, no error

    with pytest.raises(ValidationError):
        build_house('test', -1, 2)  # Value validation: @validate_io raises a Failure

    with pytest.raises(ValidationError):
        build_house('', 12, 2)  # Value validation: @validate_io raises a Failure


@pytest.mark.skipif(sys.version_info < (3, 7), reason="checktypes does not seem to work on old python versions "
                                                      "see https://gitlab.com/yahya-abou-imran/checktypes/issues/2")
def test_readme_combining_checktypes():
    """ Tests that the checktypes library can play well in valid8 """

    from valid8 import validate
    from checktypes import checktype
    PositiveInt = checktype('PositiveInt', int, lambda x: x > 0)

    x = 1
    validate('x', x, custom=PositiveInt.validate)

    with pytest.raises(ValidationError) as exc_info:
        x = -1
        validate('x', x, custom=PositiveInt.validate)

    e = exc_info.value
    assert str(e) == "Error validating [x=-1]. Validation function [validate] raised ValueError: expected " \
                     "'PositiveInt' but got -1."
