from valid8.base import Failure


class HasWrongType(Failure):
    help_msg = 'Value should be an instance of {ref_type}'


def instance_of(ref):
    """ Validates that x is an instance of ref """

    def instance_of_ref(x):
        if isinstance(x, ref):
            return True
        else:
            raise HasWrongType(wrong_value=x, ref_type=ref)

    instance_of_ref.__name__ = 'instance_of_{}'.format(ref)
    return instance_of_ref


class IsWrongType(Failure):
    help_msg = 'Value should be a type that is a subclass of {ref_type}'


def subclass_of(ref):
    """ Validates that x is an instance of ref """

    def subclass_of_ref(x):
        if type(x) is type and issubclass(x, ref):
            return True
        else:
            raise IsWrongType(wrong_value=x, ref_type=ref)

    subclass_of_ref.__name__ = 'subclass_of_{}'.format(ref)
    return subclass_of_ref
