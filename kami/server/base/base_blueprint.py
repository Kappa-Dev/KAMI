"""Handlers for base functionalities of webserver"""

from flask import (Blueprint, Response, request, send_from_directory,
                   redirect, url_for, render_template)
from flex.loading.schema.paths.path_item.operation.responses.single.schema\
    import schema_validator
from base.webserver_utils import (apply_on_node, apply_on_parent, empty_path,
                                  apply_on_node_with_parent)
import json
import flex
# from metamodels import (base_metamodel, metamodel_kappa, kami, base_kami)
# from exporters import KappaExporter
import os
import subprocess

import regraph.tree as tree
from regraph.primitives import graph_to_json, relabel_node

GUI_FOLDER = os.path.join(os.path.dirname(__file__), '../../client/')
YAML = os.path.join(os.path.dirname(__file__), '../iRegraph_api.yaml')
json_schema_context = flex.load(YAML)


# the app blueprint handles the generic regraph requests
app = Blueprint("app", __name__, template_folder=GUI_FOLDER)

# @app.route("/hierarchy/", methods=["POST"])
# @app.route("/hierarchy/<path:path_to_graph>", methods=["POST"])
# def import_sub_hierachy(path_to_graph=""):
#     try:
#         (parent_cmd, graph_name) = parse_path(app.cmd,path_to_graph)
#     except KeyError as e:
#         return("the path is not valid", 404)
#     if graph_name is None:
#         return("the empty path is not valid", 404)
#     sub_hierarchy = request.json
#     try:
#         schema = schema_validator({'$ref': '#/definitions/GraphHierarchy'},
#                                   context=json_schema_context)
#         flex.core.validate(schema, sub_hierarchy, context=json_schema_context)
#     except ValueError as e:
#         return(str(e), 404)
#     top_graph_name = sub_hierarchy["name"]
#     if top_graph_name != graph_name:
#         return("the name of the top graph must be the same as the url", 404)
#     try:
#         parent_cmd.add_subHierarchy(sub_hierarchy)
#         return("Hierarchy added successfully", 200)
#     except (ValueError, KeyError) as e:
#         return (str(e), 404)


@app.route("/hierarchy/", methods=["GET"])
@app.route("/hierarchy/<path:path_to_graph>", methods=["GET"])
def get_hierarchy(path_to_graph=""):
    include_rules = request.args.get("rules") == "true"
    include_graphs = request.args.get("include_graphs") == "true"
    depth_bound = request.args.get("depth_bound")
    if depth_bound:
        try:
            depth_bound = int(depth_bound)
        except ValueError:
            return ("depth_bound is not an integer", 404)
    else:
        depth_bound = None

    return get_graph_hierarchy(path_to_graph, include_graphs,
                               include_rules, depth_bound)


# TODO : garbage collect ?
@app.route("/hierarchy/", methods=["DELETE"])
@app.route("/hierarchy/<path:path_to_graph>", methods=["DELETE"])
def delete_hierarchy(path_to_graph=""):
    if empty_path(path_to_graph):
        return ("cannot delete top graph", 404)

    def callback(graph_id):
        app.hie().remove_graph(graph_id, reconnect=False)
        return ("graph removed", 200)
    return apply_on_node(app.hie(), app.top, path_to_graph, callback)


@app.route("/rule/", methods=["DELETE"])
@app.route("/rule/<path:path_to_graph>/", methods=["DELETE"])
def delete_rule(path_to_graph=""):
    return delete_hierarchy(path_to_graph)


@app.route("/graph/", methods=["GET"])
@app.route("/graph/<path:path_to_graph>", methods=["GET"])
def dispatch_get_graph(path_to_graph=""):
    return get_typed_graph(path_to_graph)


def get_untyped_graph(path_to_graph):
    if empty_path(path_to_graph):
        return ("top level does not have a graph", 404)

    def callback(graph_id):
        json_rep = json.dumps(graph_to_json(app.hie().node[graph_id].graph))
        resp = Response(response=json_rep,
                        status=200,
                        mimetype="application/json")
        return resp

    return apply_on_node(app.hie(), app.top, path_to_graph, callback)


def get_typed_graph(path_to_graph):
    if empty_path(path_to_graph):
        return ("top level does not have a graph", 404)

    def callback(graph_id, parent_id):
        json_rep = json.dumps(tree.typed_graph_to_json(app.hie(), graph_id,
                                                       parent_id))
        resp = Response(response=json_rep,
                        status=200,
                        mimetype="application/json")
        return resp

    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, callback)


