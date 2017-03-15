from flask import Blueprint, Response, request 
import json
from metamodels import (base_metamodel, metamodel_kappa, kami, base_kami)
from exporters import KappaExporter
from webserver_utils import get_command, parse_path
import flex
from flex.loading.schema.paths.path_item.operation.responses.single.schema\
    import schema_validator

import os
import subprocess

base_name = "kappa_base_metamodel"
metamodel_name = "kappa_metamodel"

YAML = os.path.join(os.path.dirname(__file__), 'iRegraph_api.yaml')
json_schema_context = flex.load(YAML)

kami_blueprint = Blueprint("kami_blueprint", __name__)

@kami_blueprint.route("/graph/get_kappa/", methods=["POST"])
@kami_blueprint.route("/graph/get_kappa/<path:path_to_graph>", methods=["POST"])
def get_kappa(path_to_graph=""):
    def get_kappa_aux(command):
        if "names" not in request.json.keys():
            return ("the nugget names object does not contain a field names",
                    404)
        nuggets_names = request.json["names"]
        if command.graph.metamodel_ == kami:
            print("kami")
            command.link_states()
            new_kappa_command = command.to_kappa_like()
            kappa_meta = kami_blueprint.cmd.subCmds[base_name].subCmds[metamodel_name]
            new_kappa_command.parent = kappa_meta
            new_kappa_command.graph.metamodel_ = kappa_meta.graph
            command = new_kappa_command
        if command.graph.metamodel_ != metamodel_kappa:
            return("not a valid action graph", 404)
        for n in nuggets_names:
            if n not in command.subCmds.keys():
                return ("Nugget " + n + " does not exist in action graph: " +
                        path_to_graph, 404)
        if nuggets_names == []:
            nuggets_names = command.subCmds.keys()
        graph_list = [command.subCmds[n].graph for n in nuggets_names]
        nugget_list = [g for g in graph_list 
                       if "exception_nugget" not in g.graph_attr.keys()]
        try:
            (agent_dec, rules, variables_dec) =\
                     KappaExporter.compile_nugget_list(nugget_list)
            json_rep = {}
            json_rep["kappa_code"] = agent_dec+"\n"+variables_dec+"\n"+rules
            resp = Response(response=json.dumps(json_rep),
                            status=200,
                            mimetype="application/json")
            return resp
        except ValueError as e:
            return (str(e), 412)
    return get_command(kami_blueprint.cmd, path_to_graph, get_kappa_aux)


@kami_blueprint.route("/graph/to_metakappa/", methods=["PUT"])
@kami_blueprint.route("/graph/to_metakappa/<path:path_to_graph>",
                      methods=["PUT"])
def to_metakappa(path_to_graph=""):
    def to_metakappa_aux(command):
        new_metamodel_name = request.args.get("new_metamodel_name")
        if not new_metamodel_name:
            return ("the query parameter new_metamodel_name is necessary", 404)
        try:
            command.link_states()
            new_kappa_command = command.to_kappa_like()
            kappa_meta = kami_blueprint.cmd.subCmds[base_name].subCmds[metamodel_name]
            if new_metamodel_name in kappa_meta.subCmds.keys():
                raise KeyError("The new metamodel name already exists")
            kappa_meta.subCmds[new_metamodel_name] = new_kappa_command
            new_kappa_command.parent = kappa_meta
            new_kappa_command.name = new_metamodel_name
            new_kappa_command.graph.metamodel_ = kappa_meta.graph
            return ("translation done", 200)
        except (ValueError, KeyError) as e:
            return (str(e), 412)
    return get_command(kami_blueprint.cmd, path_to_graph, to_metakappa_aux)


@kami_blueprint.route("/graph/link_components/", methods=["PUT"])
@kami_blueprint.route("/graph/link_components/<path:path_to_graph>",
                      methods=["PUT"])
def link_components(path_to_graph=""):
    def link_components_aux(command):
        if command.graph.metamodel_ != kami:
            return("the graph has to be an action graph", 404)
        component1 = request.args.get("component1")
        component2 = request.args.get("component2")
        if not (component1 and component2):
            return("parameters component1 and component2 are necessary", 404)
        try:
            command.link_components(component1, component2)
            return("component linked", 200)
        except (ValueError, KeyError) as e:
            return(str(e), 412)
    return get_command(kami_blueprint.cmd, path_to_graph, link_components_aux)


@kami_blueprint.route("/graph/graph_from_nodes/", methods=["POST"])
@kami_blueprint.route("/graph/graph_from_nodes/<path:path_to_graph>",
                      methods=["POST"])
def graph_from_nodes(path_to_graph=""):
    """create a graph typed by the selected nodes"""
    try:
        (parent_cmd, graph_name) = parse_path(kami_blueprint.cmd, path_to_graph)
    except KeyError as e:
        return ("the path is not valid", 404)
    if graph_name is None:
        return ("the empty path is not valid", 404)
    nodes = request.json
    try:
        schema = schema_validator({'$ref': '#/definitions/NameList'},
                                  context=json_schema_context)
        flex.core.validate(schema, nodes, context=json_schema_context)
    except ValueError as e:
        return(str(e), 404)
    try:
        parent_cmd.new_graph_from_nodes(nodes["names"], graph_name)
        return("graph created successfully", 200)
    except (ValueError, KeyError) as e:
        return (str(e), 404)

# functions used to add the kami metamodels to the hierarchy
def include_kappa_metamodel(server, base_name=base_name,
                            metamodel_name=metamodel_name):
    try:
        server.cmd.new_graph(base_name)
        server.cmd.subCmds[base_name].graph = base_metamodel
        server.cmd.subCmds[base_name].new_graph(metamodel_name)
        server.cmd.subCmds[base_name].subCmds[metamodel_name].graph = metamodel_kappa
    except KeyError as e:
        return (str(e), 404)


def include_kami_metamodel(server, base_name="kami_base",
                           metamodel_name="kami"):
    try:
        server.cmd.new_graph(base_name)
        server.cmd.subCmds[base_name].graph = base_kami
        server.cmd.subCmds[base_name].new_graph(metamodel_name)
        server.cmd.subCmds[base_name].subCmds[metamodel_name].graph = kami
    except KeyError as e:
        return (str(e), 404)