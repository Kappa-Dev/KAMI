"""handle requests relative to mu-calculus checking"""

from flask import Blueprint, Response, request
import json
from base.webserver_utils import apply_on_node
import flex
from flex.loading.schema.paths.path_item.operation.responses.single.schema\
    import schema_validator

import os
import subprocess


mu_blueprint = Blueprint("mu_blueprint", __name__)


@mu_blueprint.route("/graph/check/", methods=["GET"])
@mu_blueprint.route("/graph/check/<path:path_to_graph>", methods=["GET"])
def check(path_to_graph=""):
    def check_aux(graph_id):
        rep = mu_blueprint.hie().check_all_ancestors(graph_id)
        print(rep)
        resp = Response(response=json.dumps(rep),
                        status=200,
                        mimetype="application/json")
        return resp
    return apply_on_node(mu_blueprint.hie(), mu_blueprint.top,
                         path_to_graph, check_aux)