def get_graph_hierarchy(path, include_graphs, include_rules, depth_bound):
    def get_status():
        if include_rules:
            if include_graphs:
                return 213
            else:
                return 212
        else:
            if include_graphs:
                return 210
            else:
                return 211

    def callback(node_id, parent_id):
        json_rep = json.dumps(tree.to_json_tree(app.hie(), node_id, parent_id,
                                                include_rules, include_graphs,
                                                depth_bound))
        resp = Response(
            response=json_rep,
            status=get_status(),
            mimetype="application/json")
        return resp

    return apply_on_node_with_parent(app.hie(), app.top, path, callback)


@app.route("/rule/", methods=["POST"])
@app.route("/rule/<path:path_to_graph>", methods=["POST"])
def create_rule(path_to_graph=""):
    pattern_name = request.args.get("pattern_name")

    def callback(parent_id, name):
        tree.new_rule(app.hie(), parent_id, name, pattern_name)
        return("rule created", 200)

    return apply_on_parent(app.hie(), app.top, path_to_graph, callback)


# TODO
@app.route("/rule/", methods=["GET"])
@app.route("/rule/<path:path_to_graph>", methods=["GET"])
def get_rule(path_to_graph=""):
    def callback(rule_id, parent_id):
        json_rep = json.dumps(tree.typed_rule_to_json(app.hie(), rule_id,
                                                      parent_id))
        resp = Response(
            response=json_rep,
            status=200,
            mimetype="application/json")
        return resp
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph,
                                     callback)


@app.route("/graph/", methods=["POST"])
@app.route("/graph/<path:path_to_graph>", methods=["POST"])
def create_graph(path_to_graph=""):
    def callback(parent_id, name):
        tree.new_graph(app.hie(), parent_id, name)
        return ("graph added", 200)
    return apply_on_parent(app.hie(), app.top, path_to_graph, callback)


# TODO
# @app.route("/graph/matchings/", methods=["GET"])
# @app.route("/graph/matchings/<path:path_to_graph>", methods=["GET"])
# def get_matchings(path_to_graph=""):
#     try:
#         (parent_cmd, graph_name) = parse_path(app.cmd, path_to_graph)
#         if graph_name is None:
#             return("the empty path does not contain a top graph", 404)
#         rule_name = request.args.get("rule_name")
#         if not rule_name:
#             return("the rule_name argument is missing", 404)
#         if rule_name not in parent_cmd.subRules.keys():
#             return("the rule does not exists", 404)
#         if graph_name not in parent_cmd.subCmds.keys():
#             return("the graph does not exists", 404)

#         resp = Response(
#                  response=json.dumps(parent_cmd.get_matchings(rule_name,
#                                                               graph_name)),
#                  status=200,
#                  mimetype="application/json")
#         return resp
#     except KeyError as e:
#         return Response(response="graph not found : " + str(e), status=404)


# TODO
# @app.route("/graph/apply/", methods=["POST"])
# @app.route("/graph/apply/<path:path_to_graph>", methods=["POST"])
# def apply_rule(path_to_graph=""):
#     rule_name = request.args.get("rule_name")
#     target_graph = request.args.get("target_graph")
#     try:
#         matching = {d["left"]: d["right"] for d in request.json}
#     except KeyError as e:
#         return("the matching argument is necessary", 404)
#     if not (rule_name and target_graph):
#         return("the rule_name and target_graph arguments are necessary", 404)
#     try:
#         (parent_cmd, new_name) = parse_path(app.cmd, path_to_graph)
#         if not parent_cmd.valid_new_name(new_name):
#             return("Graph or rule already exists with this name", 409)
#         elif rule_name not in parent_cmd.subRules.keys():
#             return("The rule does not exist", 409)
#         elif target_graph not in parent_cmd.subCmds.keys():
#             return("The target_graph does not exist", 409)
#         else:
#             parent_cmd._do_apply_rule_no_catching(
#                 rule_name, target_graph, new_name, matching)
#             return("new graph created", 200)

#     except (KeyError, ValueError) as e:
#         return(str(e), 404)

@app.route("/graph/add_node/", methods=["PUT"])
@app.route("/graph/add_node/<path:path_to_graph>", methods=["PUT"])
def add_node_graph(path_to_graph=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, add_node)


