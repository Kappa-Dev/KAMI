"""Collection of untils for identification of entities in a KAMI model."""
import networkx as nx
import numpy as np

from regraph import Rule
from regraph.primitives import get_node, get_edge, add_node_attrs

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


def identify_gene(model, gene):
    """Find corresponding gene in action graph."""
    for node in model.genes():
        gene_attrs = get_node(model.action_graph, node)
        if "uniprotid" in gene_attrs.keys() and\
           gene.uniprotid in gene_attrs["uniprotid"]:
            return node
    return None


def _identify_fragment(model, fragment, ref_agent, fragment_type):
    fragment_candidates = model.ag_predecessors_of_type(
        ref_agent, fragment_type)
    return find_fragment(
        fragment.meta_data(), fragment.location(),
        {
            f: (
                get_node(model.action_graph, f),
                get_edge(model.action_graph, f, ref_agent)
            )
            for f in fragment_candidates
        }
    )


def identify_region(model, region, ref_agent):
    """Find corresponding region in action graph."""
    if ref_agent not in model.genes():
        raise KamiHierarchyError(
            "Agent with UniProtID '%s' is not found in the action graph" %
            ref_agent
        )
    else:
        return _identify_fragment(model, region, ref_agent, "region")


def identify_site(model, site, ref_agent):
    """Find corresponding site in action graph."""
    if ref_agent not in model.genes() and ref_agent not in model.regions():
        raise KamiHierarchyError(
            "Gene with the UniProtAC '%s' is not found in the action graph" %
            ref_agent
        )
    else:
        return _identify_fragment(model, site, ref_agent, "site")


def identify_residue(model, residue, ref_agent,
                     add_aa=False, rewriting=False):
    """Find corresponding residue.

    residue : kami.entities.residue
        Input residue entity to search for
    ref_agent
        Id of the reference agent to which residue belongs,
        can reference either to a gene, a region or a site
        of the action graph
    add_aa : bool
        Add aa value if location is found but aa is not
    rewriting : bool
        If True, add aa value using SqPO rewriting, otherwise
        using primitives (used if `add_aa` is True)
    """
    ref_gene = model.get_gene_of(ref_agent)
    residue_candidates = model.get_attached_residues(ref_gene)
    if residue.loc is not None:
        for res in residue_candidates:
            res_agent_edge = get_edge(
                model.action_graph, res, ref_agent)
            if "loc" in res_agent_edge.keys():
                if residue.loc == int(list(res_agent_edge["loc"])[0]):
                    res_node = get_node(model.action_graph, res)
                    if not residue.aa.issubset(
                        res_node["aa"]) and\
                            add_aa is True:
                        if rewriting:
                            pattern = nx.DiGraph()
                            pattern.add_node(res)
                            rule = Rule.from_transform(pattern)
                            rule.inject_add_node_attrs(
                                res, {"aa": {residue.aa}})
                            model.rewrite(
                                "action_graph", rule, instance={res: res})
                        else:
                            add_node_attrs(
                                model.action_graph,
                                res,
                                {"aa": res_node["aa"].union(residue.aa)})
                    return res
    else:
        for res in residue_candidates:
            res_agent_edge = get_edge(model.action_graph, res, ref_agent)
            if "loc" not in res_agent_edge.keys() or\
               res_agent_edge["loc"].is_empty():
                res_node = get_node(model.action_graph, res)
                if residue.aa <= res_node["aa"]:
                    return res
                elif add_aa is True:
                    if rewriting:
                        pattern = nx.DiGraph()
                        pattern.add_node(res)
                        rule = Rule.from_transform(pattern)
                        rule.inject_add_node_attrs(
                            res, {"aa": {residue.aa}})
                        instance = {
                            n: n for n in pattern.nodes()
                        }
                        instance[res] = res
                        model.rewrite(
                            "action_graph", rule, instance=instance)
                    else:
                        add_node_attrs(
                            model.action_graph,
                            res,
                            {"aa": res_node["aa"].union(residue.aa)})
                    return res
    return None


def identify_state(model, state, ref_agent):
    """Find corresponding state of reference agent."""
    state_candidates = model.get_attached_states(ref_agent)
    for s in state_candidates:
        name = list(get_node(model.action_graph, s)["name"])[0]
        # values = model.action_graph.node[pred][name]
        if state.name == name:
                # if state.value not in values:
                #     add_node_attrs(
                #         model.action_graph,
                #         pred,
                #         {name: {state.value}})
            return s
    return None
