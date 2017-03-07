from math import sqrt

import kami_to_metakappa
from regraph.library.graph_hierarchy import Hierarchy


class KamiHierarchy(Hierarchy):
    """ extends the Hierarchy class with kami specific functionality"""

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def to_kappa_like(self, *args):
        """ convert a hierarchy typed by kami
        to a hierarchy typed by the kappa metamodel"""
        return kami_to_metakappa.to_kappa_like(self, *args)

    def link_states(self, *args):
        """automatically complete nuggets when possible """
        return kami_to_metakappa.link_states(self, *args)

    # precondition : the graph must be an action graph
    def link_components(self, comp1, comp2):
        """ link two componenst together with brk, bnd"""
        bnd_name = self.unique_node_id("bnd")
        self.graph.add_node(bnd_name, "bnd")
        brk_name = self.unique_node_id("brk")
        self.graph.add_node(brk_name, "brk")
        loc1 = self.unique_node_id("loc")
        self.graph.add_node(loc1, "locus")
        loc2 = self.unique_node_id("loc")
        self.graph.add_node(loc2, "locus")
        self.graph.add_edge(loc1, comp1)
        self.graph.add_edge(loc1, bnd_name)
        self.graph.add_edge(loc1, brk_name)
        self.graph.add_edge(loc2, comp2)
        self.graph.add_edge(loc2, bnd_name)
        self.graph.add_edge(loc2, brk_name)
        if "positions" in self.graph.graph_attr.keys():
            positions = self.graph.graph_attr["positions"]
            if comp1 in positions.keys():
                xpos1 = positions[comp1].get("x", 0)
                ypos1 = positions[comp1].get("y", 0)
            else:
                (xpos1, ypos1) = (0, 0)
            if comp2 in positions.keys():
                xpos2 = positions[comp2].get("x", 0)
                ypos2 = positions[comp2].get("y", 0)
            else:
                (xpos2, ypos2) = (0, 0)
            difx = xpos2 - xpos1
            dify = ypos2 - ypos1
            if (difx, dify) != (0, 0):
                distance = sqrt(difx*difx + dify*dify)
                vect = (difx/distance, dify/distance)
                positions[loc1] = {"x": xpos1+vect[0]*distance/3,
                                   "y": ypos1+vect[1]*distance/3}
                positions[loc2] = {"x": xpos1+vect[0]*distance/3*2,
                                   "y": ypos1+vect[1]*distance/3*2}
                positions[bnd_name] = {"x": (xpos1+vect[0]*distance/2 +
                                             vect[1]*60),
                                       "y": (ypos1+vect[1]*distance/2 -
                                             vect[0]*60)}
                positions[brk_name] = {"x": (xpos1+vect[0]*distance/2 -
                                             vect[1]*60),
                                       "y": (ypos1+vect[1]*distance/2 +
                                             vect[0]*60)}

   
