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
        print(new_hierarchy)
        print(hierarchy)
        assert(new_hierarchy == hierarchy)

        assert(hierarchy.action_graph is hierarchy.node["action_graph"].graph)
        assert(hierarchy.action_graph_typing is
               hierarchy.edge["action_graph"]["kami"].mapping)
        assert(hierarchy.mod_template is
               hierarchy.node["mod_template"].graph)
        assert(hierarchy.bnd_template is hierarchy.node["bnd_template"].graph)
        assert(hierarchy.semantic_action_graph is
               hierarchy.node["semantic_action_graph"].graph)
