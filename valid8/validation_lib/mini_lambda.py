try:
    from valid8.validation_lib.types import instance_of
    from mini_lambda import make_lambda_friendly_method

    Instance_of = make_lambda_friendly_method(instance_of, 'instance_of')
except ImportError:
    pass