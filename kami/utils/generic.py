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


def normalize_to_iterable(arg):
    """Normalize argument to be an iterable."""
    if arg is not None:
        if type(arg) == str:
            return [arg]
        elif type(arg) == list:
            return arg
        elif not isinstance(arg, collections.Iterable):
            return [arg]
        else:
            return arg
    else:
        return []


def nodes_of_type(graph, typing, type_name):
    """Get action graph nodes of a specified type."""
    nodes = []

    if graph is not None and\
       len(typing) > 0:
        for node in graph.nodes():
            if typing[node] == type_name:
                nodes.append(node)
    return nodes
