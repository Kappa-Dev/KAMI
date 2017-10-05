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
                                           Residue, State, NuggetAnnotation,
                                           MotifAgent, Motif)
from kami.data_structures.kami_hierarchy import KamiHierarchy
from kami.resolvers.identifiers import KamiIdentifier


class TestSh2Semantics(object):

    def test_sh2_pY_semantics(self):

        phos = State("phosphorylation", True)
        dok1_gene = Agent("Q99704", synonyms=["DOK1", "p62DOK1"])
        # ptail = PhysicalRegion(Region(name="Phospho-tail"))
        dok1_pY398 = MotifAgent(
            Motif([Residue("Y", 398, phos)], name="Phospho-tail"),
            PhysicalAgent(dok1_gene)
        )

        abl2 = PhysicalAgent(Agent("P42684", synonyms=["ABL2"]))
        sh2 = PhysicalRegion(Region(name="SH2"))

        abl2_sh2 = PhysicalRegionAgent(sh2, abl2)
        # dok1_pY398_ptail = PhysicalRegionAgent(ptail, dok1_pY398)

        bnd527 = BinaryBinding([dok1_pY398], [abl2_sh2])
        print(bnd527)

        hierarchy = create_nuggets([bnd527])
        # print(hierarchy)
        # print_graph(hierarchy.node["nugget_1"].graph)
        # print_graph(hierarchy.action_graph)

    def test_multiple_sh2(self):
        phos = State("phosphorylation", True)
        sh2n = PhysicalRegion(Region(name="SH2", order=1))
        sh2c = PhysicalRegion(Region(name="SH2", order=2))

        pik3r1 = PhysicalAgent(Agent("P27986", synonyms=["PIK3R1", "PI3K1"]))
        pik3r1_sh2n = PhysicalRegionAgent(sh2n, pik3r1)
        pik3r1_sh2c = PhysicalRegionAgent(sh2c, pik3r1)

        frs2_gene = Agent("Q8WU20", synonyms=["FRS2"])
        frs2_pY196 = PhysicalAgent(
            frs2_gene, residues=[Residue("Y", 196, phos)])
        frs2_pY349 = PhysicalAgent(
            frs2_gene, residues=[Residue("Y", 349, phos)])

        bnds = []
        bnds.append(BinaryBinding([frs2_pY196], [pik3r1_sh2n]))
        bnds.append(BinaryBinding([frs2_pY349], [pik3r1_sh2c]))
