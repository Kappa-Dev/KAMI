""" webserver with kami and mu calculus functionnalities"""

import os
import json
import networkx as nx
from flask import Flask, request
# from server_hierarchy import ServerHierarchy
from base.base_blueprint import app
from kami.server.kami.kami_blueprint import kami_blueprint
from kami.server.mu_calculus.mu_blueprint import mu_blueprint
from regraph.tree import from_json_tree, to_json_tree, new_action_graph, add_types
from regraph.primitives import graph_to_json, add_edge
from regraph.hierarchy import MuHierarchy
from kami.server.kami.metamodels import untypedkami, untyped_base_kami, kami_basekami

from flask_cors import CORS


class ServerHierarchy(MuHierarchy):
    """hierarchy class with kami and mu-calculus functionalities"""
    def __init__(self):
        super().__init__()
        self.add_graph("/", nx.DiGraph(), {"name": "/"})
        # self.node["/"].graph = None


class MyFlask(Flask):
    """flask server containing a hierarchy """

    def __init__(self, name, template_folder, hierarchy_constructor):
        super().__init__(name,
                         static_url_path="")
        self._hie = hierarchy_constructor()
        self.top = "/"

    def hie(self): return self._hie

SERVER = MyFlask(__name__,
                 template_folder="RegraphGui",
                 hierarchy_constructor=ServerHierarchy)

# configures server
SERVER.config['DEBUG'] = True
CORS(SERVER)

# give a pointer to the hierarchy to the blueprints
app.hie = SERVER.hie
app.top = SERVER.top
kami_blueprint.hie = SERVER.hie
kami_blueprint.top = SERVER.top
mu_blueprint.hie = SERVER.hie
mu_blueprint.top = SERVER.top

# make the SERVER use the blueprints:
# app handles the generic requests
# kami_blueprint handles the kami specific requests
SERVER.register_blueprint(app)
SERVER.register_blueprint(mu_blueprint)
SERVER.register_blueprint(kami_blueprint)


# add the kami graphs to the hierarchy
# include_kappa_metamodel(SERVER)
# include_kami_metamodel(SERVER)


# load the exemples.json file to the hierarchy
# EXAMPLE = os.path.join(os.path.dirname(__file__), 'example.json')
# EXAMPLE = "/home/stan/Downloads/hierarchy (52).json"
EXAMPLE = "/home/stan/Downloads/bigwnt.json"
with open(EXAMPLE) as data_file:
    DATA = json.load(data_file)
    new_hie = SERVER._hie.__class__()
    new_hie.remove_graph("/")
    from_json_tree(new_hie, DATA, None)
    add_types(new_hie)
    SERVER._hie = new_hie


# import and replace hierarchy
@SERVER.route("/hierarchy/", methods=["PUT"])
@SERVER.route("/hierarchy/<path:path_to_graph>", methods=["PUT"])
def replace_hierachy(path_to_graph=""):
    hierarchy = request.json
    if hierarchy["name"] != "/":
        return ("the name of the top graph must be /", 404)
    new_hie = SERVER._hie.__class__()
    new_hie.remove_graph("/")
    from_json_tree(new_hie, hierarchy, None)
    add_types(new_hie)
    SERVER._hie = new_hie
    return("hierarchy replaced", 200)


# import and replace hierarchy from partially typed nuggets
@SERVER.route("/hierarchy2/", methods=["PUT"])
@SERVER.route("/hierarchy2/<path:path_to_graph>", methods=["PUT"])
def replace_hierachy2(path_to_graph=""):
    hierarchy = request.json
    print("hie", hierarchy)
    for g in hierarchy["graphs"]:
        if "attrs" not in g.keys():
            g["attrs"] = g["graph"]["attrs"]
    kami_json = {}
    kami_json["graph"] = graph_to_json(untypedkami)
    kami_json["id"] = "kami"
    kami_json["attrs"] = {"name": "kami"}
    hierarchy["graphs"].append(kami_json)
    new_typings = []
    to_ag_functions = {}
    for mapping in hierarchy["typing"]:
        if mapping["to"] == "action_graph":
            to_ag_functions[mapping["from"]] = mapping["mapping"]
        else:
            new_typings.append(mapping)
    hierarchy["typing"] = new_typings

    new_hie = ServerHierarchy.from_json(SERVER._hie.__class__, hierarchy)
    new_hie.add_graph("kami_base", untyped_base_kami, {"name": "kami_base"})
    new_hie.add_typing("kami_base", "/", {}, total=False)
    new_hie.add_typing("kami", "kami_base", kami_basekami, total=True)
    new_action_graph(new_hie, to_ag_functions)
    SERVER._hie = new_hie
    return("hierarchy replaced", 200)

if __name__ == "__main__":
    SERVER.run(host='0.0.0.0')
