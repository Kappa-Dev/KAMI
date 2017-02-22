"""nose tests for the mu_graph_hierarchy"""

from nose.tools import assert_equals
from mu_graph_hierarchy import MuHierarchy


class TestMuHierarchy(object):
    """verification of formulae from parent graphs"""
    def __init__(self):
        self.hie = MuHierarchy("/", None)
        hie = self.hie
        hie.graph = None
        hie.new_graph("g1")
        self.hie1 = hie.subCmds["g1"]
        hie1 = self.hie1
        hie1.add_node("agent", None)
        hie1.add_node("region", None)
        hie1.add_edge("region", "agent")
        hie1.graph.graph_attr["formulae"] = \
            ["or(not cnt(Region),<1<=Adj>cnt(Agent))"]
        hie1.new_graph("g2")
        self.hie2 = hie1.subCmds["g2"]
        hie2 = self.hie2
        hie2.add_node("a1", "agent")
        hie2.add_node("r1", "region")
        hie2.add_node("r2", "region")
        hie2.add_edge("r1", "a1")

    def test1(self):
        """r2 does not verify the formula"""
        assert_equals(self.hie2.check(),
                      {'g1':
                       {'or(not cnt(Region),<1<=Adj>cnt(Agent))': "['r2']"}})

    def test2(self):
        """after adding an edge all the node are valid"""
        self.hie2.add_edge("r2", "a1")
        assert_equals(self.hie2.check(),
                      {'g1': {'or(not cnt(Region),<1<=Adj>cnt(Agent))': "[]"}})

