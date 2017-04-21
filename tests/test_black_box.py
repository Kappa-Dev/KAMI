"""."""
from regraph.primitives import print_graph

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
                                           Residue, State, NuggetAnnotation,
                                           )


class TestBlackBox:
    """."""

    def __init__(self):

        self.interactions = []
        
        # 1a. Simple modification example
        enz_res = Residue("S", 100, State("phospho", True))
        enz_reg = PhysicalRegion(
            Region(100, 200),
            states=[State("activity", True)]
        )
        enzyme_entity = PhysicalAgent(Agent("E"), regions=[enz_reg], residues=[enz_res])

        sub_bound_1 = PhysicalAgent(
            Agent("A"),
            states=[State("activity", True)]
        )
        sub_bound_2 = PhysicalAgent(
            Agent("A"),
            states=[State("activity", True)]
        )

        substrate_entity = PhysicalAgent(
            Agent("S"),
            bounds=[[sub_bound_1], [sub_bound_2]]
        )

        mod_state = State("activity", False)
        value = True

        mod1 = Modification(
            enzyme_entity, substrate_entity, mod_state, value
        )

        self.interactions.append(mod1)

        # 1b. Complex modification example
        enzyme_agent = Agent("Enzyme")
        enzyme_ph_agent = PhysicalAgent(enzyme_agent)
        enzyme_region = PhysicalRegion(Region(100, 200, "sh2"))
        enzyme = PhysicalRegionAgent(enzyme_region, enzyme_ph_agent)

        substrate_agent = Agent("Substrate")
        state = State("phosphorylation", True)
        reg_residue = Residue("S", 102, state)

        substrate_region = PhysicalRegion(
            Region(222, 333),
            residues=[reg_residue]
        )

        substrate_residues = [
            Residue("T", "222"),
            Residue("S", "56", State("phosphorylation", True))
        ]

        substrate_state = State("activity", True)

        next_level_bound = PhysicalRegionAgent(
            PhysicalRegion(
                Region(224, 234)
            ),
            PhysicalAgent(
                Agent("A")
            )
        )

        substrate_bound = PhysicalAgent(
            Agent("B"),
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
        self.interactions.append(mod2)

    def test_create_nuggets(self):
        create_nuggets(self.interactions)
