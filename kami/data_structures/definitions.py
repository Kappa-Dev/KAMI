"""Collection of data structures for protein products/families definitions."""
import copy
from regraph import Rule, get_node

from kami.aggregation.generators import Generator, KamiGraph
from kami.aggregation.identifiers import EntityIdentifier


class Definition:
    """."""

    def _valid(self):
        """Validate product definition.

        Checks consistency of input protein definition
        against protoform definition.
        """
        # Normalize product_components
        for product in self.product_names:
            if product not in self.product_components.keys():
                self.product_components[product] = dict()

        for v in self.product_components.values():
            if "regions" not in v.keys():
                v["regions"] = []
            if "sites" not in v.keys():
                v["sites"] = []
            if "residues" not in v.keys():
                v["residues"] = []
            if "states" not in v.keys():
                v["states"] = []

        # Check consistency
        for product, component_dict in self.product_components.items():
            for name, components in component_dict.items():
                try:
                    protoform_components = getattr(self.protoform, name)
                    for component in components:
                        found_in_protoform = False
                        for p_component in protoform_components:
                            if component.issubset(p_component):
                                found_in_protoform = True
                                break
                        if not found_in_protoform:
                            return False
                except Exception as e:
                    return False

        return True

    def __init__(self, protoform, product_names, product_components):
        """Initialize protein definition object."""
        self.protoform = protoform
        self.product_names = product_names
        self.product_components = product_components

        if not self._valid():
            raise ValueError()

    def generate_rule(self):
        """Generate a rewriting rule for instantiation."""
        generator = Generator()
        # Initialize KamiGraph container for protoform
        protoform_graph = KamiGraph()
        generator.generate_gene(
            protoform_graph, self.protoform)
        # Set protoform graph as a reference graph of
        # our generator
        generator.entity_identifier = EntityIdentifier(
            protoform_graph.graph, protoform_graph.meta_typing,
            immediate=False)

        products_graph = KamiGraph()

        for product in self.product_names:
            # Create a Gene object for every product
            new_gene = copy.deepcopy(self.protoform)
            new_gene.regions = self.product_components[product]["regions"]
            new_gene.sites = self.product_components[product]["sites"]
            new_gene.residues = self.product_components[product]["residues"]
            new_gene.states = self.product_components[product]["states"]

            generator.generate_gene(
                products_graph,
                new_gene)

        rule = Rule(
            p=products_graph.graph,
            lhs=protoform_graph.graph,
            rhs=products_graph.graph,
            p_lhs=products_graph.reference_typing)
        return rule


class Family:
    """."""

    def __init__(self):
        pass
