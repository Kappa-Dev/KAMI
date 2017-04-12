"""."""
from regraph.library.primitives import print_graph

from kami.nugget_generators import (ModGenerator,
                                    AutoModGenerator,)
from kami.data_structures.entities import (PhysicalAgent, Agent,
                                           PhysicalRegion, Region,
                                           PhysicalRegionAgent,
                                           Residue, State, NuggetAnnotation,
                                           )


class TestNuggetGenerators(object):
    """Collection of tests for nugget generators."""

    def test_simple_mod_nugget(self):
        enz_res = Residue("S", 100, State("phospho", True))
        enzyme_entity = PhysicalAgent(Agent("4334778", ["EGFR"]), residues=[enz_res])

        sub_bound_1 = PhysicalAgent(
            Agent("232324", ["Agent 2"]),
            states=[State("activity", True)]
        )
        sub_bound_2 = PhysicalAgent(
            Agent("232324", ["Agent 2"]),
            states=[State("activity", True)]
        )

        substrate_entity = PhysicalAgent(
            Agent("34343434", ["Agent1"]),
            bounds=[[sub_bound_1], [sub_bound_2]]
        )

        mod_state = State("activity", False)
        value = True

        mod_generator = ModGenerator(enzyme_entity, substrate_entity, mod_state, value)

        print_graph(mod_generator.nugget)
        print(mod_generator.meta_typing)
        print(mod_generator.template_relation)

    def test_complex_mod_nugget(self):

        enzyme_agent = Agent("B123232", ["BRAF"], {"GO": "121313"})
        enzyme_ph_agent = PhysicalAgent(enzyme_agent)
        enzyme_region = PhysicalRegion(Region(100, 200, "sh2"))
        enzyme = PhysicalRegionAgent(enzyme_region, enzyme_ph_agent)

        substrate_agent = Agent("M344343", ["MAPK1"])
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
                Agent("R3344", ["RAF"])
            )
        )

        substrate_bound = PhysicalAgent(
            Agent("E237378", ["EGFR"]),
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

        gen = ModGenerator(enzyme, substrate, mod_target, True)
        assert(len(gen.nugget.nodes()) == len(gen.meta_typing.keys()))

        print_graph(gen.nugget)
        print(gen.meta_typing)
        print(gen.template_relation)

    def test_auto_mod_nugget(self):
        agent = Agent("R344353", ["RAF"])

        a1 = PhysicalAgent(Agent("E343434", ["EGFR"]))
        a2 = PhysicalAgent(Agent("M345777", ["MEK"]))

        ph_agent = PhysicalAgent(agent, bounds=[[a1, a2]])

        enz_region = Region(100, 200, "region")

        reg_residue = Residue(["T", "S"])
        ph_enz_region = PhysicalRegion(enz_region, [reg_residue])

        sub_region = Region(300, 450)
        ph_sub_region = PhysicalRegion(sub_region, states=[State("activity", True)])

        state = State("phosphorylation", False)
        residue = Residue("S", 402, state)

        gen = AutoModGenerator(
            ph_agent, residue, True,
            enz_region=ph_enz_region,
            sub_region=ph_sub_region
        )
        assert(len(gen.nugget.nodes()) == len(gen.meta_typing.keys()))

        print_graph(gen.nugget)
        print(gen.meta_typing)
        print(gen.template_relation)

    def test_trans_mod_nugget(self):
        pass