@app.route("/graph/rename_node/", methods=["PUT"])
@app.route("/graph/rename_node/<path:path_to_graph>", methods=["PUT"])
def rename_node_graph(path_to_graph=""):
    return apply_on_node(app.hie(), app.top, path_to_graph, rename_node)


@app.route("/graph/add_edge/", methods=["PUT"])
@app.route("/graph/add_edge/<path:path_to_graph>", methods=["PUT"])
def add_edge_graph(path_to_graph=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, add_edge)


@app.route("/graph/rm_node/", methods=["PUT"])
@app.route("/graph/rm_node/<path:path_to_graph>", methods=["PUT"])
def rm_node_graph(path_to_graph=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, rm_node)


@app.route("/graph/merge_node/", methods=["PUT"])
@app.route("/graph/merge_node/<path:path_to_graph>", methods=["PUT"])
def merge_node_graph(path_to_graph=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, merge_nodes)

@app.route("/graph/clone_node/", methods=["PUT"])
@app.route("/graph/clone_node/<path:path_to_graph>", methods=["PUT"])
def clone_node_graph(path_to_graph=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, clone_node)

@app.route("/graph/rm_edge/", methods=["PUT"])
@app.route("/graph/rm_edge/<path:path_to_graph>", methods=["PUT"])
def rm_edge_graph(path_to_graph=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, rm_edge)


@app.route("/graph/add_attr/", methods=["PUT"])
@app.route("/graph/add_attr/<path:path_to_graph>", methods=["PUT"])
def add_attr_graph(path_to_graph=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, add_attr)


# @app.route("/graph/update_attr/", methods=["PUT"])
# @app.route("/graph/update_attr/<path:path_to_graph>", methods=["PUT"])
# def update_attr_graph(path_to_graph=""):
#     return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, update_attr)


@app.route("/graph/rm_attr/", methods=["PUT"])
@app.route("/graph/rm_attr/<path:path_to_graph>", methods=["PUT"])
def rm_attr_graph(path_to_graph=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, remove_attr)


# @app.route("/graph/add_edge_attr/", methods=["PUT"])
# @app.route("/graph/add_edge_attr/<path:path_to_graph>", methods=["PUT"])
# def add_edge_attr_graph(path_to_graph=""):
#     return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, add_edge_attr)


# @app.route("/graph/update_edge_attr/", methods=["PUT"])
# @app.route("/graph/update_edge_attr/<path:path_to_graph>", methods=["PUT"])
# def update_edge_attr_graph(path_to_graph=""):
#     return apply_on_node(app.hie(), app.top, path_to_graph, update_edge_attr)


# @app.route("/graph/rm_edge_attr/", methods=["PUT"])
# @app.route("/graph/rm_edge_attr/<path:path_to_graph>", methods=["PUT"])
# def rm_edge_attr_graph(path_to_graph=""):
#     return apply_on_node(app.hie(), app.top, path_to_graph, remove_edge_attr)


@app.route("/rule/add_node/", methods=["PUT"])
@app.route("/rule/add_node/<path:path_to_rule>", methods=["PUT"])
def add_node_rule(path_to_rule=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule, add_node)


@app.route("/rule/add_edge/", methods=["PUT"])
@app.route("/rule/add_edge/<path:path_to_rule>", methods=["PUT"])
def add_edge_rule(path_to_rule=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule, add_edge)


@app.route("/rule/rm_node/", methods=["PUT"])
@app.route("/rule/rm_node/<path:path_to_rule>", methods=["PUT"])
def rm_node_rule(path_to_rule=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule, rm_node)


@app.route("/rule/merge_node/", methods=["PUT"])
@app.route("/rule/merge_node/<path:path_to_rule>", methods=["PUT"])
def merge_node_rule(path_to_rule=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule, merge_nodes)


@app.route("/rule/clone_node/", methods=["PUT"])
@app.route("/rule/clone_node/<path:path_to_rule>", methods=["PUT"])
def clone_node_rule(path_to_rule=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule, clone_node)


@app.route("/rule/rm_edge/", methods=["PUT"])
@app.route("/rule/rm_edge/<path:path_to_rule>", methods=["PUT"])
def rm_edge_rule(path_to_rule=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule, rm_edge)


@app.route("/rule/add_attr/", methods=["PUT"])
@app.route("/rule/add_attr/<path:path_to_rule>", methods=["PUT"])
def add_attr_rule(path_to_rule=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule, add_attr)


