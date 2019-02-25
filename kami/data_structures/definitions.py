"""Collection of data structures for protein products/families definitions."""
import copy
from regraph import Rule, get_node, get_edge
from regraph.utils import keys_by_value

from kami.aggregation.generators import Generator, KamiGraph
from kami.aggregation.identifiers import EntityIdentifier

from kami.utils.id_generators import (generate_new_id)


class Definition:
    """Class for protein product definitions.

    Attributes
    ----------
    protoform : kami.data_structures.entities.Gene
        Original de-contextualised protoform object (including
        all required components that will be subjected to removal
        or cloning)
    product_names : iterable
        Iterable with product names
    product_components : dict
        Dictionary whose keys are product names and whose values
        are dictionaries of components. Dictionaries with components
        are of the form {<component_type>: <collection_of_components>},
        e.g. {"regions": [Region(name="SH2")],
        "residues": [Residue("Y", 100)]}. Represent the components
        that stay preserved after instantiation from the protoform.
    """

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

    def generate_rule(self, reference_graph, meta_typing):
        """Generate a rewriting rule for instantiation."""
        generator = Generator(bookkeeping=True)

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
        product_genes = dict()
        for product in self.product_names:
            # Create a Gene object for every product
            new_gene = copy.deepcopy(self.protoform)
            new_gene.regions = self.product_components[product]["regions"]
            new_gene.sites = self.product_components[product]["sites"]
            new_gene.residues = self.product_components[product]["residues"]
            new_gene.states = self.product_components[product]["states"]

            product_genes[product] = generator.generate_gene(
                products_graph,
                new_gene)

        # Augment LHS with all the incident components and actions
        reference_identifier = EntityIdentifier(
            reference_graph,
            meta_typing)

        instances = reference_identifier.find_matching_in_graph(
            protoform_graph.graph,
            protoform_graph.meta_typing)

        if len(instances) != 1:
            if len(instances) == 0:
                raise ValueError("Smth is wierd, no instances of a def!")
            else:
                raise ValueError("Smth is wierd, too many instances of a def!")

        instance = instances[0]

        protoform_gene = keys_by_value(protoform_graph.meta_typing, "gene")[0]
        protoform_gene_reference = instance[protoform_gene]

        def _add_node_to_rule(node, meta_typing):
            # little helper function for adding a node +
            # incident edges to the instantiation rule
            node_attrs = get_node(reference_graph, node)
            protoform_graph.add_node(
                node, node_attrs,
                meta_typing=meta_typing, reference_typing=node)
            instance[node] = node
            protoform_node = node
            product_nodes = []
            for product, gene in product_genes.items():
                product_node_id = generate_new_id(
                    products_graph.graph, node)
                product_nodes.append(product_node_id)
                products_graph.add_node(
                    product_node_id, node_attrs,
                    meta_typing=meta_typing,
                    reference_typing=node)
            return protoform_node, product_nodes

        def _add_edge_to_rule(s, t, ref_s, ref_t, products_s, products_t):
            # little helper function for adding a node +
            # incident edges to the instantiation rule
            edge_attrs = get_edge(reference_graph, ref_s, ref_t)
            protoform_graph.add_edge(s, t, edge_attrs)
            for i, ps in enumerate(products_s):
                products_graph.add_edge(
                    ps, products_t[i],
                    edge_attrs)

        # Duplicate all the subcomponents not removed in products
        component_types = ["region", "site", "residue", "state"]
        # for component_type in component_types:
        visited = set()
        next_level_to_visit = {
            protoform_gene:
                (
                    protoform_gene_reference,
                    list(product_genes.values()),
                    set([pr for pr in reference_graph.predecessors(protoform_gene_reference)
                         if meta_typing[pr] in component_types])
                )
        }
        while len(next_level_to_visit) > 0:
            new_level_to_visit = dict()
            for father, (father_reference, father_products, preds) in next_level_to_visit.items():
                for p in preds:
                    if p not in visited:
                        if p not in instance.values():
                            # Add component nodes and edges to the rule
                            prot_p_id, prod_p_ids = _add_node_to_rule(p, meta_typing[p])
                            _add_edge_to_rule(
                                prot_p_id,
                                father,
                                p,
                                father_reference,
                                prod_p_ids,
                                father_products)
                            new_level_to_visit[prot_p_id] = (
                                p, prod_p_ids,
                                set([pr for pr in reference_graph.predecessors(p)
                                     if meta_typing[pr] in component_types]))
                        else:
                            new_level_to_visit[keys_by_value(instance, p)[0]] = (
                                p,
                                keys_by_value(products_graph.reference_typing, keys_by_value(instance, p)[0]),
                                set([pr for pr in reference_graph.predecessors(p)
                                    if meta_typing[pr] in component_types]))
                        visited.add(p)
                if meta_typing[father_reference] in ["gene", "region", "site"]:
                    bnds = reference_identifier.successors_of_type(
                        father_reference, "bnd")
                    mods = reference_identifier.successors_of_type(
                        father_reference, "mod")
                    for action in bnds + mods:
                        if action not in visited:
                            prot_action_id, prod_action_ids = _add_node_to_rule(
                                action, meta_typing[action])
                            _add_edge_to_rule(
                                father, prot_action_id,
                                father_reference, action,
                                father_products, prod_action_ids)
                            visited.add(action)

            next_level_to_visit = new_level_to_visit

        states = reference_identifier.ancestors_of_type(protoform_gene_reference, "state")

        rule = Rule(
            p=products_graph.graph,
            lhs=protoform_graph.graph,
            rhs=products_graph.graph,
            p_lhs=products_graph.reference_typing)
        return rule, instance

    def to_json(self):
        """Convert Definition object to JSON dictionary."""
        json_dict = {}
        json_dict["protoform"] = self.protoform.to_json()
        json_dict["product_names"] = self.product_names
        json_dict["product_components"] = dict()
        for product, components in self.product_components.items():
            json_dict["product_components"][product] = {
                name: [el.to_json() for el in elements]
                for name, elements in components.items()
            }
        return json_dict


class Family:
    """."""

    def __init__(self):
        pass
