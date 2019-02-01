"""Classes for KAMI knowledge corpora.

Corpora in KAMI are decontextualised signalling knowledge bases.
"""

import copy
import time

import networkx as nx

from kami.resources import default_components

from regraph import (Rule, Neo4jHierarchy, NetworkXHierarchy)
from regraph.primitives import (add_node, add_edge,
                                get_node, get_edge,
                                add_nodes_from,
                                add_edges_from)

from kami.utils.generic import normalize_to_set
from kami.utils.id_generators import generate_new_id
from kami.aggregation.bookkeeping import (anatomize_gene,
                                          reconnect_residues,
                                          reconnect_sites,
                                          connect_nested_fragments,
                                          connect_transitive_components)
from kami.aggregation.generators import generate_nugget
from kami.aggregation.semantics import (apply_mod_semantics,
                                        apply_bnd_semantics)
from kami.aggregation.identifiers import EntityIdentifier
from kami.exceptions import KamiHierarchyError


class KamiCorpus(object):
    """Class for Kami corpora (de-contextualized knowledge).

    Attributes
    ----------
    _backend : str, "networkx" or "neo4j"
    _hierarchy :
    _nugget_count :
    action_graph :
    nugget :
    mod_template :
    bnd_templae :
    semantic_action_graph :
    """

    nugget_dict_factory = dict
    semantic_nugget_dict_factory = dict

    def __init__(self, ag=None, ag_typing=None, ag_semantics=None,
                 nuggets=None, nuggets_template_rels=None,
                 nuggets_ag_typing=None, nuggets_semantic_rels=None,
                 backend="networkx", uri=None, user=None,
                 password=None):
        """Initialize a KAMI model.

        By default action graph is empty, typed by `meta_model` (meta-model)
        `self.action_graph` -- direct access to the action graph.
        `self.action_graph_typing` -- direct access to typing of
        the action graph nodes by the meta-model.
        `self.mod_template` and `self.bnd_template` -- direct access to
        the nugget template graphs.
        """
        self._backend = backend
        if backend == "networkx":
            self._hierarchy = NetworkXHierarchy()
        elif backend == "neo4j":
            self._hierarchy = Neo4jHierarchy(uri, user, password)

        # Add KAMI-specific invariant components of the hierarchy
        for graph_id, graph, attrs in default_components.GRAPHS:
            if graph_id not in self._hierarchy.graphs():
                self._hierarchy.add_empty_graph(graph_id, attrs)
                g = self._hierarchy.get_graph(graph_id)
                add_nodes_from(g, graph["nodes"])
                add_edges_from(g, graph["edges"])

        for s, t, mapping, attrs in default_components.TYPING:
            if (s, t) not in self._hierarchy.typings():
                self._hierarchy.add_typing(s, t, mapping, attrs=attrs)
        for rule_id, rule, attrs in default_components.RULES:
            self._hierarchy.add_rule(rule_id, rule, attrs)
        for s, t, (lhs_mapping, rhs_mapping), attrs in default_components.RULE_TYPING:
            self._hierarchy.add_rule_typing(
                s, t, lhs_mapping, rhs_mapping,
                lhs_total=True, rhs_total=True, attrs=attrs)
        for u, v, rel, attrs in default_components.RELATIONS:
            if (u, v) not in self._hierarchy.relations():
                self._hierarchy.add_relation(u, v, rel, attrs)

        # Initialization of knowledge-related components
        # Action graph related init
        if ag is not None:
            # ag = copy.deepcopy(ag)
            self._hierarchy.add_graph("action_graph", ag, {"type": "action_graph"})

            if ag_typing is not None:
                ag_typing = copy.deepcopy(ag_typing)
                self._hierarchy.add_typing("action_graph", "meta_model", ag_typing)

            if ag_semantics is not None:
                ag_semantics = copy.deepcopy(ag_semantics)
                self._hierarchy.add_relation(
                    "action_graph", "semantic_action_graph",
                    ag_semantics)

        self.nugget_dict_factory = ndf = self.nugget_dict_factory

        self.nugget = ndf()

        # Nuggets related init
        if nuggets is not None:
            for nugget_id, nugget_graph in nuggets:
                self._hierarchy.add_graph(
                    nugget_id, nugget_graph, {"type": "nugget"})
                self.nugget[nugget_id] = self._hierarchy.get_graph(
                    nugget_id)

        if nuggets_ag_typing is not None:
            for nugget_id, typing in nuggets_ag_typing.items():
                self._hierarchy.add_typing(
                    nugget_id, "action_graph", typing)

        if nuggets_template_rels is not None:
            for nugget_id, nugget_rels in nuggets_template_rels.items():
                for template_id, rel in nugget_rels.items():
                    self._hierarchy.add_relation(
                        nugget_id, template_id, rel)

        if nuggets_semantic_rels is not None:
            for nugget_id, nugget_rels in nuggets_semantic_rels.items():
                for s_nugget_id, rel in nugget_rels.items():
                    self._hierarchy.add_relation(
                        nugget_id,
                        s_nugget_id,
                        rel
                    )

        self._init_shortcuts()
        return

    def _init_shortcuts(self):
        """Initialize kami-specific shortcuts."""
        if "action_graph" in self._hierarchy.graphs():
            self.action_graph =\
                self._hierarchy.get_graph("action_graph")
        else:
            self.action_graph = None

        self.mod_template = self._hierarchy.get_graph("mod_template")
        self.bnd_template = self._hierarchy.get_graph("bnd_template")
        self.semantic_action_graph = self._hierarchy.get_graph(
            "semantic_action_graph")
        self.nugget = self.nugget_dict_factory()
        for n in self._hierarchy.graphs():
            if "nugget" in self._hierarchy.get_graph_attrs(n)["type"]:
                self.nugget[n] = self._hierarchy.get_graph(n)
        self._nugget_count = len(self.nuggets())

    def create_empty_action_graph(self):
        """Creat an empty action graph in the hierarchy."""
        self._hierarchy.add_empty_graph(
            "action_graph",
            {"type": "action_graph"}
        )
        self._hierarchy.add_typing(
            "action_graph",
            "meta_model",
            dict()
        )
        self._hierarchy.add_relation(
            "action_graph",
            "semantic_action_graph",
            dict()
        )
        self.action_graph = self._hierarchy.get_graph("action_graph")
        # self.action_graph_typing = self._hierarchy.get_typing(
        #  "action_graph", "meta_model")
        return

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

    @classmethod
    def from_json(cls, json_data, backend="networkx", ignore=None, directed=True):
        """Create hierarchy from json representation."""
        default_graphs = [graph_id for graph_id,
                          _, _ in default_components.GRAPHS]
        default_typings = [(s, t) for s, t, _, _ in default_components.TYPING]
        default_rules = [rule_id for rule_id, _, _ in default_components.RULES]
        default_rule_typings = [(s, t)
                                for s, t, _, _, _ in default_components.RULE_TYPING]
        default_relations = [(s, t)
                             for s, t, _ in default_components.RELATIONS]

        # filter nodes and edges of the hierarchy that are created by default
        ignore_components = {
            "graphs": default_graphs,
            "typing": default_typings,
            "rules": default_rules,
            "rule_typing": default_rule_typings,
            "relations": default_relations
        }
        if backend == "networkx":
            hierarchy = NetworkXHierarchy.from_json(
                json_data, ignore_components, directed)
        elif backend == "neo4j":
            hierarchy = Neo4jHierarchy.from_json(
                json_data, ignore_components, directed)
        model = cls.from_hierarchy(hierarchy)
        model._init_shortcuts()
        return model

    @classmethod
    def from_hierarchy(cls, hierarchy):
        """Initialize KamiCorpus obj from a graph hierarchy."""
        model = cls()
        model._hierarchy = hierarchy
        model._init_shortcuts()
        return model

    @classmethod
    def copy(cls, corpus):
        """Create a copy of the corpus."""
        if corpus._backend == "networkx":
            hierarchy_copy = NetworkXHierarchy.copy(corpus._hierarchy)
        elif corpus._backend == "neo4j":
            hierarchy_copy = Neo4jHierarchy.copy(corpus._hierarchy)
        return cls.from_hierarchy(hierarchy_copy)

    @classmethod
    def load(cls, filename, backend="networkx", directed=True):
        """Load a KamiCorpus from its json representation."""
        if backend == "networkx":
            hierarchy = NetworkXHierarchy.load(filename)
        elif backend == "neo4j":
            hierarchy = Neo4jHierarchy.load(filename)
        return KamiCorpus.from_hierarchy(hierarchy)

    def get_action_graph_typing(self):
        """Get typing of the action graph by meta model."""
        typing = dict()
        if ("action_graph", "meta_model") in self._hierarchy.typings():
            typing =\
                self._hierarchy.get_typing("action_graph", "meta_model")
        return typing

    def is_nugget_graph(self, node_id):
        graph_attrs = self._hierarchy.get_graph_attrs(node_id)
        if "type" in graph_attrs.keys():
            if "nugget" in graph_attrs["type"]:
                return True
        return False

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
            if "semantic_nugget" in self._hierarchy.get_graph_attrs(node_id)["type"]:
                nuggets.append(node_id)
        return nuggets

    def nugget_relations(self):
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

    def mod_semantic_nuggets(self):
        """Get a list of semantic nuggets related to mod interactions."""
        nuggets = []
        for node_id in self._hierarchy.graphs():
            if "semantic_nugget" in self._hierarchy.get_graph_attrs(node_id)["type"] and\
               "mod" in self._hierarchy.get_graph_attrs(node_id)["interaction_type"]:
                nuggets.append(node_id)
        return nuggets

    def bnd_semantic_nuggets(self):
        """Get a list of semantic nuggets related to bnd interactions."""
        nuggets = []
        for node_id in self._hierarchy.graphs():
            if "semantic_nugget" in self._hierarchy.get_graph_attrs(node_id)["type"] and\
               "bnd" in self._hierarchy.get_graph_attrs(node_id)["interaction_type"]:
                nuggets.append(node_id)
        return nuggets

    def empty(self):
        """Test if hierarchy is empty."""
        return (len(self.nuggets()) == 0) and\
               ((self.action_graph is None) or
                (len(self.action_graph.nodes()) == 0))

    def nodes_of_type(self, type_name):
        """Get action graph nodes of a specified type."""
        nodes = []
        action_graph_typing = self.get_action_graph_typing()

        if self.action_graph is not None and\
           len(action_graph_typing) > 0:
            for node in self.action_graph.nodes():
                if action_graph_typing[node] == type_name:
                    nodes.append(node)
        return nodes

    def get_ag_node_data(self, node_id):
        if node_id not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '{}' is not found in the action graph".format(node_id))
        data = dict()
        node_attrs = get_node(self.action_graph, node_id)

        for key, value in node_attrs.items():
            data[key] = value.toset()

        action_graph_typing = self.get_action_graph_typing()

        if action_graph_typing[node_id] == "residue":
            gene_node = self.get_gene_of(node_id)
            edge_attrs = get_edge(self.action_graph, node_id, gene_node)
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

    def genes(self):
        """Get a list of agent nodes in the action graph."""
        return self.nodes_of_type("gene")

    def regions(self):
        """Get a list of region nodes in the action graph."""
        return self.nodes_of_type("region")

    def sites(self):
        """Get a list of site nodes in the action graph."""
        return self.nodes_of_type("site")

    def bindings(self):
        """Get a list of bnd nodes in the action graph."""
        return self.nodes_of_type("bnd")

    def modifications(self):
        """Get a list of bnd nodes in the action graph."""
        return self.nodes_of_type("mod")

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

    def get_gene_of(self, element_id):
        """Get agent id conntected to the element."""
        action_graph_typing = self.get_action_graph_typing()

        if action_graph_typing[element_id] == "gene":
            return element_id
        else:
            # bfs to find a gene
            visited = set()
            next_level_to_visit = self.action_graph.successors(
                element_id)
            while len(next_level_to_visit) > 0:
                new_level_to_visit = set()
                for n in next_level_to_visit:
                    if n not in visited:
                        visited.add(n)
                        if action_graph_typing[n] == "gene":
                            return n
                    new_level_to_visit.update(
                        self.action_graph.successors(n))
                next_level_to_visit = new_level_to_visit
        raise KamiHierarchyError(
            "No gene node is associated with an element '{}'".fromat(
                element_id))
        return None

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
        self._hierarchy.set_node_typing(
            "action_graph", "meta_model", node_id, meta_type)

    def add_gene(self, gene, rewriting=False):
        """Add gene node to action graph.

        gene : kami.entities.Gene
        rewriting : bool
            Flag indicating if the action graph should be modified
            by SqPO rewriting (if True) or primitive operations (if False)
        """
        if self.action_graph is None:
            self.create_empty_action_graph()
        if gene.uniprotid:
            gene_id = gene.uniprotid
        else:
            gene_id = generate_new_id(
                self.action_graph, "unkown_agent")
        if rewriting:
            rule = Rule.from_transform(nx.DiGraph())
            rule.inject_add_node(gene_id, gene.meta_data())
            rhs_typing = {"meta_model": {gene_id: "gene"}}
            _, rhs_instance = self.rewrite(
                "action_graph", rule, instance={},
                rhs_typing=rhs_typing)
            return rhs_instance[gene_id]
        else:
            add_node(self.action_graph, gene_id, gene.meta_data())
            self.set_ag_meta_type(gene_id, "gene")
            return gene_id

    def add_mod(self, attrs=None, semantics=None, rewriting=False):
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

        if rewriting:
            rule = Rule.from_transform(nx.DiGraph())
            rule.inject_add_node(mod_id, attrs)
            rhs_typing = {"meta_model": {mod_id: "mod"}}
            _, rhs_instance = self.rewrite(
                "action_graph", rule, instance={},
                rhs_typing=rhs_typing)
            res_mod_id = rhs_instance[mod_id]
        else:
            add_node(self.action_graph, mod_id, attrs)
            self.set_ag_meta_typing(mod_id, "mod")
            res_mod_id = mod_id

        # add semantic relations of the node
        for s in semantics:
            self.add_ag_node_semantics(res_mod_id, s)

        return res_mod_id

    def add_ag_node_semantics(self, node_id, semantic_node):
        """Add relation of `node_id` with `semantic_node`."""
        self._hierarchy.set_node_relation(
            "action_graph",
            "semantic_action_graph",
            node_id, semantic_node)
        return

    def ag_node_semantics(self, node_id):
        """Get semantic nodes related to the `node_id`."""
        result = set()
        rel = self._hierarchy.get_relation(
            "action_graph", "semantic_action_graph")
        for node, semantic_nodes in rel.items():
            if node == node_id:
                result.update(semantic_nodes)
        return result

    def add_region(self, region, ref_gene, semantics=None, rewriting=False):
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
        if ref_gene not in self.genes():
            raise KamiHierarchyError(
                "Gene '{}' is not found in the action graph".format(ref_gene))

        semantics = normalize_to_set(semantics)

        region_id = generate_new_id(
            self.action_graph, "{}_{}".format(ref_gene, str(region)))

        if rewriting:
            pattern = nx.DiGraph()
            pattern.add_node(ref_gene)
            rule = Rule.from_transform(pattern)
            rule.inject_add_node(region_id, region.meta_data())
            rule.inject_add_edge(region_id, ref_gene, region.location())
            rhs_typing = {"meta_model": {region_id: "region"}}
            _, rhs_instance = self.rewrite(
                "action_graph", rule, instance={ref_gene: ref_gene},
                rhs_typing=rhs_typing)
            res_region_id = rhs_instance[region_id]
        else:
            add_node(self.action_graph, region_id, region.meta_data())
            self.set_ag_meta_type(region_id, "region")
            add_edge(
                self.action_graph, region_id, ref_gene, region.location())
            res_region_id = region_id

        if semantics is not None:
            for s in semantics:
                self.add_ag_node_semantics(res_region_id, s)

        # reconnect all the residues & sites of the corresponding gene
        # that lie in the region range
        reconnect_residues(
            self, ref_gene,
            self.get_attached_residues(ref_gene),
            [res_region_id])

        reconnect_sites(
            self, ref_gene,
            self.get_attached_sites(ref_gene),
            [res_region_id]
        )

        return res_region_id

    def add_site(self, site, ref_agent, semantics=None, rewriting=True):
        """Add site node to the action graph."""
        ref_agent_in_genes = ref_agent in self.genes()
        ref_agent_in_regions = ref_agent in self.regions()

        if ref_agent_in_genes:
            ref_gene = ref_agent
        else:
            ref_gene = self.get_gene_of(ref_agent)

        semantics = normalize_to_set(semantics)

        if not ref_agent_in_genes and not ref_agent_in_regions:
            raise KamiHierarchyError(
                "Neither agent nor region '%s' is not "
                "found in the action graph" %
                ref_agent
            )
        site_id = generate_new_id(
            self.action_graph, "{}_{}".format(ref_agent, str(site)))

        if rewriting:
            pattern = nx.DiGraph()
            pattern.add_node(ref_gene)
            instance = {ref_gene: ref_gene}
            if not ref_agent_in_genes:
                pattern.add_node(ref_agent)
                instance[ref_agent] = ref_agent
            rule = Rule.from_transform(pattern)
            rule.inject_add_node(site_id, site.meta_data())
            rule.inject_add_edge(site_id, ref_gene, site.location())
            if not ref_agent_in_genes:
                rule.inject_add_edge(site_id, ref_agent, site.location())
            rhs_typing = {"meta_model": {site_id: "site"}}
            _, rhs_instance = self.rewrite(
                "action_graph", rule, instance, rhs_typing=rhs_typing)
            new_site_id = rhs_instance[site_id]
        else:
            add_node(self.action_graph, site_id, site.meta_data())
            self.set_ag_meta_type(site_id, "site")
            add_edge(self.action_graph, site_id, ref_agent, site.location())
            new_site_id = site_id

        for sem in semantics:
            self.add_ag_node_semantics(site_id, sem)

        reconnect_residues(
            self, ref_gene, self.get_attached_residues(ref_gene),
            sites=[new_site_id])
        reconnect_sites(
            self, ref_gene, [new_site_id],
            self.get_attached_regions(ref_gene))

        return site_id

    def add_residue(self, residue, ref_agent, semantics=None, rewriting=False):
        """Add residue node to the action_graph."""
        if ref_agent not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '{}' does not exist in the action graph".format(
                    ref_agent))

        ref_agent_in_genes = ref_agent in self.genes()
        ref_agent_in_regions = ref_agent in self.regions()
        ref_agent_in_sites = ref_agent in self.sites()

        if not ref_agent_in_genes and not ref_agent_in_regions and\
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
            self, "action_graph")

        # try to find an existing residue with this
        residue_id = identifier.identify_residue(
            residue, ref_agent, add_aa=True, rewriting=rewriting)

        # if residue with this loc does not exist: create one
        if residue_id is None:

            residue_id = generate_new_id(
                self.action_graph, "{}_{}".format(ref_agent, str(residue)))

            if ref_agent_in_genes:
                ref_gene = ref_agent
            else:
                ref_gene = self.get_gene_of(ref_agent)

            if rewriting:
                pattern = nx.DiGraph()
                pattern.add_node(ref_gene)
                instance = {ref_gene: ref_gene}
                if not ref_agent_in_genes:
                    pattern.add_node(ref_agent)
                    instance[ref_agent] = ref_agent
                rule = Rule.from_transform(pattern)
                rule.inject_add_node(residue_id, residue.meta_data())
                rule.inject_add_edge(residue_id, ref_gene, residue.location())
                if not ref_agent_in_genes:
                    rule.inject_add_edge(
                        residue_id, ref_agent, residue.location())
                rhs_typing = {"meta_model": {residue_id: "residue"}}
                _, rhs_instance = self.rewrite(
                    "action_graph", rule, instance, rhs_typing=rhs_typing)
                new_residue_id = rhs_typing[residue_id]
            else:
                add_node(self.action_graph, residue_id,
                         residue.meta_data())
                self.set_ag_meta_type(residue_id, "residue")
                add_edge(self.action_graph, residue_id, ref_gene,
                         residue.location())
                if not ref_agent_in_genes:
                    add_edge(self.action_graph, residue_id, ref_agent)
                new_residue_id = residue_id

            # reconnect regions/sites to the new residue
            reconnect_residues(
                self, ref_gene, [new_residue_id],
                self.get_attached_regions(ref_gene),
                self.get_attached_sites(ref_gene))
        else:
            new_residue_id = residue_id

        # add semantic relations of the node
        for s in semantics:
            self.add_ag_node_semantics(new_residue_id, s)

        return new_residue_id

    def add_bnd(self, attrs=None, semantics=None):
        """Add bnd node to the action graph."""
        # TODO: nice bnd ids generation
        bnd_id = generate_new_id(self.action_graph, "bnd")

        add_node(self.action_graph, bnd_id, attrs)
        self.set_ag_meta_type(bnd_id, "bnd")

        # add semantic relations of the node
        if semantics:
            for s in semantics:
                self.add_ag_node_semantics(bnd_id, s)
        return bnd_id

    def add_state(self, state, ref_agent, semantics=None):
        """Add state node to the action graph."""
        if ref_agent not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '%s' does not exist in the action graph" %
                ref_agent
            )
        if self.get_action_graph_typing()[ref_agent] not in \
           ["gene", "region", "site", "residue"]:
            raise KamiHierarchyError(
                "Cannot add a residue to the node '%s', node type "
                "is not valid (expected 'agent', 'region', 'site' "
                "or 'residue', '%s' was provided)" %
                (ref_agent, self.get_action_graph_typing()[ref_agent])
            )

        # try to find an existing residue with this
        for state_node in self.get_attached_states(ref_agent):
            if list(get_node(self.action_graph, state_node)["name"])[0] ==\
               state.name:
                get_node(self.action_graph, state_node)[state.name].add(state.test)
                return state_node

        state_id = ref_agent + "_" + str(state)
        add_node(self.action_graph, state_id, state.meta_data())
        self.set_ag_meta_type(state_id, "state")
        add_edge(self.action_graph, state_id, ref_agent)

        # add relation to a semantic ag node
        if semantics:
            for s in semantics:
                self.add_ag_node_semantics(state_id, s)
        return state_id

    def _generate_next_nugget_id(self, name=None):
        """Generate id for a new nugget."""
        if self._nugget_count is None:
            self._nugget_count = len(self.nuggets())
        self._nugget_count += 1
        if name is None:
            name = "nugget"
        return name + "_" + str(self._nugget_count)

    def get_nugget_type(self, nugget_id):
        """Get type of the nugget specified by id."""
        return list(self._hierarchy.get_graph_attrs(nugget_id)["interaction_type"])[0]

    def get_nugget_template_rel(self, nugget_id):
        """Get relation of a nugget to a template."""
        nugget_type = self.get_nugget_type(nugget_id)
        return self._hierarchy.get_relation(
            nugget_id, nugget_type + "_template")

    def add_nugget(self, nugget_container, nugget_type,
                   template_id=None,
                   template_rel=None, desc=None,
                   add_agents=True, anatomize=True,
                   apply_semantics=True):
        """Add nugget to the hierarchy."""
        if "action_graph" not in self._hierarchy.graphs():
            self.create_empty_action_graph()

        start = time.time()

        nugget_id = self._generate_next_nugget_id()

        # 2. Create a generation rule for this nugget
        p = nx.DiGraph()
        lhs = nx.DiGraph()
        generation_rule = Rule(p, lhs, nugget_container.graph)
        rhs_typing = {
            "action_graph": nugget_container.reference_typing,
            "meta_model": nugget_container.meta_typing
        }

        # 3. Add empty graph as a nugget to the hierarchy
        attrs = {
            "type": "nugget",
            "interaction_type": nugget_type
        }
        if desc is not None:
            attrs["desc"] = desc
        self._hierarchy.add_empty_graph(nugget_id, attrs=attrs)

        self.nugget[nugget_id] = self._hierarchy.get_graph(nugget_id)
        self._hierarchy.add_typing(nugget_id, "action_graph", dict())

        # 4. Apply nugget generation rule
        g_prime, r_g_prime = self.rewrite(
            nugget_id, rule=generation_rule, instance={},
            rhs_typing=rhs_typing,
            strict=(not add_agents))

        if template_id is not None:
            template_rel = dict()
            for rhs_node, template_nodes in template_rel.items():
                if len(template_nodes) > 0:
                    nugget_node = r_g_prime[rhs_node]
                    template_rel[nugget_node] = set()
                    for el in template_nodes:
                        template_rel[nugget_node].add(el)

            self.add_template_rel(
                nugget_id, template_id,
                template_rel)
        print("\tTime to apply nugget generation rule: ", time.time() - start)

        start = time.time()
        # Get a set of genes added by the nugget
        new_gene_nodes = set()
        for node in nugget_container.graph.nodes():
            new_nugget_node = r_g_prime[node]
            ag_node = self._hierarchy.get_typing(
                nugget_id, "action_graph")[new_nugget_node]
            if self.get_action_graph_typing()[ag_node] == "gene":
                if node not in nugget_container.reference_typing.keys():
                    new_gene_nodes.add(ag_node)

        # Check if all new genes agents from the nugget should be
        # distinct in the action graph
        genes_to_merge = {
            list(get_node(self.action_graph, gene)["uniprotid"])[0]:
                set() for gene in new_gene_nodes
        }
        for gene in new_gene_nodes:
            genes_to_merge[
                list(get_node(self.action_graph, gene)["uniprotid"])[0]].add(
                    gene)

        for k, v in genes_to_merge.items():
            if len(v) > 1:
                pattern = nx.DiGraph()
                add_nodes_from(pattern, v)
                rule = Rule.from_transform(pattern)
                rule.inject_merge_nodes(v, node_id=k)
                _, rhs_instance = self.rewrite(
                    "action_graph", rule,
                    instance={
                        n: n for n in pattern.nodes()
                    })

                # self.rename_node("action_graph", rhs_instance[k], k)
                merge_result = rhs_instance[k]
                if k in new_gene_nodes:
                    new_gene_nodes.remove(k)
                for vv in v:
                    if vv in new_gene_nodes:
                        new_gene_nodes.remove(vv)
                new_gene_nodes.add(merge_result)
        print("\tTime to check gene duplicates: ", time.time() - start)

        # 5. Anatomize new genes added as the result of nugget creation
        start = time.time()
        new_ag_regions = []
        if anatomize is True:
            if len(new_gene_nodes) > 0:
                for gene in new_gene_nodes:
                    added_regions = anatomize_gene(self, gene)
                    new_ag_regions += added_regions
        print("\tTime to anatomize new genes: ", time.time() - start)

        start = time.time()
        all_genes = [
            self._hierarchy.get_typing(nugget_id, "action_graph")[node]
            for node in self.nugget[nugget_id].nodes()
            if self.get_action_graph_typing()[
                self._hierarchy.get_typing(nugget_id, "action_graph")[node]] == "gene"]

        # Apply bookkeeping updates
        connect_nested_fragments(self, all_genes)
        start_nested = time.time()
        connect_transitive_components(self, [
            self._hierarchy.get_typing(nugget_id, "action_graph")[n]
            for n in self.nugget[nugget_id].nodes()
        ] + new_ag_regions)
        print(
            "\t\tTime to conntect transitive components: ",
            time.time() - start_nested)

        for g in all_genes:
            residues = self.get_attached_residues(g)
            sites = self.get_attached_sites(g)
            regions = self.get_attached_regions(g)
            reconnect_residues(self, g, residues, regions, sites)
            reconnect_sites(self, g, sites, regions)
        print("\tTime apply bookkeeping upds: ", time.time() - start)

        # 6. Apply semantics to the nugget
        start = time.time()
        if apply_semantics is True:
            if "mod" in self._hierarchy.get_graph_attrs(
               nugget_id)["interaction_type"]:
                apply_mod_semantics(self, nugget_id)

            elif "bnd" in self._hierarchy.get_graph_attrs(
                    nugget_id)["interaction_type"]:
                apply_bnd_semantics(self, nugget_id)

        print("\tTime to perform semantic upd: ", time.time() - start)
        return nugget_id

    def add_interaction(self, interaction, add_agents=True,
                        anatomize=True, apply_semantics=True):
        """Add a n interaction to the model."""
        if "action_graph" not in self._hierarchy.graphs():
            self.create_empty_action_graph()

        identifier = EntityIdentifier(
            self.action_graph,
            self.get_action_graph_typing(),
            self, "action_graph")

        start = time.time()
        (
            nugget_container,
            nugget_type,
            template_id,
            template_rel,
            desc
        ) = generate_nugget(identifier, interaction)
        print("Time to generate nugget: ", time.time() - start)

        # Add it to the hierarchy performing respective updates
        start = time.time()
        nugget_id = self.add_nugget(
            nugget_container=nugget_container,
            nugget_type=nugget_type,
            template_id=template_id,
            template_rel=template_rel,
            desc=desc,
            add_agents=add_agents,
            anatomize=anatomize,
            apply_semantics=apply_semantics)
        print("Time to add nugget to the model: ", time.time() - start)
        return nugget_id

    def add_interactions(self, interactions, add_agents=True,
                         anatomize=True, apply_semantics=True):
        """Add a collection of interactions to the model."""
        nugget_ids = []
        for i in interactions:
            print(i)
            nugget_id = self.add_interaction(
                i, add_agents, anatomize, apply_semantics)
            nugget_ids.append(nugget_id)
        return nugget_ids

    def type_nugget_by_ag(self, nugget_id, typing):
        """Type nugget by the action graph."""
        self._hierarchy.add_typing(nugget_id, "action_graph", typing)
        return

    def type_nugget_by_meta(self, nugget_id, typing):
        """Type nugget by the meta-model."""
        self._hierarchy.add_typing(nugget_id, "meta_model", typing)
        return

    def add_template_rel(self, nugget_id, template_id, rel):
        """Relate nugget to mod template."""
        self._hierarchy.add_relation(nugget_id, template_id, rel)
        return

    def add_semantic_nugget_rel(self, nugget_id, semantic_nugget_id, rel):
        """Relate a nugget to a semantic nugget."""
        self._hierarchy.add_relation(nugget_id, semantic_nugget_id, rel)
        return

    def unique_kinase_region(self, gene):
        """Get the unique kinase region of the gene."""
        ag_sag_relation = self._hierarchy.get_relation(
            "action_graph", "semantic_action_graph")
        kinase = None
        for node in self.action_graph.predecessors(gene):
            if node in ag_sag_relation.keys() and\
               "protein_kinase" in ag_sag_relation[node]:
                    if kinase is None:
                        kinase = node
                    else:
                        return None
        return kinase

    def get_activity_state(self, gene):
        """Get activity state of a gene in the action graph."""
        states = self.get_attached_states(gene)

        for state in states:
            if "activity" in get_node(self.action_graph, state)["name"]:
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

    def get_nugget_typing(self, nugget_id):
        """Get typing of the nugget by the action graph."""
        return self._hierarchy.get_typing(
            nugget_id, "action_graph")

    def get_action_graph_attrs(self):
        """Get action graph attributes."""
        return self._hierarchy.get_graph_attrs(
            "action_graph")

    def set_action_graph_attrs(self, attrs):
        """Set action graph attributes."""
        self._hierarchy.set_graph_attrs(
            "action_graph", attrs)

    def get_ag_node(self, node):
        """Get node from the action graph."""
        return get_node(self.action_graph, node)

    def export_json(self, filename):
        """Export moodel to json."""
        self._hierarchy.export(filename)
