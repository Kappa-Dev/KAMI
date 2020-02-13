"""A set of utils for Kappa generation."""
import datetime
from abc import ABC, abstractmethod
from regraph.utils import keys_by_value

from kami.aggregation.identifiers import EntityIdentifier
from kami.utils.id_generators import generate_new_element_id


class KappaInitialCondition(object):
    """Class for representing initial conditions."""

    def __init__(self, canonical_protein=None,
                 canonical_count=None,
                 stateful_components=None,
                 bounds=None):
        """Initialize an initial condition."""
        self.canonical_protein = canonical_protein
        self.canonical_count = canonical_count
        if stateful_components is None:
            stateful_components = []
        self.stateful_components = stateful_components
        if bounds is None:
            bounds = []
        self.bounds = bounds


def _normalize_variant_name(name):
    return name.replace(" ", "_").replace(
        ",", "_").replace("/", "_").replace("-", "_")


class KappaGenerator(ABC):
    """Abstract Kappa generator."""

    @abstractmethod
    def _generate_protoforms(self):
        """Generate protoforms from the knowledge base."""
        pass

    @abstractmethod
    def _generate_stateful_sites(self, ref_node, variants):
        pass

    @abstractmethod
    def _generate_kami_bnd_sites(self, ref_node, variants):
        pass

    @abstractmethod
    def _generate_region_bnd_sites(self, ref_node, variants):
        pass

    def _generate_site_name(self, component_node, component_type,
                            existing_elements=None,
                            name_from_attrs=False, attrs_key="name",
                            variant_name=None):
        # Generate prefix with variant name
        prefix = ""
        if variant_name is not None:
            prefix = (
                variant_name.replace(
                    " ", "_").replace(",", "_").replace("/", "_").replace(
                        "-", "_") + "_"
            )

        component_name = ""
        if name_from_attrs:
            component_attrs = self.identifier.graph.get_node(
                component_node)
            if attrs_key in component_attrs:
                component_name = list(component_attrs[attrs_key])[0].replace(
                    " ", "_").replace(",", "_").replace("/", "_")

        site_name = "{}".format(component_type)
        if component_name:
            site_name = "{}_{}".format(component_name, site_name)
        site_name = prefix + site_name
        site_name = generate_new_element_id(
            existing_elements, site_name)
        return site_name

    def _generate_direct_bnd_sites(self, ref_node, variants):
        direct_bnd_sites = dict()
        if ref_node is None:
            ref_node = list(variants.values())[0]
        direct_bnds = self.identifier.successors_of_type(
            ref_node, "bnd")
        for bnd in direct_bnds:
            bnd_name = self._generate_site_name(
                bnd, "site", direct_bnd_sites.keys())
            partner_nodes = [
                b
                for b in self.identifier.graph.predecessors(bnd)
                if b != ref_node
            ]
            direct_bnd_sites[bnd] = (bnd_name, partner_nodes)
        return direct_bnd_sites

    def generate_agents(self):
        """Generate Kappa agents."""
        protoforms = self._generate_protoforms()
        self.agents = {}
        for protoform, data in protoforms.items():
            if data["hgnc_symbol"] is not None:
                agent_name = data["hgnc_symbol"]
            else:
                agent_name = protoform
            self.agents[protoform] = {}
            self.agents[protoform]["agent_name"] = agent_name
            self.agents[protoform]["ref_node"] = data["ref_node"]
            self.agents[protoform]["variants"] = data["variants"]

            # Find stateful sites (a Kappa site per every distinct state)
            stateful_sites = self._generate_stateful_sites(
                self.agents[protoform]["ref_node"],
                self.agents[protoform]["variants"])
            self.agents[protoform]["stateful_sites"] = stateful_sites

            # Generate direct binding sites
            self.agents[protoform][
                "direct_bnd_sites"] = self._generate_direct_bnd_sites(
                    self.agents[protoform]["ref_node"],
                    self.agents[protoform]["variants"])

            # Generate binding through kami sites
            self.agents[protoform][
                "kami_sites"] = self._generate_kami_bnd_sites(
                    self.agents[protoform]["ref_node"],
                    self.agents[protoform]["variants"])
            # Generate binding through kami regions
            self.agents[protoform][
                "region_bnd_sites"] = self._generate_region_bnd_sites(
                    self.agents[protoform]["ref_node"],
                    self.agents[protoform]["variants"])
        print(self.agents)

    def generate_rules(self):
        """Generate Kappa rules."""
        pass

    def generate_initial_conditions(self, concentrations, default_concentation):
        """Generate Kappa initial conditions."""
        pass

    def generate(self, concentrations=None, default_concentation=100):
        """Generate a Kappa script."""
        self.generate_agents()
        self.generate_rules()

        if concentrations is None:
            concentrations = []

        self.generate_initial_conditions(concentrations, default_concentation)

        header = "// Automatically generated from the KAMI {} '{}' {}\n\n".format(
            self.kb_type, self.kb._id,
            datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

        signatures = "// Signatures\n\n"
        for agent_uniprot, agent_data in self.agents.items():
            agent_signature = []
            if len(agent_data["variants"]) > 1:
                agent_signature.append("variant{{{}}}".format(
                    " ".join(v for v in agent_data["variants"].keys())))

            if len(agent_data["stateful_sites"]) > 0:
                agent_signature.append(",".join([
                    "{}{{0 1}}".format(v)
                    for v in agent_data["stateful_sites"].values()]))

            all_sites = list(agent_data["kami_sites"].values()) +\
                list(agent_data["direct_bnd_sites"].values()) +\
                list(agent_data["region_bnd_sites"].values())
            if len(all_sites) > 0:
                agent_signature.append(",".join([
                    "{}".format(v) for v in all_sites]))

            signatures += "%agent: {}({})".format(
                agent_data["agent_name"],
                ",".join(agent_signature)) + "\n"

        rule_repr = "\n// Rules \n\n"

        # for i, r in enumerate(self.rules):
        #     rule_repr += "'rule {}' {}\n\n".format(
        #         i + 1, r)

        variables = ""
        # if (self.default_bnd_rate or self.default_brk_rate or self.default_mod_rate):
        #     variables = "\n// variables \n\n"

        # if self.default_bnd_rate:
        #     variables += "%var: 'default_bnd_rate' {}\n".format(
        #         self.default_bnd_rate)
        # if self.default_brk_rate:
        #     variables += "%var: 'default_brk_rate' {}\n".format(
        #         self.default_brk_rate)
        # if self.default_mod_rate:
        #     variables += "%var: 'default_mod_rate' {}\n".format(
        #         self.default_mod_rate)
        init_str = ""
        # init_str = "\n".join(self.initial_conditions)

        return header + signatures + rule_repr + variables + init_str


class ModelKappaGenerator(KappaGenerator):
    """Kappa generator from KAMI models."""

    def _generate_protoforms(self):
        """Generate protoforms from the model."""
        protoforms = {}
        for protein in self.kb.proteins():
            uniprot_id = self.kb.get_uniprot(protein)
            variant_name = self.kb.get_variant_name(protein)
            hgnc_symbol = self.kb.get_hgnc_symbol(protein)
            if uniprot_id in protoforms.keys():
                protoforms[uniprot_id]["hgnc_symbol"] = hgnc_symbol
                if variant_name is None:
                    variant_name = "variant_{}".format(
                        len(protoforms[uniprot_id]["variants"]) + 1)
                protoforms[uniprot_id]["variants"][
                    _normalize_variant_name(variant_name)] = protein
            else:
                protoforms[uniprot_id] = dict()
                protoforms[uniprot_id]["ref_node"] = None
                protoforms[uniprot_id]["hgnc_symbol"] = hgnc_symbol
                if variant_name is None:
                    variant_name = "variant_1"
                protoforms[uniprot_id]["variants"] = {
                    _normalize_variant_name(variant_name): protein
                }
        return protoforms

    def _generate_stateful_sites(self, ref_node, variants):
        stateful_sites = dict()
        for var_name, var_node in variants.items():
            states = self.identifier.get_attached_states(var_node)
            for state in states:
                name = None
                if len(variants) > 1:
                    name = var_name
                stateful_sites[
                    self._generate_site_name(
                        state, "",
                        stateful_sites.keys(),
                        True, "name", name)
                ] = state
        return stateful_sites

    def _generate_kami_bnd_sites(self, ref_node, variants):
        kami_bnd_sites = dict()
        for variant_name, variant_node in variants.items():
            sites = self.identifier.get_attached_sites(variant_node)
            for s in sites:
                site_name = self._generate_site_name(
                    s, "site",
                    kami_bnd_sites.keys(),
                    True, "name",
                    variant_name if len(variants) > 1 else None)

                kami_bnd_sites[site_name] = s
        return kami_bnd_sites

    def _generate_region_bnd_sites(self, ref_node, variants):
        region_bnd_sites = dict()
        for variant_name, variant_node in variants.items():
            regions = self.identifier.get_attached_regions(variant_node)
            for r in regions:
                var_prefix = ""
                if len(variants) > 1:
                    var_prefix = variant_name
                region_name = self._generate_site_name(
                    r, "region",
                    region_bnd_sites.keys(),
                    True, "name", var_prefix)

                for bnd in self.identifier.successors_of_type(r, "bnd"):
                    bnd_name = generate_new_element_id(
                        region_bnd_sites.values(),
                        region_name + "_site")
                    partner_nodes = [
                        b
                        for b in self.identifier.graph.predecessors(bnd)
                        if b != r
                    ]
                    region_bnd_sites[bnd_name] = (
                        r,
                        bnd,
                        partner_nodes
                    )
        return region_bnd_sites

    def __init__(self, model):
        """Initialize a generator."""
        self.kb = model
        self.kb_type = "model"

        # Init default rates
        self.default_bnd_rate = None
        if model.default_bnd_rate is not None:
            self.default_bnd_rate = model.default_bnd_rate
        self.default_brk_rate = None
        if model.default_brk_rate is not None:
            self.default_brk_rate = model.default_brk_rate
        self.default_mod_rate = None
        if model.default_mod_rate is not None:
            self.default_mod_rate = model.default_mod_rate

        # Create an entity identified from the action graph
        self.identifier = EntityIdentifier(
            model.action_graph,
            model.get_action_graph_typing(),
            immediate=False)


class CorpusKappaGenerator(KappaGenerator):
    """Kappa generator from KAMI corpora and definitions."""

    def _generate_protoforms(self):
        """Generate protoforms from the corpus."""
        protoforms = {}
        for protoform in self.kb.protoforms():
            uniprot_id = self.kb.get_uniprot(protoform)
            hgnc_symbol = self.kb.get_hgnc_symbol(protoform)

            protoforms[uniprot_id] = dict()
            protoforms[uniprot_id]["hgnc_symbol"] = hgnc_symbol
            protoforms[uniprot_id]["ref_node"] = protoform
            protoforms[uniprot_id]["variants"] = dict()

            # If the protoform will be instantiated
            if protoform in self.instantiation_rules:
                rule, instance = self.instantiation_rules[protoform]
                lhs_protoform = keys_by_value(instance, protoform)[0]
                p_protoforms = keys_by_value(rule.p_lhs, lhs_protoform)
                # Retrieve variants and their names from the intantiation
                variants = []
                for p_protoform in p_protoforms:
                    rhs_node_attrs = rule.rhs.get_node(
                        rule.p_rhs[p_protoform])
                    variant_name = None
                    if "variant_name" in rhs_node_attrs:
                        variant_name = _normalize_variant_name(
                            list(rhs_node_attrs["variant_name"])[0])
                    variants.append(variant_name)
                i = 1
                for variant in variants:
                    if variant is None:
                        protoforms[uniprot_id]["variants"][
                            "variant_{}".format(i)] = None
                        i += 1
                    else:
                        protoforms[uniprot_id]["variants"][
                            _normalize_variant_name(variant)] = None
            else:
                protoforms[uniprot_id]["variants"]["variant_1"] = protoform
        return protoforms

    def _find_variants_with_component(self, rule, instance,
                                      ref_node, variants, component):
        lhs_ref_node = keys_by_value(instance, ref_node)[0]
        lhs_component = keys_by_value(instance, component)[0]
        p_variant_nodes = keys_by_value(
            rule.p_lhs, lhs_ref_node)

        variants_with_component = []
        for i, p_variant in enumerate(p_variant_nodes):
            state_found = False
            for anc in rule.p.ancestors(p_variant):
                if rule.p_lhs[anc] == lhs_component:
                    state_found = True
                    break
            if state_found:
                variant_attrs = rule.rhs.get_node(
                    rule.p_rhs[p_variant])
                if "variant_name" in variant_attrs:
                    variant_name = list(
                        variant_attrs["variant_name"])[0]
                else:
                    variant_name = list(variants.keys())[0]
                variants_with_component.append(variant_name)
        return variants_with_component

    def _generate_stateful_sites(self, ref_node, variants):
        stateful_sites = dict()
        states = self.identifier.get_attached_states(ref_node)
        for state in states:
            if len(variants) > 1:
                # We have multiple variants of the protoform,
                # we need to check if the state node is
                # removed for some of the variants
                rule, instance = self.instantiation_rules[ref_node]
                variants_with_component = self._find_variants_with_component(
                    rule, instance, ref_node, variants, state)
                for variant_name in variants_with_component:
                    stateful_sites[
                        self._generate_site_name(
                            state, "", stateful_sites.keys(),
                            True, "name", variant_name)
                    ] = state
            else:
                # We have only one variant of the protoform
                stateful_sites[
                    self._generate_site_name(
                        state, "", stateful_sites.keys(),
                        True, "name")
                ] = state
        return stateful_sites

    def _generate_kami_bnd_sites(self, ref_node, variants):
        kami_bnd_sites = dict()
        sites = self.identifier.get_attached_sites(ref_node)
        if len(variants) > 1:
            rule, instance = self.instantiation_rules[ref_node]
            for s in sites:
                variants_with_component = self._find_variants_with_component(
                    rule, instance, ref_node, variants, s)
                for variant_name in variants_with_component:
                    site_name = self._generate_site_name(
                        s, "site", kami_bnd_sites.keys(),
                        True, "name", variant_name)
                    kami_bnd_sites[site_name] = s
        else:
            for s in sites:
                site_name = self._generate_site_name(
                    s, "site", kami_bnd_sites.keys(),
                    True, "name")
                kami_bnd_sites[site_name] = s

        return kami_bnd_sites

    def _generate_region_bnd_sites(self, ref_node, variants):
        region_bnd_sites = dict()
        regions = self.identifier.get_attached_regions(ref_node)
        if len(variants) > 1:
            rule, instance = self.instantiation_rules[ref_node]
            for r in regions:
                variants_with_component = self._find_variants_with_component(
                    rule, instance, ref_node, variants, r)
                for variant_name in variants_with_component:
                    region_name = self._generate_site_name(
                        r, "region", region_bnd_sites.keys(),
                        True, "name", variant_name)
                    for bnd in self.identifier.successors_of_type(r, "bnd"):
                        bnd_name = generate_new_element_id(
                            region_bnd_sites.values(),
                            region_name + "_site")
                        partner_nodes = [
                            b
                            for b in self.identifier.graph.predecessors(bnd)
                            if b != r
                        ]
                        region_bnd_sites[bnd_name] = (
                            r,
                            bnd,
                            partner_nodes
                        )
        else:
            for r in regions:
                region_name = self._generate_site_name(
                    r, "region",
                    region_bnd_sites.keys(),
                    True, "name")

                for bnd in self.identifier.successors_of_type(r, "bnd"):
                    bnd_name = generate_new_element_id(
                        region_bnd_sites.values(),
                        region_name + "_site")
                    partner_nodes = [
                        b
                        for b in self.identifier.graph.predecessors(bnd)
                        if b != r
                    ]
                    region_bnd_sites[bnd_name] = (
                        r,
                        bnd,
                        partner_nodes
                    )
        return region_bnd_sites

    def __init__(self, corpus, definitions,
                 default_bnd_rate=None,
                 default_brk_rate=None, default_mod_rate=None):
        """Initialize a generator."""
        self.kb = corpus
        self.kb_type = "corpus"

        # Init default rates
        self.default_bnd_rate = default_bnd_rate
        self.default_brk_rate = default_brk_rate
        self.default_mod_rate = default_mod_rate

        # Create an entity identified from the action graph
        self.identifier = EntityIdentifier(
            corpus.action_graph,
            corpus.get_action_graph_typing(),
            immediate=False)

        # Generate instantiation rules from definitions
        self.instantiation_rules = dict()
        for i, d in enumerate(definitions):
            # rule, instance = self.instantiation_rules[ref_node]
            protoform = self.identifier.identify_gene(d.protoform)
            instantiation_rule, instance = d.generate_rule(
                corpus.action_graph, corpus.get_action_graph_typing())
            self.instantiation_rules[protoform] = (
                instantiation_rule, instance
            )
