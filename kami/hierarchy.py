"""."""
import copy
import networkx as nx
import numpy as np
import warnings
import time

from regraph import Rule, Hierarchy
from regraph.primitives import *

from anatomizer.new_anatomizer import GeneAnatomy
from kami.exceptions import KamiHierarchyError, KamiHierarchyWarning
from kami.resources import default_components
from kami.utils.id_generators import generate_new_id
from kami.entities import Region
from kami.resolvers.semantic_utils import (apply_mod_semantics,
                                           apply_bnd_semantics)


def find_fragment(a, dict_of_b):
    a_start = None
    a_end = None
    a_name = None
    a_order = None
    if "start" in a.keys():
        a_start = int(min(a["start"]))
    if "end" in a.keys():
        a_end = int(max(a["end"]))
    if "name" in a.keys():
        a_name = list(a["name"])[0].lower()
    if "order" in a.keys():
        a_order = list(a["order"])[0]

    satifying_fragments = []
    for b_id, b in dict_of_b.items():
        b_start = None
        b_end = None
        b_name = None
        if "start" in b.keys():
            b_start = int(min(b["start"]))
        if "end" in b.keys():
            b_end = int(max(b["end"]))
        if "name" in b.keys():
            b_name = list(b["name"])[0].lower()

        if a_start is not None and a_end is not None and\
           b_start is not None and b_end is not None:
            if a_start >= b_start and a_end <= b_end:
                return b_id
            elif a_start <= b_start and a_end >= b_end:
                return b_id

        if a_name is not None and b_name is not None:
            if a_name in b_name or b_name in a_name:
                satifying_fragments.append(b_id)

    if len(satifying_fragments) == 1:
        return satifying_fragments[0]
    elif len(satifying_fragments) > 1:
        # Try to find if there is a unique region in a list of
        # satisfying regions with the same order number
        if a_order is not None:
            same_order_fragments = []
            for b_id in satifying_fragments:
                if "order" in dict_of_b[b_id].keys():
                    if a_order in dict_of_b[b_id]["order"]:
                        same_order_fragments.append(b_id)
            # if not explicit order number was found
            if len(same_order_fragments) == 0:
                try:
                    start_orders = np.argsort([
                        int(min(dict_of_b[b_id]["start"]))
                        for b_id in satifying_fragments
                        if "start" in dict_of_b[b_id].keys()
                    ])
                    return satifying_fragments[
                        start_orders[a_order - 1]]
                except:
                    return None
            elif len(same_order_fragments) == 1:
                return same_order_fragments[0]
            else:
                return None
    else:
        return None


