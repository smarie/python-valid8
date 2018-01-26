def append_all_custom_variants(base_function, custom_boolean_testers, custom_failure_raisers, dest_list):
    """
    Utility method used by the tests

    :param base_function:
    :param custom_boolean_testers:
    :param custom_failure_raisers:
    :param dest_list:
    :return:
    """
    if 'custom_boolean' in base_function.__name__:
        print('{} uses custom boolean checkers'.format(base_function.__name__))
        for cust in custom_boolean_testers:
            dest_list.append(create_custom_function(base_function, cust))

    elif 'custom_raiser' in base_function.__name__:
        print('{} uses custom failure raisers'.format(base_function.__name__))
        for cust in custom_failure_raisers:
            dest_list.append(create_custom_function(base_function, cust))

    else:
        print('{} uses ALL custom functions'.format(base_function.__name__))
        for cust in custom_boolean_testers + custom_failure_raisers:
            dest_list.append(create_custom_function(base_function, cust))


def create_custom_function(base_function, cust):
    def cust_f(t):
        print('calling function {} with custom func {}'.format(base_function.__name__, cust.__name__))
        return base_function(t, cust)

    cust_f.__name__ = base_function.__name__.replace('custom', 'custom_' + cust.__name__)
    return cust_f
