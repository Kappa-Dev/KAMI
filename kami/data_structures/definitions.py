"""Collection of data structures for protein products/families definitions."""
import copy
import warnings

import regraph.primitives as primitives
from regraph import Rule, get_node, get_edge, set_node_attrs
from regraph.utils import keys_by_value

from kami.aggregation.generators import Generator, KamiGraph
from kami.aggregation.identifiers import EntityIdentifier

from kami.data_structures.entities import Gene, Region, Site, Residue, State
from kami.utils.id_generators import (generate_new_id)


class Product(object):

    def __init__(self, removed_components, residues, name=None, desc=None):
        self.removed_components = {}
        if "regions" in removed_components:
            self.removed_components["regions"] = removed_components["regions"]
        else:
            self.removed_components["regions"] = []
        if "sites" in removed_components:
            self.removed_components["sites"] = removed_components["sites"]
        else:
            self.removed_components["sites"] = []
        if "residues" in removed_components:
            self.removed_components["residues"] = removed_components["residues"]
        else:
            self.removed_components["residues"] = []
        if "states" in removed_components:
            self.removed_components["states"] = removed_components["states"]
        else:
            self.removed_components["states"] = []
        self.residues = residues
        self.name = name
        self.desc = desc

    def generate_graph(self, reference_graph, gene_node):
        """Generate variant graph."""
        graph = KamiGraph(reference_graph.graph, reference_graph.meta_typing)

        entity_identifier = EntityIdentifier(
            reference_graph.graph, reference_graph.meta_typing,
            immediate=False)

        # remove components
        def remove_component(node):
            # Find all the subcomponents and remove them
            components = entity_identifier.subcomponents(node)
            for n in components:
                graph.remove_node(n)

        for region in self.removed_components["regions"]:
            region_node = entity_identifier.identify_region(
                region, gene_node)
            if region_node:
                remove_component(region_node)
            else:
                warnings.warn(
                    "Element was not found in the reference graph!")
        for site in self.removed_components["sites"]:
            site_node = entity_identifier.identify_site(
                site, gene_node)
            if site_node:
                remove_component(site_node)
            else:
                warnings.warn(
                    "Element was not found in the reference graph!")
        for residue in self.removed_components["residues"]:
            residue_node = entity_identifier.identify_residue(
                residue, gene_node)
            if residue_node:
                remove_component(residue_node)
            else:
                warnings.warn(
                    "Element was not found in the reference graph!")
        for state in self.removed_components["states"]:
            state_node = entity_identifier.identify_state(
                state, gene_node)
            if state_node:
                remove_component(state_node)
            else:
                warnings.warn(
                    "Element was not found in the reference graph!")

        return graph

    @classmethod
    def from_json(cls, json_dict, name):
        """Retreive Product from json."""
        removed_components = {}
        if "removed_components" in json_dict:
            if "regions" in json_dict["removed_components"]:
                removed_components["regions"] = []
                for el in json_dict["removed_components"]["regions"]:
                    removed_components["regions"].append(
                        Region.from_json(el))
            if "sites" in json_dict["removed_components"]:
                removed_components["sites"] = []
                for el in json_dict["removed_components"]["sites"]:
                    removed_components["sites"].append(
                        Site.from_json(el))
            if "residues" in json_dict["removed_components"]:
                removed_components["residues"] = []
                for el in json_dict["removed_components"]["residues"]:
                    removed_components["residues"].append(
                        Residue.from_json(el))
            if "states" in json_dict["removed_components"]:
                removed_components["states"] = []
                for el in json_dict["removed_components"]["states"]:
                    removed_components["states"].append(
                        State.from_json(el))
        residues = []
        if "residues" in json_dict:
            for r in json_dict["residues"]:
                residues.append(Residue.from_json(r))

        desc = None
        if "desc" in json_dict:
            desc = json_dict["desc"]
        return cls(removed_components, residues, name, desc)



