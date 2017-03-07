""" webserver with kami and mu calculus functionnalities"""

import os
import json
from flask import Flask, request
from server_hierarchy import ServerHierarchy
from webserver_base import app
from webserver_mu import mu_blueprint
from regraph.library.tree import from_json_tree, to_json_tree
# from webserver_kami import (include_kami_metamodel,
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
# kami_blueprint.cmd = SERVER.cmd
mu_blueprint.hie = SERVER.hie
mu_blueprint.top = SERVER.top

# make the SERVER use the blueprints:
# app handles the generic requests
# kami_blueprint handles the kami specific requests
SERVER.register_blueprint(app)
SERVER.register_blueprint(mu_blueprint)
# SERVER.register_blueprint(kami_blueprint)


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

if __name__ == "__main__":
    SERVER.run(host='0.0.0.0')