@app.route("/rule/rm_attr/", methods=["PUT"])
@app.route("/rule/rm_attr/<path:path_to_rule>", methods=["PUT"])
def rm_attr_rule(path_to_rule=""):
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule, remove_attr)


def add_node(graph_id, parent_id):
    node_id = request.args.get("node_id")
    if not node_id:
        return ("the node_id argument is necessary", 404)
    node_type = request.args.get("node_type")
    if node_type == "" or node_type == "notype":
        node_type = None
    tree.add_node(app.hie(), graph_id, parent_id, node_id, node_type)
    return("node added", 200)


def rename_node(graph_id):
    node_id = request.args.get("node_id")
    if not node_id:
        return("the node_id argument is necessary", 412)
    new_name = request.args.get("new_name")
    if not new_name:
        return("the new_name argument is necessary", 412)
    app.hie().rename_node(graph_id, node_id, new_name)
    return ("node name modified", 200)


def modify_attr(f):
    node_id = request.args.get("node_id")
    if not node_id:
        return("the node_id argument is necessary", 412)
    attributes = request.json
    f(node_id, attributes)
    return("attributes modified", 200)


def update_attr(graph_id, parent_id):
    return ("TODO ?", 404)


def remove_attr(graph_id, parent_id):
    def callback(node_id, attributes):
        tree.remove_attributes(app.hie(), graph_id, parent_id, node_id,
                               attributes)
    return modify_attr(callback)


def add_attr(graph_id, parent_id):
    def callback(node_id, attributes):
        tree.add_attributes(app.hie(), graph_id, parent_id, node_id, attributes)
    return modify_attr(callback)


# TODO ?
def modify_edge_attr(f):
    source = request.args.get("source")
    target = request.args.get("target")
    if not (source and target):
        return "the source and target arguments are necessary"
    try:
        attributes = request.json
        f(source, target, attributes)
        return("attributes modified", 200)
    except ValueError as e:
        return("error: " + str(e), 412)


# TODO ?
def update_edge_attr(command):
    return modify_edge_attr(command.graph.update_edge_attrs)


# TODO ?
def update_edge_attr(command):
    return modify_edge_attr(command.main_graph().remove_edge_attrs)


# TODO ?
def add_edge_attr(command):
    return modify_edge_attr(command.main_graph().add_edge_attrs)


def add_edge(graph_id, parent_id):
    source_node = request.args.get("source_node")
    target_node = request.args.get("target_node")
    if not (source_node and target_node):
        return("The source_node and target_node arguments are necessary", 412)
    tree.add_edge(app.hie(), graph_id, parent_id, source_node, target_node)
    return("edge added", 200)


def rm_node(graph_id, parent_id):
    node_id = request.args.get("node_id")
    force_flag = request.args.get("force") == "true"
    if not node_id:
        return ("the node_id argument is necessary", 404)
    tree.rm_node(app.hie(), graph_id, parent_id, node_id, force=force_flag)
    return("node deleted", 200)


def merge_nodes(graph_id, parent_id):
    node1 = request.args.get("node1")
    node2 = request.args.get("node2")
    new_node_id = request.args.get("new_node_id")
    if not (node1 and node2 and new_node_id):
        return("the arguments node1, node2 and new_node_id are necessary", 412)
    if node1 == node2:
        return("You cannot merge a node with it self", 412)
    # force_flag = request.args.get("force") == "true"
    tree.merge_nodes(app.hie(), graph_id, parent_id, node1, node2, new_node_id)
    return("nodes merged", 200)


def clone_node(graph_id, parent_id):
    node_id = request.args.get("node_id")
    new_node_id = request.args.get("new_node_id")
    if not (node_id and new_node_id):
        return("the node_id and new_node_id arguments are necessary", 412)
    tree.clone_node(app.hie(), graph_id, parent_id, node_id, new_node_id)
    return("node cloned", 200)


def rm_edge(graph_id, parent_id):
    source_node = request.args.get("source_node")
    target_node = request.args.get("target_node")
    if not (source_node and target_node):
        return("The source_node and target_node arguments are necessary", 412)
    tree.rm_edge(app.hie(), graph_id, parent_id, source_node, target_node)
    return("Edge removed", 200)


