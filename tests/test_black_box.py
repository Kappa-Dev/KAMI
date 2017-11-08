"""Unit testing of black box functionality."""

from regraph.primitives import (print_graph)

from kami.resolvers.black_box import create_nuggets
from kami.interactions import (Modification,
                               BinaryBinding)
from kami.entities import (Gene, Region, RegionActor, Residue,
                           Site, SiteActor, State)
from kami.hierarchy import KamiHierarchy


class TestBlackBox(object):
    """Test class for black box functionality."""

    def __init__(self):
        """Initialize with an empty hierarchy."""
        self.hierarchy = KamiHierarchy()

    def test_simple_mod_nugget(self):
        """Simple modification interaction example."""
        enz_res = Residue("S", 100, State("phospho", True))
        enz_reg = Region(
            start=150,
            end=170,
            states=[State("activity", True)]
        )
        enzyme_entity = Gene("P00533", regions=[enz_reg], residues=[enz_res])

        sub_bound_1 = Gene("P28482", states=[State("activity", True)])
        sub_bound_2 = Gene("P28482", states=[State("activity", True)])

        substrate_entity = Gene("P04049", bounds=[[sub_bound_1], [sub_bound_2]])

        mod_state = State("activity", False)
        value = True

        mod1 = Modification(
            enzyme_entity, substrate_entity, mod_state, value
        )
        # Create corresponding nugget in the hierarchy
        create_nuggets([mod1], hierarchy=self.hierarchy,
                       add_agents=True, anatomize=False)

    def test_complex_mod_nugget(self):
        """Complex modification interaction example."""
        enzyme_agent = Gene("P04049")
        enzyme_region = Region(100, 200, "lala")
        enzyme = RegionActor(enzyme_agent, enzyme_region)

        state = State("phosphorylation", True)
        reg_residue = Residue("S", 550, state)
        substrate_region = Region(
            start=500,
            end=600,
            residues=[reg_residue]
        )

        substrate_residues = [
            Residue("T", 100),
            Residue("S", 56, State("phosphorylation", True))
        ]

        substrate_state = State("activity", True)

        next_level_bound = RegionActor(
            Gene("P04637"),
            Region(start=224, end=234)
        )

        substrate_bound = Gene(
            "P12931",
            bounds=[next_level_bound]
        )

        substrate = Gene(
            "P00533",
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
        mek1 = Gene("Q02750")
        stat3 = Gene("P40763")
        mod_state = Residue("S", 727, State("phosphorylation", False))
        value = True

        mod1 = Modification(mek1, stat3, mod_state, value)

        mod_state_1 = Residue("Y", 705, State("phosphorylation", False))

        mod2 = Modification(mek1, stat3, mod_state_1, value)

        erk1 = Gene("P27361")

        mod_state_2 = Residue("T", 201, State("phosphorylation", False))

        mod3 = Modification(mek1, erk1, mod_state_2, value)

        erk2 = Gene("P28482")
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

    def test_sh2_py_semantics(self):
        """."""
        phos = State("phosphorylation", True)
        dok1_py398 = Gene(
            "Q99704",
            synonyms=["DOK1", "p62DOK1"],
            residues=[Residue("Y", 398, phos)]
        )

        abl2 = Gene("P42684", synonyms=["ABL2"])
        sh2 = Region(name="SH2")

        abl2_sh2 = RegionActor(abl2, sh2)

        bnd527 = BinaryBinding([dok1_py398], [abl2_sh2])
        print(bnd527)

        hierarchy = create_nuggets([bnd527])
        # print(hierarchy)
        # print_graph(hierarchy.node["nugget_1"].graph)
        # print_graph(hierarchy.action_graph)

    def test_multiple_sh2(self):
        """."""
        phos = State("phosphorylation", True)
        sh2n = Region(name="SH2", order=1)
        sh2c = Region(name="SH2", order=2)

        pik3r1 = Gene("P27986", synonyms=["PIK3R1", "PI3K1"])
        pik3r1_sh2n = RegionActor(pik3r1, sh2n)
        pik3r1_sh2c = RegionActor(pik3r1, sh2c)

        frs2_py196 = Gene(
            "Q8WU20",
            synonyms=["FRS2"],
            residues=[Residue("Y", 196, phos)]
        )
        frs2_py349 = Gene(
            "Q8WU20",
            synonyms=["FRS2"],
            residues=[Residue("Y", 349, phos)]
        )

        bnds = []
        bnds.append(BinaryBinding([frs2_py196], [pik3r1_sh2n]))
        bnds.append(BinaryBinding([frs2_py349], [pik3r1_sh2c]))
