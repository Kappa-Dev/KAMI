"""Define here the hierarchy class used by the server"""
# from kami_graph_hierarchy import KamiHierarchy
from regraph.library.hierarchy import MuHierarchy
import networkx as nx


# class ServerHierarchy(KamiHierarchy, MuHierarchy):
#     """hierarchy class with kami and mu-calculus functionalities"""
#     def __init__(self, name, parent):
#         super().__init__(name, parent)

class ServerHierarchy(MuHierarchy):
    """hierarchy class with kami and mu-calculus functionalities"""
    def __init__(self):
        super().__init__()
        self.add_graph("/", nx.DiGraph(), {"name": "/"})
        # self.node["/"].graph = None
