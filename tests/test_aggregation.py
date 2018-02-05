"""."""
from kami.resolvers.generators import ModGenerator, BndGenerator
from kami.hierarchy import KamiHierarchy
from kami.entities import *
from kami.interactions import *

from regraph.primitives import print_graph


class TestNewGenerators:
    """."""

    def test_mod_generation(self):
        """."""
        hie = KamiHierarchy()
        hie.create_empty_action_graph()

        modgen = ModGenerator(hie)

        mod = Modification(
            RegionActor(
                gene=Gene("P00533", states=[State("phosphorylation", True)]),
                region=Region(name="Kinase_region", start=750, end=850)),
            Gene("P12931"),
            Residue("T", 100, State("phosphorylation", False)),
            True
        )
        n1_id = modgen.generate(mod)

        mod = Modification(
            Gene("P00533", states=[State("activity", True), State("phosphorylation", False)]),
            Gene("P00519"),
            Residue("Y", 500, State("phosphorylation", False)),
            True
        )
        n2_id = modgen.generate(mod)

    #     mod = Modification(
    #         Gene("P00533"),
    #         Gene("P00519"),
    #         State("phosphorylation", False),
    #         True
    #     )
    #     n3_id = modgen.generate(mod)

    # # def test_bnd_generation(self):
    # #     hie = KamiHierarchy()
    # #     hie.create_empty_action_graph()

    #     bndgen = BndGenerator(hie)
    #     bnd = Binding(
    #         [RegionActor(gene=Gene("P62993"), region=Region(name="SH2"))],
    #         [Gene("Q8WU20",
    #               synonyms=["FRS2"],
    #               residues=[Residue("Y", 196, State("phosphorylation", True))])]
    #     )
    #     n_id = bndgen.generate(bnd)

    #     bnd = Binding(
    #         [RegionActor(gene=Gene("P62993"), region=Region(name="SH2"))],
    #         [SiteActor(gene=Gene("P00533"), site=Site(name="pY"))]
    #     )
    #     n_id = bndgen.generate(bnd)

    #     # print_graph(hie.action_graph)
        # edge_list = hie.ag_to_edge_list()
        # with open("lala.csv", "w+") as f:
        #     for u, v in edge_list:
        #         f.write("%s, %s\n" % (u, v))
        print(hie.relation["action_graph"]["semantic_action_graph"])
        print(hie.action_graph.edges())