# @app.route("/graph/add_constraint/", methods=["PUT"])
# @app.route("/graph/add_constraint/<path:path_to_graph>", methods=["PUT"])
# def add_constraint(path_to_graph=""):
#     input_or_output = request.args.get("input_or_output")
#     node_id = request.args.get("node_id")
#     constraint_node = request.args.get("constraint_node")
#     le_or_ge = request.args.get("le_or_ge")
#     bound = request.args.get("bound")
#     if not (input_or_output and node_id and
#             constraint_node and le_or_ge and bound):
#         return("argument missing", 404)
#     try:
#         int_bound = int(bound)
#     except ValueError:
#         return("could not convert bound to integer", 404)

#     if le_or_ge == "le":
#         def condition(x):
#             return x <= int_bound
#         viewableCondition = constraint_node + " <= " + bound
#     elif le_or_ge == "ge":
#         def condition(x):
#             return x >= int_bound
#         viewableCondition = constraint_node + " >= " + bound
#     else:
#         return ("uncorrect value for argument ge_or_le", 404)

#     if input_or_output == "input":
#         def add_constraint_to(command):
#             try:
#                 command.add_input_constraint(
#                     node_id, constraint_node, condition, viewableCondition)
#                 return ("constraint added", 200)
#             except ValueError as e:
#                 return(str(e), 412)
#     elif input_or_output == "output":
#         def add_constraint_to(command):
#             try:
#                 command.addOutputConstraint(
#                     node_id, constraint_node, condition, viewableCondition)
#                 return("constraint added", 200)
#             except ValueError as e:
#                 return (str(e), 412)
#     else:
#         return ("uncorrect value for argument input_or_output", 404)

#     return(get_command(app.cmd, path_to_graph, add_constraint_to))


# @app.route("/graph/delete_constraint/", methods=["PUT"])
# @app.route("/graph/delete_constraint/<path:path_to_graph>", methods=["PUT"])
# def delete_constraint(path_to_graph=""):
#     input_or_output = request.args.get("input_or_output")
#     node_id = request.args.get("node_id")
#     constraint_node = request.args.get("constraint_node")
#     le_or_ge = request.args.get("le_or_ge")
#     bound = request.args.get("bound")
#     if not (input_or_output and node_id and
#             constraint_node and le_or_ge and bound):
#         return("argument missing", 404)
#     try:
#         int_bound = int(bound)
#     except ValueError:
#         return("could not convert bound to integer", 404)

#     if le_or_ge == "le":
#         viewableCondition = constraint_node + " <= " + bound
#     elif le_or_ge == "ge":
#         viewableCondition = constraint_node + " >= " + bound
#     else:
#         return ("uncorrect value for argument ge_or_le", 404)

#     if input_or_output == "input":
#         def delete_constraint_to(command):
#             try:
#                 command.delete_input_constraint(node_id, viewableCondition)
#                 return ("constraint deleted", 200)
#             except ValueError as e:
#                 return(str(e), 412)
#     elif input_or_output == "output":
#         def delete_constraint_to(command):
#             try:
#                 command.delete_output_constraint(node_id, viewableCondition)
#                 return("constraint deleted", 200)
#             except ValueError as e:
#                 return (str(e), 412)
#     else:
#         return ("uncorrect value for argument input_or_output", 404)

#     return(get_command(app.cmd, path_to_graph, delete_constraint_to))


# @app.route("/graph/validate_constraints/", methods=["PUT"])
# @app.route("/graph/validate_constraints/<path:path_to_graph>", methods=["PUT"])
# def validate_constraint(path_to_graph=""):
#     def check_constraint(command):
#         wrong_nodes = command.graph.checkConstraints()
#         if wrong_nodes:
#             return (json.dumps(wrong_nodes), 412)
#         else:
#             return("graph validated", 200)
#     return(get_command(app.cmd, path_to_graph, check_constraint))


@app.route("/graph/rename_graph/", methods=["PUT"])
@app.route("/graph/rename_graph/<path:path_to_graph>", methods=["PUT"])
def rename_graph(path_to_graph=""):
    return rename(path_to_graph)


@app.route("/rule/rename_rule/", methods=["PUT"])
@app.route("/rule/rename_rule/<path:path_to_graph>", methods=["PUT"])
def rename_rule(path_to_graph=""):
    return rename(path_to_graph)


def rename(path_to_graph):
    new_name = request.args.get("new_name")
    if not new_name:
        return ("The new_name argument is necessary", 404)

    def callback(graph_id ,parent_id):
        tree.rename_child(app.hie(), graph_id, parent_id, new_name)
        return ("rule renamed", 200)

    return apply_on_node_with_parent(app.hie(), app.top, path_to_graph, callback)

