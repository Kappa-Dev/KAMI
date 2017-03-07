from regraph.library.tree import child_from_path


def _get_father_id(hie, top, path_to_graph):
    path_list = [s for s in path_to_graph.split("/") if s and not s.isspace()]
    if path_list == []:
        raise ValueError("/ is not a valid name")
        # graph_id = None
        # parent_id = top
    else:
        graph_id = path_list[-1]
        parent_id = child_from_path(hie, top, path_list[:-1])
    return (parent_id, graph_id)


def _get_node_id(hie, top, path_to_graph):
    path_list = [s for s in path_to_graph.split("/") if s and not s.isspace()]
    return child_from_path(hie, top, path_list)


def same_graphs(hie, top, path1, path2):
    """test if two path lead to the same graph"""
    path_list1 = [s for s in path1.split("/") if s and not s.isspace()]
    path_list2 = [s for s in path2.split("/") if s and not s.isspace()]
    return (_get_node_id(hie, top, path_list1) ==
            _get_node_id(hie, top, path_list2))


def empty_path(path):
    """test if a path is empty"""
    path_list = [s for s in path.split("/") if s and not s.isspace()]
    return path_list == []


def apply_on_node(hie, top, path, callback):
    """apply callback on node identified by path starting from top"""
    # try:
    node_id = _get_node_id(hie, top, path)
    return callback(node_id)
    # except ValueError as err:
    #     return (str(err), 404)


def apply_on_node_with_parent(hie, top, path, callback):
    """apply callback on node identified by path starting from top"""
    # try:
    node_id = _get_node_id(hie, top, path)
    try:
        (parent_id, _) = _get_father_id(hie, top, path)
    except ValueError:
        parent_id = None
    return callback(node_id, parent_id)
    # except ValueError as err:
    #     return (str(err), 404)


def apply_on_parent(hie, top, path, callback):
    """apply callback on parent of node identified by path starting from top"""
    # try:
    (parent_id, node_name) = _get_father_id(hie, top, path)
    return callback(parent_id, node_name)
    # except ValueError as err:
    #     return (str(err), 404)

