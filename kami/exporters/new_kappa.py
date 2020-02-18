"""A set of utils for Kappa generation."""
import datetime
import json
import warnings

from abc import ABC, abstractmethod
from regraph.utils import keys_by_value

from kami.aggregation.identifiers import EntityIdentifier
from kami.data_structures.entities import State, Residue, Region, Site, Protein, RegionActor, SiteActor
from kami.utils.id_generators import generate_new_element_id
from kami.exceptions import KappaGenerationWarning


class KappaInitialCondition(object):
    """Class for representing initial conditions."""

    def __init__(self, canonical_protein=None,
                 canonical_count=None,
                 stateful_components=None,
                 bonds=None):
        """Initialize an initial condition."""
        self.canonical_protein = canonical_protein
        self.canonical_count = canonical_count
        if stateful_components is None:
            stateful_components = []
        self.stateful_components = stateful_components
        if bonds is None:
            bonds = []
        self.bonds = bonds


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

    @abstractmethod
    def _generate_mod_rules(self, nugget_identifier, ag_typing, template_rel,
                            bnd_relation=None):
        pass

    @abstractmethod
    def _generate_bnd_rules(self, nugget_identifier, ag_typing, template_rel):
        pass

    def _get_agent_name(self, ag_node, uniprotid):
        # Find agent name
        agent_name = self.agents[uniprotid]["agent_name"]
        # Find agent variant
        variant_name = self._get_variant_name(ag_node, uniprotid)
        return agent_name, variant_name

    def _generate_bnds_and_partners(self, component):
        partner_nodes = dict()
        for bnd in self.identifier.successors_of_type(component, "bnd"):
            nodes = [
                b
                for b in self.identifier.graph.predecessors(bnd)
                if b != component
            ]
            partner_nodes[bnd] = nodes
        return partner_nodes

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
            sep = ""
            if len(site_name) > 0:
                sep = "_"
            site_name = "{}{}{}".format(component_name, sep, site_name)
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
                [v[0]
                 for v in self.agents[protoform]["direct_bnd_sites"].values()])
            partner_nodes = [
                b
                for b in self.identifier.graph.predecessors(bnd)
                if b != ref_node
            ]
            self.agents[protoform]["direct_bnd_sites"][bnd] =\
                (bnd_name, partner_nodes)

    def _generate_agent_state_strs(self, nugget_identifier, ag_typing, agent,
                                   ag_uniprot_id, variant=None, to_ignore=None):
        """Generate string representation of states"""
        if to_ignore is None:
            to_ignore = []
        # Find agent states
        state_repr = []
        states = nugget_identifier.get_attached_states(agent)
        for s in states:
            if s not in to_ignore:
                # get state value (True always renders to 1, False to 0)
                state_attrs = nugget_identifier.graph.get_node(s)
                value = "on" if list(state_attrs["test"])[0] else "off"
                ag_state = ag_typing[s]
                if variant and (ag_state in self.agents[
                        ag_uniprot_id]["variants"][
                            variant]["stateful_sites"]):
                    state_repr.append(
                        self.agents[
                            ag_uniprot_id]["variants"][
                                variant]["stateful_sites"][
                                    ag_state] + "{{{}}}".format(value))
                else:
                    state_repr.append(
                        self.agents[
                            ag_uniprot_id]["generic_stateful_sites"][
                                ag_state] + "{{{}}}".format(value))
        # agent_states = ",".join(state_repr)
        return state_repr

    def _generate_bond_strs(self, nugget_identifier, ag_typing, template_rel,
                            role, agent, bnd, uniprotid, variant=None):
        """Generate string representation of bnd sites"""
        ag_bnd = ag_typing[bnd]
        agent_bnd_sites = []
        if role + "_partner_site" in template_rel and\
           len(template_rel[role + "_partner_site"]) > 0:
            sites = nugget_identifier.get_attached_sites(agent)
            for s in sites:
                if s in template_rel[role + "_partner_site"]:
                    ag_site = ag_typing[s]
                    if variant and (ag_site, ag_bnd) in self.agents[uniprotid]["variants"][
                            variant]["kami_bnd_sites"]:
                        agent_bnd_sites.append(
                            self.agents[uniprotid]["variants"][
                                variant]["kami_bnd_sites"][(ag_site, ag_bnd)][0])
                    else:
                        agent_bnd_sites.append(
                            self.agents[uniprotid]["generic_kami_bnd_sites"][
                                (ag_site, ag_bnd)][0])
        elif role + "_partner_region" in template_rel and\
                len(template_rel[role + "_partner_region"]) != 0:
            regions = nugget_identifier.get_attached_regions(agent)
            for r in regions:
                if r in template_rel[role + "_partner_region"]:
                    ag_region = ag_typing[r]
                    if variant and (ag_region, ag_bnd) in self.agents[uniprotid][
                            "variants"][variant]["region_bnd_sites"]:
                        agent_bnd_sites.append(self.agents[uniprotid][
                            "variants"][variant]["region_bnd_sites"][
                                (ag_region, ag_bnd)][0])
                    else:
                        agent_bnd_sites.append(self.agents[uniprotid][
                            "generic_region_bnd_sites"][(ag_region, ag_bnd)][0])
        else:
            agent_bnd_sites.append(
                self.agents[uniprotid][
                    "direct_bnd_sites"][ag_bnd][0])
        return agent_bnd_sites

    def _generate_mod_agent_lhs_rhs(self, uniprotid, agent_name, variant,
                                    states, bnd_sites, target_states=None):
        if target_states is None:
            target_states = []
        if len(self.agents[uniprotid]["variants"]) > 1:
            signature = ["variant{{{}}}".format(variant)]
        else:
            signature = []
        if len(states) > 0:
            signature.append(states)

        if len(bnd_sites) > 0:
            signature += [
                "{}[{}]".format(s, i + 1)
                for i, s in enumerate(bnd_sites)]

        agent_lhs = "{}({})".format(
            agent_name,
            ", ".join(signature + [
                "{}{{{}}}".format(s[1], "off" if s[2] else "on") for s in target_states]))
        agent_rhs = "{}({})".format(
            agent_name,
            ", ".join(signature) +
            (", " if len(signature) > 0 and len(target_states) > 0 else "") +
            ",".join(
                "{}{{{}}}".format(s[1], s[2])
                for s in target_states))
        return agent_lhs, agent_rhs

    def _generate_bnd_partner_str(self, nugget_identifier, ag_typing,
                                  template_rel, role, agent, bnd, uniprotid,
                                  bnd_flag=True, variant=None):
        agent_name = self.agents[uniprotid]["agent_name"]

        variant_str = ""
        if len(self.agents[uniprotid]["variants"]) > 1:
            variant_str = "variant{{{}}}".format(variant)

        state_repr = self._generate_agent_state_strs(
            nugget_identifier, ag_typing, agent, uniprotid, variant)

        # Find agent agent bnd sites
        agent_bnd_sites = self._generate_bond_strs(
            nugget_identifier,
            ag_typing, template_rel, role,
            agent, bnd, uniprotid, variant)

        state_signature = variant_str + (
            ", " if len(variant_str) > 0 else "") + ", ".join(state_repr)
        lhs = "{}({})".format(
            agent_name,
            state_signature +
            (", " if len(state_signature) > 0 else "") +
            ", ".join(
                "{}[.]".format(s)
                if bnd_flag is True
                else "{}[{}]".format(s, i + 1)
                for i, s in enumerate(agent_bnd_sites))
        )
        rhs = "{}({})".format(
            agent_name,
            state_signature +
            (", " if len(state_signature) > 0 else "") +
            ",".join(
                "{}[{}]".format(s, i + 1)
                if bnd_flag is True
                else "{}[.]".format(s)
                for i, s in enumerate(agent_bnd_sites))
        )
        return lhs, rhs

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
            self.agents[protoform]["generic_stateful_sites"] = dict()
            self.agents[protoform]["generic_kami_bnd_sites"] = dict()
            self.agents[protoform]["generic_region_bnd_sites"] = dict()
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

        # print(json.dumps(self.agents, indent="   "))

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
                nugget_desc = self.kb.get_nugget_desc(
                    n).replace("\n", ", ")

            self.rules[n]["desc"] = nugget_desc

            if "mod_template" in relations:
                template_rel = self.kb._hierarchy.get_relation(
                    "mod_template", n)
                bnd_relation = None
                if "bnd_template" in relations:
                    bnd_relation = self.kb._hierarchy.get_relation(
                        "bnd_template", n)

                # Generate rules from the nugget
                rules, rate = self._generate_mod_rules(
                    nugget_identifier, ag_typing, template_rel, bnd_relation)
                if rate is None:
                    rate = "'default_mod_rate'"
            else:
                template_rel = self.kb._hierarchy.get_relation(
                    "bnd_template", n)
                # Generate rules from the nugget
                rules, rate, bnd_flag = self._generate_bnd_rules(
                    nugget_identifier, ag_typing, template_rel)
                if rate is None:
                    if bnd_flag:
                        rate = "'default_bnd_rate'"
                    else:
                        rate = "'default_brk_rate'"
            self.rules[n]["rules"] = rules
            self.rules[n]["rate"] = rate

    def generate_initial_conditions(self, concentrations, default_concentation):
        """Generate Kappa initial conditions."""
        def _retreive_states_and_bonds(state_nodes, comp, n, variant=None):
            if isinstance(comp, State):
                for s_node, site_name in state_nodes.items():
                    state_attrs = self.identifier.graph.get_node(s_node)
                    s_name = list(state_attrs["name"])[0]
                    if comp.name == s_name:
                        condition_dict["states"][
                            site_name] = "on" if comp.test else "off"
            elif isinstance(comp, Residue):
                _retreive_states_and_bonds(state_nodes, comp.state, n)
            elif isinstance(comp, Site):
                for residue in comp.residues:
                    _retreive_states_and_bonds(state_nodes, residue, n)
                for state in comp.states:
                    _retreive_states_and_bonds(state_nodes, state, n)
                for bound in comp.bound_to:
                    site_node = self.identifier.identify_site(
                        comp, protein_node)
                    generic_sites = self.agents[protoform][
                        "generic_kami_bnd_sites"]
                    bnds = set()
                    bnd_dict = dict()
                    for (other_site_node, bnd_node), data in generic_sites.items():
                        if other_site_node == site_node:
                            bnds.add(bnd_node)
                    if len(bnds) > 1:
                        warnings.warn(
                            "Multiple binding actions found!", KappaGenerationWarning)
                    elif len(bnds) == 1:
                        bnd = list(bnds)[0]
                        site_name = generic_sites[(site_node, bnd)][0]
                        bnd_dict[bnd] = (
                            site_name,
                            generic_sites[(site_node, bnd)][1]
                        )
                    else:
                        variant_sites = self.agents[protoform][
                            "variants"][variant]["kami_bnd_sites"]
                        for (other_site_node, bnd_node), data in variant_sites.items():
                            if other_site_node == site_node:
                                bnds.add(bnd_node)
                        if len(bnds) > 1:
                            warnings.warn(
                                "Multiple binding actions found!", KappaGenerationWarning)
                        else:
                            bnd = list(bnds)[0]
                            site_name = variant_sites[(site_node, bnd)][0]
                            bnd_dict[bnd] = (
                                site_name,
                                variant_sites[(site_node, bnd)][1]
                            )
                    _retreive_bonds(bnd_dict, bound, n)
            elif isinstance(comp, Region):
                for site in comp.sites:
                    _retreive_states_and_bonds(state_nodes, site, n)
                for residue in comp.residues:
                    _retreive_states_and_bonds(state_nodes, residue, n)
                for state in comp.states:
                    _retreive_states_and_bonds(state_nodes, state, n)
                for bound in comp.bound_to:
                    region_node = self.identifier.identify_region(
                        comp, protein_node)
                    generic_regions = self.agents[protoform][
                        "generic_region_bnd_sites"]
                    bnd_dict = {}
                    bnds = set()
                    for (other_region_node, bnd_node), data in generic_regions.items():
                        if other_region_node == region_node:
                            bnds.add(bnd_node)
                    if len(bnds) > 1:
                        warnings.warn(
                            "Multiple binding actions found!", KappaGenerationWarning)
                    elif len(bnds) == 1:
                        bnd = list(bnds)[0]
                        region_name = generic_regions[(region_node, bnd)][0]
                        bnd_dict[bnd] = (
                            region_name,
                            generic_regions[(region_node, bnd)][1]
                        )
                    else:
                        variant_regions = self.agents[protoform][
                            "variants"][variant]["region_bnd_sites"]
                        for (other_region_node, bnd_node), data in variant_regions.items():
                            if other_region_node == region_node:
                                bnds.add(bnd_node)
                        if len(bnds) > 1:
                            warnings.warn(
                                "Multiple binding actions found!", KappaGenerationWarning)
                        else:
                            bnd = list(bnds)[0]
                            region_name = variant_regions[(region_node, bnd)][0]
                            bnd_dict[bnd] = (
                                region_name,
                                variant_regions[(region_node, bnd)][1]
                            )
                    _retreive_bonds(bnd_dict, bound, n)

        def _retreive_bonds(bnd_dict, comp, n):
            var_name = None
            if isinstance(comp, Protein):
                var_name = comp.name
            else:
                var_name = comp.variant_name

            partner_id = self.identifier.identify_protein(
                Protein(comp.protoform, name=var_name))
            if partner_id is None:
                partner_id = self.identifier.identify_gene(comp.protoform)
            partner_uniprot = comp.protoform.uniprotid

            for bnd_node, (site_name, partners) in bnd_dict.items():
                if isinstance(comp, Protein):
                    if self.identifier.graph.exists_edge(
                            partner_id, bnd_node):
                        # Find the site of the partner
                        partner_site_name = self.agents[partner_uniprot][
                            "direct_bnd_sites"][bnd_node][0]
                        condition_dict["bonds"][site_name] = (
                            partner_site_name,
                            self.agents[partner_uniprot]["agent_name"]
                        )
                elif isinstance(comp, RegionActor):
                    partner_region_id = self.identifier.identify_region(
                        comp.region, partner_id)
                    if self.identifier.graph.exists_edge(
                            partner_region_id, bnd_node):
                        # Find the site of the partner
                        generic_region_bnd_sites =\
                            self.agents[partner_uniprot]["generic_region_bnd_sites"]

                        partner_site_name = None

                        for (region_id, bnd_id) in generic_region_bnd_sites:
                            if region_id == partner_region_id:
                                partner_site_name = generic_region_bnd_sites[
                                    (region_id, bnd_id)][0]
                        if not partner_site_name:
                            if comp.variant_name:
                                variant_name = _normalize_variant_name(comp.variant_name)
                                variant_region_bnd_sites =\
                                    self.agents[partner_uniprot]["variants"][
                                        variant_name]["region_bnd_sites"]
                            elif len(self.agents[partner_uniprot]["variants"]) == 1:
                                unique_variant = list(
                                    self.agents[partner_uniprot]["variants"])[0]
                                variant_region_bnd_sites =\
                                    self.agents[partner_uniprot]["variants"][unique_variant][
                                        "region_bnd_sites"]
                            else:
                                warnings.warn(
                                    "Variant name is not specified, and there are multiple variants",
                                    KappaGenerationWarning)

                            for (region_id, bnd_id) in variant_region_bnd_sites:
                                if region_id == partner_region_id:
                                    partner_site_name = variant_region_bnd_sites[
                                        (region_id, bnd_id)][0]
                        if partner_site_name:
                            condition_dict["bonds"][
                                site_name] = (
                                partner_site_name,
                                self.agents[partner_uniprot]["agent_name"]
                            )
                        else:
                            warnings.warn(
                                "Region was not identified", KappaGenerationWarning)

                elif isinstance(comp, SiteActor):
                    partner_site_id = self.identifier.identify_site(
                        comp.site, partner_id)
                    if self.identifier.graph.exists_edge(
                            partner_site_id, bnd_node):
                        # Find the site of the partner
                        generic_kami_bnd_sites =\
                            self.agents[partner_uniprot]["generic_kami_bnd_sites"]

                        partner_site_name = None
                        for (site_id, bnd_id) in generic_kami_bnd_sites:
                            if site_id == partner_site_id:
                                partner_site_name = generic_kami_bnd_sites[
                                    (site_id, bnd_id)][0]
                        if not partner_site_name:
                            if comp.variant_name:
                                variant_name = _normalize_variant_name(comp.variant_name)
                                variant_kami_bnd_sites =\
                                    self.agents[partner_uniprot]["variants"][
                                        variant_name]["kami_bnd_sites"]
                            elif len(self.agents[partner_uniprot]["variants"]) == 1:
                                unique_variant = list(
                                    self.agents[partner_uniprot]["variants"])[0]
                                variant_kami_bnd_sites =\
                                    self.agents[partner_uniprot]["variants"][unique_variant][
                                        "kami_bnd_sites"]
                            else:
                                warnings.warn(
                                    "Variant name is not specified, and there are multiple variants",
                                    KappaGenerationWarning)

                            for (site_id, bnd_id) in variant_kami_bnd_sites:
                                if site_id == partner_site_id:
                                    partner_site_name = variant_kami_bnd_sites[
                                        (site_id, bnd_id)][0]

                        if partner_site_name:
                            condition_dict["bonds"][
                                site_name] = (
                                partner_site_name,
                                self.agents[partner_uniprot]["agent_name"],
                            )
                        else:
                            warnings.warn(
                                "Site was not identified", KappaGenerationWarning)

        if len(concentrations) > 0:
            for condition in concentrations:
                protoform =\
                    condition.canonical_protein.protoform.uniprotid
                protein_node = self.identifier.identify_protein(
                    condition.canonical_protein)
                if protein_node is None:
                    protein_node = self.identifier.identify_gene(
                        condition.canonical_protein.protoform)

                agent_dict = None
                generic_stateful_sites = generic_stateful_sites = self.agents[
                    protoform]["generic_stateful_sites"]

                # Add canonical count to the respecitve agent's variant
                if condition.canonical_protein.name:
                    variant = _normalize_variant_name(
                        condition.canonical_protein.name)
                    if variant in self.agents[protoform]["variants"]:
                        self.agents[protoform]["variants"][variant][
                            "initial_conditions"] = {
                            "canonical": condition.canonical_count
                        }
                        agent_dict = self.agents[protoform][
                            "variants"][variant]
                    else:
                        warnings.warn(
                            "Variant '{}' is not present in the signature of '{}', ".format(
                                variant, self.agents[protoform]["agent_name"]) +
                            "generating initial condition for a default agent",
                            KappaGenerationWarning)
                else:
                    variant = list(
                        self.agents[protoform]["variants"].keys())[0]
                    self.agents[protoform]["variants"][
                        variant]["initial_conditions"] = {}
                    self.agents[protoform]["variants"][variant][
                        "initial_conditions"]["canonical"] = condition.canonical_count

                    agent_dict = self.agents[protoform][
                        "variants"][variant]

                if agent_dict:
                    agent_dict["initial_conditions"]["non_canonical"] = []
                    # agent_dict["initial_conditions"]["stateful_count"] = dict()
                    # agent_dict["initial_conditions"]["bonds_count"] = dict()
                    # Add counts of stateful agents
                    for component, count in condition.stateful_components:
                        condition_dict = {
                            "states": {},
                            "bonds": {},
                            "count": count
                        }
                        state_nodes = dict()
                        state_nodes.update(agent_dict["stateful_sites"])
                        state_nodes.update(generic_stateful_sites)
                        _retreive_states_and_bonds(
                            state_nodes, component, count, variant)
                        agent_dict["initial_conditions"]["non_canonical"].append(
                            condition_dict)

                    # Add bound initial conditions
                    for component, count in condition.bonds:
                        condition_dict = {
                            "bonds": {},
                            "count": count
                        }
                        _retreive_bonds(
                            self.agents[protoform]["direct_bnd_sites"],
                            component, count)
                        agent_dict["initial_conditions"]["non_canonical"].append(
                            condition_dict)

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

        initial_conditions = "// Initial conditions\n\n"
        signatures = "// Signatures\n\n"
        for agent_uniprot, agent_data in self.agents.items():
            agent_signature = []
            concentrations_str = []

            # Generate variant states
            if len(agent_data["variants"]) > 1:
                agent_signature.append("variant{{{}}}".format(
                    " ".join(v for v in agent_data["variants"].keys())))

            # Generate generic stateful sites
            if len(agent_data["generic_stateful_sites"]) > 0:
                agent_signature.append(", ".join([
                    "{}{{off on}}".format(v)
                    for v in agent_data["generic_stateful_sites"].values()
                ]))

            # Generate generic bnd sites
            all_sites = [
                v[0] for v in list(
                    agent_data["direct_bnd_sites"].values()) +
                list(agent_data["generic_kami_bnd_sites"].values()) +
                list(agent_data["generic_region_bnd_sites"].values())
            ]

            # Generate varian-specific stateful and bnd sites
            for variant, variant_data in agent_data["variants"].items():
                if len(variant_data["stateful_sites"]) > 0:
                    agent_signature.append(", ".join([
                        "{}{{off on}}".format(v)
                        for v in variant_data["stateful_sites"].values()
                    ]))

                all_sites += [
                    v[0]
                    for v in list(variant_data["kami_bnd_sites"].values()) +
                    list(variant_data["region_bnd_sites"].values())
                ]

                # Generate initial conditions
                if "initial_conditions" in variant_data:
                    variant_str = ""
                    if len(agent_data["variants"]) > 1:
                        variant_str = "variant{{{}}}".format(variant)
                    # Canonical count
                    concentrations_str.append("{} {}({})".format(
                        variant_data["initial_conditions"]["canonical"],
                        agent_data["agent_name"], variant_str))
                    # Stateful counts
                    for condition in variant_data[
                            "initial_conditions"]["non_canonical"]:
                        count = condition["count"]

                        elements = []
                        if len(variant_str) > 0:
                            elements.append(variant_str)

                        if "states" in condition:
                            for site, value in condition["states"].items():
                                states_str = "{}{{{}}}".format(site, value)
                                elements.append(states_str)

                        # Bound counts
                        for site, (partner_site, partner_agent) in condition[
                                "bonds"].items():
                            bond_str = (
                                "{}[{}.{}]".format(
                                    site, partner_site, partner_agent)
                            )
                            elements.append(bond_str)
                        concentrations_str.append("{} {}({})".format(
                            count,
                            agent_data["agent_name"], ", ".join(elements)))

            # Add generated sites to the agent signature
            if len(all_sites) > 0:
                agent_signature.append(", ".join([
                    "{}".format(v) for v in all_sites]))

            signatures += "%agent: {}({})".format(
                agent_data["agent_name"],
                ", ".join(agent_signature)) + "\n"

            if len(concentrations_str) > 0:
                initial_conditions += (
                    "// Concentrations of {}\n".format(agent_data["agent_name"]) +
                    "\n".join(
                        ["%init: {}".format(conc) for conc in concentrations_str]) +
                    "\n\n"
                )

        rule_repr = "\n// Rules \n\n"

        i = 1
        for data in self.rules.values():
            if data["desc"]:
                rule_repr += "// {} \n".format(data["desc"])
            for r in data["rules"]:
                rule_repr += "'rule {}' {} @ {} \n".format(
                    i, r, data["rate"])
                i += 1
            rule_repr += "\n"

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

        return header + signatures + rule_repr + variables + initial_conditions