class NewDefinition:
    """Class for protein product definitions.

    Attributes
    ----------
    gene : kami.data_structures.entities.Gene
        Reference gene object
    products : dict
        Dictionary whose keys are product names and whose values
        are kami.data_structuires.definitions.Product objects
    """

    def __init__(self, gene, products):
        self.gene = gene
        self.products = products

    def _generate_protoform_graph(self, reference_graph, meta_typing):
        protoform_graph = KamiGraph()
        entity_identifier = EntityIdentifier(
            reference_graph, meta_typing,
            immediate=False)
        gene_node = entity_identifier.identify_gene(self.gene)
        if gene_node is not None:
            # Build protoform graph
            subcomponents = entity_identifier.subcomponents(gene_node)
            for c in subcomponents:
                protoform_graph.add_node(
                    c, get_node(reference_graph, c),
                    meta_typing[c])
            for s in subcomponents:
                for t in subcomponents:
                    if primitives.exists_edge(reference_graph, s, t):
                        protoform_graph.add_edge(
                            s, t,
                            get_edge(reference_graph, s, t))
        return protoform_graph, gene_node

    def generate_rule(self, reference_graph, meta_typing):
        protoform_graph, gene_node = self._generate_protoform_graph(
            reference_graph, meta_typing)
        products_graph = KamiGraph()
        p_lhs = {}

        product_genes_nodes = {}
        for i, product in enumerate(self.products):
            # product_name = product.name
            product_graph = product.generate_graph(
                protoform_graph, gene_node)
            # Add copy of generated product graph to P
            for n in product_graph.nodes():
                new_name = "{}{}".format(n, i + 1)
                if protoform_graph.meta_typing[n] == "gene":
                    product_genes_nodes[product.name] = new_name
                products_graph.add_node(
                    new_name,
                    get_node(product_graph.graph, n))
                p_lhs["{}{}".format(n, i + 1)] = n
            for s, t in product_graph.edges():
                products_graph.add_edge(
                    "{}{}".format(s, i + 1),
                    "{}{}".format(t, i + 1),
                    get_edge(product_graph.graph, s, t))
        rule = Rule(
            p=products_graph.graph,
            lhs=protoform_graph.graph,
            rhs=products_graph.graph,
            p_lhs=p_lhs)

        for product in self.products:
            rule.inject_add_node_attrs(
                product_genes_nodes[product.name],
                {
                    "variant_name": product.name,
                    "variant_desc": product.desc
                })

        return rule, {n: n for n in protoform_graph.nodes()}

    @classmethod
    def from_json(cls, json_dict):
        """Retreive def from json."""
        products = []
        for name, val in json_dict["products"].items():
            products.append(Product.from_json(val, name=name))
        return cls(Gene(json_dict["protoform"]), products)



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
        for name, data in self.products.items():
            if "regions" not in data["components"].keys():
                data["components"]["regions"] = []
            if "sites" not in data["components"].keys():
                data["components"]["sites"] = []
            if "residues" not in data["components"].keys():
                data["components"]["residues"] = []
            if "states" not in data["components"].keys():
                data["components"]["states"] = []

        # Check consistency
        for product_name, data in self.products.items():
            for name, components in data["components"].items():
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
                    print(e)
                    return False

        return True

    def __init__(self, protoform, products):
        """Initialize protein definition object."""
        self.protoform = protoform
        self.products = products

        if not self._valid():
            raise ValueError()

    def _generate_graphs(self, reference_graph, meta_typing,
                         single_product_graph=False):
        # Initialize KamiGraph container for protoform
        generator = Generator(bookkeeping=True)

        protoform_graph = KamiGraph()
        generator.generate_gene(
            protoform_graph, self.protoform)

        # Set protoform graph as a reference graph of
        # our generator
        generator.entity_identifier = EntityIdentifier(
            protoform_graph.graph, protoform_graph.meta_typing,
            immediate=False)

        product_graphs = {}
        if single_product_graph:
            product_graphs["single"] = KamiGraph()

        product_genes = dict()
        for product, data in self.products.items():
            # Create a Gene object for every product
            new_gene = copy.deepcopy(self.protoform)
            new_gene.regions = data["components"]["regions"]
            new_gene.sites = data["components"]["sites"]
            new_gene.residues = data["components"]["residues"]
            new_gene.states = data["components"]["states"]

            if single_product_graph:
                product_genes[product] = generator.generate_gene(
                    product_graphs["single"],
                    new_gene)
            else:
                graph = KamiGraph()
                product_genes[product] = generator.generate_gene(
                    graph,
                    new_gene)
                product_graphs[product] = graph
                set_node_attrs(
                    graph.graph,
                    product_genes[product],
                    {
                        "variant_name": product,
                        "variant_desc": data["desc"]
                    },
                    update=False)

        return protoform_graph, product_genes, product_graphs

    def generate_rule(self, reference_graph, meta_typing):
        """Generate a rewriting rule for instantiation."""
        protoform_graph, product_genes, product_graphs = self._generate_graphs(
            reference_graph, meta_typing, single_product_graph=True)

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
                print([str(protoform_graph.graph.node[n]) for n in protoform_graph.graph.nodes()])
            else:
                raise ValueError("Smth is wierd, too many instances of a def!")

        instance = instances[0]
        protoform_gene = keys_by_value(protoform_graph.meta_typing, "gene")[0]
        protoform_gene_reference = instance[protoform_gene]

        products_graph = product_graphs["single"]
        p_lhs = products_graph.reference_typing

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
                p_lhs[product_node_id] = node
            return protoform_node, product_nodes

        def _add_edge_to_rule(s, t, ref_s, ref_t, products_s, products_t):
            # little helper function for adding a node +
            # incident edges to the instantiation rule
            edge_attrs = get_edge(reference_graph, ref_s, ref_t)
            if (s, t) not in protoform_graph.edges():
                protoform_graph.add_edge(s, t, edge_attrs)
            for i, ps in enumerate(products_s):
                if len(products_s) == len(products_t):
                    if (ps, products_t[i]) not in products_graph.edges():
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
                            new_father = keys_by_value(instance, p)[0]
                            new_level_to_visit[new_father] = (
                                p,
                                keys_by_value(products_graph.reference_typing, new_father),
                                set([pr for pr in reference_graph.predecessors(p)
                                    if meta_typing[pr] in component_types]))
                        visited.add(p)

                    for s in reference_graph.successors(p):
                        if s in instance.values():
                            prot_p_id = keys_by_value(instance, p)[0]
                            prod_p_ids = keys_by_value(p_lhs, p)
                            _add_edge_to_rule(
                                prot_p_id,
                                keys_by_value(instance, s)[0],
                                p,
                                s,
                                prod_p_ids,
                                keys_by_value(p_lhs, keys_by_value(instance, s)[0]))

            next_level_to_visit = new_level_to_visit

        states = reference_identifier.ancestors_of_type(protoform_gene_reference, "state")

        rule = Rule(
            p=products_graph.graph,
            lhs=protoform_graph.graph,
            rhs=products_graph.graph,
            p_lhs=p_lhs)
        for g, n_id in product_genes.items():
            rule.inject_add_node_attrs(
                n_id,
                {
                    "variant_name": g,
                    "variant_desc": self.products[g]["desc"]
                })
        return rule, instance

    def to_json(self):
        """Convert Definition object to JSON dictionary."""
        json_dict = {}
        json_dict["protoform"] = self.protoform.to_json()
        json_dict["products"] = dict()
        for product, data in self.products.items():
            json_dict["products"][product] = {
                "components": {
                    name: [el.to_json() for el in elements]
                    for name, elements in data["components"].items()
                },
                "desc": data["desc"]
            }
        return json_dict

    @classmethod
    def from_json(cls, json_data):
        """Create a Definition object from JSON representation."""
        protoform = Gene.from_json(json_data["protoform"])
        products = {}
        # product_names = json_data["product_names"]
        # product_components = {}
        for product_name, data in json_data["products"].items():
            products[product_name] = {
                "components": {},
                "desc": data["desc"]
            }
            if "regions" in data["components"].keys():
                products[product_name]["components"]["regions"] = []
                for r in data["components"]["regions"]:
                    products[product_name]["components"]["regions"].append(
                        Region.from_json(r))
            if "sites" in data["components"].keys():
                products[product_name]["components"]["sites"] = []
                for r in data["components"]["sites"]:
                    products[product_name]["components"]["sites"].append(
                        Site.from_json(r))
            if "residues" in data["components"].keys():
                products[product_name]["components"]["residues"] = []
                for r in data["components"]["residues"]:
                    products[product_name]["components"]["residues"].append(
                        Residue.from_json(r))
            if "states" in data["components"].keys():
                products[product_name]["components"]["states"] = []
                for r in data["components"]["states"]:
                    products[product_name]["components"]["states"].append(
                        State.from_json(r))
        return cls(protoform, products)
