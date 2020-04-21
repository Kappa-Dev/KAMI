"""Collection of data structures for querying KAMI corpora and models."""
import itertools
import copy
import warnings

from regraph import NXGraph

from kamiql.parser import parse_query

from kami.resources.metamodels import meta_model_base_typing, meta_model
from kami.exceptions import KamiQLError, KamiQLWarning


# Global variables used to query nuggets and the action graph
META_MODEL = NXGraph()
META_MODEL.add_nodes_from(meta_model["nodes"])
META_MODEL.add_edges_from(meta_model["edges"])
META_TYPES = list(meta_model_base_typing.keys())
GENERIC_TYPES = list(set(meta_model_base_typing.values()))
GENERIC_TYPE_EXTENSION = {
    "component": ["protoform", "region", "site", "residue"],
    "interaction": ["bnd", "mod"],
    "state": ["state"]
}


def isinteraction(types):
    for t in types:
        if t in ["mod", "bnd"]:
            return True
    return False


def iscomponent(types):
    for t in types:
        if t in GENERIC_TYPE_EXTENSION["component"]:
            return True
    return False


def _generate_path_from_state(s, t, s_types, t_types, existing_nodes):
    """Generate a pattern realizatons for '(:state)-*->(:component)'.

    To do so, we add a dummy component as a proxy:
    - '(:state)-->(_dummy:component)-->(:component)'.
    """
    path_realizations = []
    if "state" in s_types:
        if iscomponent(t_types):
            dummy_state = _generate_fresh_variable(existing_nodes, "state")
            existing_nodes.add(dummy_state)
            path_realizations.append(
                {
                    "nodes": [dummy_state],
                    "meta_typing": {
                        dummy_state: ["residue", "site", "region"]},
                    "edges": [(s, dummy_state), (dummy_state, t)]
                })
    return path_realizations


def _generate_path_from_mod(s, t, s_types, t_types, existing_nodes):
    """Generate a pattern realizatons for '(:interaction)-*->(component)'.

    This query is a syntactic sugar for '(:mod)-->(:state)-*->(:component)',
    it therefore gives rise to:
    - '(:mod)-->(_dummy:state)-->(:component)' and
    - '(:mod)-->(_dummy1:state)-(_dummy2:component)->(:component)'
    """
    path_realizations = []
    if isinteraction(s_types) and iscomponent(t_types):
        dummy_state = _generate_fresh_variable(existing_nodes, "state")
        existing_nodes.add(dummy_state)
        path_realizations.append({
            "nodes": [dummy_state],
            "meta_typing": {
                dummy_state: ["state"]
            },
            "edges": [(s, dummy_state), (dummy_state, t)]
        })
        dummy_component = _generate_fresh_variable(
            existing_nodes, "component")
        existing_nodes.add(dummy_component)
        path_realizations.append({
            "nodes": [dummy_state, dummy_component],
            "meta_typing": {
                dummy_state: ["state"],
                dummy_component: ["residue", "site", "region"]
            },
            "edges": [
                (s, dummy_state),
                (dummy_state, dummy_component),
                (dummy_component, t)
            ]
        })
    return path_realizations


def _generate_undir_path_from_interaction(s, t, s_types, t_types, existing_nodes):
    # The remaining option for '(:component)-*-(:interaction)'
    # gives a rise to '(:component)<--(_dummy:component)-->(:interaction)'
    path_realizations = []
    if (isinteraction(s_types) and iscomponent(t_types)) or\
       (iscomponent(s_types) and isinteraction(t_types)):
        dummy_component = _generate_fresh_variable(
            existing_nodes, "component")
        existing_nodes.add(dummy_component)
        path_realizations.append({
            "nodes": [dummy_component],
            "meta_typing": {
                dummy_component: ["site", "region"]
            },
            "edges": [(dummy_component, s), (dummy_component, t)]
        })
    return path_realizations


def _generate_fresh_variable(existing_variables, label):
    """Generate a fresh variable name."""
    if label is None:
        label = "node"
    index = 1
    name = "{}{}".format(label, index)
    while name in existing_variables:
        index += 1
        name = "{}{}".format(label, index)
    return name


def _get_meta_types(label):
    label = label.lower()
    if label in META_TYPES:
        return [label]
    elif label in GENERIC_TYPES:
        return GENERIC_TYPE_EXTENSION[label]
    else:
        raise KamiQLError(
            "Node type '{}' is unknown. Node type should be either "
            "a generic type ('component', "
            "'state', 'interaction') or the meta-model node type "
            "('protoform', 'region', etc).".format(label))


def _exists_valid_edge(source_types, target_types, undirected=False):
    """Check if the edge is allowed by the meta-model."""
    valid_edge_found = False
    for st in source_types:
        for tt in target_types:
            if (st, tt) in META_MODEL.edges():
                valid_edge_found = True
                break
            elif undirected:
                if (tt, st) in META_MODEL.edges():
                    valid_edge_found = True
                    break
    return valid_edge_found


