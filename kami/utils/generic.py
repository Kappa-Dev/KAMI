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
        # print("Finished after: ", time.time() - start)


def _clean_up_nuggets(kb):
    for nugget in kb.nuggets():
        if kb._backend == "neo4j":
            # Query to remove edge to a mod/bnd from/to the actor that contains
            # a residue with the empty aa
            query = (
                "MATCH (residue:{})-[:edge*1..]->(gene:{})\n".format(nugget, nugget) +
                "WHERE (residue)-[:typing]->()-[:typing]->(:meta_model {id: 'residue'}) AND \n" +
                "      (gene)-[:typing]->()-[:typing]->(:meta_model {id: 'gene'}) AND \n" +
                "      NOT EXISTS(residue.aa) or residue.aa = []\n " +
                "OPTIONAL MATCH (gene)<-[:edge*0..]-(proxy:{})-[r:edge]->(action:{})\n".format(
                    nugget, nugget) +
                "WHERE (action)-[:typing]->()-[:typing]->(:meta_model {id: 'bnd'}) OR\n" +
                "      (action)-[:typing]->()-[:typing]->(:meta_model {id: 'mod'})\n"
                "DELETE r\n" +
                "WITH gene\n" +
                "OPTIONAL MATCH (gene)<-[:edge*0..]-(proxy:{})<-[:edge]-(state:{})<-[r:edge]-(mod:{})".format(
                    nugget, nugget, nugget) +
                "WHERE (state)-[:typing]->()-[:typing]->(:meta_model {id: 'state'}) AND" +
                "(mod)-[:typing]->()-[:typing]->(:meta_model {id: 'mod'})" +
                "DELETE r"
            )
            kb._hierarchy.execute(query)
            # # Query to remove edge to the action from the actor that contains
            # # a state with the empty test
            # query = (
            #     "MATCH (state:{})-[:edge*1..]->(gene:{})\n".format(nugget, nugget) +
            #     "WHERE (state)-[:typing]->()-[:typing]->(:meta_model {id: 'state'}) AND \n" +
            #     "      (gene)-[:typing]->()-[:typing]->(:meta_model {id: 'gene'} AND \n" +
            #     "      NOT EXISTS(state.test) or state.test = []\n " +
            #     "OPTIONAL MATCH (gene)<-[:edge*0..]-(proxy:{})-[r:edge]->(action:{})\n".format(
            #         nugget, nugget) +
            #     "WHERE (action)-[:typing]->()-[:typing]->(:meta_model {id: 'bnd'}) OR\n" +
            #     "      (action)-[:typing]->()-[:typing]->(:meta_model {id: 'mod'})\n"
            #     "DELETE r\n" +
            #     "OPTIONAL MATCH (gene)<-[:edge*0..]-(proxy:{})<-[:edge]-(state:{})<-[r:edge]-(mod:{})".format(
            #         nugget, nugget, nugget) +
            #     "WHERE (state)-[:typing]->()-[:typing]->(:meta_model {id: 'state'}) AND" +
            #     "(mod)-[:typing]->()-[:typing]->(:meta_model {id: 'mod'})" +
            #     "DELETE r"
            # )
            # kb._hierarchy.execute(query)

            # Remove all the graph components disconected from the action node
            query = (
                "MATCH (n:{}), (m:{})\n".format(
                    nugget, nugget, kb._action_graph_id) +
                "WHERE ((m)-[:typing]->(:{})-[:typing]->({{id: 'bnd'}}) OR \n".format(
                    kb._action_graph_id) +
                "       (m)-[:typing]->(:{})-[:typing]->({{id: 'mod'}})) AND \n".format(
                    kb._action_graph_id) +
                "      NOT (n)-[:edge*1..]-(m) AND n.id <> m.id\n" +
                "DETACH DELETE n"
            )
            kb._hierarchy.execute(query)
