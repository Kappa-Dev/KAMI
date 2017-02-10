from regraph.library.kami_to_metakappa import to_kappa_like, link_states
from regraph.library.graph_hierarchy import Hierarchy


class KamiHierarchy(Hierarchy):
    """ extends the Hierarchy class with kami specific functionality"""

    def __init__(self, name, parent):
        super().__init__(name, parent)
    
    def to_kappa_like(*args):
        return to_kappa_like(*args)

    def link_states(*args):
        return link_states(*args)

