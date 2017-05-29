"""."""
from kami.exceptions import KamiIndentifierError


class KamiIdentifier:
    """Set of utils for identification of proteins and interactions."""

    def __init__(self, action_graph, action_graph_typing):
        self.action_graph = action_graph
        self.action_graph_typing = action_graph_typing

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
        """Get agent id conntected to the region."""
        for suc in self.action_graph.successors(region_id):
            if suc in self.action_graph_typing.keys() and\
               self.action_graph_typing[suc] == "agent":
                return suc
        return None

    def identify_agent(self, agent):
        """Identify agent in the action graph."""
        for node in self.get_agents():
            if self.action_graph.node[node]["uniprotid"] ==\
               agent["uniprotid"]:
                return node
        return None

    def identify_region(self, region, father_ref):
        """Find corresponding region in action graph."""
        # currently assume there is no nesting of regions at the moment
        region_candidates = self.get_regions_of_agent(father_ref)
        for reg in region_candidates:
            start = list(self.action_graph.node[reg]["start"])[0]
            end = list(self.action_graph.node[reg]["end"])[0]
            if region["start"] >= start and region["end"] <= end:
                return reg
        return None

    def identify_residue(self, residue, father_ref):
        residue_candidates = self.get_attached_residues(father_ref)
        for res in residue_candidates:
            if self.action_graph.node[res]["loc"] == residue["loc"] and\
               residue["aa"] <= self.action_graph.node[res]["aa"]:
                return res
        return None

    def identify_state(self, state, father_ref):
        for pred in self.action_graph.predecessors(father_ref):
            if pred in self.action_graph_typing.keys() and\
               self.action_graph_typing[pred] == "state":
                names = set(self.action_graph.node[pred].keys())
                values = list(self.action_graph.node[pred].values())[0]
                if names == {state.keys()[0]} and state.values()[0] in values:
                    return pred
        return None

    def identify_binding(self, locus_node, is_bnd_node, partner):
        locus_ref_id = None
        is_bnd_ref_id = None
        return locus_ref_id, is_bnd_ref_id