class KamiHierarchy(Hierarchy):
    """Kami-specific hierarchy class."""

    # Similar to NetworkX node_dict_factory
    nugget_dict_factory = dict
    semantic_nugget_dict_factory = dict

    def _init_shortcuts(self):
        """Initialize kami-specific shortcuts."""
        if "action_graph" in self.nodes():
            self.action_graph = self.node["action_graph"].graph
        else:
            self.action_graph = None

        if ("action_graph", "kami") in self.edges():
            self.action_graph_typing =\
                self.edge["action_graph"]["kami"].mapping
        else:
            self.action_graph_typing = None
        self.mod_template = self.node["mod_template"].graph
        self.bnd_template = self.node["bnd_template"].graph
        self.semantic_action_graph = self.node["semantic_action_graph"].graph

    def rewrite(self, graph_id, rule, instance=None,
                lhs_typing=None, rhs_typing=None,
                strict=True, inplace=True):
        """."""
        g_prime, r_g_prime = super().rewrite(
            graph_id, rule, instance,
            lhs_typing, rhs_typing,
            strict, inplace)
        self._init_shortcuts()
        return (g_prime, r_g_prime)

    def create_empty_action_graph(self):
        """Creat an empty action graph in the hierarchy."""
        self.add_graph(
            "action_graph",
            nx.DiGraph(),
            {"type": "action_graph"}
        )
        self.add_typing(
            "action_graph",
            "kami",
            dict()
        )
        self.add_relation(
            "action_graph",
            "semantic_action_graph",
            dict()
        )
        self.action_graph = self.node["action_graph"].graph
        self.action_graph_typing = self.edge["action_graph"]["kami"].mapping

        return

    def __init__(self, ag=None, ag_typing=None, ag_semantics=None,
                 nuggets=None, nuggets_template_rels=None,
                 nuggets_ag_typing=None, nuggets_semantic_rels=None):
        """Initialize a KAMI hierarchy.

        By default action graph is empty, typed by `kami` (meta-model)
        `self.action_graph` -- direct access to the action graph.
        `self.action_graph_typing` -- direct access to typing of
        the action graph nodes by the meta-model.
        `self.mod_template` and `self.bnd_template` -- direct access to
        the nugget template graphs.
        """
        Hierarchy.__init__(self)

        # Add KAMI-specific invariant components of the hierarchy
        for graph_id, graph, attrs in default_components.GRAPHS:
            self.add_graph(graph_id, graph, attrs)
        for s, t, mapping, attrs in default_components.TYPING:
            self.add_typing(s, t, mapping, attrs=attrs)
        for rule_id, rule, attrs in default_components.RULES:
            self.add_rule(rule_id, rule, attrs)
        for s, t, (lhs_mapping, rhs_mapping), attrs in default_components.RULE_TYPING:
            self.add_rule_typing(s, t, lhs_mapping, rhs_mapping,
                                 lhs_total=True, rhs_total=True, attrs=attrs)
        for u, v, rel, attrs in default_components.RELATIONS:
            self.add_relation(u, v, rel, attrs)

        # Initialization of knowledge-related components
        # Action graph related init
        if ag is not None:
            ag = copy.deepcopy(ag)
            self.add_graph("action_graph", ag, {"type": "action_graph"})

            if ag_typing is not None:
                ag_typing = copy.deepcopy(ag_typing)
                self.add_typing("action_graph", "kami", ag_typing)

            if ag_semantics is not None:
                ag_semantics = copy.deepcopy(ag_semantics)
                self.add_relation("action_graph", "semantic_action_graph",
                                  ag_semantics)

        self.nugget_dict_factory = ndf = self.nugget_dict_factory

        self.nugget = ndf()

        # Nuggets related init
        if nuggets is not None:
            for nugget_id, nugget_graph in nuggets:
                self.add_graph(
                    nugget_id, nugget_graph, {"type": "nugget"})
                self.nugget[nugget_id] = self.node[nugget_id].graph

        if nuggets_ag_typing is not None:
            for nugget_id, typing in nuggets_ag_typing.items():
                self.add_typing(
                    nugget_id, "action_graph", typing)

        if nuggets_template_rels is not None:
            for nugget_id, nugget_rels in nuggets_template_rels.items():
                for template_id, rel in nugget_rels.items():
                    self.add_relation(
                        nugget_id, template_id, rel)

        if nuggets_semantic_rels is not None:
            for nugget_id, nugget_rels in nuggets_semantic_rels.items():
                for s_nugget_id, rel in nugget_rels.items():
                    self.add_relation(
                        nugget_id,
                        s_nugget_id,
                        rel
                    )

        self._init_shortcuts()
        return

    @classmethod
    def from_json(cls, json_data, ignore=None, directed=True):
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

        hierarchy = super().from_json(json_data, ignore_components, directed)
        hierarchy._init_shortcuts()
        return hierarchy

    @classmethod
    def load(cls, filename, directed=True):
        """Load a KamiHierarchy from its json representation."""
        hierarchy = super().load(filename)
        hierarchy._init_shortcuts()
        return hierarchy

    def nuggets(self):
        """Get a list of nuggets in the hierarchy."""
        nuggets = []
        for node_id in self.nodes():
            if "nugget" in self.node[node_id].attrs["type"]:
                nuggets.append(node_id)
        return nuggets

    def semantic_nuggets(self):
        """Get a list of semantic nuggets in the hierarchy."""
        nuggets = []
        for node_id in self.nodes():
            if "semantic_nugget" in self.node[node_id].attrs["type"]:
                nuggets.append(node_id)
        return nuggets

    def templates(self):
        """Get a list of templates in the hierarchy."""
        templates = []
        for node_id in self.nodes():
            if "template" in self.node[node_id].attrs["type"]:
                templates.append(node_id)
        return templates

    def mod_semantic_nuggets(self):
        """Get a list of semantic nuggets related to mod interactions."""
        nuggets = []
        for node_id in self.nodes():
            if "semantic_nugget" in self.node[node_id].attrs["type"] and\
               "mod" in self.node[node_id].attrs["interaction_type"]:
                nuggets.append(node_id)
        return nuggets

    def bnd_semantic_nuggets(self):
        """Get a list of semantic nuggets related to bnd interactions."""
        nuggets = []
        for node_id in self.nodes():
            if "semantic_nugget" in self.node[node_id].attrs["type"] and\
               "bnd" in self.node[node_id].attrs["interaction_type"]:
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
        if self.action_graph is not None and\
           self.action_graph_typing is not None:
            for node in self.action_graph.nodes():
                if self.action_graph_typing[node] == type_name:
                    nodes.append(node)
        return nodes

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
            if self.action_graph_typing[suc] == meta_type:
                succs.append(suc)
        return succs

    def ag_predecessors_of_type(self, node_id, meta_type):
        """Get predecessors of a node of a specific type."""
        preds = []
        for pred in self.action_graph.predecessors(node_id):
            if self.action_graph_typing[pred] == meta_type:
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
        if self.action_graph_typing[element_id] == "gene":
            return element_id
        else:
            # bfs to find a gene
            visited = set()
            next_level_to_visit = self.action_graph.successors(element_id)
            while len(next_level_to_visit) > 0: 
                new_level_to_visit = set()
                for n in next_level_to_visit:
                    if n not in visited:
                        visited.add(n)
                        if self.action_graph_typing[n] == "gene":
                            return n
                    new_level_to_visit.update(
                        self.action_graph.successors(n))
                next_level_to_visit = new_level_to_visit
        raise KamiHierarchyError(
            "No gene node is associated with an element '{}'".fromat(element_id))
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

    def add_gene(self, gene):
        """Add gene node to action graph."""
        if self.action_graph is None:
            self.create_empty_action_graph()
        if gene.uniprotid:
            gene_id = gene.uniprotid
        else:
            i = 1
            name = "unkown_agent_"
            while name + str(i) in self.action_graph.nodes():
                i += 1
            gene_id = name + str(i)

        add_node(self.action_graph, gene_id, gene.to_attrs())
        self.action_graph_typing[gene_id] = "gene"
        return gene_id

    def add_mod(self, attrs=None, semantics=None):
        """Add mod node to the action graph."""
        # TODO: nice mod ids generation
        mod_id = generate_new_id(self.action_graph, "mod")

        add_node(self.action_graph, mod_id, attrs)
        self.action_graph_typing[mod_id] = "mod"

        # add semantic relations of the node
        if semantics:
            for s in semantics:
                self.add_ag_node_semantics(mod_id, s)

        return mod_id

    def add_ag_node_semantics(self, node_id, semantic_node):
        """Add relation of `node_id` with `semantic_node`."""
        if node_id in self.relation["action_graph"][
                "semantic_action_graph"].keys():
            self.relation["action_graph"]["semantic_action_graph"][
                node_id].add(semantic_node)
        else:
            self.relation["action_graph"]["semantic_action_graph"][
                node_id] = {semantic_node}
        return

    def ag_node_semantics(self, node_id):
        """Get semantic nodes related to the `node_id`."""
        result = []
        pairs = self.relation["action_graph"]["semantic_action_graph"]
        for node, semantic_node in pairs:
            if node == node_id:

                result.append(semantic_node)
        return result

    def add_region(self, region, ref_agent, semantics=None):
        """Add region node to action graph connected to `ref_agent`."""
        # found node in AG corresponding to reference agent
        if ref_agent not in self.genes():
            raise KamiHierarchyError(
                "Agent '%s' is not found in the action graph" %
                ref_agent
            )

        region_id = "%s_region_%s" % (ref_agent, str(region))

        if region_id in self.action_graph.nodes():
            region_id = generate_new_id(self.action_graph, region_id)

        add_node(self.action_graph, region_id, region.to_attrs())
        self.action_graph_typing[region_id] = "region"
        add_edge(self.action_graph, region_id, ref_agent)

        if semantics is not None:
            for sem in semantics:
                self.relation["action_graph"][
                    "semantic_action_graph"][region_id] = sem

        # reconnect all the residues & sites of the corresponding gene
        # that lie in the region range
        if region.start is not None and region.end is not None:
            for residue in self.get_attached_residues(ref_agent):
                if "loc" in self.action_graph.node[residue].keys():
                    loc = list(self.action_graph.node[residue]["loc"])[0]
                    if loc >= region.start and loc <= region.end:
                        add_edge(self.action_graph, residue, region_id)

            for site in self.get_attached_sites(ref_agent):
                if "start" in self.action_graph.node[site].keys() and\
                   "end" in self.action_graph.node[site].keys():
                    start = min(self.action_graph.node[site]["start"])
                    end = max(self.action_graph.node[site]["end"])
                    if start >= region.start and end <= region.end:
                        add_edge(self.action_graph, site, region_id)

        return region_id

    def add_site(self, site, ref_agent, semantics=None):
        """Add site node to the action graph."""
        ref_agent_in_genes = ref_agent in self.genes()
        ref_agent_in_regions = ref_agent in self.regions()

        if not ref_agent_in_genes and not ref_agent_in_regions:
            raise KamiHierarchyError(
                "Neither agent nor region '%s' is not "
                "found in the action graph" %
                ref_agent
            )
        site_id = "%s_%s" % (ref_agent, str(site))

        if site_id in self.action_graph.nodes():
            site_id = generate_new_id(self.action_graph, site_id)
        add_node(self.action_graph, site_id, site.to_attrs())
        assert(site_id in self.action_graph.nodes())
        self.action_graph_typing[site_id] = "site"
        add_edge(self.action_graph, site_id, ref_agent)
        assert((site_id, ref_agent) in self.action_graph.edges())

        if semantics is not None:
            for sem in semantics:
                self.relation["action_graph"]["semantic_action_graph"].add(
                    (site_id, sem)
                )

        # find if there are regions to which it may be included
        if ref_agent_in_genes:
            for region in self.get_attached_regions(ref_agent):
                if site.start and site.end:
                    if "start" in self.action_graph.node[region] and\
                       "end" in self.action_graph.node[region]:
                        if int(site.start) >= min(self.action_graph.node[
                            region]["start"]) and\
                           int(site.end) <= max(self.action_graph.node[
                                region]["end"]):
                            add_edge(self.action_graph, site_id, region)
            # reconnect all the residues of the corresponding gene
            # that lie in the region range

            if site.start is not None and site.end is not None:
                for residue in self.get_attached_residues(ref_agent):
                    if "loc" in self.action_graph.node[residue].keys():
                        loc = list(self.action_graph.node[residue]["loc"])[0]
                        if loc >= site.start and loc <= site.end:
                            add_edge(self.action_graph, residue, site_id)

        elif ref_agent_in_regions:
            gene_id = self.get_gene_of(ref_agent)
            add_edge(self.action_graph, site_id, gene_id)
            # reconnect all the residues of the corresponding gene
            # that lie in the region range
            if site.start is not None and site.end is not None:
                for residue in self.get_attached_residues(gene_id):
                    if "loc" in self.action_graph.node[residue].keys():
                        loc = list(self.action_graph.node[residue]["loc"])[0]
                        if loc >= site.start and loc <= site.end:
                            add_edge(self.action_graph, residue, site_id)

        return site_id

    def add_residue(self, residue, ref_agent, semantics=None):
        """Add residue node to the action_graph."""
        if ref_agent not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '%s' does not exist in the action graph" %
                ref_agent
            )

        ref_agent_in_genes = ref_agent in self.genes()
        ref_agent_in_regions = ref_agent in self.regions()
        ref_agent_in_sites = ref_agent in self.sites()

        if not ref_agent_in_genes and not ref_agent_in_regions and\
           not ref_agent_in_sites:
            raise KamiHierarchyError(
                "Cannot add a residue to the node '%s', node type "
                "is not valid (expected 'agent', 'region' or 'site', '%s' was provided)" %
                (ref_agent, self.action_graph_typing[ref_agent])
            )

        # try to find an existing residue with this
        res = self.identify_residue(residue, ref_agent, True)
        # if residue with this loc does not exist: create one
        if res is None:
            if ref_agent_in_genes:
                residue_id = "%s_residue" % ref_agent
                if residue.loc is not None:
                    residue_id += "_%s" % residue.loc
                else:
                    residue_id = generate_new_id(self.action_graph, residue_id)
                add_node(self.action_graph, residue_id, residue.to_attrs())
                self.action_graph_typing[residue_id] = "residue"
                add_edge(self.action_graph, residue_id, ref_agent)

                for region in self.get_attached_regions(ref_agent):
                    if residue.loc:
                        if "start" in self.action_graph.node[region] and\
                           "end" in self.action_graph.node[region]:
                            start = min(
                                self.action_graph.node[region]["start"])
                            end = max(
                                self.action_graph.node[region]["end"])
                            if int(residue.loc) >= start and\
                               int(residue.loc) <= end:
                                add_edge(self.action_graph, residue_id, region)

                for site in self.get_attached_regions(ref_agent):
                    if residue.loc:
                        if "start" in self.action_graph.node[site] and\
                           "end" in self.action_graph.node[site]:
                            start = min(
                                self.action_graph.node[site]["start"])
                            end = max(
                                self.action_graph.node[site]["end"])
                            if int(residue.loc) >= start and\
                               int(residue.loc) <= end:
                                add_edge(self.action_graph, residue_id, site)
            else:
                gene_id = self.get_gene_of(ref_agent)
                residue_id = "%s_residue" % gene_id
                if residue.loc is not None:
                    residue_id += "_%s" % residue.loc
                else:
                    residue_id = generate_new_id(self.action_graph, residue_id)

                add_node(self.action_graph, residue_id, residue.to_attrs())
                self.action_graph_typing[residue_id] = "residue"
                add_edge(self.action_graph, residue_id, ref_agent)
                add_edge(self.action_graph, residue_id, gene_id)

                if ref_agent_in_regions:
                    for site in self.get_attached_regions(gene_id):
                        if residue.loc:
                            if "start" in self.action_graph.node[site] and\
                               "end" in self.action_graph.node[site]:
                                start = min(
                                    self.action_graph.node[site]["start"])
                                end = max(
                                    self.action_graph.node[site]["end"])
                                if int(residue.loc) >= start and\
                                   int(residue.loc) <= end:
                                    add_edge(self.action_graph, residue_id, site)
                else:
                    region_id = self.get_region_of(ref_agent)
                    if region_id is not None:
                        add_edge(self.action_graph, residue_id, region_id)

            # add semantic relations of the node
            if semantics:
                for s in semantics:
                    self.add_ag_node_semantics(residue_id, s)

        return residue_id

    def add_bnd(self, attrs=None, semantics=None):
        """Add bnd node to the action graph."""
        # TODO: nice bnd ids generation
        bnd_id = generate_new_id(self.action_graph, "bnd")

        add_node(self.action_graph, bnd_id, attrs)
        self.action_graph_typing[bnd_id] = "bnd"

        # add semantic relations of the node
        if semantics:
            for s in semantics:
                self.add_ag_node_semantics(bnd_id, s)
        return bnd_id

    def add_locus(self, attrs=None, semantics=None):
        """Add locus node to the action graph."""
        # TODO: nice locus ids generation
        locus_id = generate_new_id(self.action_graph, "locus")

        add_node(self.action_graph, locus_id, attrs)
        self.action_graph_typing[locus_id] = "locus"

        # add semantic relations of the node
        if semantics:
            for s in semantics:
                self.add_ag_node_semantics(locus_id, s)
        return locus_id

    def add_state(self, state, ref_agent, semantics=None):
        """Add state node to the action graph."""
        if ref_agent not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '%s' does not exist in the action graph" %
                ref_agent
            )
        if self.action_graph_typing[ref_agent] not in \
           ["gene", "region", "site", "residue"]:
            raise KamiHierarchyError(
                "Cannot add a residue to the node '%s', node type "
                "is not valid (expected 'agent', 'region', 'site' "
                "or 'residue', '%s' was provided)" %
                (ref_agent, self.action_graph_typing[ref_agent])
            )

        # try to find an existing residue with this
        for state_node in self.get_attached_states(ref_agent):
            if list(self.action_graph.node[state_node].keys())[0] == state.name:
                self.action_graph.node[state_node][state.name].add(state.value)
                return state_node

        state_id = ref_agent + "_" + str(state)
        add_node(self.action_graph, state_id, state.to_attrs())
        self.action_graph_typing[state_id] = "state"
        add_edge(self.action_graph, state_id, ref_agent)

        # add relation to a semantic ag node
        if semantics:
            for s in semantics:
                self.add_ag_node_semantics(state_id, s)
        return state_id

    def identify_gene(self, gene):
        """Find corresponding gene in action graph."""
        for node in self.genes():
            if "uniprotid" in self.action_graph.node[node].keys() and\
               gene.uniprotid in self.action_graph.node[node]["uniprotid"]:
                return node
        return None

    def _identify_fragment(self, fragment, ref_agent, fragment_type):
        fragment_candidates = self.ag_predecessors_of_type(
            ref_agent, fragment_type)
        return find_fragment(
            fragment.to_attrs(),
            {f: self.action_graph.node[f] for f in fragment_candidates})

    def identify_region(self, region, ref_agent):
        """Find corresponding region in action graph."""
        if ref_agent not in self.genes():
            raise KamiHierarchyError(
                "Agent with UniProtID '%s' is not found in the action graph" %
                ref_agent
            )
        else:
            return self._identify_fragment(region, ref_agent, "region")

    def identify_site(self, site, ref_agent):
        """Find corresponding site in action graph."""
        if ref_agent not in self.genes() and ref_agent not in self.regions():
            raise KamiHierarchyError(
                "Agent with UniProtID '%s' is not found in the action graph" %
                ref_agent
            )
        else:
            return self._identify_fragment(site, ref_agent, "site")

    def identify_residue(self, residue, ref_agent, add_aa=False):
        """Find corresponding residue.

        `residue` -- input residue entity to search for
        `ref_agent` -- reference to an agent to which residue belongs.
        Can reference either to an agent or to a region
        in the action graph.
        `add_aa` -- add aa value if location is found but aa not
        """
        ref_gene = self.get_gene_of(ref_agent)
        residue_candidates = self.get_attached_residues(ref_gene)
        if residue.loc is not None:
            for res in residue_candidates:
                if "loc" in self.action_graph.node[res].keys():
                    if residue.loc == int(list(self.action_graph.node[res]["loc"])[0]):
                        if residue.aa <= self.action_graph.node[res]["aa"]:
                            return res
                        elif add_aa is True:
                            self.action_graph.node[res]["aa"] =\
                                self.action_graph.node[res]["aa"].union(
                                    residue.aa
                            )
                            return res
        else:
            for res in residue_candidates:
                if "loc" not in self.action_graph.node[res].keys() or\
                   self.action_graph.node[res]["loc"].is_empty():
                    if residue.aa <= self.action_graph.node[res]["aa"]:
                        return res
                    elif add_aa is True:
                        self.action_graph.node[res]["aa"] =\
                            self.action_graph.node[res]["aa"].union(
                            residue.aa
                        )
                        return res
        return None

    def identify_state(self, state, ref_agent):
        """Find corresponding state of reference agent."""
        for pred in self.action_graph.predecessors(ref_agent):
            if pred in self.action_graph_typing.keys() and\
               self.action_graph_typing[pred] == "state":
                name = list(self.action_graph.node[pred].keys())[0]
                values = self.action_graph.node[pred][name]
                if state.name == name:
                    if state.value not in values:
                        add_node_attrs(
                            self.action_graph,
                            pred,
                            {name: {state.value}})
                    return pred
        return None

    def _generate_nugget_id(self, name=None):
        """Generate id for a new nugget."""
        if name:
            if name not in self.nodes():
                nugget_id = name
            else:
                i = 1
                nugget_id = name + "_" + str(i)
                while nugget_id in self.nodes():
                    i += 1
                    nugget_id = name + "_" + str(i)
        else:
            name = "nugget"
            i = 1
            nugget_id = name + "_" + str(i)
            while nugget_id in self.nodes():
                i += 1
                nugget_id = name + "_" + str(i)
        return nugget_id

    def add_nugget(self, nugget, nugget_type, add_agents=True,
                   anatomize=True, apply_semantics=True, name=None):
        """Add nugget to the hierarchy."""

        nugget_id = self._generate_nugget_id()

        p = nx.DiGraph()
        lhs = nx.DiGraph()

        # 2. Create a generation rule for this nugget
        generation_rule = Rule(p, lhs, nugget.graph)
        rhs_typing = {
            "action_graph": nugget.ag_typing,
            "kami": nugget.meta_typing
        }

        # 3. Add empty graph as a nugget to the hierarchy
        self.add_graph(
            nugget_id,
            lhs,
            {
                "type": "nugget",
                "interaction_type": nugget_type
            }
        )
        self.nugget[nugget_id] = self.node[nugget_id].graph
        self.add_typing(nugget_id, "action_graph", dict())

        # 4. Apply nugget generation rule
        g_prime, r_g_prime = self.rewrite(
            nugget_id, rule=generation_rule, instance={},
            lhs_typing={}, rhs_typing=rhs_typing,
            strict=(not add_agents), inplace=True)

        self.add_template_rel(
            nugget_id, nugget.template_id, nugget.template_rel)

        # Get a set of genes added by the nugget
        new_gene_nodes = set()
        for node in self.nugget[nugget_id].nodes():
            ag_node = self.typing[nugget_id]["action_graph"][node]
            if self.action_graph_typing[ag_node] == "gene":
                if node not in nugget.ag_typing:
                    new_gene_nodes.add(ag_node)

        # Check if all new genes agents from the nugget should be
        # distinct in the action graph
        genes_to_merge = {
            list(self.action_graph.node[gene]["uniprotid"])[0]: set() for gene in new_gene_nodes
        }
        for gene in new_gene_nodes:
            genes_to_merge[list(self.action_graph.node[gene]["uniprotid"])[0]].add(gene) 
        for k, v in genes_to_merge.items():
            if len(v) > 1:
                pattern = nx.DiGraph()
                add_nodes_from(pattern, v)
                rule = Rule.from_transform(pattern)
                rule.inject_merge_nodes(v, node_id=k)
                _, rhs_instance = self.rewrite("action_graph", rule)
                self.rename_node("action_graph", rhs_instance[k], k)
                for vv in v:
                    if vv != k:
                        new_gene_nodes.remove(vv)

        # 5. Anatomize new genes added as the result of nugget creation
        new_ag_regions = []
        if anatomize is True:
            if len(new_gene_nodes) > 0:
                for gene in new_gene_nodes:
                    new_ag_regions += self.anatomize_gene(gene)

        all_genes = [
            self.typing[nugget_id]["action_graph"][node]
             for node in self.nugget[nugget_id].nodes()
             if self.action_graph_typing[
                self.typing[nugget_id]["action_graph"][node]] == "gene"]

        self._connect_nested_fragments(all_genes)
        self._connect_transitive_components([
            self.typing[nugget_id]["action_graph"][n]
            for n in self.nugget[nugget_id].nodes()
            ] + new_ag_regions)
        # Merge sites
        for g in all_genes: 
            residues = self.get_attached_residues(g)
            sites = self.get_attached_sites(g)
            self._merge_sites(residues + sites)

        # 6. Apply semantics to the nugget
        if apply_semantics is True:
            if "mod" in self.node[nugget_id].attrs["interaction_type"]:
                apply_mod_semantics(self, nugget_id)
            elif "bnd" in self.node[nugget_id].attrs["interaction_type"]:
                apply_bnd_semantics(self, nugget_id)

        # 7. Add semantic relations found for the nugget
        for semantic_nugget, rel in nugget.semantic_rels.items():
            self.add_semantic_nugget_rel(
                nugget_id, semantic_nugget, rel
            )

        return nugget_id

    def _merge_sites(self, nodes):
        pattern = nx.DiGraph()
        pattern.add_edges_from([("residue", "site1"), ("residue", "site2")])
        site_merging_rule = Rule.from_transform(pattern)
        site_merging_rule.inject_merge_nodes(["site1", "site2"])
        lhs_typing = {
            "kami": {
                "residue": "residue",
                "site1": "site",
                "site2": "site"
            }
        }
        instances = self.find_matching(
            "action_graph", pattern, pattern_typing=lhs_typing,
            nodes=nodes)
        visited_sites = set()
        for instance in instances:
            if instance["site1"] not in visited_sites or instance["site2"] not in visited_sites:
                self.rewrite("action_graph", site_merging_rule, instance)
                visited_sites.add(instance["site1"])
                visited_sites.add(instance["site2"])

    def _connect_transitive_components(self, new_nodes):
        """Add edges between components connected transitively."""
        connecting_rules = []

        gene_region_site = nx.DiGraph()
        add_nodes_from(gene_region_site, ["gene", "region", "site"])
        add_edges_from(
            gene_region_site, [("region", "gene"), ("site", "region")])
        gene_region_site_rule = Rule.from_transform(gene_region_site)
        gene_region_site_rule.inject_add_edge("site", "gene")
        lhs_typing = {
            "kami": {"gene": "gene", "region": "region", "site": "site"}
        }
        connecting_rules.append((gene_region_site_rule, lhs_typing))

        region_site_residue = nx.DiGraph()
        add_nodes_from(region_site_residue, ["region", "site", "residue"])
        add_edges_from(
            region_site_residue, [("site", "region"), ("residue", "site")])
        region_site_residue_rule = Rule.from_transform(region_site_residue)
        region_site_residue_rule.inject_add_edge("residue", "region")
        lhs_typing = {
            "kami": {"region": "region", "site": "site", "residue": "residue"}
        }
        connecting_rules.append((region_site_residue_rule, lhs_typing))

        # Create a rule that for a pattent 'gene'<-'region'<-'residue'
        # adds an edge 'gene'<-'residue'
        # TODO: what if such residue already existed (maybe need to merge smth)
        gene_region_residue = nx.DiGraph()
        add_nodes_from(gene_region_residue, ["gene", "region", "residue"])
        add_edges_from(
            gene_region_residue, [("region", "gene"), ("residue", "region")])
        gene_region_residue_rule = Rule.from_transform(gene_region_residue)
        gene_region_residue_rule.inject_add_edge("residue", "gene")
        lhs_typing = {
            "kami": {"gene": "gene", "region": "region", "residue": "residue"}
        }
        connecting_rules.append((gene_region_residue_rule, lhs_typing))

        gene_site_residue = nx.DiGraph()
        add_nodes_from(gene_site_residue, ["gene", "site", "residue"])
        add_edges_from(
            gene_site_residue, [("site", "gene"), ("residue", "site")])
        gene_site_residue_rule = Rule.from_transform(gene_site_residue)
        gene_site_residue_rule.inject_add_edge("residue", "gene")
        lhs_typing = {
            "kami": {"gene": "gene", "site": "site", "residue": "residue"}
        }
        connecting_rules.append((gene_site_residue_rule, lhs_typing))

        for rule, lhs_typing in connecting_rules:
            instances = self.find_matching(
                "action_graph", rule.lhs, pattern_typing=lhs_typing,
                nodes=new_nodes)
            for instance in instances:
                self.rewrite("action_graph", rule, instance)

    def _connect_nested_fragments(self, genes):
        for gene in genes:
            regions = self.get_attached_regions(gene)
            for site in self.get_attached_sites(gene):
                f = find_fragment(
                    self.action_graph.node[site],
                    {r: self.action_graph.node[r] for r in regions})
                if f is not None:
                    if self.action_graph_typing[f] == "region" and\
                       (site, f) not in self.action_graph.edges():
                        add_edge(self.action_graph, site, f)

    def anatomize_gene(self, gene):
        """Anatomize existing gene node in the action graph."""
        new_regions = list()
        if gene not in self.action_graph.nodes() or\
           self.action_graph_typing[gene] != "gene":
            raise KamiHierarchyError(
                "Gene node '%s' does not exist in the hierarchy!" % gene)

        anatomy = None

        if "uniprotid" in self.action_graph.node[gene] and\
           len(self.action_graph.node[gene]["uniprotid"]) == 1:
            anatomy = GeneAnatomy(
                list(
                    self.action_graph.node[gene]["uniprotid"])[0],
                merge_features=True,
                nest_features=False,
                merge_overlap=0.005,
                offline=True
            )
        elif "hgnc_symbol" in self.action_graph.node[gene] and\
             len(self.action_graph.node[gene]["hgnc_symbol"]) == 1:
            anatomy = GeneAnatomy(
                list(
                    self.action_graph.node[gene]["hgnc_symbol"])[0],
                merge_features=True,
                nest_features=False,
                merge_overlap=0.05,
                offline=True
            )
        elif "synonyms" in self.action_graph.node[gene] and\
             len(self.action_graph.node[gene]["synonyms"]) > 0:
            for s in self.action_graph.node[gene]["synonyms"]:
                anatomy = GeneAnatomy(
                    s,
                    merge_features=True,
                    nest_features=False,
                    merge_overlap=0.05,
                    offline=True
                )
                if anatomy is not None:
                    break
        if anatomy is not None:

            # Generate an update rule to add
            # entities fetched by the anatomizer

            lhs = nx.DiGraph()
            add_nodes_from(lhs, ["gene"])
            instance = {"gene": gene}

            anatomization_rule = Rule.from_transform(lhs)
            anatomization_rule.inject_add_node_attrs(
                "gene", {"hgnc_symbol": anatomy.hgnc_symbol})
            anatomization_rule_typing = {
                "kami": {}
            }
            # Build a rule that adds all regions and sites
            semantic_relations = dict()
            new_regions = []
            for domain in anatomy.domains:
                if domain.feature_type == "Domain":
                    region = Region(
                        name=" ".join(
                            [n.replace("iSH2", "").replace("inter-SH2", "")
                             for n in domain.short_names]),
                        start=domain.start,
                        end=domain.end,
                        label=domain.prop_label)

                    region_id = "%s_%s" % (gene, str(region))
                    if region_id in self.action_graph.nodes():
                        region_id = generate_new_id(
                            self.action_graph, region_id)
                    anatomization_rule.inject_add_node(
                        region_id, region.to_attrs())
                    new_regions.append(region_id)
                    anatomization_rule.inject_add_edge(
                        region_id, "gene")

                    anatomization_rule_typing["kami"][region_id] = "region"
                    # Resolve semantics
                    semantic_relations[region_id] = set()
                    if "IPR000719" in domain.ipr_ids:
                        semantic_relations[region_id].add("protein_kinase")
                        # autocomplete with activity
                        activity_state_id = "%s_%s" % (region_id, "activity")
                        if activity_state_id in self.action_graph.nodes():
                            activity_state_id = generate_new_id(
                                self.action_graph, activity_state_id)
                        anatomization_rule.inject_add_node(
                            activity_state_id, {"activity": {True}})
                        anatomization_rule.inject_add_edge(
                            activity_state_id, region_id)
                        semantic_relations[activity_state_id] = {"activity"}
                        anatomization_rule_typing["kami"][
                            activity_state_id] = "state"
                    if "IPR000980" in domain.ipr_ids:
                        semantic_relations[region_id].add("sh2_domain")

            existing_regions = self.get_attached_regions(gene)
            for existing_region in existing_regions:
                matching_region = find_fragment(
                    self.action_graph.node[existing_region],
                    {n: anatomization_rule.rhs.node[n] for n in new_regions})
                if matching_region is not None:
                    anatomization_rule._add_node_lhs(existing_region)
                    instance[existing_region] = existing_region
                    new_name = anatomization_rule.inject_merge_nodes(
                        [existing_region, matching_region])
                    semantic_relations[new_name] = semantic_relations[matching_region]
                    del semantic_relations[matching_region]
                    new_regions.remove(matching_region)
                    new_regions.append(new_name)

            _, rhs_g = self.rewrite(
                "action_graph", anatomization_rule,
                instance, rhs_typing=anatomization_rule_typing,
                strict=True, inplace=True)

            for new_node_id, semantics in semantic_relations.items():
                for s in semantics:
                    if rhs_g[new_node_id] in self.relation["action_graph"][
                            "semantic_action_graph"].keys():
                        self.relation["action_graph"][
                            "semantic_action_graph"][rhs_g[new_node_id]].add(s)
                    else:
                        self.relation["action_graph"][
                            "semantic_action_graph"][rhs_g[new_node_id]] = {s}
        else:
            warnings.warn(
                "Unable to anatomize gene node '%s'" % gene,
                KamiHierarchyWarning)
        return new_regions

    def type_nugget_by_ag(self, nugget_id, typing):
        """Type nugget by the action graph."""
        self.add_typing(nugget_id, "action_graph", typing)
        return

    def type_nugget_by_meta(self, nugget_id, typing):
        """Type nugget by the meta-model."""
        self.add_typing(nugget_id, "kami", typing)
        return

    def add_template_rel(self, nugget_id, template_id, rel):
        """Relate nugget to mod template."""
        self.add_relation(nugget_id, template_id, rel)
        return

    def add_semantic_nugget_rel(self, nugget_id, semantic_nugget_id, rel):
        """Relate a nugget to a semantic nugget."""
        self.add_relation(nugget_id, semantic_nugget_id, rel)
        return

    def ag_to_edge_list(self, agent_ids="hgnc_symbol"):
        edge_list = []
        for u, v in self.action_graph.edges():
            if self.action_graph_typing[u] == "gene":
                hgnc = None
                if "hgnc_symbol" in self.action_graph.node[u].keys():
                    hgnc = list(self.action_graph.node[u]["hgnc_symbol"])[0]
                if hgnc is not None:
                    n1 = hgnc
                else:
                    n1 = u
            else:
                n1 = u.replace(",", "").replace(" ", "")
            if self.action_graph_typing[v] == "gene":
                hgnc = None
                if "hgnc_symbol" in self.action_graph.node[v].keys():
                    hgnc = list(self.action_graph.node[v]["hgnc_symbol"])[0]
                if hgnc is not None:
                    n2 = hgnc
                else:
                    n2 = v
            else:
                n2 = v.replace(",", "").replace(" ", "")
            edge_list.append((n1, n2))
        return edge_list

    def unique_kinase_region(self, gene):
        """Get the unique kinase region of the gene."""
        ag_sag_relation = self.relation[
            "action_graph"]["semantic_action_graph"]
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
        states = self.get_attached_states(gene)

        for state in states:
            if "activity" in self.action_graph.node[state].keys():
                return state
        return None
