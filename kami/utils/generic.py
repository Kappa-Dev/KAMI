"""Collection of generic utils used in KAMI."""
import collections


def normalize_to_set(arg):
    """Normalize argument to be an iterable."""
    if arg is not None:
        if type(arg) == str:
            return {arg}
        elif type(arg) == list:
            return set(arg)
        elif not isinstance(arg, collections.Iterable):
            return set([arg])
        else:
            return arg
    else:
        return []
