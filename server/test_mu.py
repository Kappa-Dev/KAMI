"""nose tests for the mu module"""

from nose.tools import assert_equals
from regraph.library.data_structures import TypedDiGraph
from mu import parse_formula


def check_type(graph, type_name):
    """ returns a function that test if a node has type type_name"""
    def _aux(node):
        return graph.node[node].type_ == type_name
    return _aux


class TestFormula(object):
    """ testing mu calculus evaluation """

    def __init__(self):
        self.graph_ = TypedDiGraph()
        self.graph_.add_node('1', 'Agent')
        self.graph_.add_node('2', 'Region')
        self.graph_.add_node('3', 'Region')

        edges = [
            ('2', '1'),
            ('3', '1')
        ]

        self.graph_.add_edges_from(edges)

        self.formula1 = parse_formula("or(not cnt(Region),<1<=Adj>cnt(Agent))")
        self.constants = {type_name: check_type(self.graph_, type_name)
                          for type_name in ["Agent", "Region"]}
        self.relations = {"Adj": self.graph_.__getitem__}

    def test_evaluation(self):
        rep = self.formula1.evaluate(self.graph_.nodes(), self.relations,
                                     self.constants)
        assert_equals(rep, {'1': True, '2': True, '3': True})

    def test_evaluation2(self):
        self.graph_.add_node('4', 'Region')
        rep = self.formula1.evaluate(self.graph_.nodes(), self.relations,
                                     self.constants)
        assert_equals(rep, {'1': True, '2': True, '3': True, '4': False})

    def test_evaluation3(self):
        self.graph_.add_node('4', 'Region')
        self.graph_.add_edge('4', '1')
        rep = self.formula1.evaluate(self.graph_.nodes(), self.relations,
                                     self.constants)
        assert_equals(rep, {'1': True, '2': True, '3': True, '4': True})
