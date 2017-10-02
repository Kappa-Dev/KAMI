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
from kami.resolvers.generators import NuggetContrainer
from kami.resolvers.identifiers import KamiIdentifier


class TestBlackBox:
    """."""

    def __init__(self):

        self.interactions = []

        # 1a. Simple modification example
        enz_res = Residue("S", 100, State("phospho", True))
        enz_reg = PhysicalRegion(
            Region(150, 170),
            states=[State("activity", True)]
        )
        enzyme_entity = PhysicalAgent(Agent("P00533"), regions=[enz_reg], residues=[enz_res])

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

        self.interactions.append(mod1)

        # 1b. Complex modification example
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
        self.interactions.append(mod2)

    def test_create_nuggets(self):
        create_nuggets(self.interactions, add_agents=True, anatomize=False)

    # def test_add_nugget_graph(self):

    #     h = KamiHierarchy()

    #     n = nx.DiGraph()
    #     add_nodes_from(n, [
    #         ("Q9UN19", {"uniprotid": {"Q9UN19"}}),
    #         ("Q9UN19_Y139", {"aa": {"Y"}, "loc": {139}}),
    #         ("Q9UN19_Y139_phosphorylation", {"phosphorylation": {True}}),
    #         ("Q9UN19_region_100_200", {"start": {100}, "end": {200}}),
    #         ("mod", {"value": {True}}),
    #         ("Q16539", {"uniprotid": {"Q16539"}}),
    #         ("Q16539_activity", {"active": {True}}),
    #         ("P16333", {"uniprotid": {"P16333"}})
    #     ])
    #     add_edges_from(n, [
    #         ("Q9UN19_Y139", "Q9UN19"),
    #         ("Q9UN19_Y139_phosphorylation", "Q9UN19_Y139"),
    #         ("Q9UN19_region_100_200", "Q9UN19"),
    #         ("Q9UN19_region_100_200", "mod"),
    #         ("mod", "Q16539_activity"),
    #         ("Q16539_activity", "Q16539"),
    #         ("Q9UN19_region_100_200", "Q9UN19_region_100_200_locus_Q9UN19_region_100_200_is_bnd_P16333"),
    #         ("Q9UN19_region_100_200_is_bnd_P16333", "Q9UN19_region_100_200_locus_Q9UN19_region_100_200_is_bnd_P16333"),
    #         ("Q9UN19_region_100_200_is_bnd_P16333", "P16333_locus_Q9UN19_region_100_200_is_bnd_P16333"),
    #         ("P16333", "P16333_locus_Q9UN19_region_100_200_is_bnd_P16333")
    #     ])

    #     nugget = NuggetContrainer(
    #         n,
    #         meta_typing={
    #             "Q9UN19": "agent",
    #             "Q16539": "agent",
    #             "Q9UN19_Y139": "residue",
    #             "Q9UN19_Y139_phosphorylation": "state",
    #             "mod": "mod",
    #             "Q16539_activity": "state",
    #             "Q9UN19_region_100_200": "region",
    #             "P16333": "agent",
    #             "Q9UN19_region_100_200_is_bnd_P16333": "is_bnd",
    #             "P16333_locus_Q9UN19_region_100_200_is_bnd_P16333": "locus",
    #             "Q9UN19_region_100_200_locus_Q9UN19_region_100_200_is_bnd_P16333": "locus"
    #         }
    #     )

    #     h.add_nugget_magical(
    #         nugget,
    #         KamiIdentifier
    #     )

    def test_sh2_pY_semantics(self):

        phos = State("phosphorylation", True)
        dok1_gene = Agent("Q99704", synonyms=["DOK1", "p62DOK1"])
        # ptail = PhysicalRegion(Region(name="Phospho-tail"))
        dok1_pY398 = PhysicalAgent(dok1_gene, residues=[Residue("Y", 398, phos)])

        abl2 = PhysicalAgent(Agent("P42684", synonyms=["ABL2"]))
        sh2 = PhysicalRegion(Region(name="SH2"))

        abl2_sh2 = PhysicalRegionAgent(sh2, abl2)
        # dok1_pY398_ptail = PhysicalRegionAgent(ptail, dok1_pY398)

        bnd527 = BinaryBinding([dok1_pY398], [abl2_sh2])
        print(bnd527)
        # bnd = BinaryBinding(
        #     [PhysicalRegionAgent(
        #         PhysicalRegion(
        #             Region(
        #                 100, 200, "SH2"
        #             )
        #         ),
        #         PhysicalAgent(
        #             Agent(
        #                 "P00533"
        #             )
        #         )
        #     )],
        #     [
        #         PhysicalAgent(
        #             Agent(
        #                 "Q00534"
        #             )
        #         ),
        #         PhysicalAgent(
        #             Agent(
        #                 "R00533"
        #             )
        #         )
        #     ],
        #     direct=True
        # )
        # print(bnd)
        hierarchy = create_nuggets([bnd527])
        print(hierarchy)
        print_graph(hierarchy.node["nugget_1"].graph)
        print_graph(hierarchy.action_graph)