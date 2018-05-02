"""Collection of untils for identification of entities in a KAMI model."""
import numpy as np
from regraph.primitives import add_node_attrs

from kami.exceptions import KamiHierarchyError


def find_fragment(a_meta_data, a_location, dict_of_b):
    """Find a protein fragment in a collection of other fragments."""
    a_start = None
    a_end = None
    a_name = None
    a_interpro = None
    a_order = None
    if "start" in a_location.keys():
        a_start = int(min(a_location["start"]))
    if "end" in a_location.keys():
        a_end = int(max(a_location["end"]))
    if "name" in a_meta_data.keys():
        a_name = list(a_meta_data["name"])[0].lower()
    if "interproid" in a_meta_data.keys():
        a_interpro = a_meta_data["interproid"]
    if "order" in a_location.keys():
        a_order = list(a_location["order"])[0]

    satisfying_fragments = []
    for b_id, (b_meta_data, b_location) in dict_of_b.items():
        b_start = None
        b_end = None
        b_name = None
        b_interpro = None
        if "start" in b_location.keys():
            b_start = int(min(b_location["start"]))
        if "end" in b_location.keys():
            b_end = int(max(b_location["end"]))
        if "name" in b_meta_data.keys():
            b_name = list(b_meta_data["name"])[0].lower()
        if "interproid" in b_meta_data.keys():
            b_interpro = b_meta_data["interproid"]

        if a_start is not None and a_end is not None and\
           b_start is not None and b_end is not None:
            if a_start >= b_start and a_end <= b_end:
                return b_id
            elif a_start <= b_start and a_end >= b_end:
                return b_id
        elif a_name is not None and b_name is not None:
            if a_name in b_name or b_name in a_name:
                satisfying_fragments.append(b_id)
        elif a_interpro is not None and b_interpro is not None:
            if len(a_interpro.intersection(b_interpro)) > 0:
                satisfying_fragments.append(b_id)

    if len(satisfying_fragments) == 1:
        return satisfying_fragments[0]
    elif len(satisfying_fragments) > 1:
        # Try to find if there is a unique region in the list of
        # satisfying regions with the same order number
        if a_order is not None:
            same_order_fragments = []
            for b_id in satisfying_fragments:
                if "order" in dict_of_b[b_id][1].keys():
                    if a_order in dict_of_b[b_id][1]["order"]:
                        same_order_fragments.append(b_id)
            # if not explicit order number was found
            if len(same_order_fragments) == 0:
                try:
                    start_orders = np.argsort([
                        int(min(dict_of_b[b_id][0]["start"]))
                        for b_id in satisfying_fragments
                        if "start" in dict_of_b[b_id][0].keys()
                    ])
                    return satisfying_fragments[
                        start_orders[a_order - 1]]
                except:
                    return None
            elif len(same_order_fragments) == 1:
                return same_order_fragments[0]
            else:
                return None
    else:
        return None


def identify_gene(hierarchy, gene):
    """Find corresponding gene in action graph."""
    for node in hierarchy.genes():
        if "uniprotid" in hierarchy.action_graph.node[node].keys() and\
           gene.uniprotid in hierarchy.action_graph.node[node]["uniprotid"]:
            return node
    return None


def _identify_fragment(hierarchy, fragment, ref_agent, fragment_type):
    fragment_candidates = hierarchy.ag_predecessors_of_type(
        ref_agent, fragment_type)
    return find_fragment(
        fragment.meta_data(), fragment.location(),
        {
            f: (
                hierarchy.action_graph.node[f],
                hierarchy.action_graph.edge[f][ref_agent])
            for f in fragment_candidates
        }
    )


def identify_region(hierarchy, region, ref_agent):
    """Find corresponding region in action graph."""
    if ref_agent not in hierarchy.genes():
        raise KamiHierarchyError(
            "Agent with UniProtID '%s' is not found in the action graph" %
            ref_agent
        )
    else:
        return _identify_fragment(hierarchy, region, ref_agent, "region")


def identify_site(hierarchy, site, ref_agent):
    """Find corresponding site in action graph."""
    if ref_agent not in hierarchy.genes() and ref_agent not in hierarchy.regions():
        raise KamiHierarchyError(
            "Gene with the UniProtAC '%s' is not found in the action graph" %
            ref_agent
        )
    else:
        return _identify_fragment(hierarchy, site, ref_agent, "site")


def identify_residue(hierarchy, residue, ref_agent, add_aa=False):
    """Find corresponding residue.

    `residue` -- input residue entity to search for
    `ref_agent` -- reference to an agent to which residue belongs.
    Can reference either to an agent or to a region
    in the action graph.
    `add_aa` -- add aa value if location is found but aa not
    """
    ref_gene = hierarchy.get_gene_of(ref_agent)
    residue_candidates = hierarchy.get_attached_residues(ref_gene)
    if residue.loc is not None:
        for res in residue_candidates:
            if "loc" in hierarchy.action_graph.edge[res][ref_agent].keys():
                if residue.loc == int(list(hierarchy.action_graph.edge[res][
                        ref_agent]["loc"])[0]):
                    if residue.aa <= hierarchy.action_graph.node[res]["aa"]:
                        return res
                    elif add_aa is True:
                        hierarchy.action_graph.node[res]["aa"] =\
                            hierarchy.action_graph.node[res]["aa"].union(
                                residue.aa
                        )
                        return res
    else:
        for res in residue_candidates:
            if "loc" not in hierarchy.action_graph.edge[res][ref_agent].keys() or\
               hierarchy.action_graph.edge[res][ref_agent]["loc"].is_empty():
                if residue.aa <= hierarchy.action_graph.node[res]["aa"]:
                    return res
                elif add_aa is True:
                    hierarchy.action_graph.node[res]["aa"] =\
                        hierarchy.action_graph.node[res]["aa"].union(
                        residue.aa
                    )
                    return res
    return None


def identify_state(hierarchy, state, ref_agent):
    """Find corresponding state of reference agent."""
    for pred in hierarchy.action_graph.predecessors(ref_agent):
        if pred in hierarchy.action_graph_typing.keys() and\
           hierarchy.action_graph_typing[pred] == "state":
            name = list(hierarchy.action_graph.node[pred].keys())[0]
            values = hierarchy.action_graph.node[pred][name]
            if state.name == name:
                if state.value not in values:
                    add_node_attrs(
                        hierarchy.action_graph,
                        pred,
                        {name: {state.value}})
                return pred
    return None