def build_ag_patterns(elements):
    """Build patterns to match in the action graph.

    General rule: varaible length edges don't pass through interactions
    """

    existing_nodes = set()

    def _retrieve_node(d):
        node_label = (
            d["node_label"] if "node_label" in d else None)
        node_var = (
            d["node_var"]
            if "node_var" in d
            else _generate_fresh_variable(existing_nodes, node_label))
        node_attrs = d["node_attrs"] if "node_attrs" in d else None
        return node_var, node_attrs, _get_meta_types(node_label)

    generic_pattern = {
        "nodes": [],
        "directed_edges": [],
        "undirected_edges": [],
    }
    meta_typing = {}
    undirected_paths = []
    directed_paths = []

    for element in elements:
        if "edge_type" in element:
            # It's an edge
            if element["edge_type"] == "directed":
                s_var, s_attrs, s_types = _retrieve_node(element["source"])
                if s_var not in existing_nodes:
                    existing_nodes.add(s_var)
                    generic_pattern["nodes"].append((s_var, s_attrs))
                    if len(s_types) > 0:
                        meta_typing[s_var] = s_types
                t_var, t_attrs, t_types = _retrieve_node(element["target"])
                if t_var not in existing_nodes:
                    existing_nodes.add(t_var)
                    generic_pattern["nodes"].append((t_var, t_attrs))
                    if len(t_types) > 0:
                        meta_typing[t_var] = t_types
                if not element["path"]:
                    if _exists_valid_edge(s_types, t_types):
                        edge_attrs = (
                            element["edge_attrs"]
                            if "edge_attrs" in element else None
                        )
                        generic_pattern["directed_edges"].append(
                            (s_var, t_var, edge_attrs))
                    else:
                        warnings.warn(
                            "No edge from a type in {} to any of ".format(
                                s_types) +
                            "the types {} exists in the meta-model".format(
                                t_types),
                            KamiQLWarning)
                        return []
                else:
                    directed_paths.append((s_var, t_var))
            else:
                # It's an undirected edge
                s_var, s_attrs, s_types = _retrieve_node(element["left"])
                if s_var not in existing_nodes:
                    existing_nodes.add(s_var)
                    generic_pattern["nodes"].append((s_var, s_attrs))
                    if len(s_types) > 0:
                        meta_typing[s_var] = s_types
                t_var, t_attrs, t_types = _retrieve_node(element["right"])
                if t_var not in existing_nodes:
                    existing_nodes.add(t_var)
                    generic_pattern["nodes"].append((t_var, t_attrs))
                    if len(t_types) > 0:
                        meta_typing[t_var] = t_types
                if not element["path"]:
                    if _exists_valid_edge(s_types, t_types, True):
                        edge_attrs = element[
                            "edge_attrs"] if "edge_attrs" in element else None
                        generic_pattern["undirected_edges"].append(
                            (s_var, t_var, edge_attrs))
                    else:
                        warnings.warn(
                            "No undirected edge from the types '{}' ".format(
                                s_types) +
                            "to any of the types '{}' exists in the meta-model".format(
                                t_types),
                            KamiQLWarning)
                        return []
                else:
                    undirected_paths.append((s_var, t_var))
        else:
            # It's a node
            node_var, node_attrs, node_types = _retrieve_node(element)
            generic_pattern["nodes"].append(
                (node_var, node_attrs))
            if len(node_types) > 0:
                meta_typing[node_var] = node_types

    new_pattern_components = []

    # Process directed paths
    for s_var, t_var in directed_paths:
        path_realizations = []
        s_meta_type = meta_typing[s_var]
        t_meta_type = meta_typing[t_var]
        if _exists_valid_edge(s_meta_type, t_meta_type):
            # path as a direct edge
            path_realizations.append(
                {
                    "nodes": [],
                    "meta_typing": {},
                    "edges": [(s_var, t_var)]
                })

        # generate realization of the path as multiple edges
        path_realizations += _generate_path_from_state(
            s_var, t_var, s_meta_type, t_meta_type, existing_nodes)
        path_realizations += _generate_path_from_mod(
            s_var, t_var, s_meta_type, t_meta_type, existing_nodes)
        new_pattern_components.append(path_realizations)

    # Process undirected paths
    for s_var, t_var in undirected_paths:
        path_realizations = []
        s_meta_type = meta_typing[s_var]
        t_meta_type = meta_typing[t_var]
        if _exists_valid_edge(s_meta_type, t_meta_type, True):
            # path as an undirect edge
            path_realizations.append(
                {
                    "nodes": [],
                    "meta_typing": {},
                    "edges": [(s_var, t_var)]
                })
        # generate realization of the path as multiple edges
        path_realizations += _generate_path_from_state(
            s_var, t_var, s_meta_type, t_meta_type, existing_nodes)
        path_realizations += _generate_path_from_state(
            t_var, s_var, t_meta_type, s_meta_type, existing_nodes)

        path_realizations += _generate_path_from_mod(
            s_var, t_var, s_meta_type, t_meta_type, existing_nodes)
        path_realizations += _generate_path_from_mod(
            t_var, s_var, t_meta_type, s_meta_type, existing_nodes)

        path_realizations += _generate_undir_path_from_interaction(
            s_var, t_var, s_meta_type, t_meta_type, existing_nodes)
        new_pattern_components.append(path_realizations)

    combinations = itertools.product(*new_pattern_components)

    patterns = []
    for combination in combinations:
        pattern = copy.deepcopy(generic_pattern)
        pattern_typing = {
            "meta_model": copy.deepcopy(meta_typing)
        }
        for portion in combination:
            pattern["nodes"] += portion["nodes"]
            pattern["directed_edges"] += portion["edges"]
            pattern_typing["meta_model"].update(portion["meta_typing"])
        patterns.append((pattern, pattern_typing))
    return patterns


class KamiQLEngine(object):
    """KAMIql engine."""

    def __init__(self, kb):
        """Initialize a KAMIqlEngine."""
        self._kb = kb

    def query_action_graph(self, query):
        """Execute a KAMIql query on the action graph."""
        pattern_elements = parse_query(query)
        patterns = build_ag_patterns(pattern_elements)

        result = []
        for pattern_dict, pattern_typing in patterns:
            print("Matching pattern.....")
            print(pattern_dict)
            result += self._kb._hierarchy.advanced_find_matching(
                self._kb._action_graph_id,
                pattern_dict, pattern_typing)
