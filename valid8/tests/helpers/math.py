try:
    from math import isfinite, inf
except ImportError:
    inf = float('inf')
    def isfinite(x):
        return x != inf and x != -inf
