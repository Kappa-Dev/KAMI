"""Tests related to KamiHierarchy data structure."""
from kami.data_structures.kami_hierarchy import KamiHierarchy


class TestKamiHierarchy(object):
    """."""

    def test_empty_component_getters(self):
        """Test getters for various hierarchy components."""
        hierarchy = KamiHierarchy()
        assert(len(hierarchy.action_graph.nodes()) == 0)
        assert(len(hierarchy.nuggets()) == 0)
        assert(hierarchy.empty())

        json_hierarchy = hierarchy.to_json()
        new_hierarchy = KamiHierarchy.from_json(json_hierarchy)
        assert(isinstance(new_hierarchy, KamiHierarchy))
