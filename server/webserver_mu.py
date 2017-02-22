"""handle requests relative to mu-calculus checking"""

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


mu_blueprint = Blueprint("mu_blueprint", __name__)

@mu_blueprint.route("/graph/check/", methods=["GET"])
@mu_blueprint.route("/graph/check/<path:path_to_graph>", methods=["GET"])
def check(path_to_graph=""):
    def check_aux(command):
        try:
            rep = command.check()
            resp = Response(response=json.dumps(rep),
                            status=200,
                            mimetype="application/json")
            return resp
        except (ValueError) as e:
            return (str(e), 412)
    return get_command(mu_blueprint.cmd, path_to_graph, check_aux)
