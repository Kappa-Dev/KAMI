"""."""
import networkx as nx

from regraph.primitives import (print_graph,
                                add_nodes_from,
                                add_edges_from)

from kami.resolvers.black_box import create_nuggets
from kami.data_structures.interactions import (Modification,
                                               AutoModification,
                                               TransModification,
                                               BinaryBinding,
                                               AnonymousModification,
                                               Complex)
from kami.data_structures.entities import (PhysicalAgent, Agent,
                                           PhysicalRegion, Region,
                                           PhysicalRegionAgent,
                                           Residue, State, NuggetAnnotation,)
from kami.data_structures.kami_hierarchy import KamiHierarchy
from kami.resolvers.generators import NuggetContainer
from kami.resolvers.identifiers import KamiIdentifier


class TestBlackBox(object):
    """."""
    def __init__(self):
        # Initialize with an empty hierarchy
        self.hierarchy = KamiHierarchy()

    def test_simple_mod_nugget(self):
        """Simple modification interaction example."""
        enz_res = Residue("S", 100, State("phospho", True))
        enz_reg = PhysicalRegion(
            Region(150, 170),
            states=[State("activity", True)]
        )
        enzyme_entity = PhysicalAgent(Agent("P00533"), regions=[
                                      enz_reg], residues=[enz_res])

        sub_bound_1 = PhysicalAgent(
            Agent("P28482"),
            states=[State("activity", True)]
        )
        sub_bound_2 = PhysicalAgent(
            Agent("P28482"),
            states=[State("activity", True)]
        )
        substrate_entity = PhysicalAgent(
            Agent("P04049"),
            bounds=[[sub_bound_1], [sub_bound_2]]
        )

        mod_state = State("activity", False)
        value = True

        mod1 = Modification(
            enzyme_entity, substrate_entity, mod_state, value
        )
        # Create corresponding nugget in the hierarchy
        create_nuggets([mod1], hierarchy=self.hierarchy, add_agents=True, anatomize=False)

    def test_complex_mod_nugget(self):
        """Complex modification interaction example."""
        enzyme_agent = Agent("P04049")
        enzyme_ph_agent = PhysicalAgent(enzyme_agent)
        enzyme_region = PhysicalRegion(Region(100, 200, "lala"))
        enzyme = PhysicalRegionAgent(enzyme_region, enzyme_ph_agent)

        substrate_agent = Agent("P00533")

        state = State("phosphorylation", True)
        reg_residue = Residue("S", 550, state)
        substrate_region = PhysicalRegion(
            Region(500, 600),
            residues=[reg_residue]
        )

        substrate_residues = [
            Residue("T", 100),
            Residue("S", 56, State("phosphorylation", True))
        ]

        substrate_state = State("activity", True)

        next_level_bound = PhysicalRegionAgent(
            PhysicalRegion(
                Region(224, 234)
            ),
            PhysicalAgent(
                Agent("P04637")
            )
        )

        substrate_bound = PhysicalAgent(
            Agent("P12931"),
            bounds=[next_level_bound]
        )

        substrate = PhysicalAgent(
            substrate_agent,
            regions=[substrate_region],
            residues=substrate_residues,
            states=[substrate_state],
            bounds=[substrate_bound]
        )

        mod_target = Residue("S", "33", State("phosphorylation", False))
        mod2 = Modification(enzyme, substrate, mod_target, True)
        create_nuggets([mod2], add_agents=True, anatomize=False)

    def test_phospho_semantics(self):
        """Test black box processing using phosphorylation semantics."""
        mek1 = PhysicalAgent(Agent("Q02750"))
        stat3 = PhysicalAgent(Agent("P40763"))
        mod_state = Residue("S", 727, State("phosphorylation", False))
        value = True

        mod1 = Modification(mek1, stat3, mod_state, value)

        mod_state_1 = Residue("Y", 705, State("phosphorylation", False))

        mod2 = Modification(mek1, stat3, mod_state_1, value)

        erk1 = PhysicalAgent(Agent("P27361"))

        mod_state_2 = Residue("T", 201, State("phosphorylation", False))

        mod3 = Modification(mek1, erk1, mod_state_2, value)

        erk2 = PhysicalAgent(Agent("P28482"))
        mod_state_3 = Residue("T", 182, State("phosphorylation", False))

        mod4 = Modification(mek1, erk2, mod_state_3, value)

        interactions = [mod1, mod2, mod3, mod4]

        hierarchy = create_nuggets(
            interactions,
            add_agents=True,
            anatomize=True
        )
        print(hierarchy.action_graph.nodes())
        print(hierarchy.relation["action_graph"]["semantic_action_graph"].rel)
        print(hierarchy)
        print_graph(hierarchy.action_graph)
        print(hierarchy.relation["action_graph"]["semantic_action_graph"].rel)
