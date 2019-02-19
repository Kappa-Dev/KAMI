"""Collection of data structures for instantiated KAMI models."""
import datetime
from regraph import (Neo4jHierarchy, NetworkXHierarchy)
from regraph.primitives import (add_nodes_from,
                                add_edges_from)

from kami.data_structures.annotations import CorpusAnnotation
from kami.resources import default_components


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
        self._backend = backend
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
