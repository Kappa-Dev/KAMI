from flask import Flask
import json
from regraph.library.kami_graph_hierarchy import KamiHierarchy
# from metamodels import (base_metamodel, metamodel_kappa, kami, base_kami)
from webserver_base import app
from webserver_kami import (include_kami_metamodel, include_kappa_metamodel, kami_blueprint)
from flask_cors import CORS, cross_origin

class MyFlask(Flask):
    def __init__(self, name, template_folder, hierarchy_constructor):
        super().__init__(name, static_url_path="", template_folder=template_folder)
        self.cmd = hierarchy_constructor("/", None)
        self.cmd.graph = None

server = MyFlask(__name__,
   template_folder="RegraphGui",
   hierarchy_constructor=KamiHierarchy)

server.config['DEBUG'] = True
CORS(server)

# give a pointer to the hierarchy to the blueprints 

app.cmd = server.cmd
kami_blueprint.cmd = server.cmd

# make the server use the blueprints
# app handles the generic requests
# kami_blueprint handles the kami specific requests

server.register_blueprint(app)
server.register_blueprint(kami_blueprint)


# add the kami graphs to the hierarchy
include_kappa_metamodel(server)
include_kami_metamodel(server)


# load the exemples.json file to the hierarchy
with open('example.json') as data_file:
    data = json.load(data_file)
server.cmd.merge_hierarchy(data)

if __name__ == "__main__":
    server.run(host='0.0.0.0')