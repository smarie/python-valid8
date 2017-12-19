import pytest

from valid8 import instance_of, HasWrongType, subclass_of, IsWrongType, assert_valid


def test_instance_of():
    """ tests that the instance_of() function works """
    assert instance_of(str)('r')
    assert instance_of(int)(True)

    with pytest.raises(HasWrongType):
        instance_of(str)(1)

    with pytest.raises(HasWrongType):
        instance_of(int)('r')

    assert_valid('instance', 'r', instance_of(str))


def test_subclass_of():
    """ tests that the subclass_of() function works """
    assert subclass_of(int)(bool)

    with pytest.raises(IsWrongType):
        subclass_of(str)(int)

    with pytest.raises(IsWrongType):
        subclass_of(int)('r')
