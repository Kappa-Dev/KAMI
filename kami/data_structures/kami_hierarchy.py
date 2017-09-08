"""."""
import networkx as nx

from regraph.hierarchy import Hierarchy
from regraph.primitives import (add_node,
                                add_edge)

from kami.exceptions import KamiHierarchyError
from kami.resources import (metamodels,
                            nugget_templates,
                            semantic_nuggets,
                            semantic_AG)


class KamiHierarchy(Hierarchy):
    """Kami-specific hierarchy class."""

    def __init__(self):
        """Initialize empty kami hierarchy.

        By default action graph is empty, typed by `kami` (meta-model)
        `self.action_graph` -- direct access to the action graph.
        `self.action_graph_typing` -- direct access to typing of
        the action graph nodes by the meta-model.
        `self.mod_template` and `self.bnd_template` -- direct access to
        the nugget template graphs.
        """
        Hierarchy.__init__(self)

        self.add_graph("kami", metamodels.kami)

        action_graph = nx.DiGraph()
        self.add_graph("action_graph", action_graph)
        self.add_typing("action_graph", "kami", dict())
        self.action_graph = self.node["action_graph"].graph
        self.action_graph_typing = self.edge["action_graph"]["kami"].mapping

        self.add_graph("mod_template", nugget_templates.mod_nugget)
        self.add_typing("mod_template", "kami", nugget_templates.mod_kami_typing)
        self.mod_template = self.node["mod_template"].graph

        self.add_graph("bnd_template", nugget_templates.bnd_nugget)
        self.add_typing("bnd_template", "kami", nugget_templates.bnd_kami_typing)
        self.bnd_template = self.node["bnd_template"].graph

        self.add_graph("phosphorylation", semantic_nuggets.phosphorylation)
        self.add_graph("semantic_action_graph", semantic_AG.semantic_action_graph)
        self.add_typing(
            "phosphorylation",
            "semantic_action_graph",
            semantic_nuggets.phosphorylation_semantic_AG,
            total=True
        )

        self.add_typing(
            "semantic_action_graph",
            "kami",
            semantic_AG.kami_typing,
            total=True
        )
        self.add_relation("action_graph", "semantic_action_graph", set())
        return

    @classmethod
    def from_json(cls, json_data, directed=True):
        """Create hierarchy from json representation."""
        hierarchy = Hierarchy.from_json(json_data, directed=directed)
        hierarchy.action_graph = hierarchy.node["action_graph"].graph
        hierarchy.action_graph_typing = hierarchy.edge["action_graph"]["kami"].mapping
        hierarchy.mod_template = hierarchy.node["mod_template"].graph
        hierarchy.bnd_template = hierarchy.node["bnd_template"].graph
        return hierarchy

    def _generate_agent_id(self, agent):
        pass

    def _generate_region_id(self, region):
        pass

    def _generate_residue_id(self, residue):
        pass

    def _generate_state_id(self, state):
        pass

    def get_agents(self):
        """Get a list of agent nodes in the action graph."""
        agents = []
        for node in self.action_graph.nodes():
            if node in self.action_graph_typing.keys() and\
               self.action_graph_typing[node] == "agent":
                agents.append(node)
        return agents

    def get_regions(self):
        """Get a list of region nodes in the action graph."""
        regions = []
        for node in self.action_graph.nodes():
            if node in self.action_graph_typing.keys() and\
               self.action_graph_typing[node] == "region":
                regions.append(node)
        return regions

    def get_mods_of_region(self, region_id):
        mods = []
        for suc in self.action_graph.successors(region_id):
            if self.action_graph_typing[suc] == "mod":
                mods.append(suc)
        return mods

    def get_regions_of_agent(self, agent_id):
        """Get a list of regions belonging to a specified agent."""
        regions = []
        for pred in self.action_graph.predecessors(agent_id):
            if pred in self.action_graph_typing.keys() and\
               self.action_graph_typing[pred] == "region":
                regions.append(pred)
        return regions

    def get_attached_residues(self, agent_id):
        """Get a list of residues attached to a node with `agent_id`."""
        residues = []
        # collect residues directly connected
        for pred in self.action_graph.predecessors(agent_id):
            if pred in self.action_graph_typing.keys() and\
               self.action_graph_typing[pred] == "residue":
                residues.append(pred)
        return residues

    def get_attached_states(self, agent_id):
        """Get a list of states attached to a node with `agent_id`."""
        states = []
        # collect residues directly connected
        for pred in self.action_graph.predecessors(agent_id):
            if pred in self.action_graph_typing.keys() and\
               self.action_graph_typing[pred] == "state":
                states.append(pred)
        return states

    def get_agent_by_region(self, region_id):
        """Get agent id conntected to the region."""
        for suc in self.action_graph.successors(region_id):
            if suc in self.action_graph_typing.keys() and\
               self.action_graph_typing[suc] == "agent":
                return suc
        return None

    def add_agent(self, agent):
        """Add agent node to action graph."""
        if agent.uniprotid:
            agent_id = agent.uniprotid
        else:
            i = 1
            name = "unkown_agent_"
            while name + str(i) in self.action_graph.nodes():
                i += 1
            agent_id = name + str(i)

        add_node(self.action_graph, agent_id, agent.to_attrs())
        self.action_graph_typing[agent_id] = "agent"
        return agent_id

    def add_mod(self, attrs, semantics=None):
        """Add mod node to the action graph."""
        # TODO: nice mod ids generation
        i = 1
        name = "mod"
        mod_id = name + str(i)
        while mod_id in self.action_graph.nodes():
            i += 1
            mod_id = name + str(i)

        add_node(self.action_graph, mod_id, attrs)
        self.action_graph_typing[mod_id] = "mod"

        # add semantic relations of the node
        if semantics:
            for s in semantics:
                self.add_ag_node_semantics(mod_id, s)

        return mod_id

    def add_ag_node_semantics(self, node_id, semantic_node):
        """Add relation of `node_id` with `semantic_node`."""
        self.relation["action_graph"]["semantic_action_graph"].rel.add(
            (node_id, semantic_node)
        )
        return

    def ag_node_semantics(self, node_id):
        """Get semantic nodes related to the `node_id`."""
        result = []
        pairs = self.relation["action_graph"]["semantic_action_graph"].rel
        for node, semantic_node in pairs:
            if node == node_id:

                result.append(semantic_node)
        return result

    def add_region(self, region, ref_agent, kinase=False):
        """Add region node to action graph connected to `ref_agent`."""
        found = False
        ref_agent_id = None

        # found node in AG corresponding to reference agent
        agent_nodes = self.get_agents()
        for node in agent_nodes:
            if ref_agent in self.action_graph.node[node]["uniprotid"]:
                found = True
                ref_agent_id = node
        if not found:
            raise KamiHierarchyError(
                "Agent with UniProtID '%s' is not found in the action graph" %
                ref_agent
            )
        region_id = "%s_region_%s_%s" %\
                    (ref_agent, region.start, region.end)

        add_node(self.action_graph, region_id, region.to_attrs())
        self.action_graph_typing[region_id] = "region"
        add_edge(self.action_graph, region_id, ref_agent_id)

        if kinase is True:
            self.relation["action_graph"]["semantic_action_graph"].rel.add((region_id, "kinase"))
        return region_id

    def add_residue(self, residue, ref_agent):
        """Add residue node to the action_graph."""
        if ref_agent not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '%s' does not exist in the action graph" %
                ref_agent
            )
        if self.action_graph_typing[ref_agent] != "agent" and\
           self.action_graph_typing[ref_agent] != "region":
            raise KamiHierarchyError(
                "Cannot add a residue to the node '%s', node kami type "
                "is not valid (expected 'agent' or 'region', '%s' was provided)" %
                self.action_graph_typing[ref_agent]
            )

        # try to find an existing residue with this
        for res in self.get_attached_residues(ref_agent):
            if list(self.action_graph.node[res]["loc"])[0] == residue.loc:
                self.action_graph.node[res]["aa"].update(residue.aa)
                return res

        # if residue with this loc does not exist: create one
        residue_id = None

        if self.action_graph_typing[ref_agent] == "agent":
            residue_id = "%s_residue_%s" % (ref_agent, str(residue.loc))
            add_node(self.action_graph, residue_id, residue.to_attrs())
            for region in self.get_regions_of_agent(ref_agent):
                if residue.loc:
                    if int(residue.loc) >= list(self.action_graph.node[region]["start"])[0] and\
                       int(residue.loc) <= list(self.action_graph.node[region]["end"])[0]:
                        add_edge(self.action_graph, residue_id, region)
            add_edge(self.action_graph, residue_id, ref_agent)

        else:
            residue_id = "%s_residue_%s" % (ref_agent, str(residue.loc))
            agent = self.get_agent_by_region(ref_agent)
            add_node(self.action_graph, residue_id, residue.to_attrs())
            add_edge(self.action_graph, residue_id, ref_agent)
            add_edge(self.action_graph, residue_id, agent)

        if residue_id:
            self.action_graph_typing[residue_id] = "residue"

        return residue_id

    def add_state(self, state, ref_agent):
        """Add state node to the action graph."""
        if ref_agent not in self.action_graph.nodes():
            raise KamiHierarchyError(
                "Node '%s' does not exist in the action graph" %
                ref_agent
            )
        if self.action_graph_typing[ref_agent] not in \
           ["agent", "region", "residue"]:
            raise KamiHierarchyError(
                "Cannot add a residue to the node '%s', node kami type "
                "is not valid (expected 'agent' or 'region', '%s' was provided)" %
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

        return state_id

    def find_agent(self, agent):
        """Find corresponding agent in action graph."""
        agents = self.get_agents()
        for node in agents:
            if agent.uniprotid in self.action_graph.node[node]["uniprotid"]:
                return node
        return None

    def find_region(self, region, ref_agent):
        """Find corresponding region in action graph."""
        found = False
        agent_node = None
        agent_nodes = self.get_agents()
        for node in agent_nodes:
            if ref_agent in self.action_graph.node[node]["uniprotid"]:
                found = True
                agent_node = node
        if not found:
            raise KamiHierarchyError(
                "Agent with UniProtID '%s' is not found in the action graph" %
                ref_agent
            )
        else:
            # currently assume there is no nesting of regions at the moment
            region_candidates = self.get_regions_of_agent(agent_node)
            for reg in region_candidates:
                start = list(self.action_graph.node[reg]["start"])[0]
                end = list(self.action_graph.node[reg]["end"])[0]
                if region.start >= start and region.end <= end:
                    return reg
        return None

    def find_residue(self, residue, ref_agent):
        """Find corresponding residue.

        `residue` -- input residue entity to search for
        `ref_agent` -- reference to an agent to which residue belongs.
        Can reference either to an agent or to a region
        in the action graph.
        """
        residue_candidates = self.get_attached_residues(ref_agent)
        for res in residue_candidates:
            if residue.loc in self.action_graph.node[res]["loc"] and\
               residue.aa <= self.action_graph.node[res]["aa"]:
                return res
        return None

    def find_state(self, state, ref_agent):
        """Find corresponding state of reference agent."""
        for pred in self.action_graph.predecessors(ref_agent):
            if pred in self.action_graph_typing.keys() and\
               self.action_graph_typing[pred] == "state":
                names = set(self.action_graph.node[pred].keys())
                values = list(self.action_graph.node[pred].values())[0]
                if state.name in names and state.value in values:
                    return pred
        return None

    def generate_nugget_id(self, name=None):
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

    def add_nugget(self, nugget, name=None):
        """Add nugget to the hierarchy."""
        nugget_id = self.generate_nugget_id()
        self.add_graph(nugget_id, nugget)
        return nugget_id

    def type_nugget_by_ag(self, nugget_id, typing):
        """Type nugget by the action graph."""
        self.add_typing(nugget_id, "action_graph", typing)
        return

    def type_nugget_by_meta(self, nugget_id, typing):
        """Type nugget by the meta-model."""
        self.add_typing(nugget_id, "kami", typing)
        return

    def add_mod_template_rel(self, nugget_id, rel):
        """Relate nugget to mod template."""
        self.add_relation(nugget_id, "mod_template", rel)
        return

    def add_semantic_nugget_rel(self, nugget_id, semantic_nugget_id, rel):
        """Relate a nugget to a semantic nugget."""
        self.add_relation(nugget_id, semantic_nugget_id, rel)
        return

    def merge_model(self, nugget, action_graph, ag_relation):
        """Merge hierarchy with an input model."""
        pass

    def add_nugget_magical(self, nugget, identifier_cls, add_agents=True,
                           anatomize=True, merge_actions=True,
                           apply_semantics=True):
        """Add nugget to the hierarchy + black box."""
        def _process_state(node_id, father):
            state_ref_id = identifier.identify_state(
                nugget.graph.node[node_id], father
            )
            if not state_ref_id:
                if add_agents:
                    pass
            else:
                relation.add((node_id, state_ref_id))
            return

        def _process_residue(node_id, father):
            residue_ref_id = identifier.identify_residue(
                nugget.graph.node[node_id], father
            )
            if not residue_ref_id:
                if add_agents:
                    pass
            else:
                relation.add((node_id, residue_ref_id))
            for pred in nugget.graph.predecessors(node_id):
                _process_state(pred, father)
                visited.add(pred)
            return

        def _process_is_bnd(locus_node, is_bnd_node, father):
            # first identify partners that connect from
            # the other side of locus
            for suc in nugget.graph.successors(is_bnd_node):
                if suc not in visited:
                    partner_locus = suc
                    for partner in nugget.graph.predecessors(suc):
                        if nugget.meta_typing[partner] == "agent":

                            partner_agent = _process_agent(partner)
                            visited.add(partner)
                            visited.add(partner_locus)
                            locus_ref_id, is_bnd_ref_id = identifier.identify_binding(
                                nugget.graph.node[locus_node],
                                nugget.graph.node[is_bnd_node],
                                nugget.graph.node[partner]
                            )
                            if not locus_ref_id:
                                pass
                            else:
                                relation.add((locus_node, locus_ref_id))
                                relation.add((is_bnd_node, is_bnd_ref_id))
                        elif nugget.meta_typing[partner] == "region":
                            partner_agent = nugget.graph.successors(partner)[0]
                            partner_agent_ref = _process_agent(partner_agent)
                            visited.add(partner_agent)
                            _process_region(partner, partner_agent_ref)
                            visited.add(partner)
                            visited.add(partner_locus)
                            locus_ref_id, is_bnd_ref_id = identifier.identify_binding(
                                nugget.graph.node[locus_node],
                                nugget.graph.node[is_bnd_node],
                                nugget.graph.node[partner]
                            )
                            if not locus_ref_id:
                                pass
                            else:
                                relation.add((locus_node, locus_ref_id))
                                relation.add((is_bnd_node, is_bnd_ref_id))
                        else:
                            pass

        def _process_region(node_id, father):
            region_ref_id = identifier.identify_region(
                nugget.graph.node[node_id], father
            )
            if not region_ref_id:
                if add_agents:
                    region_ref_id = "%s_region_%s_%s" %\
                        (
                            father,
                            list(nugget.graph.node[node_id]["start"])[0],
                            list(nugget.graph.node[node_id]["end"])[0]
                        )
                    add_node(self.action_graph, region_ref_id, nugget.graph.node[node_id])
                    self.action_graph_typing[region_ref_id] = "region"
            relation.add((node_id, region_ref_id))
            for pred in nugget.graph.predecessors(node):
                if nugget.meta_typing[pred] == "residue":
                    _process_residue(pred, region_ref_id)
                    visited.add(pred)
                elif nugget.meta_typing[pred] == "state":
                    _process_state(pred, region_ref_id)
                    visited.add(pred)
            for suc in nugget.graph.successors(node_id):
                if nugget.meta_typing[suc] == "locus":
                    if suc not in visited:
                        visited.add(suc)
                        for locus_pred in nugget.graph.predecessors(suc):
                            if nugget.meta_typing[locus_pred] == "is_bnd":
                                if locus_pred not in visited:
                                    visited.add(locus_pred)
                                    _process_is_bnd(suc, locus_pred, region_ref_id)

        def _process_agent(node_id):
            ref_id = identifier.identify_agent(nugget.graph.node[node_id])
            if not ref_id:
                if add_agents:
                    ref_id = list(nugget.graph.node[node_id]["uniprotid"])[0]
                    add_node(self.action_graph, ref_id, nugget.graph.node[node_id])
                    self.action_graph_typing[ref_id] = "agent"
            relation.add((node_id, ref_id))
            for pred in nugget.graph.predecessors(node):
                if nugget.meta_typing[pred] == "region":
                    if pred not in visited:
                        visited.add(pred)
                        _process_region(pred, ref_id)
                elif nugget.meta_typing[pred] == "residue":
                    if pred not in visited:
                        visited.add(pred)
                        _process_residue(pred, ref_id)
                elif nugget.meta_typing[pred] == "state":
                    if pred not in visited:
                        visited.add(pred)
                        _process_state(pred, ref_id)
            for suc in nugget.graph.successors(node):
                if nugget.meta_typing[suc] == "locus":
                    if suc not in visited:
                        visited.add(suc)
                        for locus_pred in nugget.graph.predecessors(suc):
                            if nugget.meta_typing[locus_pred] == "is_bnd":
                                if locus_pred not in visited:
                                    visited.add(locus_pred)
                                    _process_is_bnd(suc, locus_pred, ref_id)
            return ref_id

        identifier = identifier_cls(
            self.action_graph, self.action_graph_typing
        )

        relation = set()
        visited = set()
        for node in nugget.graph.nodes():
            if node not in visited:
                if nugget.meta_typing[node] == "agent":
                    ref_id = _process_agent(node)
                    visited.add(node)
