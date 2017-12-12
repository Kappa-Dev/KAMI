"""."""
from kami.resolvers.new_generators import ModGenerator
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
                gene=Gene("P00533"),
                region=Region(name="Kinase_region", start=750, end=850)),
            Gene("P12931"),
            Residue("T", 100, State("phosphorylation", False)),
            True
        )
        n_id = modgen.generate(mod)

        mod = Modification(
            RegionActor(
                gene=Gene("P00533"),
                region=Region(name="Kinase_region", start=750, end=850)),
            Gene("P00519"),
            Residue("Y", 500, State("phosphorylation", False)),
            True
        )
        n_id = modgen.generate(mod)
        print_graph(hie.action_graph)
        print_graph(hie.nugget[n_id])
        print(hie.relation["action_graph"]["semantic_action_graph"].rel)