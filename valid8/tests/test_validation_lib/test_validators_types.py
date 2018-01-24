import pytest

from valid8 import instance_of, HasWrongType, subclass_of, IsWrongType, assert_valid


def test_instance_of():
    """ tests that the instance_of() function works """

    # Basic function
    assert instance_of('r', str)
    assert instance_of(True, int)

    with pytest.raises(HasWrongType):
        instance_of(1, str)

    with pytest.raises(HasWrongType):
        instance_of('r', int)

    # Function generator
    assert instance_of(str)('r')
    assert instance_of(int)(True)

    with pytest.raises(HasWrongType):
        instance_of(str)(1)

    with pytest.raises(HasWrongType):
        instance_of(int)('r')

    assert_valid('instance', 'r', instance_of(str))


def test_subclass_of():
    """ tests that the subclass_of() function works """

    # Basic function
    assert subclass_of(bool, int)

    with pytest.raises(IsWrongType):
        subclass_of(int, str)

    with pytest.raises(TypeError):
        subclass_of('r', int)

    # Function generator
    assert subclass_of(int)(bool)

    with pytest.raises(IsWrongType):
        subclass_of(str)(int)

    with pytest.raises(TypeError):
        subclass_of(int)('r')