# @app.route("/graph/get_kappa/", methods=["POST"])
# @app.route("/graph/get_kappa/<path:path_to_graph>", methods=["POST"])
# def get_kappa(path_to_graph=""):
#     def get_kappa_aux(command):
#         if "names" not in request.json.keys():
#             return ("the nugget names object does not contain a field names",
#                     404)
#         nuggets_names = request.json["names"]
#         if command.graph.metamodel_ == kami:
#             command.link_states()
#             new_kappa_command = command.to_kappa_like()
#             kappa_meta = app.cmd.subCmds[base_name].subCmds[metamodel_name]
#             new_kappa_command.parent = kappa_meta
#             # new_kappa_command.name = new_metamodel_name
#             new_kappa_command.graph.metamodel_ = kappa_meta.graph
#             command = new_kappa_command
#         if command.graph.metamodel_ != metamodel_kappa:
#             return("not a valid action graph", 404)
#         # app.cmd.subCmds[base_name].subCmds[metamodel_name].graph = metamodel_kappa
#         for n in nuggets_names:
#             if n not in command.subCmds.keys():
#                 return ("Nugget " + n + " does not exist in action graph: " +
#                         path_to_graph, 404)
#         if nuggets_names == []:
#             nuggets_names = command.subCmds.keys()
#         graph_list = [command.subCmds[n].graph for n in nuggets_names]
#         nugget_list = [g for g in graph_list 
#                        if "exception_nugget" not in g.graph_attr.keys()]
#         try:
#             (agent_dec, rules, variables_dec) =\
#                      KappaExporter.compile_nugget_list(nugget_list)
#             json_rep = {}
#             json_rep["kappa_code"] = agent_dec+"\n"+variables_dec+"\n"+rules
#             # json_rep["agent_decl"] = agent_dec
#             # json_rep["rules"] = rules
#             # json_rep["variable_decl"] = variables_dec
#             resp = Response(response=json.dumps(json_rep),
#                             status=200,
#                             mimetype="application/json")
#             return (resp)
#         except ValueError as e:
#             return (str(e), 412)
#     return get_command(app.cmd, path_to_graph, get_kappa_aux)


@app.route("/version/", methods=["GET"])
def get_version():
    commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"])
    return("https://github.com/Kappa-Dev/ReGraph/commit/"+commit_hash.decode(), 200)


@app.route("/favicon.ico", methods=["GET"])
def get_icon():

    return send_from_directory(GUI_FOLDER, "favicon.ico")


@app.route("/", methods=["GET"])
def goto_gui():
    return redirect(url_for("app.get_gui"))


@app.route("/guidark/index.js", methods=["GET"])
@app.route("/gui/index.js", methods=["GET"])
def get_index():
    return render_template("index.js", server_url=request.url_root[:-1])


@app.route("/guidark/index2.js", methods=["GET"])
@app.route("/gui/index2.js", methods=["GET"])
def get_index2():
    return render_template("index2.js", server_url=request.url_root[:-1])


@app.route("/gui/kr.css", methods=["GET"])
def get_kr():
    resp = Response(response=render_template("kr.css",
                                             css_defs="def_light.css"),
                    status=200,
                    mimetype="text/css")
    return resp


@app.route("/guidark/kr.css", methods=["GET"])
def get_dark_kr():
    resp = Response(response=render_template("kr.css",
                                             css_defs="def_dark.css"),
                    status=200,
                    mimetype="text/css")
    return resp


@app.route("/guidark/", methods=["GET"])
@app.route("/guidark/<path:path>", methods=["GET"])
@app.route("/gui/", methods=["GET"])
@app.route("/gui/<path:path>", methods=["GET"])
def get_gui(path="index.html"):
    return send_from_directory(GUI_FOLDER, path)


@app.route("/fonts/<path:path>", methods=["GET"])
def get_font(path=""):
    return send_from_directory(GUI_FOLDER, path)


@app.route("/graph/get_graph_attr/", methods=["GET"])
@app.route("/graph/get_graph_attr/<path:path_to_graph>", methods=["GET"])
def get_graph_attr(path_to_graph=""):
    def get_graph_attr_aux(graph_id):
        resp = Response(response=json.dumps(app.hie().node[graph_id].attrs),
                        status=200,
                        mimetype="application/json")
        return resp
    return apply_on_node(app.hie(), app.top, path_to_graph, get_graph_attr_aux)


