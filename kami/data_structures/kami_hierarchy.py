"""."""
import networkx as nx

from regraph.hierarchy import Hierarchy

from kami.resources import (metamodels,
                            nugget_templates)


class KamiHierarchy(Hierarchy):
    """Kami-specific hierarchy class."""

    def __init__(self):
        """Initialize empty kami hierarchy."""
        Hierarchy.__init__(self)
        self.add_graph("kami", metamodels.kami)

        action_graph = nx.DiGraph()
        self.add_graph("action_graph", action_graph)
        self.add_typing("action_graph", "kami", dict())
        self.action_graph = self.node["action_graph"].graph

        self.add_graph("mod_template", nugget_templates.mod_nugget)
        self.add_typing("mod_template", "kami", nugget_templates.mod_kami_typing)
        self.mod_template = self.node["mod_template"].graph

        self.add_graph("bnd_template", nugget_templates.bnd_nugget)
        self.add_typing("bnd_template", "kami", nugget_templates.bnd_kami_typing)
        self.bnd_template = self.node["bnd_template"].graph
        return

    def _generate_agent_id(self, agent):
        pass

    def _generate_region_id(self, region):
        pass

    def _generate_residue_id(self, residue):
        pass

    def _generate_state_id(self, state):
        pass

    def add_agent_to_ag(self, agent):
        pass

    def add_region_to_ag(self, region, ref_agent):
        pass

    def add_residue_to_ag(self, residue, ref_agent):
        pass

    def add_state_to_ag(self, state, ref_agent):
        pass

    def find_agent(self, agent):
        pass

    def find_region(self, region, ref_agent):
        pass
