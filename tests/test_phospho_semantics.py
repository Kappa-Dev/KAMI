"""."""
from regraph.primitives import print_graph

from kami.data_structures.entities import Agent, PhysicalAgent, Residue, State
from kami.data_structures.interactions import Modification
from kami.resolvers.black_box import create_nuggets


class TestPhosphSemantics:

    def __init__(self):

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

        self.interactions = [mod1, mod2, mod3, mod4]

    def test_create_nuggets(self):
        hierarchy = create_nuggets(
            self.interactions,
            add_agents=True,
            anatomize=True
        )
        # print(hierarchy.action_graph.nodes())
        # print(hierarchy.relation["action_graph"]["semantic_action_graph"].rel)
        # print(hierarchy)
        # print_graph(hierarchy.action_graph)
        # print(hierarchy.relation["action_graph"]["semantic_action_graph"].rel)