@app.route("/graph/update_graph_attr/", methods=["PUT"])
@app.route("/graph/update_graph_attr/<path:path_to_graph>", methods=["PUT"])
def update_graph_attr(path_to_graph=""):
    def update_graph_attr_aux(graph_id):
        if not isinstance(request.json, dict):
            return("the body must be a json object", 404)
        tree.recursive_merge(app.hie().node[graph_id].attrs, request.json)
        return ("merge successful", 200)
    return apply_on_node(app.hie(), app.top, path_to_graph, update_graph_attr_aux)


@app.route("/graph/delete_graph_attr/", methods=["PUT"])
@app.route("/graph/delete_graph_attr/<path:path_to_graph>", methods=["PUT"])
def delete_graph_attr(path_to_graph=""):
    def delete_graph_attr_aux(graph_id):
        if not isinstance(request.json, list):
            return("the body must be a list of keys", 412)
        if request.json == []:
            return("the body must not be the empty list", 412)
        keypath = list(request.json)
        current_dict = app.hie().node[graph_id].attrs
        while len(keypath) > 1:
            k = keypath.pop(0)
            if k in current_dict.keys() and isinstance(current_dict[k], dict):
                current_dict = current_dict[k]
            else:
                return("the key "+str(k) +
                       " does not correspond to a dictionnary", 412)
        if keypath[0] in current_dict:
            del current_dict[keypath[0]]
        return ("deletion successful", 200)
    return apply_on_node(app.hie(), app.top, path_to_graph,
                         delete_graph_attr_aux)


# @app.route("/graph/unfold/", methods=["PUT"])
# @app.route("/graph/unfold/<path:path_to_graph>", methods=["PUT"])
# def unfold_nuggets(path_to_graph=""):
#     def unfold_nuggets_aux(command):
#         new_metamodel_name = request.args.get("new_metamodel_name")
#         if not new_metamodel_name:
#             return("the query parameter new_metamodel_name is necessary", 404)
#         if not isinstance(request.json, list):
#             return("the body must be a list of subgraphs", 412)
#         if request.json == []:
#             return("the body must not be the empty list", 412)
#         nuggets = list(request.json)
#         try:
#             command.unfold_abstract_nuggets(new_metamodel_name, nuggets)
#             return("unfolding done", 200)
#         except (ValueError, KeyError) as e:
#             return(str(e), 412)
#     return get_command(app.cmd, path_to_graph, unfold_nuggets_aux)


@app.route("/graph/get_children/", methods=["GET"])
@app.route("/graph/get_children/<path:path_to_graph>", methods=["GET"])
def get_children(path_to_graph=""):
    def get_children_aux(graph_id):
        node_id = request.args.get("node_id")
        if not node_id:
            return("the query parameter node_id is necessary", 404)
        nugget_list = tree.get_children_by_node(app.hie(), graph_id, node_id)
        resp = Response(response=json.dumps({"children": nugget_list}),
                        status=200,
                        mimetype="application/json")
        return resp
    return apply_on_node(app.hie(), app.top, path_to_graph, get_children_aux)


@app.route("/graph/merge_graphs/", methods=["POST"])
@app.route("/graph/merge_graphs/<path:path_to_graph>", methods=["POST"])
def merge_graphs(path_to_graph=""):
    def merge_graphs_aux(parent_id, graph_name):
        graph1 = request.args.get("graph1")
        if not graph1:
            return "argument graph1 is required"
        graph2 = request.args.get("graph2")
        if not graph2:
            return "argument graph2 is required"
        relation = request.json
        try:
            schema = schema_validator({'$ref': '#/definitions/Matching'},
                                      context=json_schema_context)
            flex.core.validate(schema, relation, context=json_schema_context)
            rel = [(c["left"], c["right"]) for c in relation]
        except ValueError as e:
            return(str(e), 404)
        tree.merge_graphs(app.hie(), parent_id, graph1, graph2, rel, graph_name)
        return("graphs merged successfully", 200)
    return apply_on_parent(app.hie(), app.top, path_to_graph, merge_graphs_aux)


@app.route("/graph/graph_from_nodes/", methods=["POST"])
@app.route("/graph/graph_from_nodes/<path:path_to_graph>",
           methods=["POST"])
