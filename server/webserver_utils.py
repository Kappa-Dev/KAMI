# todo : pass cmd as an argument to the functions

def parse_path(cmd, path_to_graph):
    l = [s for s in path_to_graph.split("/") if s and not s.isspace()]
    if l == []:
        graph_name = None
        parent_cmd = cmd
    else:
        graph_name = l[-1]
        parent_cmd = cmd.get_sub_hierarchy(l[:-1])
    return (parent_cmd, graph_name)


def get_cmd(cmd, path):
    path_list = [s for s in path.split("/") if s and not s.isspace()]
    return(cmd.get_sub_hierarchy(path_list))

def get_command(cmd, path_to_graph, callback):
    try:
        (parent_cmd, child_name) = parse_path(cmd, path_to_graph)
        if child_name in parent_cmd.subCmds.keys():
            command = parent_cmd.subCmds[child_name]
            return callback(command)
        elif child_name in parent_cmd.subRules.keys():
            command = parent_cmd.subRules[child_name]
            return callback(command)
        else:
            raise(KeyError)
    except KeyError as e:
        return("Graph not found: {}".format(e), 404)

