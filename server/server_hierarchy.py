"""Define here the hierarchy class used by the server"""
from kami_graph_hierarchy import KamiHierarchy
from mu_graph_hierarchy import MuHierarchy


class ServerHierarchy(KamiHierarchy, MuHierarchy):
    """hierarchy class with kami and mu-calculus functionalities"""
    def __init__(self, name, parent):
        super().__init__(name, parent)
