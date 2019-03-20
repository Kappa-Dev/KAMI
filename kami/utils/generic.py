"""Collection of generic utils used in KAMI."""
import collections
import copy
import time

from regraph.primitives import attrs_from_json
from kami.exceptions import KamiException


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


def _init_from_data(kb, data, instantiated=False):
    """."""
    if data is not None:
        if "action_graph" in data.keys():
            # ag = copy.deepcopy(ag)
            print("Loading action graph...")
            start = time.time()
            kb._hierarchy.add_graph_from_json(
                kb._action_graph_id,
                data["action_graph"],
                {"type": "action_graph"},
                holistic=True)
            print("Finished after: ", time.time() - start)

            if "action_graph_typing" in data.keys():
                ag_typing = copy.deepcopy(
                    data["action_graph_typing"])
            else:
                raise KamiException(
                    "Error loading knowledge base from json: "
                    "action graph should be typed by the meta-model!")
            print("Setting action graph typing...")
            start = time.time()
            kb._hierarchy.add_typing(
                kb._action_graph_id, "meta_model", ag_typing)
            print("Finished after: ", time.time() - start)

            if not instantiated:
                print("Loading action graph semmantics...")
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
                print("Finished after: ", time.time() - start)
        else:
            if kb._action_graph_id not in kb._hierarchy.graphs():
                kb.create_empty_action_graph()

        # Nuggets related init
        print("Adding nuggets...")
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
                    attrs,
                    holistic=True)
                kb.nugget[nugget_data["id"]] = kb._hierarchy.get_graph(
                    nugget_graph_id)

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
        print("Finished after: ", time.time() - start)
