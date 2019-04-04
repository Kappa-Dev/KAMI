"""Collection of data structures for instantiated KAMI models."""
import datetime
import json
import os

from regraph import (Neo4jHierarchy, NetworkXHierarchy)
from regraph.primitives import (add_nodes_from,
                                add_edges_from,
                                get_node,
                                graph_to_json,
                                attrs_to_json)
from regraph.utils import relation_to_json

from kami.aggregation.identifiers import EntityIdentifier
from kami.data_structures.annotations import CorpusAnnotation
from kami.resources import default_components
from kami.utils.generic import (nodes_of_type, _init_from_data)

from kami.exceptions import KamiHierarchyError


class KamiModel(object):
    """Class for instantiated KAMI models.

    Attributes
    ----------
    _id : str
    _backend : str, "networkx" or "neo4j"
    _hierarchy : regraph.neo4j(networkx).Neo4j(NetworkX)Hierarchy

    annotation : kami.data_structures.annotations.CorpusAnnotation
    creation_time : str
    last_modified : str
    corpus_id : str
    seed_genes : iterable of str
    definitions : iterable of kami.data_structure.definitions.Definition

    action_graph : rengraph.neo4j.Neo4jGraph / regraph.networkx.DiGraph
    nugget : dict
    mod_template : rengraph.neo4j.Neo4jGraph / regraph.networkx.DiGraph
    bnd_templae : rengraph.neo4j.Neo4jGraph / regraph.networkx.DiGraph

    """

    nugget_dict_factory = dict

    def __init__(self, model_id, annotation=None,
                 creation_time=None, last_modified=None,
                 corpus_id=None, seed_genes=None, definitions=None,
                 backend="networkx",
                 uri=None, user=None, password=None, driver=None, data=None):
        """Initialize a KAMI model."""
        self._id = model_id
        self._action_graph_id = self._id + "_action_graph"
        self._corpus_id = corpus_id
        self._backend = backend
        self._seed_genes = seed_genes
        self._definitions = definitions

        if backend == "networkx":
            self._hierarchy = NetworkXHierarchy()
        elif backend == "neo4j":
            if driver is not None:
                self._hierarchy = Neo4jHierarchy(driver=driver)
            else:
                self._hierarchy = Neo4jHierarchy(uri, user, password)

        if creation_time is None:
            creation_time = str(datetime.datetime.now())
        self.creation_time = creation_time
        if annotation is None:
            annotation = CorpusAnnotation()
        self.annotation = annotation
        if last_modified is None:
            last_modified = self.creation_time
        self.last_modified = last_modified

        # Add KAMI-specific invariant components of the hierarchy
        for graph_id, graph, attrs in default_components.MODEL_GRAPHS:
            if graph_id not in self._hierarchy.graphs():
                self._hierarchy.add_empty_graph(graph_id, attrs)
                g = self._hierarchy.get_graph(graph_id)
                add_nodes_from(g, graph["nodes"])
                add_edges_from(g, graph["edges"])

        for s, t, mapping, attrs in default_components.MODEL_TYPING:
            if (s, t) not in self._hierarchy.typings():
                self._hierarchy.add_typing(s, t, mapping, attrs=attrs)
        for rule_id, rule, attrs in default_components.RULES:
            self._hierarchy.add_rule(rule_id, rule, attrs)
        for s, t, (
                lhs_mapping,
                rhs_mapping), attrs in default_components.MODEL_RULE_TYPING:
            self._hierarchy.add_rule_typing(
                s, t, lhs_mapping, rhs_mapping,
                lhs_total=True, rhs_total=True, attrs=attrs)
        for u, v, rel, attrs in default_components.RELATIONS:
            if (u, v) not in self._hierarchy.relations():
                self._hierarchy.add_relation(u, v, rel, attrs)

        self.nugget_dict_factory = ndf = self.nugget_dict_factory
        self.nugget = ndf()

        _init_from_data(self, data, True)

        self._init_shortcuts()
        return

    def _init_shortcuts(self):
        """Initialize kami-specific shortcuts."""
        if self._action_graph_id in self._hierarchy.graphs():
            self.action_graph =\
                self._hierarchy.get_graph(self._action_graph_id)
        else:
            self.action_graph = None

        self.mod_template = self._hierarchy.get_graph(
            "mod_template")
        self.bnd_template = self._hierarchy.get_graph(
            "bnd_template")

        self.nugget = self.nugget_dict_factory()
        for n in self._hierarchy.graphs():
            graph_attrs = self._hierarchy.get_graph_attrs(n)
            if "type" in graph_attrs.keys() and\
               "nugget" in graph_attrs["type"] and\
               "model_id" in graph_attrs.keys() and\
               self._id in graph_attrs["model_id"]:
                self.nugget[n] = self._hierarchy.get_graph(n)

    def create_empty_action_graph(self):
        """Creat an empty action graph in the hierarchy."""
        if self._action_graph_id not in self._hierarchy.graphs():
            self._hierarchy.add_empty_graph(
                self._action_graph_id,
                {"type": "action_graph",
                 "model_id": self._id}
            )
            self._hierarchy.add_typing(
                self._action_graph_id,
                "meta_model",
                dict()
            )
            self._hierarchy.add_relation(
                self._action_graph_id,
                "semantic_action_graph",
                dict()
            )
            self.action_graph = self._hierarchy.get_graph(
                self._action_graph_id)

    def rewrite(self, graph_id, rule, instance=None,
                rhs_typing=None, strict=False):
        """Overloading of the rewrite method."""
        if instance is None:
            instance = {
                n: n for n in rule.lhs.nodes()
            }
        g_prime, r_g_prime = self._hierarchy.rewrite(
            graph_id, rule=rule, instance=instance,
            rhs_typing=rhs_typing, strict=strict)
        self._init_shortcuts()
        return (g_prime, r_g_prime)

    def find_matching(self, graph_id, pattern,
                      pattern_typing=None, nodes=None):
        """Overloading of the find matching method."""
        return self._hierarchy.find_matching(
            graph_id, pattern,
            pattern_typing, nodes)

    def get_action_graph_typing(self):
        """Get typing of the action graph by meta model."""
        typing = dict()
        if (self._action_graph_id, "meta_model") in self._hierarchy.typings():
            typing =\
                self._hierarchy.get_typing(self._action_graph_id, "meta_model")
        return typing

    def get_action_graph_attrs(self):
        """Get action graph attributes."""
        return self._hierarchy.get_graph_attrs(
            self._action_graph_id)

    def is_nugget_graph(self, node_id):
        """Test if node of the hierarchy is nugget."""
        graph_attrs = self._hierarchy.get_graph_attrs(node_id)
        if "type" in graph_attrs.keys():
            if "model_id" in graph_attrs.keys() and\
               "nugget" in graph_attrs["type"] and\
               self._id in graph_attrs["model_id"]:
                return True
        return False

    def get_nugget_desc(self, nugget_id):
        """Get nugget description string."""
        nugget_attrs = self._hierarchy.get_graph_attrs(nugget_id)
        if 'desc' in nugget_attrs.keys():
            if type(nugget_attrs['desc']) == str:
                nugget_desc = nugget_attrs['desc']
            else:
                nugget_desc = list(nugget_attrs['desc'])[0]
        else:
            nugget_desc = ""
        return nugget_desc

    def get_nugget_type(self, nugget_id):
        """Get type of the nugget specified by id."""
        return list(self._hierarchy.get_graph_attrs(nugget_id)["interaction_type"])[0]

    def get_nugget_template_rel(self, nugget_id):
        """Get relation of a nugget to a template."""
        nugget_type = self.get_nugget_type(nugget_id)
        return self._hierarchy.get_relation(
            nugget_id, nugget_type + "_template")

    def get_nugget_typing(self, nugget_id):
        """Get typing of the nugget by the action graph."""
        return self._hierarchy.get_typing(
            nugget_id, self._action_graph_id)

    def nuggets(self):
        """Get a list of nuggets in the hierarchy."""
        nuggets = []
        for node_id in self._hierarchy.graphs():
            if self.is_nugget_graph(node_id):
                nuggets.append(node_id)
        return nuggets

    def empty(self):
        """Test if model is empty."""
        return (len(self.nuggets()) == 0) and\
               ((self.action_graph is None) or
                (len(self.action_graph.nodes()) == 0))

    def proteins(self):
        """Get a list of agent nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "gene")

    def bindings(self):
        """Get a list of bnd nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "bnd")

    def modifications(self):
        """Get a list of bnd nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "mod")

    @classmethod
    def from_hierarchy(cls, model_id, hierarchy, annotation=None,
                       creation_time=None, last_modified=None,
                       corpus_id=None, seed_genes=None, definitions=None):
        """Initialize KamiCorpus obj from a graph hierarchy."""
        model = cls(model_id, annotation=annotation,
                    creation_time=creation_time, last_modified=last_modified,
                    corpus_id=corpus_id, seed_genes=seed_genes,
                    definitions=definitions)
        model._hierarchy = hierarchy
        model._init_shortcuts()
        return model

    @classmethod
    def from_json(cls, model_id, json_data, annotation=None,
                  creation_time=None, last_modified=None,
                  corpus_id=None, seed_genes=None, definitions=None,
                  backend="networkx",
                  uri=None, user=None, password=None, driver=None):
        """Create hierarchy from json representation."""
        model = cls(model_id, annotation=annotation,
                    creation_time=creation_time, last_modified=last_modified,
                    corpus_id=corpus_id, seed_genes=seed_genes, definitions=definitions,
                    backend=backend,
                    uri=uri, user=user, password=password, driver=driver,
                    data=json_data)
        return model

    @classmethod
    def load_json(cls, model_id, filename, annotation=None,
                  creation_time=None, last_modified=None,
                  corpus_id=None, seed_genes=None, definitions=None,
                  backend="networkx",
                  uri=None, user=None, password=None, driver=None):
        """Load a KamiCorpus from its json representation."""
        if os.path.isfile(filename):
            with open(filename, "r+") as f:
                json_data = json.loads(f.read())
                model = cls.from_json(
                    model_id, json_data, annotation=annotation,
                    creation_time=creation_time, last_modified=last_modified,
                    corpus_id=corpus_id, seed_genes=seed_genes, definitions=definitions,
                    backend=backend,
                    uri=uri, user=user, password=password, driver=driver)
            return model
        else:
            raise KamiHierarchyError("File '%s' does not exist!" % filename)

    def export_json(self, filename):
        """Export model to json."""
        with open(filename, 'w') as f:
            j_data = self.to_json()
            json.dump(j_data, f)

    def to_json(self):
        """Return json repr of the corpus."""
        json_data = {}
        json_data["model_id"] = self._id

        json_data["origin"] = {}
        json_data["origin"]["corpus_id"] = self._corpus_id
        json_data["origin"]["seed_genes"] = self._seed_genes
        json_data["origin"]["definitions"] = self._definitions

        json_data["annotation"] = self.annotation.to_json()
        json_data["creation_time"] = self.creation_time
        json_data["last_modified"] = self.last_modified

        json_data["action_graph"] = graph_to_json(self.action_graph)
        json_data["action_graph_typing"] = self.get_action_graph_typing()
        json_data["action_graph_semantics"] = relation_to_json(
            self._hierarchy.get_relation(self._action_graph_id, "semantic_action_graph"))

        json_data["nuggets"] = []
        for nugget in self.nuggets():
            template = self.get_nugget_type(nugget) + "_template"
            nugget_json = {
                "id": nugget,
                "graph": graph_to_json(self.nugget[nugget]),
                "desc": self.get_nugget_desc(nugget),
                "typing": self.get_nugget_typing(nugget),
                "attrs": attrs_to_json(self._hierarchy.get_graph_attrs(nugget)),
                "template_rel": (
                    template,
                    relation_to_json(self.get_nugget_template_rel(nugget))
                ),
            }

            json_data["nuggets"].append(nugget_json)
        return json_data

    def get_gene_data(self, gene_id):
        """."""
        attrs = get_node(self.action_graph, gene_id)
        uniprotid = None
        if "uniprotid" in attrs.keys():
            uniprotid = list(attrs["uniprotid"])[0]
        hgnc_symbol = None
        if "hgnc_symbol" in attrs.keys():
            hgnc_symbol = list(attrs["hgnc_symbol"])[0]
        nuggets = self._hierarchy.get_graphs_having_typing(
            self._action_graph_id, gene_id)
        return (uniprotid, hgnc_symbol, nuggets)

    def get_modification_data(self, mod_id):

        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, self._action_graph_id)

        enzyme_genes = identifier.ancestors_of_type(mod_id, "gene")
        substrate_genes = identifier.descendants_of_type(mod_id, "gene")
        nuggets = self._hierarchy.get_graphs_having_typing(
            self._action_graph_id, mod_id)
        return (nuggets, enzyme_genes, substrate_genes)

    def get_binding_data(self, bnd_id):

        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, self._action_graph_id)

        all_genes = identifier.ancestors_of_type(bnd_id, "gene")
        nuggets = self._hierarchy.get_graphs_having_typing(
            self._action_graph_id, bnd_id)
        return (nuggets, all_genes)

    def get_uniprot(self, gene_id):
        attrs = get_node(self.action_graph, gene_id)
        uniprotid = None
        if "uniprotid" in attrs.keys():
            uniprotid = list(attrs["uniprotid"])[0]
        return uniprotid

    def get_variant_name(self, gene_id):
        attrs = get_node(self.action_graph, gene_id)
        uniprotid = None
        if "variant_name" in attrs.keys():
            uniprotid = list(attrs["variant_name"])[0]
        return uniprotid

    def get_hgnc_symbol(self, gene_id):
        attrs = get_node(self.action_graph, gene_id)
        hgnc_symbol = None
        if "hgnc_symbol" in attrs.keys():
            hgnc_symbol = list(attrs["hgnc_symbol"])[0]
        return hgnc_symbol
