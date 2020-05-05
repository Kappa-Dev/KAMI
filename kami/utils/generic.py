"""Collection of generic utils used in KAMI."""
import collections
import copy
import time

from regraph.utils import attrs_from_json
from kami.exceptions import KamiException
# from kami.aggregation import identifiers


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
        return set()


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
            if node in typing:
                if typing[node] == type_name:
                    nodes.append(node)
    return nodes


def _init_from_data(kb, data, instantiated=False):
    """Init knowledge base from json data."""
    if data is not None:
        if "action_graph" in data.keys():
            # ag = copy.deepcopy(ag)
            # print("Loading action graph...")
            start = time.time()
            kb._hierarchy.add_graph_from_json(
                kb._action_graph_id,
                data["action_graph"],
                {"type": "action_graph"})
            # print("Finished after: ", time.time() - start)

            if "action_graph_typing" in data.keys():
                ag_typing = copy.deepcopy(
                    data["action_graph_typing"])
            else:
                raise KamiException(
                    "Error loading knowledge base from json: "
                    "action graph should be typed by the meta-model!")
            # print("Setting action graph typing...")
            start = time.time()
            kb._hierarchy.add_typing(
                kb._action_graph_id, "meta_model", ag_typing)
            # print("Finished after: ", time.time() - start)

            if not instantiated:
                # print("Loading action graph semmantics...")
                start = time.time()
                if "action_graph_semantics" in data.keys():
                    ag_semantics = copy.deepcopy(
                        data["action_graph_semantics"])
                else:
                    ag_semantics = dict()
                kb._hierarchy.add_relation(
                    kb._action_graph_id,
                    "semantic_action_graph",
                    ag_semantics)
                # print("Finished after: ", time.time() - start)
        else:
            if kb._action_graph_id not in kb._hierarchy.graphs():
                kb.create_empty_action_graph()

        # Nuggets related init
        # print("Adding nuggets...")
        start = time.time()
        if "nuggets" in data.keys():
            for nugget_data in data["nuggets"]:
                nugget_graph_id = kb._id + "_" + nugget_data["id"]
                if "graph" not in nugget_data.keys() or\
                   "typing" not in nugget_data.keys() or\
                   "template_rel" not in nugget_data.keys():
                    raise KamiException(
                        "Error loading knowledge base from json: "
                        "nugget data shoud contain typing by"
                        " action graph and template relation!")

                attrs = {}
                if "attrs" in nugget_data.keys():
                    attrs = attrs_from_json(nugget_data["attrs"])
                attrs["type"] = "nugget"
                attrs["nugget_id"] = nugget_data["id"]
                if not instantiated:
                    attrs["corpus_id"] = kb._id
                else:
                    attrs["model_id"] = kb._id
                    attrs["corpus_id"] = kb._corpus_id

                kb._hierarchy.add_graph_from_json(
                    nugget_graph_id,
                    nugget_data["graph"],
                    attrs)

                kb._hierarchy.add_typing(
                    nugget_graph_id,
                    kb._action_graph_id, nugget_data["typing"])

                kb._hierarchy.add_relation(
                    nugget_graph_id,
                    nugget_data["template_rel"][0],
                    nugget_data["template_rel"][1])

                if not instantiated:
                    if "semantic_rels" in nugget_data.keys():
                        for s_nugget_id, rel in nugget_data[
                                "semantic_rels"].items():
                            kb._hierarchy.add_relation(
                                nugget_graph_id, s_nugget_id, rel)
        # print("Finished after: ", time.time() - start)
    else:
        if kb._action_graph_id not in kb._hierarchy.graphs():
            kb.create_empty_action_graph()


def _generate_fragment_repr(corpus, protoform_node,
                            fragment_node, fragment_type="region"):
    region_attrs = corpus.action_graph.get_node(fragment_node)
    name = None
    if "name" in region_attrs:
        name = list(region_attrs["name"])[0]
    edge_attrs = corpus.action_graph.get_edge(
        fragment_node, protoform_node)
    start = None
    end = None
    if "start" in edge_attrs:
        start = list(edge_attrs["start"])[0]
    if "end" in edge_attrs:
        end = list(edge_attrs["end"])[0]
    region_str = "{} {} {}".format(
        fragment_type,
        "'{}'".format(name) if name else "with no name",
        ("({}-{})".format(start if start else "X", end if end else "X")
            if (start or end) else "")
    )
    return region_str


def _generate_residue_repr(corpus, protoform_node, residue_node):
    residue_attrs = corpus.action_graph.get_node(residue_node)
    aa = None
    if "aa" in residue_attrs:
        aa = list(residue_attrs["aa"])[0]
    edge_attrs = corpus.action_graph.get_edge(
        residue_node, protoform_node)
    loc = None
    if "loc" in edge_attrs:
        loc = list(edge_attrs["loc"])[0]

    residue_str = "residue {}{}".format(
        aa if aa else "", loc if loc else "")
    return residue_str


def _generate_ref_agent_str(corpus, ref_agent, ref_gene,
                            ref_agent_in_regions=False,
                            ref_agent_in_sites=False,
                            ref_agent_in_residues=False):
    """Generate str representation of the ref agent."""
    ref_uniprot = corpus.get_uniprot(ref_gene)
    ref_agent_str = ""
    if ref_agent_in_regions or ref_agent_in_sites:
        region_str = ""
        region_attrs = corpus.action_graph.get_node(ref_agent)
        if "name" in region_attrs:
            region_str += list(region_attrs["name"])[0]
        edge_attrs = corpus.action_graph.get_edge(
            ref_agent, ref_gene)
        if "start" in edge_attrs and "end" in edge_attrs:
            region_str += "({}-{})".format(
                list(edge_attrs["start"])[0], list(edge_attrs["end"])[0])

        region_repr = _generate_fragment_repr(
            corpus, ref_gene, ref_agent, "region" if ref_agent_in_regions else "site")
        ref_agent_str = "{} of ".format(region_repr)
    elif ref_agent_in_residues:
        ref_agent_str = _generate_residue_repr(
            corpus, ref_gene, ref_agent) + " of "

    ref_agent_str += (
        "the protoform with the UniProtAC '{}'".format(ref_uniprot)
    )
    return ref_agent_str
