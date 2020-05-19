"""Classes for KAMI knowledge corpora.

Corpora in KAMI are decontextualised signalling knowledge bases.
"""
import datetime
import json
import os

from kami.resources import default_components

from regraph import (Rule, Neo4jHierarchy, NXHierarchy, NXGraph)
from regraph.audit import VersionedHierarchy
from regraph.utils import relation_to_json, attrs_to_json, attrs_from_json

from anatomizer.anatomizer_light import fetch_canonical_sequence

from kami.utils.generic import (normalize_to_set,
                                nodes_of_type,
                                _init_from_data,
                                _generate_ref_agent_str)
from kami.utils.id_generators import generate_new_id
from kami.aggregation.bookkeeping import (anatomize_gene,
                                          apply_bookkeeping,
                                          reconnect_residues,
                                          reconnect_sites)
from kami.aggregation.generators import generate_nugget
from kami.aggregation.semantics import (apply_mod_semantics,
                                        apply_bnd_semantics)
from kami.aggregation.identifiers import EntityIdentifier
from kami.data_structures.annotations import CorpusAnnotation, ModelAnnotation
from kami.data_structures.models import KamiModel
from kami.data_structures.interactions import Interaction

from kami.exceptions import KamiHierarchyError, KamiException


class KamiCorpus(object):
    """Class for KAMI knowledge corpora.

    Attributes
    ----------
    _id : str,
        Identifier of the knowledge corpus
    _backend : str, "networkx" or "neo4j"
    _hierarchy : NXHierarchy or Neo4jHierarchy
        Graph hierarchy object containg the corpus
    _action_graph_id : hashable
        Id of the action graph in the graph hierarchy


    annotation: kami.data_structures.annotations.CorpusAnnotation
    creation_time : str
    last_modified : str

    action_graph : Neo4jGraph / NXGraph
    mod_template : Neo4jGraph / NXGraph
    bnd_templae :  Neo4jGraph / NXGraph
    semantic_action_graph :  Neo4jGraph / NXGraph
    """

    nugget_dict_factory = dict
    semantic_nugget_dict_factory = dict

    def __init__(self, corpus_id, annotation=None,
                 creation_time=None, last_modified=None,
                 backend="networkx",
                 uri=None, user=None, password=None, driver=None,
                 data=None):
        """Initialize a KAMI corpus.

        By default action graph is empty, typed by `meta_model` (meta-model)
        `self.action_graph` -- direct access to the action graph.
        `self.action_graph_typing` -- direct access to typing of
        the action graph nodes by the meta-model.
        `self.mod_template` and `self.bnd_template` -- direct access to
        the nugget template graphs.
        """
        self._id = corpus_id
        self._action_graph_id = self._id + "_action_graph"
        self._backend = backend
        if backend == "networkx":
            self._hierarchy = NXHierarchy()
        elif backend == "neo4j":
            self._hierarchy = Neo4jHierarchy(
                uri=uri, user=user, password=password, driver=driver)
        self._versioning = VersionedHierarchy(self._hierarchy)

        if creation_time is None:
            creation_time = datetime.datetime.now().strftime(
                "%d-%m-%Y %H:%M:%S")
        self.creation_time = creation_time
        if annotation is None:
            annotation = CorpusAnnotation()
        self.annotation = annotation
        if last_modified is None:
            last_modified = self.creation_time
        self.last_modified = last_modified

        # Add KAMI-specific invariant components of the hierarchy
        for graph_id, graph, attrs in default_components.GRAPHS:
            if graph_id not in self._hierarchy.graphs():
                self._hierarchy.add_empty_graph(graph_id, attrs)
                g = self._hierarchy.get_graph(graph_id)
                g.add_nodes_from(graph["nodes"])
                g.add_edges_from(graph["edges"])

        for s, t, mapping, attrs in default_components.TYPING:
            if (s, t) not in self._hierarchy.typings():
                self._hierarchy.add_typing(s, t, mapping, attrs=attrs)
        for rule_id, rule, attrs in default_components.RULES:
            self._hierarchy.add_rule(rule_id, rule, attrs)
        for s, t, (
                lhs_mapping,
                rhs_mapping), attrs in default_components.RULE_TYPING:
            self._hierarchy.add_rule_typing(
                s, t, lhs_mapping, rhs_mapping,
                lhs_total=True, rhs_total=True, attrs=attrs)
        for u, v, rel, attrs in default_components.RELATIONS:
            if (u, v) not in self._hierarchy.relations():
                self._hierarchy.add_relation(u, v, rel, attrs)

        # Initialization of knowledge-related components
        # Action graph related init
        _init_from_data(self, data)

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
        self.semantic_action_graph = self._hierarchy.get_graph(
            "semantic_action_graph")
        self._nugget_count = len(self.nuggets())

    def get_nugget(self, nugget_id):
        """Get a nugget by ID."""
        for node_id in self._hierarchy.graphs():
            if self.is_nugget_graph(node_id):
                return self._hierarchy.get_graph(nugget_id)
        raise KamiException("Nugget '{}' is not found".format(nugget_id))

    def clear(self):
        """Clear data elements of corpus."""
        for n in self.nuggets():
            self._hierarchy.remove_graph(n)
        self._hierarchy.remove_graph(self._action_graph_id)

    def create_empty_action_graph(self):
        """Creat an empty action graph in the hierarchy."""
        if self._action_graph_id not in self._hierarchy.graphs():
            self._hierarchy.add_empty_graph(
                self._action_graph_id,
                {"type": "action_graph",
                 "corpus_id": self._id}
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
                rhs_typing=None, strict=False,
                message="Corpus update", update_type="manual"):
        """Overloading of the rewrite method."""
        r_g_prime, _ = self._versioning.rewrite(
            graph_id, rule=rule, instance=instance,
            rhs_typing=rhs_typing, strict=strict,
            message=message, update_type=update_type)
        self._init_shortcuts()
        return r_g_prime

    def find_matching(self, graph_id, pattern,
                      pattern_typing=None, nodes=None):
        """Overloading of the find matching method."""
        return self._hierarchy.find_matching(
            graph_id, pattern,
            pattern_typing, nodes)

    @classmethod
    def from_hierarchy(cls, corpus_id, hierarchy, annotation=None,
                       creation_time=None, last_modified=None):
        """Initialize KamiCorpus obj from a graph hierarchy."""
        model = cls(corpus_id, annotation=annotation,
                    creation_time=creation_time, last_modified=last_modified)
        model._hierarchy = hierarchy
        model._init_shortcuts()
        return model

    @classmethod
    def copy(cls, corpus_id, corpus):
        """Create a copy of the corpus."""
        if corpus._backend == "networkx":
            hierarchy_copy = NXHierarchy.copy(corpus._hierarchy)
        elif corpus._backend == "neo4j":
            hierarchy_copy = Neo4jHierarchy.copy(corpus._hierarchy)
        return cls.from_hierarchy(corpus_id, hierarchy_copy)

    def get_action_graph_typing(self):
        """Get typing of the action graph by meta model."""
        typing = dict()
        if (self._action_graph_id, "meta_model") in self._hierarchy.typings():
            typing =\
                self._hierarchy.get_typing(self._action_graph_id, "meta_model")
        return typing

    def is_nugget_graph(self, node_id):
        """Test if a hierarchy graph is a nugget."""
        graph_attrs = self._hierarchy.get_graph_attrs(node_id)
        if "type" in graph_attrs.keys():
            if "nugget" in graph_attrs["type"] and\
               "corpus_id" in graph_attrs and\
               self._id in graph_attrs["corpus_id"] and\
               "model_id" not in graph_attrs.keys():
                return True
        return False

    def is_protoform(self, ref_node):
        """Check if the AG node represents a protoform."""
        return self.get_action_graph_typing()[ref_node] == "protoform"

    def is_region(self, ref_node):
        """Check if the AG node represents a region."""
        return self.get_action_graph_typing()[ref_node] == "region"

    def is_site(self, ref_node):
        """Check if the AG node represents a site."""
        return self.get_action_graph_typing()[ref_node] == "site"

    def is_residue(self, ref_node):
        """Check if the AG node represents a residue."""
        return self.get_action_graph_typing()[ref_node] == "residue"

    def nuggets(self):
        """Get a list of nuggets in the hierarchy."""
        nuggets = []
        for node_id in self._hierarchy.graphs():
            if self.is_nugget_graph(node_id):
                nuggets.append(node_id)
        return nuggets

    def semantic_nuggets(self):
        """Get a list of semantic nuggets in the hierarchy."""
        nuggets = []
        for node_id in self._hierarchy.graphs():
            attrs = self._hierarchy.get_graph_attrs(
                node_id)
            if "type" in attrs and "semantic_nugget" in attrs["type"]:
                nuggets.append(node_id)
        return nuggets

    def nugget_relations(self):
        """Get all relations of nuggets."""
        nugget_rels = list()
        for u, v in self._hierarchy.relations():
            if self.is_nugget_graph(u):
                nugget_rels.append((u, v))
        return nugget_rels

    def templates(self):
        """Get a list of templates in the hierarchy."""
        templates = []
        for node_id in self._hierarchy.graphs():
            if "template" in self._hierarchy.get_graph_attrs(node_id)["type"]:
                templates.append(node_id)
        return templates

    def get_nugget_semantic_rels(self, nugget_id):
        """Get nugget semantic relations."""
        all_rels = self._hierarchy.adjacent_relations(nugget_id)
        semantic_nuggets = self.semantic_nuggets()
        result = {}
        for r in all_rels:
            if r in semantic_nuggets:
                result[r] = self._hierarchy.get_relation(nugget_id, r)
        return result

    def mod_semantic_nuggets(self):
        """Get a list of semantic nuggets related to mod interactions."""
        nuggets = []
        for node_id in self._hierarchy.graphs():
            if "semantic_nugget" in self._hierarchy.get_graph_attrs(
                    node_id)["type"] and\
               "mod" in self._hierarchy.get_graph_attrs(
                    node_id)["interaction_type"]:
                nuggets.append(node_id)
        return nuggets

    def bnd_semantic_nuggets(self):
        """Get a list of semantic nuggets related to bnd interactions."""
        nuggets = []
        for node_id in self._hierarchy.graphs():
            if "semantic_nugget" in self._hierarchy.get_graph_attrs(
                    node_id)["type"] and\
               "bnd" in self._hierarchy.get_graph_attrs(
                    node_id)["interaction_type"]:
                nuggets.append(node_id)
        return nuggets

    def empty(self):
        """Test if hierarchy is empty."""
        return (len(self.nuggets()) == 0) and\
               ((self.action_graph is None) or
                (len(self.action_graph.nodes()) == 0))

    def get_ag_node_data(self, node_id):
        """Get data of the action graph node."""
        if node_id not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '{}' is not found in the action graph".format(node_id))
        data = dict()
        node_attrs = self.action_graph.get_node(node_id)

        for key, value in node_attrs.items():
            data[key] = value.toset()

        action_graph_typing = self.get_action_graph_typing()

        if action_graph_typing[node_id] == "residue":
            gene_node = self.get_protoform_of(node_id)
            edge_attrs = self.action_graph.get_edge(node_id, gene_node)
            if "loc" in edge_attrs:
                data["loc"] = edge_attrs["loc"].toset()
        elif action_graph_typing[node_id] == "site" or\
                action_graph_typing[node_id] == "region":
            if "start" in edge_attrs:
                data["start"] = edge_attrs["start"].toset()
            if "end" in edge_attrs:
                data["end"] = edge_attrs["end"].toset()
            if "order" in edge_attrs:
                data["order"] = edge_attrs["order"].toset()
        return data

    def protoforms(self):
        """Get a list of agent nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "protoform")

    def get_protoform_by_uniprot(self, uniprotid):
        """Get a protoform by the UniProt AC."""
        for protoform in self.protoforms():
            attrs = self.action_graph.get_node(protoform)
            u = list(attrs["uniprotid"])[0]
            if u == uniprotid:
                return protoform
        return None

    def get_attached_bnd(self, node, immediate=True):
        """Get BND nodes attached to the specified node."""
        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, self._action_graph_id,
            immediate=immediate)

        return identifier.get_attached_bnd(node)

    def get_attached_mod(self, node, immediate=True, all_directions=False):
        """Get MOD nodes attached to the specified node."""
        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, self._action_graph_id,
            immediate=immediate)

        return identifier.get_attached_mod(node, all_directions=all_directions)

    def merge_ag_nodes(self, nodes, message=""):
        """Merge nodes of the action graph."""
        ag_typing = self.get_action_graph_typing()
        if len(set([ag_typing[n] for n in nodes])) == 1:
            pattern = NXGraph()
            pattern.add_nodes_from(nodes)
            r = Rule.from_transform(pattern)
            r.inject_merge_nodes(nodes)
            self.rewrite(
                self._action_graph_id, r,
                message=message,
                update_type="manual")
        else:
            raise KamiException(
                "Cannot merge action graph nodes of different type!")

    def merge_bnds_of(self, node, subset=None, message=""):
        """Merge BND nodes of the specified node."""
        all_bnds = self.get_attached_bnd(node)
        if subset is not None:
            for el in subset:
                if el not in all_bnds:
                    raise KamiException(
                        "Node with id '{}' is not in the list of ".format(el) +
                        "attached bnd nodes of '{}'".format(node))
            bnds_to_merge = subset
        else:
            bnds_to_merge = all_bnds
        self.merge_ag_nodes(bnds_to_merge, message)

    def regions(self):
        """Get a list of region nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "region")

    def sites(self):
        """Get a list of site nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "site")

    def bindings(self):
        """Get a list of bnd nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "bnd")

    def modifications(self):
        """Get a list of bnd nodes in the action graph."""
        return nodes_of_type(
            self.action_graph, self.get_action_graph_typing(), "mod")

    def ag_successors_of_type(self, node_id, meta_type):
        """Get successors of a node of a specific type."""
        succs = []
        for suc in self.action_graph.successors(node_id):
            if self.get_action_graph_typing()[suc] == meta_type:
                succs.append(suc)
        return succs

    def ag_predecessors_of_type(self, node_id, meta_type):
        """Get predecessors of a node of a specific type."""
        preds = []
        for pred in self.action_graph.predecessors(node_id):
            if self.get_action_graph_typing()[pred] == meta_type:
                preds.append(pred)
        return preds

    def get_attached_regions(self, agent_id):
        """Get a list of regions belonging to a specified agent."""
        return self.ag_predecessors_of_type(agent_id, "region")

    def get_attached_sites(self, agent_id):
        """Get a list of sites belonging to a specified agent."""
        return self.ag_predecessors_of_type(agent_id, "site")

    def get_attached_residues(self, agent_id):
        """Get a list of residues attached to a node with `agent_id`."""
        return self.ag_predecessors_of_type(agent_id, "residue")

    def get_attached_states(self, agent_id):
        """Get a list of states attached to a node with `agent_id`."""
        return self.ag_predecessors_of_type(agent_id, "state")

    def get_protoform_of(self, element_id):
        """Get agent id conntected to the element."""
        action_graph_typing = self.get_action_graph_typing()

        if action_graph_typing[element_id] == "protoform":
            return element_id
        else:
            # bfs to find a protoform
            visited = set()
            next_level_to_visit = list(self.action_graph.successors(
                element_id))
            while len(next_level_to_visit) > 0:
                new_level_to_visit = set()
                for n in next_level_to_visit:
                    if n not in visited:
                        visited.add(n)
                        if action_graph_typing[n] == "protoform":
                            return n
                    new_level_to_visit.update(
                        self.action_graph.successors(n))
                next_level_to_visit = new_level_to_visit
        raise KamiHierarchyError(
            "No protoform node is associated with an element '{}'".format(
                element_id))
        return None

    def get_protoforms_of_bnd(self, bnd_node):
        """Get protoforms associated with a bidnind node."""
        protoforms = set()
        for s in self.action_graph.predecessors(bnd_node):
            protoforms.add(self.get_protoform_of(s))
        return protoforms

    def get_enzymes_of_mod(self, mod_node):
        """Get enzymes of the modification action."""
        protoforms = set()
        for s in self.action_graph.predecessors(mod_node):
            protoforms.add(self.get_protoform_of(s))
        return protoforms

    def get_substrates_of_mod(self, mod_node):
        """Get substrates of the modification action."""
        protoforms = set()
        for s in self.action_graph.successors(mod_node):
            protoforms.add(self.get_protoform_of(s))
        return protoforms

    def get_region_of(self, element_id):
        """Get region id conntected to the element."""
        regions = self.ag_successors_of_type(element_id, "region")
        if len(regions) == 1:
            return regions[0]
        elif len(regions) == 0:
            return None
        else:
            raise KamiHierarchyError(
                "More than one region ('%s') is associated "
                "with a single site '%s'" % (", ".join(regions), element_id)
            )
        return None

    def set_ag_meta_type(self, node_id, meta_type):
        """Set typing of a node from the AG by the meta-model."""
        ag_typing = self.get_action_graph_typing()
        ag_typing[node_id] = meta_type
        self._hierarchy._update_mapping(
            self._action_graph_id, "meta_model", ag_typing)

    def add_ag_node_semantics(self, node_id, semantic_node):
        """Add relation of `node_id` with `semantic_node`."""
        self._hierarchy.set_node_relation(
            self._action_graph_id,
            "semantic_action_graph",
            node_id, semantic_node)
        return

    def ag_node_semantics(self, node_id):
        """Get semantic nodes related to the `node_id`."""
        result = set()
        rel = self._hierarchy.get_relation(
            self._action_graph_id, "semantic_action_graph")
        for node, semantic_nodes in rel.items():
            if node == node_id:
                result.update(semantic_nodes)
        return result

    def add_mod(self, attrs=None, semantics=None):
        """Add mod node to the action graph.

        attrs : dict
            Dictionary with mod node attributes
        semantics: str or iterable of str
            Semantics of the mod node (available semantics: `phosopo`,
            `dephospho`)
        rewriting : bool
            Flag indicating if the action graph should be modified
            by SqPO rewriting (if True) or primitive operations (if False)
        """
        semantics = normalize_to_set(semantics)

        mod_id = generate_new_id(self.action_graph, "mod")

        rule = Rule.from_transform(NXGraph())
        rule.inject_add_node(mod_id, attrs)
        rhs_typing = {"meta_model": {mod_id: "mod"}}

        message = (
            "Added a modification mechanism"
        )

        rhs_instance = self.rewrite(
            self._action_graph_id, rule, instance={},
            rhs_typing=rhs_typing,
            message=message,
            update_type="manual")
        res_mod_id = rhs_instance[mod_id]

        # add semantic relations of the node
        for s in semantics:
            self.add_ag_node_semantics(res_mod_id, s)

        return res_mod_id

    def add_bnd(self, attrs=None, semantics=None):
        """Add bnd node to the action graph."""
        semantics = normalize_to_set(semantics)

        bnd_id = generate_new_id(self.action_graph, "bnd")

        rule = Rule.from_transform(NXGraph())
        rule.inject_add_node(bnd_id, attrs)
        rhs_typing = {"meta_model": {bnd_id: "bnd"}}

        message = (
            "Added a binding mechanism"
        )

        rhs_instance = self.rewrite(
            self._action_graph_id, rule, instance={},
            rhs_typing=rhs_typing,
            message=message,
            update_type="manual")
        res_bnd_id = rhs_instance[bnd_id]

        # add semantic relations of the node
        for s in semantics:
            self.add_ag_node_semantics(res_bnd_id, s)

        return res_bnd_id

    def add_protoform(self, protoform, anatomize=True):
        """Add protoform node to action graph.

        protoform : kami.entities.Protoform
        rewriting : bool
            Flag indicating if the action graph should be modified
            by SqPO rewriting (if True) or primitive operations (if False)
        """
        if self.action_graph is None:
            self.create_empty_action_graph()
        if protoform.uniprotid:
            gene_id = protoform.uniprotid
        else:
            gene_id = generate_new_id(
                self.action_graph, "unkown_agent")
        rule = Rule.from_transform(NXGraph())
        rule.inject_add_node(gene_id, protoform.meta_data())
        rhs_typing = {"meta_model": {gene_id: "protoform"}}
        rhs_instance = self.rewrite(
            self._action_graph_id, rule, instance={},
            rhs_typing=rhs_typing,
            message="Added the protoform with the UniProtAC '{}'".format(
                gene_id),
            update_type="manual")

        if anatomize is True:
            anatomize_gene(self, rhs_instance[gene_id])

        return rhs_instance[gene_id]

    def add_region(self, region, ref_gene, semantics=None):
        """Add a region node to action graph connected to the reference agent.

        region : kami.entities.Region
            Region to add
        ref_gene
            Id of the reference agent node in the action graph
        semantics: str or iterable of str
            Semantics of the mod node (available semantics: `protein_kinase`,
            `sh2_domain`)
        rewriting : bool
            Flag indicating if the action graph should be modified
            by SqPO rewriting (if True) or primitive operations (if False)
        """
        # find the node corresponding to reference agent in the AG
        if not self.is_protoform(ref_gene):
            raise KamiHierarchyError(
                "Protoform '{}' is not found in the action graph".format(
                    ref_gene))

        ref_uniprot = self.get_uniprot(ref_gene)

        semantics = normalize_to_set(semantics)

        region_id = generate_new_id(
            self.action_graph, "{}_{}".format(ref_gene, str(region)))

        pattern = NXGraph()
        pattern.add_node(ref_gene)
        rule = Rule.from_transform(pattern)
        rule.inject_add_node(region_id, region.meta_data())
        rule.inject_add_edge(region_id, ref_gene, region.location())
        rhs_typing = {"meta_model": {region_id: "region"}}

        message = (
            "Added the region '{}' to the protoform ".format(region) +
            "with the UniProtAC '{}'".format(ref_uniprot)
        )

        rhs_instance = self.rewrite(
            self._action_graph_id, rule, instance={ref_gene: ref_gene},
            rhs_typing=rhs_typing, message=message,
            update_type="manual")
        res_region_id = rhs_instance[region_id]

        if semantics is not None:
            for s in semantics:
                self.add_ag_node_semantics(res_region_id, s)

        # reconnect all the residues & sites of the corresponding protoform
        # that lie in the region range
        reconnect_residues(
            self.get_entity_identifier(), ref_gene,
            self.get_attached_residues(ref_gene),
            [res_region_id])

        reconnect_sites(
            self.get_entity_identifier(), ref_gene,
            self.get_attached_sites(ref_gene),
            [res_region_id]
        )

        return res_region_id

    def add_site(self, site, ref_agent, semantics=None):
        """Add site node to the action graph."""
        ref_agent_in_protoforms = self.is_protoform(ref_agent)
        ref_agent_in_regions = self.is_region(ref_agent)

        if ref_agent_in_protoforms:
            ref_gene = ref_agent
        else:
            ref_gene = self.get_protoform_of(ref_agent)

        semantics = normalize_to_set(semantics)

        if not ref_agent_in_protoforms and not ref_agent_in_regions:
            raise KamiHierarchyError(
                "Neither agent nor region '%s' is not "
                "found in the action graph" %
                ref_agent
            )

        site_id = generate_new_id(
            self.action_graph, "{}_{}".format(ref_agent, str(site)))

        pattern = NXGraph()
        pattern.add_node(ref_gene)
        instance = {ref_gene: ref_gene}
        if not ref_agent_in_protoforms:
            pattern.add_node(ref_agent)
            instance[ref_agent] = ref_agent
        rule = Rule.from_transform(pattern)
        rule.inject_add_node(site_id, site.meta_data())
        rule.inject_add_edge(site_id, ref_gene, site.location())
        if not ref_agent_in_protoforms:
            rule.inject_add_edge(site_id, ref_agent, site.location())
        rhs_typing = {"meta_model": {site_id: "site"}}

        ref_agent_str = _generate_ref_agent_str(
            self, ref_agent, ref_gene, ref_agent_in_regions)

        message = (
            "Added the site '{}' to the ".format(site) +
            ref_agent_str
        )

        rhs_instance = self.rewrite(
            self._action_graph_id, rule, instance, rhs_typing=rhs_typing,
            message=message, update_type="manual")
        new_site_id = rhs_instance[site_id]

        for sem in semantics:
            self.add_ag_node_semantics(site_id, sem)

        reconnect_residues(
            self.get_entity_identifier(), ref_gene, self.get_attached_residues(
                ref_gene),
            sites=[new_site_id])
        reconnect_sites(
            self.get_entity_identifier(), ref_gene, [new_site_id],
            self.get_attached_regions(ref_gene))

        return site_id

    def add_residue(self, residue, ref_agent, semantics=None):
        """Add residue node to the action_graph."""
        if ref_agent not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '{}' does not exist in the action graph".format(
                    ref_agent))

        ref_agent_in_protoforms = self.is_protoform(ref_agent)
        ref_agent_in_regions = self.is_region(ref_agent)
        ref_agent_in_sites = self.is_site(ref_agent)

        if not ref_agent_in_protoforms and not ref_agent_in_regions and\
           not ref_agent_in_sites:
            raise KamiHierarchyError(
                "Cannot add a residue to the node '%s', node type "
                "is not valid (expected 'agent', 'region' or 'site', '%s' "
                "was provided)" %
                (ref_agent, self.get_action_graph_typing()[ref_agent])
            )

        semantics = normalize_to_set(semantics)

        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, self._action_graph_id)

        # try to find an existing residue with this
        residue_id = identifier.identify_residue(
            residue, ref_agent, add_aa=True)

        # if residue with this loc does not exist: create one
        if residue_id is None:

            residue_id = generate_new_id(
                self.action_graph, "{}_{}".format(ref_agent, str(residue)))

            if ref_agent_in_protoforms:
                ref_gene = ref_agent
            else:
                ref_gene = self.get_protoform_of(ref_agent)

            pattern = NXGraph()
            pattern.add_node(ref_gene)
            instance = {ref_gene: ref_gene}
            if not ref_agent_in_protoforms:
                pattern.add_node(ref_agent)
                instance[ref_agent] = ref_agent
            rule = Rule.from_transform(pattern)
            rule.inject_add_node(residue_id, residue.meta_data())
            rule.inject_add_edge(residue_id, ref_gene, residue.location())
            if not ref_agent_in_protoforms:
                rule.inject_add_edge(
                    residue_id, ref_agent, residue.location())
            rhs_typing = {"meta_model": {residue_id: "residue"}}

            ref_agent_str = _generate_ref_agent_str(
                self, ref_agent, ref_gene, ref_agent_in_regions,
                ref_agent_in_sites)

            message = (
                "Added the residue '{}' to the ".format(residue) +
                ref_agent_str
            )

            rhs_instance = self.rewrite(
                self._action_graph_id, rule, instance,
                rhs_typing=rhs_typing, message=message,
                update_type="manual")
            new_residue_id = rhs_instance[residue_id]

            # reconnect regions/sites to the new residue
            reconnect_residues(
                self.get_entity_identifier(), ref_gene, [new_residue_id],
                self.get_attached_regions(ref_gene),
                self.get_attached_sites(ref_gene))
        else:
            new_residue_id = residue_id

        # add semantic relations of the node
        for s in semantics:
            self.add_ag_node_semantics(new_residue_id, s)

        return new_residue_id

    def add_state(self, state, ref_agent, semantics=None):
        """Add state node to the action graph."""
        if ref_agent not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '{}' does not exist in the action graph".format(
                    ref_agent)
            )
        if self.get_action_graph_typing()[ref_agent] not in \
           ["protoform", "region", "site", "residue"]:
            raise KamiHierarchyError(
                "Cannot add a residue to the node '{}', node type "
                "is not valid (expected 'agent', 'region', 'site' "
                "or 'residue', '{}' was provided)".format(
                    ref_agent, self.get_action_graph_typing()[ref_agent])
            )

        # try to find an existing residue with this
        for state_node in self.get_attached_states(ref_agent):
            if list(self.action_graph.get_node(state_node)["name"])[0] ==\
               state.name:
                self.action_graph.get_node(state_node)[state.name].add(
                    state.test)
                return state_node

        ref_gene = self.get_protoform_of(ref_agent)

        state_id = ref_agent + "_" + str(state)

        rule = Rule.from_transform(NXGraph())
        rule.inject_add_node(state_id, state.meta_data())
        rhs_typing = {"meta_model": {state_id: "state"}}

        pattern = NXGraph()
        pattern.add_node(ref_agent)
        rule = Rule.from_transform(pattern)
        rule.inject_add_node(state_id, state.meta_data())
        rule.inject_add_edge(state_id, ref_agent)
        instance = {ref_agent: ref_agent}

        ref_agent_in_regions = self.is_region(ref_agent)
        ref_agent_in_sites = self.is_site(ref_agent)
        ref_agent_in_residues = self.is_residue(ref_agent)

        ref_agent_str = _generate_ref_agent_str(
            self, ref_agent, ref_gene, ref_agent_in_regions,
            ref_agent_in_sites, ref_agent_in_residues)

        message = (
            "Added the state '{}' to the ".format(state) +
            ref_agent_str
        )

        rhs_instance = self.rewrite(
            self._action_graph_id, rule, instance=instance,
            rhs_typing=rhs_typing,
            message=message,
            update_type="manual")
        res_state_id = rhs_instance[state_id]

        # add relation to a semantic ag node
        if semantics:
            for s in semantics:
                self.add_ag_node_semantics(res_state_id, s)
        return res_state_id

    def _generate_next_nugget_id(self, name=None):
        """Generate id for a new nugget."""
        if self._nugget_count is None:
            self._nugget_count = len(self.nuggets())
        self._nugget_count += 1
        if name is None:
            name = "nugget"

        generated_id = name + "_" + str(self._nugget_count)
        while self._id + "_" + generated_id in self.nuggets():
            self._nugget_count += 1
            generated_id = name + "_" + str(self._nugget_count)

        return generated_id

    def get_nugget_type(self, nugget_id):
        """Get type of the nugget specified by id."""
        return list(self._hierarchy.get_graph_attrs(
            nugget_id)["interaction_type"])[0]

    def is_mod_nugget(self, nugget_id):
        """Test if the nugget represents MOD."""
        t = self.get_nugget_type(nugget_id)
        return t == "mod"

    def is_bnd_nugget(self, nugget_id):
        """Test if the nugget represents BND."""
        t = self.get_nugget_type(nugget_id)
        return t == "bnd"

    def get_enzyme(self, nugget_id):
        """Get enzyme of the MOD nugget."""
        if self.is_mod_nugget(nugget_id):
            enzyme = None
            rel = self._hierarchy.get_relation(
                "mod_template", nugget_id)
            if "enzyme" in rel and len(rel["enzyme"]) > 0:
                enzyme = list(rel["enzyme"])[0]
            return enzyme
        else:
            raise KamiException("Nugget '{}' is not a mod nugget".format(
                nugget_id))

    def get_substrate(self, nugget_id):
        """Get substrate of the MOD nugget."""
        if self.is_mod_nugget(nugget_id):
            substrate = None
            rel = self._hierarchy.get_relation(
                "mod_template", nugget_id)
            try:
                substrate = list(rel["substrate"])[0]
                return substrate
            except:
                pass
        else:
            raise KamiException("Nugget '{}' is not a mod nugget".format(
                nugget_id))

    def get_left_partner(self, nugget_id):
        """Get the left partner of the BND nugget."""
        if self.is_bnd_nugget(nugget_id):
            left = None
            rel = self._hierarchy.get_relation(
                "bnd_template", nugget_id)
            try:
                left = list(rel["left_partner"])[0]
                return left
            except:
                pass
        else:
            raise KamiException("Nugget '{}' is not a bnd nugget".format(
                nugget_id))

    def get_right_partner(self, nugget_id):
        """Get the right partner of the BND nugget."""
        if self.is_bnd_nugget(nugget_id):
            right = None
            rel = self._hierarchy.get_relation(
                "bnd_template", nugget_id)
            try:
                right = list(rel["right_partner"])[0]
                return right
            except:
                pass
        else:
            raise KamiException("Nugget '{}' is not a bnd nugget".format(
                nugget_id))

    def get_nugget_template_rel(self, nugget_id):
        """Get relation of a nugget to a template."""
        nugget_type = self.get_nugget_type(nugget_id)
        return self._hierarchy.get_relation(
            nugget_id, nugget_type + "_template")

    def get_entity_identifier(self):
        """Get an identifier object with the AG being the reference graph."""
        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            hierarchy=self,
            graph_id=self._action_graph_id,
            meta_model_id="meta_model")
        return identifier

    def add_nugget(self, nugget_container, nugget_type,
                   template_rels=None, desc=None,
                   add_agents=True, anatomize=True,
                   apply_semantics=True):
        """Add nugget to the hierarchy."""
        if self._action_graph_id not in self._hierarchy.graphs():
            self.create_empty_action_graph()

        nugget_id = self._generate_next_nugget_id()
        nugget_graph_id = self._id + "_" + nugget_id

        # 2. Create a generation rule for this nugget
        p = NXGraph()
        lhs = NXGraph()
        generation_rule = Rule(p, lhs, nugget_container.graph)
        rhs_typing = {
            self._action_graph_id: nugget_container.reference_typing,
            "meta_model": nugget_container.meta_typing
        }

        # 3. Add empty graph as a nugget to the hierarchy
        attrs = {
            "type": "nugget",
            "interaction_type": nugget_type,
            "corpus_id": self._id
        }
        if desc is not None:
            attrs["desc"] = desc
        self._hierarchy.add_empty_graph(nugget_graph_id, attrs=attrs)

        self._hierarchy.add_typing(
            nugget_graph_id, self._action_graph_id, dict())

        # 4. Apply nugget generation rule
        if desc:
            interaction_repr = desc
        else:
            # TODO: here add a small nugget summary
            interaction_repr = "no description"

        message = "Added interaction '{}'".format(
            interaction_repr)

        r_g_prime = self.rewrite(
            nugget_graph_id,
            rule=generation_rule, instance={},
            rhs_typing=rhs_typing,
            strict=(not add_agents),
            message=message,
            update_type="manual")

        if template_rels is not None:
            for template_id, template_rel in template_rels.items():
                nugget_graph_template_rel = dict()
                for rhs_node, template_nodes in template_rel.items():
                    if len(template_nodes) > 0:
                        nugget_node = r_g_prime[rhs_node]
                        nugget_graph_template_rel[nugget_node] = set()
                        for el in template_nodes:
                            nugget_graph_template_rel[nugget_node].add(el)
                self.add_template_rel(
                    nugget_graph_id, template_id,
                    nugget_graph_template_rel)

        # Get a set of protoforms added by the nugget
        new_gene_nodes = set()

        for node in nugget_container.nodes():
            if nugget_container.meta_typing[node] == "protoform":
                new_nugget_node = r_g_prime[node]

                try:
                    ag_node = self._hierarchy.get_typing(
                        nugget_graph_id, self._action_graph_id)[new_nugget_node]

                    if ag_node not in nugget_container.reference_typing.values():

                        new_gene_nodes.add(ag_node)
                except:
                    pass

        # Check if all new protoforms agents from the nugget should be
        # distinct in the action grap

        protoforms_to_merge = {
            list(self.action_graph.get_node(protoform)["uniprotid"])[0]:
                set() for protoform in new_gene_nodes
        }
        for protoform in new_gene_nodes:
            protoforms_to_merge[
                list(self.action_graph.get_node(protoform)["uniprotid"])[0]].add(
                    protoform)

        for k, v in protoforms_to_merge.items():
            if len(v) > 1:
                pattern = NXGraph()
                pattern.add_nodes_from(v)
                rule = Rule.from_transform(pattern)
                rule.inject_merge_nodes(v, node_id=k)
                rhs_instance = self.rewrite(
                    self._action_graph_id, rule,
                    instance={
                        n: n for n in pattern.nodes()
                    },
                    message="Merged protoforms with the same UniProtAC '{}'".format(
                        k),
                    update_type="auto")

                merge_result = rhs_instance[k]
                if k in new_gene_nodes:
                    new_gene_nodes.remove(k)
                for vv in v:
                    if vv in new_gene_nodes:
                        new_gene_nodes.remove(vv)
                new_gene_nodes.add(merge_result)

        # 5. Anatomize new protoforms added as the result of nugget creation
        new_ag_regions = []
        if anatomize is True:
            if len(new_gene_nodes) > 0:
                for protoform in new_gene_nodes:
                    added_regions = anatomize_gene(self, protoform)
                    new_ag_regions += added_regions

        ag_typing = self.get_action_graph_typing()
        nugget_typing = self._hierarchy.get_typing(
            nugget_graph_id, self._action_graph_id)

        all_protoforms = []

        for node in self.get_nugget(nugget_graph_id).nodes():
            ag_node = nugget_typing[node]
            if ag_typing[ag_node] == "protoform":
                all_protoforms.append(ag_node)

        # Apply bookkeeping updates
        target_nodes = [
            self._hierarchy.get_typing(
                nugget_graph_id, self._action_graph_id)[n]
            for n in self.get_nugget(nugget_graph_id).nodes()
        ] + new_ag_regions

        identifier = self.get_entity_identifier()

        apply_bookkeeping(identifier, target_nodes, all_protoforms)

        # 6. Apply semantics to the nugget
        if apply_semantics is True:
            if "mod" in self._hierarchy.get_graph_attrs(
               nugget_graph_id)["interaction_type"]:
                apply_mod_semantics(self, nugget_graph_id)

            elif "bnd" in self._hierarchy.get_graph_attrs(
                    nugget_graph_id)["interaction_type"]:
                apply_bnd_semantics(self, nugget_graph_id)

        return nugget_graph_id

    def add_interaction(self, interaction, add_agents=True,
                        anatomize=True, apply_semantics=True):
        """Add a n interaction to the model."""
        if self._action_graph_id not in self._hierarchy.graphs():
            self.create_empty_action_graph()

        (
            nugget_container,
            nugget_type,
            template_rels,
            desc
        ) = generate_nugget(self, interaction)

        # Add it to the hierarchy performing respective updates
        nugget_id = self.add_nugget(
            nugget_container=nugget_container,
            nugget_type=nugget_type,
            template_rels=template_rels,
            desc=desc,
            add_agents=add_agents,
            anatomize=anatomize,
            apply_semantics=apply_semantics)

        return nugget_id

    def add_interactions(self, interactions, add_agents=True,
                         anatomize=True, apply_semantics=True):
        """Add a collection of interactions to the model."""
        nugget_ids = []
        for i in interactions:
            nugget_id = self.add_interaction(
                i, add_agents, anatomize, apply_semantics)
            nugget_ids.append(nugget_id)
        return nugget_ids

    def type_nugget_by_ag(self, nugget_id, typing):
        """Type nugget by the action graph."""
        self._hierarchy.add_typing(
            nugget_id, self._action_graph_id, typing)
        return

    def type_nugget_by_meta(self, nugget_id, typing):
        """Type nugget by the meta-model."""
        self._hierarchy.add_typing(
            nugget_id, "meta_model", typing)
        return

    def add_template_rel(self, nugget_id, template_id, rel):
        """Relate nugget to mod template."""
        self._hierarchy.add_relation(
            nugget_id, template_id, rel)
        return

    def add_semantic_nugget_rel(self, nugget_id, semantic_nugget_id, rel):
        """Relate a nugget to a semantic nugget."""
        self._hierarchy.add_relation(
            nugget_id, semantic_nugget_id, rel)

        return

    def unique_kinase_region(self, protoform):
        """Get the unique kinase region of the protoform."""
        ag_sag_relation = self._hierarchy.get_relation(
            self._action_graph_id, "semantic_action_graph")
        kinase = None
        for node in self.action_graph.predecessors(protoform):
            if node in ag_sag_relation.keys() and\
               "protein_kinase" in ag_sag_relation[node]:
                    if kinase is None:
                        kinase = node
                    else:
                        return None
        return kinase

    def get_activity_state(self, protoform):
        """Get activity state of a protoform in the action graph."""
        states = self.get_attached_states(protoform)

        for state in states:
            if "activity" in self.action_graph.get_node(state)["name"]:
                return state
        return None

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

    def set_nugget_desc(self, nugget_id, new_desc):
        """Get nugget description string."""
        self._hierarchy.set_graph_attrs(
            nugget_id, {"desc": new_desc})

    def get_nugget_typing(self, nugget_id):
        """Get typing of the nugget by the action graph."""
        return self._hierarchy.get_typing(
            nugget_id, self._action_graph_id)

    def get_action_graph_attrs(self):
        """Get action graph attributes."""
        return self._hierarchy.get_graph_attrs(
            self._action_graph_id)

    def set_action_graph_attrs(self, attrs):
        """Set action graph attributes."""
        self._hierarchy.set_graph_attrs(
            self._action_graph_id, attrs)

    def get_ag_node(self, node):
        """Get node from the action graph."""
        return self.action_graph.get_node(node)

    def to_json(self):
        """Return json repr of the corpus."""
        json_data = {}
        json_data["corpus_id"] = self._id
        json_data["annotation"] = self.annotation.to_json()
        json_data["creation_time"] = self.creation_time
        json_data["last_modified"] = self.last_modified
        json_data["versioning"] = self._versioning.to_json()

        json_data["action_graph"] = self.action_graph.to_json()
        json_data["action_graph_typing"] = self.get_action_graph_typing()
        json_data["action_graph_semantics"] = relation_to_json(
            self._hierarchy.get_relation(
                self._action_graph_id, "semantic_action_graph"))

        json_data["nuggets"] = []
        for nugget in self.nuggets():
            template = self.get_nugget_type(nugget) + "_template"
            nugget_json = {
                "id": nugget,
                "graph": self.get_nugget(nugget).to_json(),
                "desc": self.get_nugget_desc(nugget),
                "typing": self.get_nugget_typing(nugget),
                "attrs": attrs_to_json(self._hierarchy.get_graph_attrs(
                    nugget)),
                "template_rel": (
                    template,
                    relation_to_json(self.get_nugget_template_rel(nugget))
                ),
                "semantic_rels": {
                    s: relation_to_json(self._hierarchy.get_relation(
                        nugget, s))
                    for s in self._hierarchy.adjacent_relations(nugget)
                    if s != template
                }
            }

            json_data["nuggets"].append(nugget_json)
        return json_data

    def export_json(self, filename):
        """Export corpus to json."""
        with open(filename, 'w') as f:
            j_data = self.to_json()
            json.dump(j_data, f)

    @classmethod
    def from_json(cls, corpus_id, json_data, annotation=None,
                  creation_time=None, last_modified=None,
                  backend="networkx",
                  uri=None, user=None, password=None, driver=None):
        """Create hierarchy from json representation."""
        corpus = cls(corpus_id, annotation=annotation,
                     creation_time=creation_time, last_modified=last_modified,
                     backend=backend,
                     uri=uri, user=user, password=password, driver=driver,
                     data=json_data)
        return corpus

    @classmethod
    def load_json(cls, corpus_id, filename, annotation=None,
                  creation_time=None, last_modified=None,
                  backend="networkx",
                  uri=None, user=None, password=None, driver=None):
        """Load a KamiCorpus from its json representation."""
        if os.path.isfile(filename):
            with open(filename, "r+") as f:
                json_data = json.loads(f.read())
                corpus = cls.from_json(
                    corpus_id, json_data, annotation=annotation,
                    creation_time=creation_time, last_modified=last_modified,
                    backend=backend,
                    uri=uri, user=user, password=password, driver=driver)
            return corpus
        else:
            raise KamiHierarchyError("File '{}' does not exist!".format(filename))

    def instantiate(self, model_id, definitions=None, seed_genes=None,
                    annotation=None, default_bnd_rate=None,
                    default_brk_rate=None, default_mod_rate=None):
        """Instantiate a signalling model from a corpus.

        Parameters
        ----------
        model_id : hashable
            ID of the new model.
        definitions : iterable of kami.data_structures.Definition
            List of protein definitions used for instantiation.
        seed_genes : iterable of str
            List of UniProt AC's of genes whose protoforms should be added to
            the model, the rest of the protoforms and their interactions
            are filtered (and not included in the instantiated model).
        annotation : kami.data_structures.annotations.CorpusAnnotation
            Model annotations
        """

        if annotation is None:
            annotation = ModelAnnotation()

        if self._backend == "neo4j":
            # To create a model we duplicate subgraph of the Neo4jHierarchy
            graph_dict = {
                self._id + "_action_graph": model_id + "_action_graph"
            }
            nugget_attrs = dict()
            for nugget in self.nuggets():
                graph_dict[nugget] = model_id + "_" + nugget
                attrs = self._hierarchy.get_graph_attrs(nugget)
                nugget_attrs[model_id + "_" + nugget] = attrs
                nugget_attrs[model_id + "_" + nugget][
                    "model_id"] = model_id

            self._hierarchy.duplicate_subgraph(
                graph_dict, attach_graphs=[
                    "meta_model", "bnd_template", "mod_template"])
            for k, v in nugget_attrs.items():
                self._hierarchy.set_graph_attrs(k, v)

            model = KamiModel(
                model_id, annotation,
                creation_time=str(datetime.datetime.now()),
                last_modified=str(datetime.datetime.now()),
                corpus_id=self._id,
                seed_genes=seed_genes,
                definitions=definitions,
                backend="neo4j",
                driver=self._hierarchy._driver,
                default_bnd_rate=default_bnd_rate,
                default_brk_rate=default_brk_rate,
                default_mod_rate=default_mod_rate)
        else:
            # To create a model we first copy knowledge
            # present in the corpus
            model = KamiModel(
                model_id, annotation,
                creation_time=str(datetime.datetime.now()),
                last_modified=str(datetime.datetime.now()),
                corpus_id=self._id,
                seed_genes=seed_genes,
                definitions=definitions,
                default_bnd_rate=default_bnd_rate,
                default_brk_rate=default_brk_rate,
                default_mod_rate=default_mod_rate)
            model._copy_knowledge_from_corpus(self)

        if definitions is not None:
            # We then apply an instantiation rule generated for
            # every provided definition and clean-up invalidated nuggets
            for d in definitions:
                instantiation_rule, instance = d.generate_rule(
                    self.action_graph, self.get_action_graph_typing())
                rhs_g = model.rewrite(
                    model._action_graph_id,
                    instantiation_rule,
                    instance,
                    message="Instantiation update",
                    update_type="auto")
                model._add_component_equivalence(
                    instantiation_rule, instance, rhs_g)
                model._clean_up_nuggets()
        return model

    def get_uniprot(self, gene_id):
        attrs = self.action_graph.get_node(gene_id)
        uniprotid = None
        if "uniprotid" in attrs.keys():
            uniprotid = list(attrs["uniprotid"])[0]
        return uniprotid

    def get_hgnc_symbol(self, gene_id):
        attrs = self.action_graph.get_node(gene_id)
        hgnc_symbol = None
        if "hgnc_symbol" in attrs.keys():
            hgnc_symbol = list(attrs["hgnc_symbol"])[0]
        return hgnc_symbol

    def get_synonyms(self, gene_id):
        attrs = self.action_graph.get_node(gene_id)
        synonyms = None
        if "synonyms" in attrs.keys():
            synonyms = list(attrs["synonyms"])
        return synonyms

    def get_protoform_data(self, gene_id, get_nuggets=True):
        """."""
        attrs = self.action_graph.get_node(gene_id)
        uniprotid = None
        if "uniprotid" in attrs.keys():
            uniprotid = list(attrs["uniprotid"])[0]
        hgnc_symbol = None
        if "hgnc_symbol" in attrs.keys():
            hgnc_symbol = list(attrs["hgnc_symbol"])[0]
        synonyms = None
        if "synonyms" in attrs.keys():
            synonyms = list(attrs["synonyms"])
        nuggets = None
        if get_nuggets:
            nuggets = self._hierarchy.graphs_typed_by_node(
                self._action_graph_id, gene_id)
        return (uniprotid, hgnc_symbol, synonyms, nuggets)

    def get_modification_data(self, mod_id):

        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, self._action_graph_id)

        enzyme_protoforms = identifier.ancestors_of_type(mod_id, "protoform")
        substrate_protoforms = identifier.descendants_of_type(mod_id, "protoform")
        nuggets = self._hierarchy.graphs_typed_by_node(
            self._action_graph_id, mod_id)
        return (nuggets, enzyme_protoforms, substrate_protoforms)

    def get_binding_data(self, bnd_id):
        """Get data related to a binding node."""
        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            hierarchy=self, graph_id=self._action_graph_id)

        all_protoforms = identifier.ancestors_of_type(bnd_id, "protoform")
        nuggets = self._hierarchy.graphs_typed_by_node(
            self._action_graph_id, bnd_id)
        return (nuggets, all_protoforms)

    def get_bindings(self, left_ac, right_ac):
        """Get all bnd mechanisms between left and right."""
        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            immediate=False)
        return identifier.get_bindings(left_ac, right_ac)

    def get_modifications(self, enzyme_ac, substrate_ac):
        """Get all bnd mechanisms between left and right."""
        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            immediate=False)
        return identifier.get_modifications(
            enzyme_ac, substrate_ac)

    def get_protoform_pairwise_interactions(self):
        """Get pairwise interactions between protoforms."""
        interactions = {}

        def _add_to_interactions(s, t, n, n_type, n_desc):
            if s in interactions:
                if t in interactions[s]:
                    interactions[s][t].add((n, n_type, n_desc))
                else:
                    interactions[s][t] = {(n, n_type, n_desc)}
            else:
                interactions[s] = {
                    t: {(n, n_type, n_desc)}
                }

        for n in self.nuggets():
            ag_typing = self._hierarchy.get_typing(n, self._action_graph_id)
            if self.is_mod_nugget(n):
                enzyme = self.get_enzyme(n)
                substrate = self.get_substrate(n)
                if enzyme is not None and substrate is not None:
                    _add_to_interactions(
                        ag_typing[enzyme], ag_typing[substrate],
                        n, "mod", self.get_nugget_desc(n))
            elif self.is_bnd_nugget(n):
                left = self.get_left_partner(n)
                right = self.get_right_partner(n)
                if left is not None and right is not None:
                    _add_to_interactions(
                        ag_typing[left], ag_typing[right],
                        n, "bnd", self.get_nugget_desc(n))
        return interactions

    def update_nugget_node_attr(self, nugget_id, node_id, node_attrs):
        lhs = NXGraph()
        lhs_attrs = self.get_nugget(nugget_id).get_node(node_id)
        lhs.add_node(node_id, lhs_attrs)
        p = NXGraph()
        p_attrs = {}
        for k, v in lhs_attrs.items():
            if k not in node_attrs.keys():
                p_attrs[k] = v
        p.add_node(node_id, p_attrs)
        rhs = NXGraph()
        rhs.add_node(node_id, node_attrs)
        rule = Rule(p, lhs, rhs)
        self.rewrite(
            nugget_id, rule,
            message=(
                "Manual update of the attributes (value '{}') ".format(
                    node_attrs) +
                "of the node '{}' in the nugget '{}'".format(node_id, nugget_id)
            ),
            update_type="manual"
        )

    def update_nugget_node_attr_from_json(self, nugget_id, node_id, json_node_attrs):
        self.update_nugget_node_attr(
            nugget_id, node_id, attrs_from_json(json_node_attrs))

    def update_nugget_edge_attr(self, nugget_id, source, target, edge_attrs):
        lhs = NXGraph()
        lhs_attrs = self.get_nugget(nugget_id).get_edge(source, target)
        lhs.add_nodes_from([source, target])
        lhs.add_edge(source, target, lhs_attrs)
        p = NXGraph()
        p.add_nodes_from([source, target])
        p_attrs = {}
        for k, v in lhs_attrs.items():
            if k not in edge_attrs.keys():
                p_attrs[k] = v
        p.add_edge(source, target, p_attrs)
        rhs = NXGraph()
        rhs.add_nodes_from([source, target])
        rhs.add_edge(source, target, edge_attrs)
        rule = Rule(p, lhs, rhs)
        self.rewrite(
            nugget_id, rule,
            message=(
                "Manual update of the attributes (value '{}') ".format(
                    edge_attrs) +
                "of the edge '{}->{}' in the nugget '{}'".format(
                    source, target, nugget_id)
            ),
            update_type="manual"
        )

    def update_nugget_edge_attr_from_json(self, nugget_id, source, target, json_node_attrs):
        self.update_nugget_edge_attr(
            nugget_id, source, target, attrs_from_json(json_node_attrs))

    def load_interactions_from_json(self, jsonfile, add_agents=True,
                                    anatomize=True, apply_semantics=True):
        with open(jsonfile, "r") as f:
            raw = json.load(f)
            for el in raw:
                i = Interaction.from_json(el)
                self.add_interaction(
                    i, add_agents=add_agents,
                    anatomize=anatomize, apply_semantics=apply_semantics)

    def subcomponent_nodes(self, node_id):
        """Get all the subcomponent nodes."""
        ag_typing = self.get_action_graph_typing()
        all_predecessors = self.action_graph.predecessors(node_id)
        subcomponents = set([
            p for p in all_predecessors
            if ag_typing[p] != "mod" and ag_typing[p] != "bnd"
        ] + [node_id])
        visited = set()
        next_level_to_visit = set([
            p for p in all_predecessors
            if ag_typing[p] != "mod" and ag_typing[p] != "bnd"
        ])
        while len(next_level_to_visit) > 0:
            new_level_to_visit = set()
            for n in next_level_to_visit:
                if n not in visited:
                    visited.add(n)
                    new_anc = set([
                        p
                        for p in self.action_graph.predecessors(n)
                        if ag_typing[p] != "mod" and ag_typing[p] != "bnd"
                    ])
                    subcomponents.update(new_anc)
                new_level_to_visit.update(new_anc)
            next_level_to_visit = new_level_to_visit
        return subcomponents

    def get_canonical_sequence(self, gene_node_id):
        attrs = self.action_graph.get_node(gene_node_id)
        uniprotid = self.get_uniprot(gene_node_id)
        if "canonical_sequence" in attrs:
            return list(attrs["canonical_sequence"])[0]
        else:
            seq = fetch_canonical_sequence(uniprotid)
            self.action_graph.add_node_attrs(
                gene_node_id,
                {
                    "canonical_sequence": seq
                }
            )

    def get_fragment_location(self, fragment_node_id):
        start = None
        end = None
        protoform = self.get_protoform_of(fragment_node_id)

        if protoform is not None:
            attrs = self.action_graph.get_edge(fragment_node_id, protoform)
            if "start" in attrs:
                start = list(attrs["start"])[0]
            if "end" in attrs:
                end = list(attrs["end"])[0]
        return start, end

    def get_residue_location(self, residue_node_id):
        loc = None
        protoform = self.get_protoform_of(residue_node_id)

        if protoform is not None:
            attrs = self.action_graph.get_edge(residue_node_id, protoform)
            if "loc" in attrs:
                loc = list(attrs["loc"])[0]
        return loc

    def interaction_edges(self):
        interactions = self.get_protoform_pairwise_interactions()
        edges = []
        for protoform, (partners, nuggets) in interactions.items():
            for i, partner in enumerate(partners):
                if (protoform, partner) not in edges and (partner, protoform) not in edges:
                    edges.append({"source": protoform, "target": partner})
        return edges

    def remove_nugget(self, nugget_id):
        """Remove nugget from a corpus."""
        if nugget_id in self.nuggets():
            self._hierarchy.remove_graph(nugget_id)

    def get_mechanism_nuggets(self, mechanism_id):
        """Get nuggets associated with the interaction mechanism."""
        if (self._backend == "neo4j"):
            cypher = (
                "MATCH (n:{} {{id: '{}'}}), (m)-[:typing]->(n)\n".format(
                    self._action_graph_id, mechanism_id) +
                "RETURN collect(labels(m)[0]) as nuggets"
            )
            result = self._hierarchy.execute(cypher)
            return result.single()["nuggets"]
        else:
            raise KamiException(
                "This method is not implemented for NetworkX-based hierarchies!")

    def new_branch(self, branch_name):
        """Create a new branch of the corpus."""
        self._versioning.branch(branch_name)

    def switch_branch(self, branch_name):
        """Switch to the branch of the corpus."""
        self._versioning.switch_branch(branch_name)

    def print_revision_history(self):
        """Print revision history of the corpus."""
        print("Time\tBranch\tType\tMessage")
        for n in self._versioning._revision_graph.nodes():
            print("{}\t{}\t{}\t{}".format(
                self._versioning._revision_graph.nodes[n]["time"].strftime(
                    "%d/%m/%Y %H:%M:%S"),
                self._versioning._revision_graph.nodes[n]["branch"],
                self._versioning._revision_graph.nodes[n]["update_type"]
                if "update_type" in self._versioning._revision_graph.nodes[n]
                else "auto",
                self._versioning._revision_graph.nodes[n]["message"]))
