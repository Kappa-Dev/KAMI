""" webserver with kami and mu calculus functionnalities"""

import os
import json
from flask import Flask, request
from server_hierarchy import ServerHierarchy
from webserver_base import app
from webserver_kami import kami_blueprint
from webserver_mu import mu_blueprint
from regraph.library.tree import from_json_tree, to_json_tree, new_action_graph
from regraph.library.primitives import graph_to_json, add_edge
from metamodels import untypedkami, untyped_base_kami, kami_basekami
#from webserver_kami import (include_kami_metamodel,
#                             include_kappa_metamodel,
#                             kami_blueprint)

from flask_cors import CORS


class MyFlask(Flask):
    """flask server containing a hierarchy """

    def __init__(self, name, template_folder, hierarchy_constructor):
        super().__init__(name,
                         static_url_path="")
        #  template_folder=template_folder)
        self._hie = hierarchy_constructor()
        self.top = "/"
        # self.cmd.graph = None

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
# with open(EXAMPLE) as data_file:
#     DATA = json.load(data_file)
# SERVER.cmd.merge_hierarchy(DATA)

@SERVER.route("/hierarchy/", methods=["PUT"])
@SERVER.route("/hierarchy/<path:path_to_graph>", methods=["PUT"])
def replace_hierachy(path_to_graph=""):
    hierarchy = request.json
    if hierarchy["name"] != "/":
        return ("the name of the top graph must be /", 404)
    new_hie = SERVER._hie.__class__()
    new_hie.remove_graph("/")
    from_json_tree(new_hie, hierarchy, None)
    SERVER._hie = new_hie
    return("hierarchy replaced", 200)


# def _tmp_complete_target(source, target, morph):
#     for node1 in morph:
#         for node2 in morph:
#             if ((node1, node2) in source[edges() and
#                (morph[node1], morph[node2]) not in target.edges()):
#                 add_edge(target, morph[node1], morph[node2])

@SERVER.route("/hierarchy2/", methods=["PUT"])
@SERVER.route("/hierarchy2/<path:path_to_graph>", methods=["PUT"])
def replace_hierachy2(path_to_graph=""):
    hierarchy = request.json
    print("hie",hierarchy)
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
    new_hie.add_typing("kami_base", "/", {}, total=False, ignore_attrs=True)
    new_hie.add_typing("kami", "kami_base", kami_basekami, total=True,
                       ignore_attrs=True)
    new_action_graph(new_hie, to_ag_functions)
    SERVER._hie = new_hie
    return("hierarchy replaced", 200)

if __name__ == "__main__":
    SERVER.run(host='0.0.0.0')
