"""."""
import networkx as nx

from regraph.hierarchy import Hierarchy
from regraph.primitives import (add_node,
                                add_edge)

from kami.exceptions import KamiHierarchyError
from kami.resources import (metamodels,
                            nugget_templates)


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

        self.add_graph("kami", metamodels.kami)

        action_graph = nx.DiGraph()
        self.add_graph("action_graph", action_graph)
        self.add_typing("action_graph", "kami", dict(), ignore_attrs=True)
        self.action_graph = self.node["action_graph"].graph
        self.action_graph_typing = self.edge["action_graph"]["kami"].mapping

        self.add_graph("mod_template", nugget_templates.mod_nugget)
        self.add_typing("mod_template", "kami", nugget_templates.mod_kami_typing)
        self.mod_template = self.node["mod_template"].graph

        self.add_graph("bnd_template", nugget_templates.bnd_nugget)
        self.add_typing("bnd_template", "kami", nugget_templates.bnd_kami_typing)
        self.bnd_template = self.node["bnd_template"].graph
        return

    @classmethod
    def from_json(cls, json_data):
        hierarchy = Hierarchy.from_json(json_data)
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

    def get_agent_by_region(self, region_id):
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

    def add_region(self, region, ref_agent):
        """Add region node to action graph connected to `ref_agent`."""
        found = False
        ref_agent_id = None

        # found node in AG corresponding to reference agent
        agent_nodes = self.get_agents()
        for node in agent_nodes:
            if self.action_graph.node[node]["uniprotid"] == {ref_agent}:
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
        return region_id

    def add_residue(self, residue, ref_agent):
        """."""
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
        """."""
        state_id = ref_agent + "_" + str(state)
        add_node(self.action_graph, state_id, state.to_attrs())
        self.action_graph_typing[state_id] = "state"
        add_edge(self.action_graph, state_id, ref_agent)
        return state_id

    def find_agent(self, agent):
        """Find corresponding agent in action graph."""
        agents = self.get_agents()
        for node in agents:
            if self.action_graph.node[node]["uniprotid"] == {agent.uniprotid}:
                return node
        return None

    def find_region(self, region, ref_agent):
        """Find corresponding region in action graph."""
        found = False
        agent_node = None
        agent_nodes = self.get_agents()
        for node in agent_nodes:
            if self.action_graph.node[node]["uniprotid"] == {ref_agent}:
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
            if self.action_graph.node[res]["loc"] == {residue.loc} and\
               residue.aa <= self.action_graph.node[res]["aa"]:
                return res
        return None

    def find_state(self, state, ref_agent):
        for pred in self.action_graph.predecessors(ref_agent):
            if pred in self.action_graph_typing.keys() and\
               self.action_graph_typing[pred] == "state":
                names = set(self.action_graph.node[pred].keys())
                values = list(self.action_graph.node[pred].values())[0]
                if names == {state.name} and state.value in values:
                    return pred
        return None

    def add_nugget(self, nugget, name=None):
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
        self.add_graph(nugget_id, nugget)
        return nugget_id

    def type_nugget_by_ag(self, nugget_id, typing):
        self.add_typing(nugget_id, "action_graph", typing, ignore_attrs=True)
        return

    def type_nugget_by_meta(self, nugget_id, typing):
        self.add_typing(nugget_id, "kami", typing, ignore_attrs=True)
        return

    def add_mod_template_rel(self, nugget_id, rel):
        self.add_relation(nugget_id, "mod_template", rel)
        return
