"""Collection of data structures for instantiated KAMI models."""


class KamiModel(object):
    """Class for instantiated KAMI models.

    Attributes
    ----------
    _backend : str, "networkx" or "neo4j"
    _seed_genes :
    _hierarchy :
    creation_time :
    annotation :
    definitions :
    action_graph :
    nugget :
    mod_template :
    bnd_templae :
    """

    def __init__(self, corpora, definitions,
                 seed_genes=None, annotation=None):
        """Instantiate a model from the input corpus and protein defs."""
        # Copy the hierarchy