class ModelKappaGenerator(KappaGenerator):
    """Kappa generator from KAMI models."""

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

    def _get_variant_name(self, ag_node, uniprotid):
        for variant, variant_data in self.agents[
                uniprotid]["variants"].items():
            if "ref_node" in variant_data:
                if variant_data["ref_node"] == ag_node:
                    return variant

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
                existing_stateful_sites =\
                    self.agents[protoform]["variants"][var_name][
                        "stateful_sites"].values()
                var_prefix = None
                if len(variants) > 1:
                    var_prefix = var_name
                self.agents[protoform]["variants"][var_name][
                    "stateful_sites"][state] = self._generate_site_name(
                        state, "", existing_stateful_sites,
                        name_from_attrs=True,
                        attrs_key="name", variant_name=var_prefix)

    def _generate_kami_bnd_sites(self, protoform):
        variants = self.agents[protoform]["variants"]

        for variant_name, variant_data in variants.items():
            sites = self.identifier.get_attached_sites(
                variant_data["ref_node"])
            for s in sites:
                # Generate site name
                var_prefix = None
                if len(variants) > 1:
                    var_prefix = variant_name

                existing_elements = [
                    v[0] for v in variant_data["kami_bnd_sites"].values()
                ]

                site_name = self._generate_site_name(
                    s, "site", existing_elements,
                    True, "name", var_prefix)
                partner_nodes = self._generate_bnds_and_partners(s)
                new_sites = set()
                for bnd_node, partners in partner_nodes.items():
                    name = generate_new_element_id(new_sites, site_name)
                    new_sites.add(name)
                    self.agents[protoform]["variants"][variant_name][
                        "kami_bnd_sites"][(s, bnd_node)] = (
                            name,
                            partner_nodes)

    def _generate_region_bnd_sites(self, protoform):
        for variant_name, variant_data in self.agents[protoform]["variants"].items():
            regions = self.identifier.get_attached_regions(variant_data[
                "ref_node"])
            region_bnd_sites = self.agents[protoform]["variants"][
                variant_name]["region_bnd_sites"]
            for r in regions:
                existing_elements = [
                    v[0] for v in self.agents[protoform]["variants"][
                        variant_name]["region_bnd_sites"].values()
                ]
                var_prefix = None
                if len(self.agents[protoform]["variants"]) > 1:
                    var_prefix = variant_name
                site_name = self._generate_site_name(
                    r, "region", existing_elements,
                    True, "name", var_prefix)
                partner_nodes = self._generate_bnds_and_partners(r)
                new_sites = set()
                for bnd_node, partners in partner_nodes.items():
                    name = generate_new_element_id(new_sites, site_name)
                    new_sites.add(name)
                    region_bnd_sites[(r, bnd_node)] = (
                        name,
                        partner_nodes
                    )

    def _generate_mod_rules(self, nugget_identifier, ag_typing, template_rel, bnd_relation=None):
        rules = []
        rate = None
        mod_node = list(template_rel["mod"])[0]

        # The rule is generated only if the substrate node is not None
        if "substrate" in template_rel.keys():
            substrates = template_rel["substrate"]
            if "enzyme" in template_rel.keys():
                enzymes = template_rel["enzyme"]

            # Find substrate agents and variants
            for substrate in substrates:
                ag_substrate = ag_typing[substrate]
                substrate_uniprotid = self.kb.get_uniprot(ag_substrate)

                substrate_agent_name = self.agents[substrate_uniprotid][
                    "agent_name"]
                variant = self._get_variant_name(
                    ag_substrate, substrate_uniprotid)

                states = nugget_identifier.get_attached_states(
                    substrate)

                # Get target modification state
                target_states = []
                for s in states:
                    if s in template_rel["mod_state"]:
                        # Get site of a state
                        ag_state = ag_typing[s]
                        target_site = self.agents[substrate_uniprotid][
                            "variants"][variant][
                                "stateful_sites"][ag_state]
                        # Get state value
                        mod_attrs = nugget_identifier.graph.get_node(mod_node)
                        target_value = "on" if list(mod_attrs["value"])[0] else "off"

                        target_states.append((s, target_site, target_value))

                # Generate required states of the substrate
                variant_state = ""
                if len(self.agents[substrate_uniprotid]["variants"]) > 1:
                    variant_state = "variant{{{}}}".format(variant)

                states = self._generate_agent_state_strs(
                    nugget_identifier, ag_typing, substrate,
                    substrate_uniprotid, variant,
                    to_ignore=[s[0] for s in target_states])

                substrate_states = (
                    variant_state +
                    (", " if len(variant_state) > 0 and len(states) > 0 else "") +
                    ", ".join(states)
                )

                # We are in the anonymous modification case
                if len(enzymes) > 0:
                    # Find enzyme agents and variants
                    for enzyme in enzymes:
                        ag_enzyme = ag_typing[enzyme]
                        enzyme_uniprotid = self.kb.get_uniprot(ag_enzyme)

                        enzyme_agent_name = self.agents[enzyme_uniprotid][
                            "agent_name"]
                        enzyme_variant = self._get_variant_name(
                            ag_enzyme, enzyme_uniprotid)

                        # Generate required states of the enzyme
                        variant_state = ""
                        if len(self.agents[enzyme_uniprotid]["variants"]) > 1:
                            variant_state = "variant{{{}}}".format(
                                enzyme_variant)

                        states = self._generate_agent_state_strs(
                            nugget_identifier, ag_typing, enzyme,
                            enzyme_uniprotid, enzyme_variant)

                        enzyme_states = (
                            variant_state +
                            (", " if len(variant_state) > 0 and len(states) > 0 else "") +
                            ", ".join(states)
                        )

                        # Check if the substrate is required to be bound to the enzyme
                        substrate_bnd_sites = []
                        enzyme_bnd_sites = []
                        # If nugget is related to the bnd template
                        # (i.e. substrate is required to be bound to
                        # the enzyme)
                        substrate_bnd_sites = []
                        enzyme_bnd_sites = []
                        if bnd_relation:
                            # Identify binding sites
                            bnd = list(bnd_relation["bnd"])[0]
                            substrate_bnd_sites = self._generate_bond_strs(
                                nugget_identifier,
                                ag_typing, bnd_relation, "left",
                                substrate, bnd,
                                substrate_uniprotid,
                                variant)
                            enzyme_bnd_sites = self._generate_bond_strs(
                                nugget_identifier,
                                ag_typing, bnd_relation, "right",
                                enzyme, bnd,
                                enzyme_uniprotid,
                                enzyme_variant)

                        # Generate LHS and RHS of the substrate
                        substrate_lhs, substrate_rhs =\
                            self._generate_mod_agent_lhs_rhs(
                                substrate_uniprotid, substrate_agent_name,
                                variant,
                                substrate_states,
                                substrate_bnd_sites,
                                target_states)

                        # Generate LHS and RHS of the enzyme
                        enzyme_lhs, enzyme_rhs =\
                            self._generate_mod_agent_lhs_rhs(
                                enzyme_uniprotid, enzyme_agent_name,
                                enzyme_variant,
                                enzyme_states,
                                enzyme_bnd_sites)

                        rule = "{}, {} -> {}, {}".format(
                            enzyme_lhs, substrate_lhs,
                            enzyme_rhs, substrate_rhs)
                        rules.append(rule)
                else:
                    substrate_lhs, substrate_rhs =\
                        self._generate_mod_agent_lhs_rhs(
                            substrate_uniprotid, substrate_agent_name,
                            variant,
                            substrate_states, [], target_states)
                    rule = "{} -> {}".format(
                        substrate_lhs, substrate_rhs)
                    rules.append(rule)

        rate = None
        mod_attrs = nugget_identifier.graph.get_node(mod_node)
        if "rate" in mod_attrs:
            rate = list(mod_attrs["rate"])[0]
        return rules, rate

    def _generate_bnd_rules(self, nugget_identifier, ag_typing, template_rel):
        rules = []
        bnd_node = list(template_rel["bnd"])[0]
        bnd_attrs = nugget_identifier.graph.get_node(bnd_node)
        bnd_flag = True
        if "test" in bnd_attrs:
            bnd_flag = list(bnd_attrs["test"])[0]

        if "left_partner" in template_rel.keys() and\
           "right_partner" in template_rel.keys():
            left_partner = template_rel["left_partner"]
            right_partner = template_rel["right_partner"]
            for left in left_partner:
                ag_left = ag_typing[left]
                left_uniprotid = self.kb.get_uniprot(ag_left)

                left_variant = self._get_variant_name(ag_left, left_uniprotid)

                left_lhs, left_rhs = self._generate_bnd_partner_str(
                    nugget_identifier, ag_typing, template_rel, "left",
                    left, bnd_node, left_uniprotid, bnd_flag, left_variant)

                for right in right_partner:
                    ag_right = ag_typing[right]
                    right_uniprotid = self.kb.get_uniprot(ag_right)
                    right_variant = self._get_variant_name(
                        ag_right, right_uniprotid)
                    right_lhs, right_rhs = self._generate_bnd_partner_str(
                        nugget_identifier, ag_typing, template_rel, "right",
                        right, bnd_node, right_uniprotid, bnd_flag, right_variant)

                    rules.append("{}, {} -> {}, {}".format(
                        left_lhs, right_lhs, left_rhs, right_rhs))

        bnd_attrs = nugget_identifier.graph.get_node(bnd_node)
        rate = None
        if "rate" in bnd_attrs:
            rate = list(bnd_attrs["rate"])[0]
        return rules, rate, bnd_flag


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
        # Return all variants having the specified component
        # Checks both removal of components and empty positive test
        lhs_ref_node = keys_by_value(instance, ref_node)[0]
        lhs_component = keys_by_value(instance, component)[0]
        p_variant_nodes = keys_by_value(
            rule.p_lhs, lhs_ref_node)

        variants_with_component = []
        for i, p_variant in enumerate(p_variant_nodes):
            component_found = False
            for anc in rule.p.ancestors(p_variant):
                if rule.p_lhs[anc] == lhs_component:
                    component_found = True
                    break
            if component_found:
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

    def _find_variants_with_key_residue(self, rule, instance,
                                        ref_node, variants, residue_node, aa):
        lhs_ref_node = keys_by_value(instance, ref_node)[0]
        lhs_residue = keys_by_value(instance, residue_node)[0]
        p_variant_nodes = keys_by_value(
            rule.p_lhs, lhs_ref_node)
        variants_with_component = []
        for i, p_variant in enumerate(p_variant_nodes):
            component_found = False
            for anc in rule.p.predecessors(p_variant):
                if rule.p_lhs[anc] == lhs_residue:
                    # Check aa value
                    p_res_aa = rule.p.get_node(anc)["aa"]
                    if aa in p_res_aa:
                        component_found = True
                        break
            if component_found:
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
            existing_elements = self.agents[protoform][
                "generic_stateful_sites"].values()
            self.agents[protoform]["generic_stateful_sites"][state] =\
                self._generate_site_name(
                    state, "", existing_elements, True, "name")

    def _generate_kami_bnd_sites(self, protoform):
        ref_node = self.agents[protoform]["ref_node"]
        sites = self.identifier.get_attached_sites(ref_node)

        for s in sites:
            existing_elements = self.agents[protoform][
                "generic_kami_bnd_sites"].values()
            site_name = self._generate_site_name(
                s, "site", existing_elements, True, "name")
            partner_nodes = self._generate_bnds_and_partners(s)
            new_sites = set()
            for bnd, partners in partner_nodes.items():
                name = generate_new_element_id(new_sites, site_name)
                new_sites.add(name)
                self.agents[protoform]["generic_kami_bnd_sites"][(s, bnd)] = (
                    name,
                    partner_nodes
                )

    def _generate_region_bnd_sites(self, protoform):
        ref_node = self.agents[protoform]["ref_node"]
        regions = self.identifier.get_attached_regions(ref_node)
        for r in regions:
            existing_elements = self.agents[protoform][
                "generic_region_bnd_sites"].values()
            site_name = self._generate_site_name(
                r, "region", existing_elements, True, "name")
            partner_nodes = self._generate_bnds_and_partners(r)
            new_sites = set()
            for bnd, partners in partner_nodes.items():
                name = generate_new_element_id(new_sites, site_name)
                new_sites.add(name)
                self.agents[protoform]["generic_region_bnd_sites"][(r, bnd)] = (
                    name,
                    partner_nodes
                )

    def _valid_agent_variants(self, nugget_identifier, agent_node,
                              agent_uniprotid, ag_node, ag_typing):
        # Collect a set of enzyme variants that do not
        # satisfy positive requirements
        agent_variants = set(
            self.agents[agent_uniprotid]["variants"].keys())

        invalid_variants = set()
        if ag_node in self.instantiation_rules:
            rule, instance = self.instantiation_rules[ag_node]

            # If enzyme has required components, we need to check
            # if some variants lost them
            required_components = [
                ag_typing[comp]
                for comp in
                nugget_identifier.get_attached_regions(agent_node) +
                nugget_identifier.get_attached_sites(agent_node) +
                nugget_identifier.get_attached_residues(agent_node) +
                nugget_identifier.get_attached_states(agent_node)
            ]

            for c in required_components:
                variants_with_component =\
                    self._find_variants_with_component(
                        rule, instance,
                        ag_node, agent_variants, c)
                for v in agent_variants:
                    if v not in variants_with_component:
                        invalid_variants.add(v)

            residues = nugget_identifier.get_attached_residues(agent_node)
            for r in residues:
                res_attrs = nugget_identifier.graph.get_node(r)
                aa = res_attrs["aa"]
                test = res_attrs["test"]

                if test:
                    variants_with_aa =\
                        self._find_variants_with_key_residue(
                            rule, instance,
                            ag_node, agent_variants,
                            ag_typing[r], list(aa)[0])
                for v in agent_variants:
                    if v not in variants_with_aa:
                        invalid_variants.add(v)

        return agent_variants.difference(invalid_variants)

    def _generate_mod_rules(self, nugget_identifier, ag_typing, template_rel, bnd_relation=None):
        rules = []
        rate = None
        mod_node = list(template_rel["mod"])[0]

        # The rule is generated only if the substrate node is not None
        if "substrate" in template_rel.keys():
            substrates = template_rel["substrate"]
            if "enzyme" in template_rel.keys():
                enzymes = template_rel["enzyme"]

            # Find substrate agents and variants
            for substrate in substrates:
                ag_substrate = ag_typing[substrate]
                substrate_uniprotid = self.kb.get_uniprot(ag_substrate)

                substrate_agent_name = self.agents[substrate_uniprotid][
                    "agent_name"]

                # Find vaild variants of the substrate
                valid_substrate_variants =\
                    self._valid_agent_variants(
                        nugget_identifier, substrate,
                        substrate_uniprotid, ag_substrate, ag_typing)

                states = nugget_identifier.get_attached_states(
                    substrate)

                # Get target modification state
                target_states = []
                for s in states:
                    if s in template_rel["mod_state"]:
                        # Get site of a state
                        ag_state = ag_typing[s]
                        target_site = self.agents[substrate_uniprotid][
                            "generic_stateful_sites"][ag_state]
                        # Get state value
                        mod_attrs = nugget_identifier.graph.get_node(mod_node)
                        target_value = "on" if list(mod_attrs["value"])[0] else "off"

                        target_states.append((s, target_site, target_value))

                # Generate required states of the substrate
                substrate_states = ",".join(self._generate_agent_state_strs(
                    nugget_identifier, ag_typing, substrate,
                    substrate_uniprotid, None,
                    to_ignore=[s[0] for s in target_states]))

                # We are in the anonymous modification case
                for variant in valid_substrate_variants:
                    if len(enzymes) > 0:
                        # Find enzyme agents and variants
                        for enzyme in enzymes:
                            ag_enzyme = ag_typing[enzyme]
                            enzyme_uniprotid = self.kb.get_uniprot(ag_enzyme)

                            enzyme_agent_name = self.agents[enzyme_uniprotid][
                                "agent_name"]

                            valid_ezyme_variants =\
                                self._valid_agent_variants(
                                    nugget_identifier, enzyme,
                                    enzyme_uniprotid, ag_enzyme, ag_typing)

                            # Generate required states of the enzyme
                            enzyme_states = ",".join(
                                self._generate_agent_state_strs(
                                    nugget_identifier, ag_typing, enzyme,
                                    enzyme_uniprotid))

                            # Check if the substrate is required to be bound to the enzyme
                            substrate_bnd_sites = []
                            enzyme_bnd_sites = []
                            # If nugget is related to the bnd template
                            # (i.e. substrate is required to be bound to
                            # the enzyme)
                            substrate_bnd_sites = []
                            enzyme_bnd_sites = []
                            if bnd_relation:
                                # Identify binding sites
                                bnd = list(bnd_relation["bnd"])[0]
                                substrate_bnd_sites = self._generate_bond_strs(
                                    nugget_identifier,
                                    ag_typing, bnd_relation, "left",
                                    substrate, bnd,
                                    substrate_uniprotid)
                                enzyme_bnd_sites = self._generate_bond_strs(
                                    nugget_identifier,
                                    ag_typing, bnd_relation, "right",
                                    enzyme, bnd,
                                    enzyme_uniprotid)

                            # Generate LHS and RHS of the substrate
                            substrate_lhs, substrate_rhs =\
                                self._generate_mod_agent_lhs_rhs(
                                    substrate_uniprotid, substrate_agent_name,
                                    variant, substrate_states,
                                    substrate_bnd_sites,
                                    target_states)

                            for enzyme_variant in valid_ezyme_variants:
                                # Generate LHS and RHS of the enzyme
                                enzyme_lhs, enzyme_rhs =\
                                    self._generate_mod_agent_lhs_rhs(
                                        enzyme_uniprotid, enzyme_agent_name,
                                        enzyme_variant, enzyme_states,
                                        enzyme_bnd_sites)

                                rule = "{}, {} -> {}, {}".format(
                                    enzyme_lhs, substrate_lhs,
                                    enzyme_rhs, substrate_rhs)
                                rules.append(rule)
                    else:
                        substrate_lhs, substrate_rhs =\
                            self._generate_mod_agent_lhs_rhs(
                                substrate_uniprotid, substrate_agent_name,
                                variant, substrate_states,
                                [],
                                target_states)
                        rule = "{} -> {}".format(
                            substrate_lhs, substrate_rhs)
                        rules.append(rule)

        rate = None
        mod_attrs = nugget_identifier.graph.get_node(mod_node)
        if "rate" in mod_attrs:
            rate = list(mod_attrs["rate"])[0]
        return rules, rate

    def _generate_bnd_rules(self, nugget_identifier, ag_typing, template_rel):
        rules = []
        bnd_node = list(template_rel["bnd"])[0]
        bnd_attrs = nugget_identifier.graph.get_node(bnd_node)
        bnd_flag = True
        if "test" in bnd_attrs:
            bnd_flag = list(bnd_attrs["test"])[0]

        if "left_partner" in template_rel.keys() and\
           "right_partner" in template_rel.keys():
            left_partner = template_rel["left_partner"]
            right_partner = template_rel["right_partner"]
            for left in left_partner:
                ag_left = ag_typing[left]
                left_uniprotid = self.kb.get_uniprot(ag_left)

                valid_left_variants =\
                    self._valid_agent_variants(
                        nugget_identifier, left,
                        left_uniprotid, ag_left, ag_typing)

                for left_variant in valid_left_variants:
                    left_lhs, left_rhs = self._generate_bnd_partner_str(
                        nugget_identifier, ag_typing, template_rel, "left",
                        left, bnd_node, left_uniprotid, bnd_flag, left_variant)

                    for right in right_partner:
                        ag_right = ag_typing[right]
                        right_uniprotid = self.kb.get_uniprot(ag_right)
                        valid_right_variants =\
                            self._valid_agent_variants(
                                nugget_identifier, right,
                                right_uniprotid, ag_right, ag_typing)

                        for right_variant in valid_right_variants:
                            right_lhs, right_rhs = self._generate_bnd_partner_str(
                                nugget_identifier, ag_typing, template_rel, "right",
                                right, bnd_node, right_uniprotid, bnd_flag, right_variant)

                            rules.append("{}, {} -> {}, {}".format(
                                left_lhs, right_lhs, left_rhs, right_rhs))
        bnd_attrs = nugget_identifier.graph.get_node(bnd_node)
        rate = None
        if "rate" in bnd_attrs:
            rate = list(bnd_attrs["rate"])[0]
        return rules, rate, bnd_flag
