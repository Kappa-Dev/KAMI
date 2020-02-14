"""A set of utils for Kappa generation."""
import datetime

import json
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

    def _generate_direct_bnd_sites(self, protoform):
        ref_node = self.agents[protoform]["ref_node"]
        variants = list(self.agents[protoform]["variants"].keys())
        if ref_node is None:
            ref_node = self.agents[protoform]["variants"][
                variants[0]]["ref_node"]
        direct_bnds = self.identifier.successors_of_type(
            ref_node, "bnd")
        for bnd in direct_bnds:
            bnd_name = self._generate_site_name(
                bnd, "site",
                self.agents[protoform]["direct_bnd_sites"].keys())
            partner_nodes = [
                b
                for b in self.identifier.graph.predecessors(bnd)
                if b != ref_node
            ]
            self.agents[protoform]["direct_bnd_sites"][bnd] = (
                bnd_name, partner_nodes)

    def generate_agents(self):
        """Generate Kappa agents."""
        protoforms = self._generate_protoforms()
        self.agents = {}
        for protoform, data in protoforms.items():
            if data["hgnc_symbol"] is not None:
                agent_name = data["hgnc_symbol"]
            else:
                agent_name = protoform

            # Generate agent containter
            self.agents[protoform] = {}
            self.agents[protoform]["agent_name"] = agent_name
            self.agents[protoform]["ref_node"] = data["ref_node"]
            self.agents[protoform]["variants"] = dict()
            self.agents[protoform]["direct_bnd_sites"] = dict()

            for variant_name, variant_node in data["variants"].items():
                self.agents[protoform]["variants"][variant_name] = dict()
                self.agents[protoform]["variants"][variant_name][
                    "ref_node"] = variant_node
                self.agents[protoform]["variants"][variant_name][
                    "stateful_sites"] = dict()
                self.agents[protoform]["variants"][variant_name][
                    "kami_bnd_sites"] = dict()
                self.agents[protoform]["variants"][variant_name][
                    "region_bnd_sites"] = dict()

            # Generate direct binding sites
            self._generate_direct_bnd_sites(protoform)

            # Find stateful sites (a Kappa site per every distinct state)
            self._generate_stateful_sites(protoform)
            # Generate binding through kami sites
            self._generate_kami_bnd_sites(protoform)
            # Generate binding through kami regions
            self._generate_region_bnd_sites(protoform)

        print(json.dumps(self.agents, indent="   "))

    def _generate_mod_rule(self, nugget_identifier, ag_typing, template_rel):
        # Get a MOD node
        mod_node = list(template_rel["mod"])[0]
        # The rule is generated only if the substrate node is not None
        if "substrate" in template_rel.keys():
            substrates = template_rel["substrate"]
            enzymes = []
            if "enzyme" in template_rel.keys():
                enzymes = template_rel["enzyme"]
            if len(enzymes) == 0:
                # We are in the case of anonymous modification
                pass
            else:
                # We are in the case of enzyme induced modification
                pass
            # for substrate in substrates:
            #     ag_substrate = ag_typing[substrate]
            #     ag_substrate_uniprot_id = self.kb.get_uniprot(ag_substrate)

            #     substrate_name, substrate_variant_state = _generate_agent_name(
            #         self.identifier, ag_typing, substrate,
            #         ag_substrate_uniprot_id, agents)

            #     states = nugget_identifier.get_attached_states(
            #         substrate)
            #     target_states = []
            #     for s in states:
            #         if s in template_rel["mod_state"]:
            #             # Get site of a state
            #             ag_state = ag_typing[s]
            #             target_site = agents[
            #                 ag_substrate_uniprot_id]["stateful_sites"][
            #                     ag_state]
            #             # Get state value
            #             mod_attrs = nugget.get_node(mod_node)
            #             target_value = 1 if list(mod_attrs["value"])[0] else 0

            #             target_states.append((s, target_site, target_value))

            #     substrate_states = ",".join(_generate_agent_states(
            #         nugget_identifier, ag_typing, substrate, ag_substrate_uniprot_id, agents,
            #         to_ignore=[s[0] for s in target_states]))

            #     # state_repr = _generate_agent_states(
            #     #     identifier, ag_typing, substrate, ag_substrate_uniprot_id, agents,
            #     #     [s[0] for s in target_states])
            #     # substrate_states = ",".join(state_repr)

            #     if len(enzymes) > 0:
            #         for enzyme in enzymes:
            #             ag_enzyme = ag_typing[enzyme]
            #             ag_enzyme_uniprot_id = self.kb.get_uniprot(ag_enzyme)
            #             enzyme_name, enzyme_variant_state = _generate_agent_name(
            #                 self.identifier, ag_typing, enzyme, ag_enzyme_uniprot_id, agents)
            #             enzyme_states = ",".join(_generate_agent_states(
            #                 nugget_identifier, ag_typing, enzyme, ag_enzyme_uniprot_id, agents))

            #             enzyme_bnd_sites = []
            #             substrate_bnd_sites = []
            #             if "bnd_template" in relations:
            #                 # Add binding
            #                 bnd_rel = self.kb._hierarchy.get_relation(
            #                     "bnd_template", n)

            #                 bnd = list(bnd_rel["bnd"])[0]
            #                 substrate_bnd_sites = _generate_bnd_sites(
            #                     self.identifier, ag_typing, bnd_rel, "left",
            #                     substrate, bnd, ag_substrate_uniprot_id, agents)
            #                 enzyme_bnd_sites = _generate_bnd_sites(
            #                     self.identifier, ag_typing, bnd_rel, "right",
            #                     enzyme, bnd, ag_enzyme_uniprot_id, agents)

            #             substrate_lhs = substrate_name + "("
            #             substrate_rhs = substrate_name + "("
            #             if len(substrate_variant_state) > 0:
            #                 substrate_lhs += substrate_variant_state + ","
            #                 substrate_rhs += substrate_variant_state + ","
            #             if len(substrate_states) > 0:
            #                 substrate_lhs += substrate_states + ","
            #                 substrate_rhs += substrate_states + ","
            #             if len(substrate_bnd_sites) > 0:
            #                 substrate_lhs += ",".join(
            #                     "{}[{}]".format(s, i + 1)
            #                     for i, s in enumerate(substrate_bnd_sites)) + ","
            #                 substrate_rhs += ",".join(
            #                     "{}[{}]".format(s, i + 1)
            #                     for i, s in enumerate(substrate_bnd_sites)) + ","

            #             substrate_lhs += ",".join([s[1] for s in target_states]) + ")"
            #             substrate_rhs += ",".join(
            #                 "{}{{{}}}".format(s[1], s[2])
            #                 for s in target_states) + ")"

            #             enzyme_lhs = enzyme_name + "("
            #             if len(enzyme_variant_state) > 0:
            #                 enzyme_lhs += enzyme_variant_state + ","
            #             if len(enzyme_states) > 0:
            #                 enzyme_lhs += enzyme_states
            #             if len(enzyme_bnd_sites) > 0:
            #                 enzyme_lhs += ",".join(
            #                     "{}[{}]".format(s, i + 1)
            #                     for i, s in enumerate(enzyme_bnd_sites))
            #             enzyme_lhs += ")"

            #             rule = "{}, {} -> {}, {}".format(
            #                 enzyme_lhs, substrate_lhs, enzyme_lhs,
            #                 substrate_rhs)

            #     else:
            #         substrate_lhs = substrate_name + "("
            #         substrate_rhs = substrate_name + "("
            #         if len(substrate_variant_state) > 0:
            #             substrate_lhs += substrate_variant_state + ","
            #             substrate_rhs += substrate_variant_state + ","
            #         if len(substrate_states) > 0:
            #             substrate_lhs += substrate_states + ","
            #             substrate_rhs += substrate_states + ","
            #         substrate_lhs += ",".join([s[1] for s in target_states]) + ")"
            #         substrate_rhs += ",".join(
            #             "{}{{{}}}".format(s[1], s[2])
            #             for s in target_states) + ")"
            #         rule = "{} -> {}".format(
            #             substrate_lhs, substrate_rhs)

            # rate = ""
            # mod_attrs = nugget.get_node(mod_node)
            # if "rate" in mod_attrs:
            #     rate = " @ {}".format(list(mod_attrs["rate"])[0])
            # else:
            #     if self.default_mod_rate is not None:
            #         rate = " @ 'default_mod_rate'"
            rule = None
            rate = None
            return rule, rate

    def _generate_bnd_rule(self, nugget_identifier):
        pass

    def generate_rules(self):
        """Generate Kappa rules."""
        self.rules = {}
        for n in self.kb.nuggets():
            nugget = self.kb.get_nugget(n)
            ag_typing = self.kb.get_nugget_typing(n)
            relations = self.kb._hierarchy.adjacent_relations(n)

            self.rules[n] = {}

            nugget_identifier = EntityIdentifier(
                nugget,
                {
                    k: self.kb.get_action_graph_typing()[v]
                    for k, v in ag_typing.items()},
                immediate=False)
            nugget_desc = ""
            if (self.kb.get_nugget_desc(n)):
                nugget_desc = " //{}".format(self.kb.get_nugget_desc(
                    n).replace("\n", ", "))

            self.rules[n]["desc"] = nugget_desc

            if "mod_template" in relations:
                template_rel = self.kb._hierarchy.get_relation(
                    "mod_template", n)
                # rule, rate = self._generate_mod_rule(
                #     nugget_identifier, ag_typing, template_rel)
                # self.rules[n]["rule"] = rule
                # self.rules[n]["rate"] = rate
            else:
                self._generate_bnd_rule(nugget_identifier)

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

            # if len(agent_data["stateful_sites"]) > 0:
            #     agent_signature.append(",".join([
            #         "{}{{0 1}}".format(v)
            #         for v in agent_data["stateful_sites"].values()]))

            # all_sites = list(agent_data["kami_sites"].values()) +\
            #     list(agent_data["direct_bnd_sites"].values()) +\
            #     list(agent_data["region_bnd_sites"].values())
            # if len(all_sites) > 0:
            #     agent_signature.append(",".join([
            #         "{}".format(v) for v in all_sites]))

            # signatures += "%agent: {}({})".format(
            #     agent_data["agent_name"],
            #     ",".join(agent_signature)) + "\n"

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

    def _generate_stateful_sites(self, protoform):
        variants = self.agents[protoform]["variants"]
        for var_name, var_data in variants.items():
            states = self.identifier.get_attached_states(
                var_data["ref_node"])
            for state in states:
                name = None
                if len(variants) > 1:
                    name = var_name
                self.agents[protoform]["variants"][var_name]["stateful_sites"][
                    self._generate_site_name(
                        state, "",
                        self.agents[
                            protoform]["variants"][var_name][
                                "stateful_sites"].keys(),
                        True, "name", name)
                ] = state

    def _generate_kami_bnd_sites(self, protoform):
        variants = self.agents[protoform]["variants"]

        for variant_name, variant_data in variants.items():
            sites = self.identifier.get_attached_sites(
                variant_data["ref_node"])
            for s in sites:
                site_name = self._generate_site_name(
                    s, "site",
                    self.agents[protoform]["variants"][variant_name][
                        "kami_bnd_sites"].keys(),
                    True, "name",
                    variant_name if len(variants) > 1 else None)

                self.agents[protoform]["variants"][variant_name][
                    "kami_bnd_sites"][site_name] = s

    def _generate_region_bnd_sites(self, protoform):
        for variant_name, variant_data in self.agents[protoform]["variants"].items():
            regions = self.identifier.get_attached_regions(variant_data[
                "ref_node"])
            region_bnd_sites = self.agents[protoform]["variants"][
                variant_name]["region_bnd_sites"]
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
                variants_with_component.append(_normalize_variant_name(
                    variant_name))
        return variants_with_component

    def _generate_stateful_sites(self, protoform):
        ref_node = self.agents[protoform]["ref_node"]
        states = self.identifier.get_attached_states(
            ref_node)
        for state in states:
            if len(self.agents[protoform]["variants"]) > 1:
                # We have multiple variants of the protoform,
                # we need to check if the state node is
                # removed for some of the variants
                rule, instance = self.instantiation_rules[ref_node]
                variants_with_component = self._find_variants_with_component(
                    rule, instance, ref_node,
                    self.agents[protoform]["variants"].keys(),
                    state)
                for variant_name in variants_with_component:
                    self.agents[protoform]["variants"][variant_name][
                        "stateful_sites"][
                        self._generate_site_name(
                            state, "", self.agents[protoform]["variants"][
                                variant_name]["stateful_sites"].keys(),
                            True, "name", variant_name)
                    ] = state
            else:
                # We have only one variant of the protoform
                unique_variant = list(
                    self.agents[protoform]["variants"].keys())[0]
                self.agents[protoform]["variants"][unique_variant][
                    "stateful_sites"][
                    self._generate_site_name(
                        state, "", self.agents[protoform][
                            "variants"][unique_variant][
                            "stateful_sites"].keys(),
                        True, "name")
                ] = state

    def _generate_kami_bnd_sites(self, protoform):
        ref_node = self.agents[protoform]["ref_node"]
        sites = self.identifier.get_attached_sites(ref_node)
        if len(self.agents[protoform]["variants"]) > 1:
            rule, instance = self.instantiation_rules[ref_node]
            for s in sites:
                variants_with_component = self._find_variants_with_component(
                    rule, instance, ref_node,
                    self.agents[protoform]["variants"].keys(), s)
                for variant_name in variants_with_component:
                    print(self.agents[protoform][
                        "variants"].keys())
                    kami_bnd_sites = self.agents[protoform][
                        "variants"][variant_name]["kami_bnd_sites"]
                    site_name = self._generate_site_name(
                        s, "site", kami_bnd_sites.keys(),
                        True, "name", variant_name)
                    kami_bnd_sites[site_name] = s
        else:
            unique_variant = list(
                self.agents[protoform]["variants"].keys())[0]
            kami_bnd_sites = self.agents[protoform][
                "variants"][unique_variant]["kami_bnd_sites"]
            for s in sites:
                site_name = self._generate_site_name(
                    s, "site", kami_bnd_sites.keys(),
                    True, "name")
                kami_bnd_sites[site_name] = s

    def _generate_region_bnd_sites(self, protoform):
        ref_node = self.agents[protoform]["ref_node"]
        regions = self.identifier.get_attached_regions(ref_node)
        if len(self.agents[protoform]["variants"]) > 1:
            rule, instance = self.instantiation_rules[ref_node]
            for r in regions:
                variants_with_component = self._find_variants_with_component(
                    rule, instance, ref_node,
                    self.agents[protoform]["variants"].keys(), r)
                for variant_name in variants_with_component:
                    region_bnd_sites = self.agents[protoform]["variants"][
                        variant_name]["region_bnd_sites"]

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
            unique_variant = list(
                self.agents[protoform]["variants"].keys())[0]
            region_bnd_sites = self.agents[protoform]["variants"][
                unique_variant]["region_bnd_sites"]
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

    def _generate_mod_rule(self, nugget_identifier, ag_typing, template_rel):
        # Get a MOD node
        mod_node = list(template_rel["mod"])[0]
        # The rule is generated only if the substrate node is not None
        if "substrate" in template_rel.keys():
            substrates = template_rel["substrate"]

            for substrate in substrates:
                ag_substrate = ag_typing[substrate]
                ag_substrate_uniprot = self.kb.get_uniprot(ag_substrate)
                modified_states = template_rel["mod_state"]
                # rule, instance = self.instantiation_rules[
                #     ag_substrate_uniprot]

                # for modified_state in modified_states:
                #     ag_state = ag_typing[modified_state]

                    # variants_with_component = self._find_variants_with_component(
                    #     rule, instance,
                    #     self.agents[ag_substrate_uniprot]["ref_node"],
                    #     self.agents[ag_substrate_uniprot]["variants"], ag_state)

                    # target_kappa_site = keys_by_value(
                    #     self.agents[ag_substrate_uniprot]["stateful_sites"],
                    #     ag_state)

            # Generate enzyme
            enzymes = []
            if "enzyme" in template_rel.keys() and\
                    len(template_rel["enzyme"]) > 0:
                enzymes = template_rel["enzyme"]
                # We are in the case of enzyme induced modification
                pass
            else:
                # We are in the case of anonymous modification
                pass