def graph_from_nodes(path_to_graph=""):
    """create a graph typed by the selected nodes"""
    nodes = request.json
    try:
        schema = schema_validator({'$ref': '#/definitions/NameList'},
                                  context=json_schema_context)
        flex.core.validate(schema, nodes, context=json_schema_context)
    except ValueError as e:
        return(str(e), 404)

    def callback(parent_id, name):
        tree.new_graph_from_nodes(app.hie(), nodes["names"], parent_id, name)
        return("graph created successfully", 200)

    return apply_on_parent(app.hie(), app.top, path_to_graph, callback)


@app.route("/rule/child_rule_from_nodes/", methods=["POST"])
@app.route("/rule/child_rule_from_nodes/<path:path_to_rule>",
           methods=["POST"])
def child_rule_from_nodes(path_to_rule=""):
    """create a graph typed by the selected nodes"""
    nodes = request.json
    try:
        schema = schema_validator({'$ref': '#/definitions/NameList'},
                                  context=json_schema_context)
        flex.core.validate(schema, nodes, context=json_schema_context)
    except ValueError as e:
        return(str(e), 404)

    def callback(parent_id, name):
        tree.child_rule_from_nodes(app.hie(), nodes["names"], parent_id,
                                   name)
        return("rule created successfully", 200)

    return apply_on_parent(app.hie(), app.top, path_to_rule, callback)


@app.route("/rule/apply_on_parent/", methods=["POST"])
@app.route("/rule/apply_on_parent/<path:path_to_rule>", methods=["POST"])
def apply_rule_on_parent(path_to_rule=""):
    def apply_rule_on_parent_aux(graph_id, parent_id):
        suffix = request.args.get("suffix")
        if not suffix:
            suffix = "new"
        tree.rewrite_parent(app.hie(), graph_id, parent_id, suffix)
        return ("graph rewritten", 200)
    return apply_on_node_with_parent(app.hie(), app.top, path_to_rule,
                                     apply_rule_on_parent_aux)


@app.route("/rule/get_typing/", methods=["GET"])
@app.route("/rule/get_typing/<path:path_to_rule>", methods=["GET"])
def get_rule_typing(path_to_rule=""):
    def get_rule_typing_aux(graph_id):
        parent_path = request.args.get("parent")
        if not parent_path:
            return("the query parameter parent is necessary", 404)
        mappings = tree.ancestors_rule_mapping(app.hie(), app.top, graph_id,
                                               parent_path)
        resp = Response(response=json.dumps(mappings),
                        status=200,
                        mimetype="application/json")
        return resp
    return apply_on_node(app.hie(), app.top, path_to_rule, get_rule_typing_aux)


@app.route("/graph/get_typing/", methods=["GET"])
@app.route("/graph/get_typing/<path:path_to_rule>", methods=["GET"])
def get_graph_typing(path_to_rule=""):
    def get_graph_typing_aux(graph_id):
        parent_path = request.args.get("parent")
        if not parent_path:
            return("the query parameter parent is necessary", 404)
        mapping = tree.ancestors_graph_mapping(app.hie(), app.top, graph_id,
                                               parent_path)
        resp = Response(response=json.dumps(mapping),
                        status=200,
                        mimetype="application/json")
        return resp
    return apply_on_node(app.hie(), app.top, path_to_rule, get_graph_typing_aux)


# depreciated, use get_typing that uses parent id instead of ancestor degree
@app.route("/graph/get_ancestors/", methods=["GET"])
@app.route("/graph/get_ancestors/<path:path_to_graph>", methods=["GET"])
def get_ancestors(path_to_graph=""):
    def get_ancestors_aux(graph_id):
        degree = request.args.get("degree")
        if not degree:
            return("the query parameter degree is necessary", 404)
        degree = int(degree)
        if degree < 1:
            raise ValueError("degree must be greater than one")
        mapping = tree.ancestors_mapping(app.hie(), graph_id, degree)
        resp = Response(response=json.dumps(mapping),
                        status=200,
                        mimetype="application/json")
        return resp
    return apply_on_node(app.hie(), app.top, path_to_graph, get_ancestors_aux)


@app.route("/graph/get_metadata/", methods=["GET"])
@app.route("/graph/get_metadata/<path:path_to_graph>", methods=["GET"])
def get_metadata(path_to_graph=""):
    def get_metadata_aux(graph_id):
        metadata = tree.get_metadata(app.hie(), graph_id, "/"+path_to_graph)
        resp = Response(response=json.dumps(metadata),
                        status=200,
                        mimetype="application/json")
        return resp
    return apply_on_node(app.hie(), app.top, path_to_graph, get_metadata_aux)