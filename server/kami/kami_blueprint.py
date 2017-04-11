"""handle kami specific requests"""

from flask import Blueprint, Response, request
import json
# from metamodels import (kami, base_kami)
from base.webserver_utils import (apply_on_node_with_parent,
                                  apply_on_node)
import kami.kappa as kappa
from kami.algebra import concat_test, create_compositions
import regraph.library.tree as tree
import flex
import os
from flex.loading.schema.paths.path_item.operation.responses.single.schema\
    import schema_validator


YAML = os.path.join(os.path.dirname(__file__)+"/../", 'iRegraph_api.yaml')
json_schema_context = flex.load(YAML)
kami_blueprint = Blueprint("kami_blueprint", __name__)


@kami_blueprint.route("/graph/get_kappa/", methods=["POST"])
@kami_blueprint.route("/graph/get_kappa/<path:path_to_graph>",
                      methods=["POST"])
def get_kappa(path_to_graph=""):
    def get_kappa_aux(graph_id, parent_id):
        hie = kami_blueprint.hie()
        if "names" not in request.json.keys():
            nuggets_ids = []
        else:
            nuggets_names = request.json["names"]
            nuggets_ids = [tree.child_from_name(kami_blueprint.hie(),
                                                graph_id, name)
                           for name in nuggets_names]

        if ("compositions" in request.json.keys() and
                request.json["compositions"] != []):
            compositions = request.json["compositions"]
            comp_ids = create_compositions(hie, compositions, graph_id)
            nuggets_ids += comp_ids
        else:
            comp_ids = []

        # likely to change in the future
        if parent_id != "kami":
            raise ValueError("the action graph must be typed by kami")

        kappa_code = kappa.to_kappa(kami_blueprint.hie(), graph_id, parent_id,
                                    nuggets_ids)
        # kappa_code = ""
        json_rep = {}
        json_rep["kappa_code"] = kappa_code

        # for comp in comp_ids:
        #     hie.remove_graph(comp)

        resp = Response(response=json.dumps(json_rep),
                        status=200,
                        mimetype="application/json")
        return resp
    return apply_on_node_with_parent(kami_blueprint.hie(), kami_blueprint.top,
                                     path_to_graph, get_kappa_aux)


@kami_blueprint.route("/graph/splices/", methods=["POST"])
@kami_blueprint.route("/graph/splices/<path:path_to_graph>",
                      methods=["POST"])
def make_splices(path_to_graph=""):
    def make_splices_aux(graph_id, parent_id):
        if "names" not in request.json.keys():
            splices_id = []
        else:
            splices_names = request.json["names"]
            splices_id = [tree.child_from_name(kami_blueprint.hie(),
                                               graph_id, name)
                          for name in splices_names]

        # likely to change in the future
        if parent_id != "kami":
            raise ValueError("the action graph must be typed by kami")

        kappa.compose_splices(kami_blueprint.hie(), graph_id, parent_id,
                              splices_id)
        return ("rule_created", 200)

    return apply_on_node_with_parent(kami_blueprint.hie(), kami_blueprint.top,
                                     path_to_graph, make_splices_aux)


@kami_blueprint.route("/graph/testconcat/", methods=["POST"])
@kami_blueprint.route("/graph/testconcat/<path:path_to_graph>",
                      methods=["POST"])
def testconcat(path_to_graph=""):
    def testconcat_aux(graph_id, parent_id):
        if "names" not in request.json.keys():
            splices_id = []
        else:
            hie = kami_blueprint.hie()
            splices_names = request.json["names"]
            splices_id = [tree.child_from_name(hie,
                                               graph_id, name)
                          for name in splices_names]
            pat1 = [id for id in splices_id if id.startswith("1")]
            pat2 = [id for id in splices_id if id.startswith("2")]
            g1 = hie.node[pat1[0]].graph
            g2 = hie.node[pat2[0]].graph
            pats = concat_test(g1, g2)
            for pat in pats:
                hie.add_graph(pat.name, pat.graph, {"name": pat.name})
                hie.add_typing(pat.name, "/", {})
        return ("concat_created", 200)
    return apply_on_node_with_parent(kami_blueprint.hie(), kami_blueprint.top,
                                     path_to_graph, testconcat_aux)


@kami_blueprint.route("/getparts/", methods=["GET"])
@kami_blueprint.route("/getparts/<path:path_to_graph>",
                      methods=["GET"])
def get_parts(path_to_graph=""):
    hie = kami_blueprint.hie()

    def get_parts_aux(graph_id):
        nuggets = [hie.node[child].attrs["name"]
                   for child in tree.graph_children(hie, graph_id)]
        graph_attrs = hie.node[graph_id].attrs
        if "compositions" in graph_attrs.keys():
            compositions = graph_attrs["compositions"]
        else:
            compositions = []
        json_data = {"nuggets": nuggets,
                     "compositions": compositions}
        resp = Response(response=json.dumps(json_data),
                        status=200,
                        mimetype="application/json")
        return resp

    return apply_on_node(hie, kami_blueprint.top,
                         path_to_graph, get_parts_aux)


@kami_blueprint.route("/gettypes/", methods=["GET"])
@kami_blueprint.route("/gettypes/<path:path_to_graph>",
                      methods=["GET"])
def get_types(path_to_graph=""):
    hie = kami_blueprint.hie()

    def get_types_aux(graph_id):
        node_id = request.args.get("nodeId")
        ancestors = hie.get_ancestors(graph_id)
        json_data = {}
        for (anc, typ) in ancestors.items():
            if node_id in typ.keys():
                json_data[anc] = typ[node_id]
            else:
                json_data[anc] = None

        resp = Response(response=json.dumps(json_data),
                        status=200,
                        mimetype="application/json")
        return resp

    return apply_on_node(hie, kami_blueprint.top,
                         path_to_graph, get_types_aux)


@kami_blueprint.route("/graph/link_components/", methods=["PUT"])
@kami_blueprint.route("/graph/link_components/<path:path_to_graph>",
                      methods=["PUT"])
def link_components(path_to_graph=""):
    def link_components_aux(graph_id):
        component1 = request.args.get("component1")
        component2 = request.args.get("component2")
        if not (component1 and component2):
            return("parameters component1 and component2 are necessary", 404)
        try:
            kappa.link_components(kami_blueprint.hie(), graph_id, component1,
                                  component2)
            return("component linked", 200)
        except (ValueError, KeyError) as e:
            return(str(e), 412)
    return apply_on_node(kami_blueprint.hie(), kami_blueprint.top,
                         path_to_graph, link_components_aux)
