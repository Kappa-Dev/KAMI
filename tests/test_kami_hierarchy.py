"""Tests related to KamiHierarchy data structure."""
from kami.data_structures import entities, interactions
from kami.data_structures.kami_hierarchy import KamiHierarchy
from kami.resolvers.black_box import create_nuggets


class TestKamiHierarchy(object):
    """."""

    def test_empty_hierarchy(self):
        """Test getters for various hierarchy components."""
        hierarchy = KamiHierarchy()
        assert(hierarchy.action_graph is None)
        assert(len(hierarchy.nuggets()) == 0)
        assert(hierarchy.empty())

        json_hierarchy = hierarchy.to_json()
        new_hierarchy = KamiHierarchy.from_json(json_hierarchy)
        assert(isinstance(new_hierarchy, KamiHierarchy))
        assert(new_hierarchy == hierarchy)

        hierarchy.export("test_empty_hierarchy.json")
        new_hierarchy = KamiHierarchy.load("test_empty_hierarchy.json")
        assert(isinstance(new_hierarchy, KamiHierarchy))
        assert(new_hierarchy == hierarchy)

        assert(hierarchy.mod_template is
               hierarchy.node["mod_template"].graph)
        assert(hierarchy.bnd_template is hierarchy.node["bnd_template"].graph)
        assert(hierarchy.semantic_action_graph is
               hierarchy.node["semantic_action_graph"].graph)

    def test_non_empty_hierarchy(self):
        """."""
        hierarchy = KamiHierarchy()

        plcg1_pY1253 = entities.PhysicalAgent(entities.Agent("P19174", synonyms=["PLCG1"]), residues=[
            entities.Residue("Y", 1253, state=entities.State("phosphorylation", True))])
        sh2 = entities.PhysicalRegion(entities.Region(name="SH2"))
        abl1 = entities.PhysicalAgent(
            entities.Agent("P00519", synonyms=["ABL1"]))
        abl1_sh2 = entities.PhysicalRegionAgent(sh2, abl1)
        bnd = interactions.BinaryBinding([plcg1_pY1253], [abl1_sh2])

        create_nuggets([bnd], hierarchy)
        assert(hierarchy.empty() is False)

        hierarchy.export("test_non_empty_hierarchy.json")
        new_hierarchy = KamiHierarchy.load("test_non_empty_hierarchy.json")
        assert(isinstance(new_hierarchy, KamiHierarchy))
        assert(("action_graph", "kami") in new_hierarchy.edges())
        assert(new_hierarchy == hierarchy)
