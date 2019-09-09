from pytest_cases import param_fixture
import valid8 as v

# discarded: 'base', 'entry_points', 'entry_points_annotations', 'entry_points_inline', 'utils_string', 'utils_typing'
submodules = ['composition', 'validation_lib']


exceptions_list = ['pop_kwargs']

def get_all_symbols(submodule):
    import valid8 as v
    m = getattr(v, submodule)
    return [s for s, v in vars(m).items() if not s.startswith('_') and s not in exceptions_list
            and getattr(v, '__module__', None) == 'valid8.%s' % submodule]


symbols = [(m, s) for m in submodules for s in get_all_symbols(m)]

symbol = param_fixture("symbol", [s[1] for s in symbols], ids=["%s_%s" % s for s in symbols])


def test_named_import(symbol):
    import valid8 as v
    o = getattr(v, symbol)


def test_import_from(symbol):
    exec("from valid8 import %s" % symbol)
