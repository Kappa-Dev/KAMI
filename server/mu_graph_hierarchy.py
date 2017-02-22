"""Hierarchy with mu-calculus verification methods """
from regraph.library.graph_hierarchy import Hierarchy
from lrparsing import ParseError
import mu


def _verify(phi_str, current_typing, graph):
    phi = mu.parse_formula(phi_str)
    const_names = phi.constants()
    constants = {const_name: (lambda n, const_name=const_name:
                              (str(current_typing[n]).lower() ==
                               const_name.lower()))
                 for const_name in const_names}
    relations = {
        "Adj": graph.__getitem__,
        "Suc": graph.successors,
        "Pre": graph.predecessors}

    res = phi.evaluate(graph.nodes(), relations, constants)
    return [n for (n, v) in res.items() if not v]


class MuHierarchy(Hierarchy):
    """ extends the Hierarchy class with mu-calculus
     verification functionalities """

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def check(self):
        """check that a graph verifies the formulae present in its parents"""
        if self.parent is None or self.parent.graph is None:
            return {}
        current_ancestor = self.parent
        current_typing = {n: self.graph.node[n].type_
                          for n in self.graph.nodes()}
        response = {}
        while True:
            if "formulae" in current_ancestor.graph.graph_attr.keys():
                current_rep = {}
                for phi_str in current_ancestor.graph.graph_attr["formulae"]:
                    try:
                        failed_nodes = _verify(phi_str["formula"],
                                               current_typing,
                                               self.graph)
                        current_rep[phi_str["id"]] = str(failed_nodes)
                    except (ValueError, ParseError) as err:
                        current_rep[phi_str["id"]] = str(err)
                response[current_ancestor.name] = current_rep
            if (current_ancestor.parent is None or
                    current_ancestor.parent.graph is None):
                break
            anc_typing = {n: current_ancestor.graph.node[n].type_
                          for n in current_ancestor.graph.nodes()}
            new_typing = {n_id: t3
                          for (n_id, t1) in current_typing.items()
                          for (t2, t3) in anc_typing.items()
                          if t1 == t2}
            current_typing = new_typing
            current_ancestor = current_ancestor.parent
        return response



