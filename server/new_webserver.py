""" webserver with kami functionnalities"""

import os
import json
from flask import Flask
from kami_graph_hierarchy import KamiHierarchy
from webserver_base import app
from webserver_kami import (include_kami_metamodel,
                            include_kappa_metamodel,
                            kami_blueprint)

from flask_cors import CORS


class MyFlask(Flask):
    """flask server containing a hierarchy """

    def __init__(self, name, template_folder, hierarchy_constructor):
        super().__init__(name,
                         static_url_path="",
                         template_folder=template_folder)
        self.cmd = hierarchy_constructor("/", None)
        self.cmd.graph = None

SERVER = MyFlask(__name__,
                 template_folder="RegraphGui",
                 hierarchy_constructor=KamiHierarchy)

# configures server
SERVER.config['DEBUG'] = True
CORS(SERVER)

# give a pointer to the hierarchy to the blueprints
app.cmd = SERVER.cmd
kami_blueprint.cmd = SERVER.cmd

# make the SERVER use the blueprints:
# app handles the generic requests
# kami_blueprint handles the kami specific requests
SERVER.register_blueprint(app)
SERVER.register_blueprint(kami_blueprint)


# add the kami graphs to the hierarchy
include_kappa_metamodel(SERVER)
include_kami_metamodel(SERVER)


# load the exemples.json file to the hierarchy
EXAMPLE = os.path.join(os.path.dirname(__file__), 'example.json')
with open(EXAMPLE) as data_file:
    DATA = json.load(data_file)
SERVER.cmd.merge_hierarchy(DATA)

if __name__ == "__main__":
    SERVER.run(host='0.0.0.0')
