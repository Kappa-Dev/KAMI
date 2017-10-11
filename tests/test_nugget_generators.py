"""Collection of tests for nugget generators."""
# from regraph.primitives import print_graph

from kami.nugget_generators import (ModGenerator,
                                    AutoModGenerator,
                                    TransModGenerator,
                                    BinaryBndGenerator,
                                    AnonymousModGenerator,
                                    ComplexGenerator)
from kami.data_structures.entities import (PhysicalAgent, Agent,
                                           PhysicalRegion, Region,
                                           PhysicalRegionAgent,
                                           Residue, State,
                                           )


class TestNuggetGenerators(object):
    """Test class for nugget generators."""

    def __init__(self):
        """."""
        self.generators = []

        # 1a. Simple modification generator
        enz_res = Residue("S", 100, State("phospho", True))
        enzyme_entity = PhysicalAgent(Agent("E"), residues=[enz_res])

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

        mod_generator = ModGenerator(enzyme_entity, substrate_entity, mod_state, value)

        self.generators.append(mod_generator)

        # 1b. Complex modification generator

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

        gen = ModGenerator(enzyme, substrate, mod_target, True)
        assert(len(gen.nugget.nodes()) == len(gen.meta_typing.keys()))

        # print_graph(gen.nugget)
        # print(gen.meta_typing)
        # print(gen.template_relation)

        self.generators.append(gen)

        # 2. Automodification
        agent = Agent("A")

        a1 = PhysicalAgent(Agent("B"))
        a2 = PhysicalAgent(Agent("C"))

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

        # print_graph(gen.nugget)
        # print(gen.meta_typing)
        # print(gen.template_relation)

        self.generators.append(gen)

        # 3. Transmodification
        enzyme_ph_agent = PhysicalAgent(Agent("A"))

        substrate_ph_agent = PhysicalRegionAgent(
            PhysicalRegion(Region(10, 20, "aa")),
            PhysicalAgent(Agent("A"))
        )

        gen = TransModGenerator(
            enzyme_ph_agent,
            substrate_ph_agent,
            State("activity", False),
            True
        )
        assert(len(gen.nugget.nodes()) == len(gen.meta_typing.keys()))

        # print_graph(gen.nugget)
        # print(gen.meta_typing)
        # print(gen.template_relation)

    def test_anonymous_mod_nugget(self):
        """."""
        substrate_ph_agent = PhysicalAgent(
            Agent("A"),
            residues=[
                Residue("S", 100, State("phospho", True)),
                Residue("T", 205, State("phospho", True))
            ]
        )

        gen = AnonymousModGenerator(
            substrate_ph_agent,
            State("activity", False),
            True
        )
        assert(len(gen.nugget.nodes()) == len(gen.meta_typing.keys()))

        # print_graph(gen.nugget)
        # print(gen.meta_typing)
        # print(gen.template_relation)

    def test_binary_bnd_nugget(self):
        """."""
        left_members = [
            PhysicalAgent(
                Agent("A1"), states=[State('activity', True)]
            ),
            PhysicalRegionAgent(
                PhysicalRegion(Region(100, 200, "a2"), residues=[Residue("S", 100)]),
                PhysicalAgent(Agent("A2"))
            )
        ]

        right_members = [
            PhysicalRegionAgent(
                PhysicalRegion(Region(1, 500, "b")),
                PhysicalAgent(Agent("B"), bounds=[
                    [PhysicalAgent(Agent("C")), PhysicalAgent(Agent("D"))]
                ])
            )
        ]

        gen = BinaryBndGenerator(left_members, right_members)
        # print_graph(gen.nugget)
        # print(gen.meta_typing)
        # print(gen.template_relation)

    def test_complex_nugget(self):
        """."""
        members = [
            PhysicalAgent(Agent("A")),
            PhysicalAgent(Agent("B")),
            PhysicalRegionAgent(
                PhysicalRegion(Region(1, 2)),
                PhysicalAgent(Agent("C"))
            )
        ]

        gen = ComplexGenerator(members)
        # print_graph(gen.nugget)
        # print(gen.meta_typing)

    # def add_residue_to_agent(self):
    #     pass

    # def add_state_to_agent(self):
    #     pass

    # def add_is_bnd_to_agent(self):
    #     pass

    # def add_is_free_to_agent(self):
    #     pass

    # def add_region_to_agent(self):
    #     pass

    # def insert_region(self):
    #     pass

    # def add_is_bnd_between(self):
    #     pass
