"""Kappa generation utils."""
from abc import ABC, abstractmethod
import datetime
import json
import warnings

from regraph.utils import keys_by_value

from kami.aggregation.identifiers import EntityIdentifier
from kami.data_structures.entities import (State, Residue, Region, Site,
                                           Protein, RegionActor, SiteActor)
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
    """Abstract Kappa generator.

    Attributes
    ----------
    kb : KamiCorpus or KamiModel
        Knowledge base
    kb_type : str
        Knowledge base type, "model" or "corpus"
    identifier : EntityIdentifier
        Entity identifier initialized with the action graph
        of the underlying knowldege base
    agents : dict
        Dictionary with agent definitions, including agent name
        variants, stateful and binding Kappa sites
    default_bnd_rate : float
        Default binding rate
    default_brk_rate : float
        Default unbinding rate
    default_mod_rate : float
        Default modification rate


    Abstract methods
    ----------------

    _generate_protoforms

    """

    @abstractmethod
    def _generate_protoforms(self):
        """Generate protoforms from the knowledge base.

        Return a dictionary with UniProt AC as keys and values being
        dictionaries with protoform data: hgnc_symbol, reference node
        variants, etc.
        """
        pass

    @abstractmethod
    def _generate_stateful_sites(self, protoform):
        """Generate Kappa sites that can have a state.

        A Kappa site is generated per state node in the action
        graph (model or corpus).
        """
        pass

    @abstractmethod
    def _generate_kami_bnd_sites(self, ref_node, variants):
        """Generate Kappa sites for KAMI's site nodes.

        A Kappa site is generated per binding action per KAMI
        site node.
        """
        pass

    # @abstractmethod
    # def _generate_region_bnd_sites(self, ref_node, variants):
    #     pass

    def _generate_bnds(self, component):
        bnds = self.identifier.successors_of_type(component, "bnd")
        return bnds

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
        """Generate direct binding sites.

        A Kappa site is generated per binding action
        directly adjacent to the protoform node (or protein node if model)
        """
        ref_node = self.agents[protoform]["ref_node"]
        variants = list(self.agents[protoform]["variants"].keys())
        if ref_node is None:
            ref_node = self.agents[protoform]["variants"][
                variants[0]]["ref_node"]
        direct_bnds = self.identifier.successors_of_type(
            ref_node, "bnd")

        existing_elements = self.agents[protoform]["direct_bnd_sites"].values()
        for bnd in direct_bnds:
            bnd_name = self._generate_site_name(
                bnd, "site", existing_elements)

            self.agents[protoform]["direct_bnd_sites"][bnd] = bnd_name

    def generate_agents(self):
        """Generate Kappa agents from the knowledge base."""
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
            self.agents[protoform]["stateful_sites"] = dict()
            self.agents[protoform]["kami_bnd_sites"] = dict()
            self.agents[protoform]["region_bnd_sites"] = dict()
            self.agents[protoform]["direct_bnd_sites"] = dict()

            for variant_name, variant_node in data["variants"].items():
                self.agents[protoform]["variants"][variant_name] = dict()
                self.agents[protoform]["variants"][variant_name][
                    "ref_node"] = variant_node

            # Generate direct binding sites
            self._generate_direct_bnd_sites(protoform)
            # Find stateful sites (a Kappa site per every distinct state)
            self._generate_stateful_sites(protoform)
            # Generate binding through kami sites
            self._generate_kami_bnd_sites(protoform)
            # # Generate binding through kami regions
            self._generate_region_bnd_sites(protoform)

    def _get_bnd_region_site(self, nugget_identifier, bnd_node,
                             bnd_template, role):
        """Get region or/and site taking part in the binding."""
        region = None
        site = None
        if role + "_partner_region" in bnd_template:
            for r in bnd_template[role + "_partner_region"]:
                if nugget_identifier.graph.exists_edge(r, bnd_node):
                    region = r
                    break
        if role + "_partner_site" in bnd_template:
            for s in bnd_template[role + "_partner_site"]:
                if region:
                    if nugget_identifier.graph.exists_edge(s, region):
                        site = s
                        break
                else:
                    if nugget_identifier.graph.exists_edge(s, bnd_node):
                        site = s
                        break
        return region, site

    def _generate_agent_state_strs(self, nugget_identifier, ag_typing, agent,
                                   ag_uniprot_id, to_ignore=None):
        """Generate list of string representations of active agent states."""
        if to_ignore is None:
            to_ignore = []
        # Find agent states
        state_repr = []
        states = nugget_identifier.get_attached_states(agent)
        for s in states:
            if s not in to_ignore:
                # get state value (True always renders to 'on', False to 'off')
                state_attrs = nugget_identifier.graph.get_node(s)
                value = "on" if list(state_attrs["test"])[0] else "off"
                ag_state = ag_typing[s]
                if ag_state in self.agents[ag_uniprot_id]["stateful_sites"]:
                    state_repr.append(
                        self.agents[
                            ag_uniprot_id]["stateful_sites"][
                                ag_state] + "{{{}}}".format(value))
        return state_repr

    def _generate_bound_conditions(self, nugget_identifier, ag_typing,
                                   actor_nodes, starting_bnd_index=1):
        """Retreive the list of binding conditions from the nugget.

        Parameters
        ----------
        nugget_identifier : EntityIdentifier
            Entity identifier instantiated for the input nugget graph
        ag_typing : dict
            Typing of nugget by the action graph
        actor_nodes : dict
            Dictonary of actor nodes (nodes that take part in the iteraction
            described by the nugget), keys are identifiers of actors,
            values are collection of nodes in the nugget
        starting_bnd_index : int
            Starting binding index for conditions

        Returns
        -------
        bound_condition : str
            String representing generated conditions
        actor_sites : dict
            Dictionary with actor nodes as keys and bound sites as values
        """
        def _fetch_actor_data(role, bnd_node):
            sites = set()
            uniprotid = self.kb.get_uniprot(
                ag_typing[list(bnd_template[role + "_partner"])[0]])
            nodes = set()
            for node in bnd_template[role + "_partner"]:
                region, site = self._get_bnd_region_site(
                    nugget_identifier, node,
                    bnd_template, role)
                ag_region = ag_typing[region] if region in ag_typing else None
                ag_site = ag_typing[site] if site in ag_typing else None
                site = self._find_bnd_site(
                    ag_typing[node], ag_region, ag_site, ag_typing[bnd_node])
                states = self._generate_agent_state_strs(
                    nugget_identifier, ag_typing, node, uniprotid)
                sites.add(site)
                nodes.add(node)
            if len(sites) > 0:
                warnings.warn(
                    "One of the bound coditions contains binding "
                    "to a variant dependent agent! "
                    "Choosing one of them", KappaGenerationWarning)
            return uniprotid, list(sites)[0], states, nodes

        bnds = {}  # all the bnds
        for n in nugget_identifier.graph.nodes():
            if nugget_identifier.meta_typing[n] == "bnd":
                bnd_attrs = nugget_identifier.graph.get_node(n)
                if "type" in bnd_attrs and "do" not in bnd_attrs["type"]:
                    bnds[n] = {}
                    bnd_flag = True
                    if "test" in bnd_attrs:
                        bnd_flag = list(bnd_attrs["test"])[0]
                    bnds[n]["flag"] = bnd_flag
                    bnd_template = nugget_identifier.identify_bnd_template(n)
                    bnds[n]["left_partner"] = _fetch_actor_data(
                        "left", n)
                    bnds[n]["right_partner"] = _fetch_actor_data(
                        "right", n)

        actor_dict = dict()
        for k, v in actor_nodes.items():
            for vv in v:
                actor_dict[vv] = k

        # condition_actors is here to solve the problem of chains
        # like 'A-[is-bnd]-B-[is_bnd]-C'
        condition_actors = dict()
        actor_sites = dict()
        for k in actor_nodes.keys():
            actor_sites[k] = set()
        for i, (bnd, data) in enumerate(bnds.items()):
            bnd_index = starting_bnd_index + i

            # Process the left partner
            uniprot, site, states, nodes = data["left_partner"]
            is_actor = False
            for n in nodes:
                if n in actor_dict:
                    is_actor = True
                    actor_sites[actor_dict[n]].add(
                        "{}[{}]".format(site, bnd_index))
            if not is_actor:
                agent_name = self.agents[uniprot]["agent_name"]
                nodes_hash = tuple(nodes)
                if nodes_hash in condition_actors:
                    condition_actors[nodes_hash][1].append(
                        "{}[{}]".format(site, bnd_index))
                else:
                    condition_actors[nodes_hash] = (
                        agent_name, ["{}[{}]".format(site, bnd_index)])

            # Process the right partner
            uniprot, site, states, nodes = data["right_partner"]
            is_actor = False
            for n in nodes:
                if n in actor_dict:
                    is_actor = True
                    actor_sites[actor_dict[n]].add(
                        "{}[{}]".format(site, bnd_index))
                    break
            if not is_actor:
                agent_name = self.agents[uniprot]["agent_name"]
                nodes_hash = tuple(nodes)
                if nodes_hash in condition_actors:
                    condition_actors[nodes_hash][1].append(
                        "{}[{}]".format(site, bnd_index))
                else:
                    condition_actors[nodes_hash] = (
                        agent_name, ["{}[{}]".format(site, bnd_index)])

        bound_conditions = ", ".join([
            "{}({})".format(v[0], ",".join(v[1]))
            for v in condition_actors.values()
        ])

        return bound_conditions, actor_sites

    def _find_bnd_site(self, agent, region, site, bnd):
        """Find the Kappa site for provided binding data.

        Parameters
        ----------
        agent : hashable
            Id of the reference agent node in the action graph
        region : hashable
            Id of the region node in the action graph that performs
            the binding
        site : hashable
            Id of the site node in the action graph that performs
            the binding
        bnd : hashable
            Id of the binding action in the action graph
        """
        uniprotid = self.kb.get_uniprot(agent)
        if bnd in self.agents[uniprotid]["direct_bnd_sites"]:
            return self.agents[uniprotid][
                "direct_bnd_sites"][bnd]
        elif site and (site, bnd) in self.agents[uniprotid][
                "kami_bnd_sites"]:
            return self.agents[uniprotid][
                "kami_bnd_sites"][(site, bnd)]
        elif region and (region, bnd) in self.agents[uniprotid][
                "region_bnd_sites"]:
            return self.agents[uniprotid][
                "region_bnd_sites"][(region, bnd)]

    def _retreive_actor_data(self, nugget_identifier, ag_typing,
                             actors, template_rel,
                             bnd_node=None, bnd_role=None,
                             modifiable_states=None):
        data = {"variants": {}}
        # Get the corresponding node in the AG and the UniProt AC
        for actor in actors:
            ag_node = ag_typing[actor]
            if "uniprotid" not in data:
                data["uniprotid"] =\
                    self.kb.get_uniprot(ag_node)
            # Get the list of valid variants (for which the interactions
            # is realizable)
            variants = self._get_variants(
                nugget_identifier, actor,
                data["uniprotid"],
                ag_node, ag_typing)
            # Find binding sites and state conditions for all
            # valid variants
            for variant in variants:
                data["variants"][variant] = {}

                # Find all states
                states =\
                    self._generate_agent_state_strs(
                        nugget_identifier, ag_typing,
                        actor, data["uniprotid"],
                        to_ignore=modifiable_states)
                # Find binding site name
                bnd_site = None
                if bnd_node:
                    # Find region or/and site through which bnd
                    # was performed
                    region, site = self._get_bnd_region_site(
                        nugget_identifier, bnd_node,
                        template_rel, bnd_role)
                    ag_region =\
                        ag_typing[region] if region in ag_typing else None
                    ag_site = ag_typing[site] if site in ag_typing else None
                    # Use it to find the corresponding Kappa site
                    ag_bnd_node = ag_typing[bnd_node]
                    bnd_site = self._find_bnd_site(
                        ag_node, ag_region, ag_site, ag_bnd_node)

                data["variants"][variant] = (
                    states, bnd_site
                )
        return data

    def _fold_agent(self, data):
        """Fold interaction agent.

        Check if the interaction is realizable for all the
        variants and also happens through a variant-independent site
        (the we are able to generate a generic rule with
        no variant-state). By doing this we save some nuggets from
        combinatorial explosion.
        """
        variant_dependent = True
        unique_bnd_site = None
        unique_states = None
        if len(data["variants"]) ==\
           len(self.agents[data["uniprotid"]]["variants"]):
            bnd_sites = set(
                site for _, site in data["variants"].values())
            stateful_sites = list(
                states for states, _ in data["variants"].values())
            if len(bnd_sites) == 1:
                variant_dependent = False
                unique_bnd_site = list(bnd_sites)[0]
                unique_states = stateful_sites[0]
        if not variant_dependent:
            return variant_dependent, {
                "dummy": (unique_states, unique_bnd_site)
            }
        else:
            return variant_dependent, data["variants"]

    def _generate_mod_rules(self, nugget_identifier, ag_typing,
                            template_rel):
        """Generate modification rules.

        Parameters
        ----------
        nugget_identifier : EntityIdentifier
            Identifier of entities in the input nugget graph
        ag_typing : dict
            Dictinary with nugget typing by the action graph
        template_rel : dict
            Dictionary with modification template relation
            specifying the roles of nodes in the nugget

        For every nugget a set of corresponding Kappa rules
        is generated. If an agent of modification has multiple variants
        we proceed as follows:
        - if the interaction described by the nugget is
        realizable by all the agent variants, we write a generic
        variant-state-independent rule;
        - otherwise we generate a rule for every combination of 'valid'
        variants. However, in this case generation of combinations
        of agent variants mentioned in 'is bound' conditions is
        currently not implemented (only generic agents are allowed
        in is bound conditions).
        """
        rules = []
        rate = None
        mod_node = list(template_rel["mod"])[0]
        mod_attrs = nugget_identifier.graph.get_node(mod_node)
        target_value = "on" if list(mod_attrs["value"])[0] else "off"
        rate = None
        if "rate" in mod_attrs:
            rate = list(mod_attrs["rate"])[0]

        # Find substrate UniProtAC
        substrate_uniprotid =\
            self.kb.get_uniprot(
                ag_typing[list(template_rel["substrate"])[0]])

        # Get target modification states
        target_states = []
        for s in template_rel["mod_state"]:
            # Get site of a state
            ag_state = ag_typing[s]
            target_site = self.agents[substrate_uniprotid][
                "stateful_sites"][ag_state]
            target_states.append((s, target_site, target_value))

        substrate_agent = self._retreive_actor_data(
            nugget_identifier, ag_typing,
            template_rel["substrate"], template_rel,
            modifiable_states=[s for s, _, _ in target_states])

        # Fold substrate and enzyme to variant independent actors
        # to optimize the number of generated rules
        substrate_variant_dep, folded_substrate = self._fold_agent(
            substrate_agent)

        enzyme_agent = None
        enzyme_variant_dep, folded_enzyme = None, None
        self_modification = False
        if "enzyme" in template_rel:
            for enzyme in template_rel["enzyme"]:
                for substrate in template_rel["substrate"]:
                    if enzyme == substrate:
                        self_modification = True
                        break
            if not self_modification:
                enzyme_agent = self._retreive_actor_data(
                    nugget_identifier, ag_typing,
                    template_rel["enzyme"], template_rel)
                enzyme_variant_dep, folded_enzyme = self._fold_agent(
                    enzyme_agent)

        # Generate all 'is bound' conditions
        actor_nodes = {
            "substrate": list(template_rel["substrate"]),
        }
        if "enzyme" in template_rel:
            actor_nodes["enzyme"] =\
                list(template_rel["enzyme"])

        bound_conditions, actor_sites =\
            self._generate_bound_conditions(
                nugget_identifier, ag_typing,
                actor_nodes,
                starting_bnd_index=1
            )

        # Generate modification rule strings
        substrate_kappa_agent = self.agents[
            substrate_agent["uniprotid"]]["agent_name"]
        enzyme_kappa_agent = self.agents[enzyme_agent["uniprotid"]][
            "agent_name"] if enzyme_agent else None

        def _generate_substrate(data, variant, flip=False):

            def flip_value(value):
                if value == "on":
                    return "off"
                else:
                    return "on"

            folded_target_states = dict()
            for _, site, value in target_states:
                folded_target_states[site] = value

            return (
                "{}({})".format(
                    substrate_kappa_agent,
                    ",".join(
                        (["variant{{{}}}".format(variant)]
                         if variant else []) +
                        data[0] +
                        list(actor_sites["substrate"]) +
                        [
                            "{}{{{}}}".format(
                                site,
                                flip_value(value) if flip else value)
                            for site, value in folded_target_states.items()
                        ]
                    )
                )
            )

        for substrate, substrate_data in folded_substrate.items():
            substrate_variant = substrate if substrate_variant_dep else None
            substrate_lhs_str = _generate_substrate(
                substrate_data, substrate_variant, flip=True)
            substrate_rhs_str = _generate_substrate(
                substrate_data, substrate_variant, flip=False)

            def _compose_rule(enzyme_str, bound_conditions):
                if enzyme_str is None:
                    enzyme_str = ""
                lhs = (
                    enzyme_str +
                    (", " if enzyme_str else "") +
                    substrate_lhs_str +
                    (", " if len(bound_conditions) > 0 else "") +
                    bound_conditions
                )

                rhs = (
                    enzyme_str +
                    (", " if enzyme_str else "") +
                    substrate_rhs_str +
                    (", " if len(bound_conditions) > 0 else "") +
                    bound_conditions
                )

                return lhs + " -> " + rhs

            if enzyme_agent and not self_modification:
                for enzyme, enzyme_data in folded_enzyme.items():
                    enzyme_variant = enzyme if enzyme_variant_dep else None
                    enzyme_str = "{}({})".format(
                        enzyme_kappa_agent,
                        ",".join(
                            (["variant{{{}}}".format(enzyme_variant)]
                             if enzyme_variant else []) +
                            enzyme_data[0] +
                            list(actor_sites["enzyme"])
                        )
                    )
                    rule = _compose_rule(enzyme_str, bound_conditions)
                    rules.append(rule)
            else:
                rule = _compose_rule(None, bound_conditions)
                rules.append(rule)
        return rules, rate

    def _generate_bnd_rules(self, nugget_identifier, ag_typing,
                            template_rel):
        """Generate binding rules.

        Parameters
        ----------
        nugget_identifier : EntityIdentifier
            Identifier of entities in the input nugget graph
        ag_typing : dict
            Dictinary with nugget typing by the action graph
        template_rel : dict
            Dictionary with binding template relation
            specifying the roles of nodes in the nugget

        For every nugget a set of corresponding Kappa rules
        is generated. If an agent of some binding has multiple variants
        we proceed as follows:
        - if the interaction described by the nugget is
        realizable by all the agent variants, we write a generic
        variant-state-independent rule;
        - otherwise we generate a rule for every combination of 'valid'
        variants. However, in this case generation of combinations
        of agent variants mentioned in 'is bound' conditions is
        currently not implemented (only generic agents are allowed
        in is bound conditions).
        """
        rules = []

        # Retreive information on the binding node
        bnd_node = list(template_rel["bnd"])[0]
        ag_bnd_node = ag_typing[bnd_node]
        bnd_attrs = nugget_identifier.graph.get_node(bnd_node)
        bnd_flag = True
        if "test" in bnd_attrs:
            bnd_flag = list(bnd_attrs["test"])[0]
        rate = None
        if "rate" in bnd_attrs:
            rate = list(bnd_attrs["rate"])[0]

        # Proccess left and right partners of binding:
        # - Find their UniProt AC, valid variants
        # - States and the bnd site per variant
        left_agent = self._retreive_actor_data(
            nugget_identifier, ag_typing,
            template_rel["left_partner"], template_rel,
            bnd_node=bnd_node, bnd_role="left")

        right_agent = self._retreive_actor_data(
            nugget_identifier, ag_typing,
            template_rel["right_partner"], template_rel,
            bnd_node=bnd_node, bnd_role="right")

        # Fold left and right to variant independent actors
        # to optimize the number of generated ruls
        left_variant_dep, folded_left = self._fold_agent(left_agent)
        right_variant_dep, folded_right = self._fold_agent(right_agent)

        # Generate all 'is bound' conditions
        bound_conditions, actor_sites =\
            self._generate_bound_conditions(
                nugget_identifier, ag_typing,
                {
                    "left": list(template_rel["left_partner"]),
                    "right": list(template_rel["right_partner"])
                },
                starting_bnd_index=2
            )

        # Generate rule strings
        left_kappa_agent = self.agents[
            left_agent["uniprotid"]]["agent_name"]
        right_kappa_agent = self.agents[
            right_agent["uniprotid"]]["agent_name"]

        def _generate_side(left_data, right_data, left_variant,
                           right_variant, bnd_symbol="."):
            return (
                "{}({}), {}({}){}".format(
                    left_kappa_agent,
                    ",".join(
                        (["variant{{{}}}".format(left_variant)]
                         if left_variant else []) +
                        left_data[0] +
                        [
                            "{}[{}]".format(left_data[1], bnd_symbol)
                        ] +
                        list(actor_sites["left"])
                    ),
                    right_kappa_agent,
                    ",".join(
                        (["variant{{{}}}".format(right_variant)]
                         if right_variant else []) +
                        right_data[0] +
                        [
                            "{}[{}]".format(right_data[1], bnd_symbol)
                        ] +
                        list(actor_sites["right"])
                    ),
                    (", " if len(bound_conditions) > 0 else "") +
                    bound_conditions
                )
            )

        for left, left_data in folded_left.items():
            for right, right_data in folded_right.items():
                left_variant = left if left_variant_dep else None
                right_variant = right if right_variant_dep else None
                lhs = _generate_side(
                    left_data, right_data, left_variant, right_variant,
                    bnd_symbol="." if bnd_flag else "1")
                rhs = _generate_side(
                    left_data, right_data, left_variant, right_variant,
                    bnd_symbol="1" if bnd_flag else ".")
                rules.append("{} -> {}".format(lhs, rhs))

        return rules, rate, bnd_flag

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
            rules = []
            rate = None
            rule = None
            rate = None
            if "mod_template" in relations:
                pass
                template_rel = self.kb._hierarchy.get_relation(
                    "mod_template", n)
                # Generate rules from the nugget
                rules, rate = self._generate_mod_rules(
                    nugget_identifier, ag_typing, template_rel)
                if rate is None:
                    rate = "'default_mod_rate'"
            elif "bnd_template" in relations:
                template_rel = self.kb._hierarchy.get_relation(
                    "bnd_template", n)
                # Generate rules from the nugget
                rules, rate, bnd_flag =\
                    self._generate_bnd_rules(
                        nugget_identifier, ag_typing, template_rel)
                if rate is None:
                    if bnd_flag:
                        rate = "'default_bnd_rate'"
                    else:
                        rate = "'default_brk_rate'"
            self.rules[n]["rules"] = rules
            self.rules[n]["rate"] = rate

    def generate_initial_conditions(self, concentrations, default_concentation):
        """Generate Kappa initial conditions.

        Parameters
        ----------
        concentrations : iterable of KappaInitialCondition
            Collection of initial conditions for different agens
        default_concentation : int
            Default concentration to use (# of molecules)

        The generated initial conditions are added to the `agents`
        dictionary of the generator for each agent variant. These
        initial conditions are divided into two kinds: canonical and
        non-canonical. Canonical conditions specify the molecular
        count of agents without any PTMs or present bonds, while
        non-canonical ones specify such counts for agents with PTMs
        and bonds, for example, phosphorylated EGFR or EGFR bound to
        EGF.

        """
        def _retreive_states_and_bonds(state_nodes, comp, n, variant=None):
            """Find PTMs and bound corresponding to the input component."""
            skip = False
            if isinstance(comp, State):
                for s_node, site_name in state_nodes.items():
                    state_attrs = self.identifier.graph.get_node(s_node)
                    s_name = list(state_attrs["name"])[0]
                    if comp.name == s_name:
                        condition_dict["states"][
                            site_name] = "on" if comp.test else "off"
            elif isinstance(comp, Residue):
                skip = _retreive_states_and_bonds(state_nodes, comp.state, n)
            elif isinstance(comp, Site):
                for residue in comp.residues:
                    skip = _retreive_states_and_bonds(state_nodes, residue, n)
                    if skip:
                        break
                if not skip:
                    for state in comp.states:
                        skip = _retreive_states_and_bonds(
                            state_nodes, state, n)
                        if skip:
                            break
                if not skip:
                    for bound in comp.bound_to:
                        site_node = self.identifier.identify_site(
                            comp, protein_node)
                        generic_sites = self.agents[protoform][
                            "kami_bnd_sites"]
                        bnd_dict = dict()
                        for (other_site_node, bnd_node), data in generic_sites.items():
                            if other_site_node == site_node:
                                bnd_dict[bnd_node] = data
                        if len(bnd_dict) > 0:
                            skip = _retreive_bonds(bnd_dict, bound, n)
                            if skip:
                                break
                        else:
                            warnings.warn(
                                "No binding actions with the "
                                "specified actor found!",
                                KappaGenerationWarning)
                            skip = True
                        if skip:
                            break
            elif isinstance(comp, Region):
                for site in comp.sites:
                    skip = _retreive_states_and_bonds(state_nodes, site, n)
                if not skip:
                    for residue in comp.residues:
                        skip = _retreive_states_and_bonds(
                            state_nodes, residue, n)
                        if skip:
                            break
                if not skip:
                    for state in comp.states:
                        skip = _retreive_states_and_bonds(
                            state_nodes, state, n)
                        if skip:
                            break
                if not skip:
                    for bound in comp.bound_to:
                        region_node = self.identifier.identify_region(
                            comp, protein_node)
                        generic_regions = self.agents[protoform][
                            "region_bnd_sites"]
                        bnd_dict = {}
                        for (other_region_node, bnd_node), data in generic_regions.items():
                            if other_region_node == region_node:
                                bnd_dict[bnd_node] = data
                        if len(bnd_dict) > 0:
                            skip = _retreive_bonds(bnd_dict, bound, n)
                            if skip:
                                break
                        else:
                            warnings.warn(
                                "No binding actions with the specified actor found!",
                                KappaGenerationWarning)
                            skip = True
                        if skip:
                            break
            return skip

        def _retreive_bonds(bnd_dict, comp, n, bnd_mechanism=None):
            skip = False
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

            if isinstance(comp, Protein):
                candidate_bnds = set()
                for bnd_node, site_name in bnd_dict.items():
                    if self.identifier.graph.exists_edge(partner_id, bnd_node):
                        candidate_bnds.add(bnd_node)
                if len(candidate_bnds) == 1:
                    bnd_node = list(candidate_bnds)[0]
                    # Find the site of the partner
                    partner_site_name = self.agents[partner_uniprot][
                        "direct_bnd_sites"][bnd_node]
                    condition_dict["bonds"][site_name] = (
                        partner_site_name,
                        self.agents[partner_uniprot]["agent_name"]
                    )
                elif len(candidate_bnds) > 1:
                    if bnd_mechanism in candidate_bnds:
                        # Find the site of the partner
                        partner_site_name = self.agents[partner_uniprot][
                            "direct_bnd_sites"][bnd_mechanism]
                        condition_dict["bonds"][site_name] = (
                            partner_site_name,
                            self.agents[partner_uniprot]["agent_name"]
                        )
                    else:
                        warnings.warn(
                            "Multiple binding mechanisms found: "
                            "BND node id should be specified",
                            KappaGenerationWarning)
                        skip = True
                else:
                    warnings.warn(
                        "No binding mechanisms found",
                        KappaGenerationWarning)
                    skip = True
            elif isinstance(comp, RegionActor):
                candidate_bnds = set()
                for bnd_node, site_name in bnd_dict.items():
                    partner_region_id = self.identifier.identify_region(
                        comp.region, partner_id)
                    if self.identifier.graph.exists_edge(partner_region_id, bnd_node):
                        candidate_bnds.add(bnd_node)
                if len(candidate_bnds) == 1:
                    # Find the site of the partner
                    generic_region_bnd_sites =\
                        self.agents[partner_uniprot][
                            "region_bnd_sites"]

                    partner_site_name = None
                    for (region_id, bnd_id) in generic_region_bnd_sites:
                        if region_id == partner_region_id:
                            partner_site_name = generic_region_bnd_sites[
                                (region_id, bnd_id)]

                    if partner_site_name:
                        condition_dict["bonds"][
                            site_name] = (
                            partner_site_name,
                            self.agents[partner_uniprot]["agent_name"]
                        )
                    else:
                        warnings.warn(
                            "Region was not identified", KappaGenerationWarning)
                        skip = True
                elif len(candidate_bnds) > 1:
                    if bnd_mechanism in candidate_bnds:
                        # Find the site of the partner
                        partner_site_name = self.agents[partner_uniprot][
                            "direct_bnd_sites"][bnd_mechanism]
                        condition_dict["bonds"][
                            site_name] = (
                            partner_site_name,
                            self.agents[partner_uniprot]["agent_name"]
                        )
                    else:
                        warnings.warn(
                            "Multiple binding mechanisms found: "
                            "BND node id should be specified",
                            KappaGenerationWarning)
                        skip = True
                else:
                    warnings.warn(
                        "No binding mechanisms found",
                        KappaGenerationWarning)
                    skip = True
            elif isinstance(comp, SiteActor):
                candidate_bnds = set()
                for bnd_node, site_name in bnd_dict.items():
                    partner_site_id = self.identifier.identify_site(
                        comp.site, partner_id)
                    if self.identifier.graph.exists_edge(
                            partner_site_id, bnd_node):
                        candidate_bnds.add(bnd_node)
                if len(candidate_bnds) == 1:
                    # Find the site of the partner
                    generic_kami_bnd_sites =\
                        self.agents[partner_uniprot]["kami_bnd_sites"]

                    partner_site_name = None
                    for (site_id, bnd_id) in generic_kami_bnd_sites:
                        if site_id == partner_site_id:
                            partner_site_name = generic_kami_bnd_sites[
                                (site_id, bnd_id)]

                    if partner_site_name:
                        condition_dict["bonds"][
                            site_name] = (
                            partner_site_name,
                            self.agents[partner_uniprot]["agent_name"],
                        )
                    else:
                        warnings.warn(
                            "Site was not identified", KappaGenerationWarning)
                        skip = True
                elif len(candidate_bnds) > 1:
                    if bnd_mechanism in candidate_bnds:
                        # Find the site of the partner
                        partner_site_name = self.agents[partner_uniprot][
                            "direct_bnd_sites"][bnd_mechanism]
                        condition_dict["bonds"][
                            site_name] = (
                            partner_site_name,
                            self.agents[partner_uniprot]["agent_name"]
                        )
                    else:
                        warnings.warn(
                            "Multiple binding mechanisms found: "
                            "BND node id should be specified",
                            KappaGenerationWarning)
                        skip = True
                else:
                    warnings.warn(
                        "No binding mechanisms found",
                        KappaGenerationWarning)
                    skip = True
            return skip

        if len(concentrations) > 0:
            for condition in concentrations:
                # Identify the node in the action graph corresponding
                # to the protein from the concentration
                protoform =\
                    condition.canonical_protein.protoform.uniprotid
                protein_node = self.identifier.identify_protein(
                    condition.canonical_protein)
                if protein_node is None:
                    protein_node = self.identifier.identify_gene(
                        condition.canonical_protein.protoform)

                agent_dict = None
                generic_stateful_sites = self.agents[
                    protoform]["stateful_sites"]

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
                            "Variant '{}' is not present in ".format(variant) +
                            "the signature of '{}', ".format(
                                self.agents[protoform]["agent_name"]) +
                            "generating initial condition for a default agent",
                            KappaGenerationWarning)
                else:
                    variant = list(
                        self.agents[protoform]["variants"].keys())[0]
                    self.agents[protoform]["variants"][
                        variant]["initial_conditions"] = {}
                    self.agents[protoform]["variants"][variant][
                        "initial_conditions"][
                            "canonical"] = condition.canonical_count

                    agent_dict = self.agents[protoform][
                        "variants"][variant]

                # Add non-canonical initial condititions
                if agent_dict:
                    agent_dict["initial_conditions"]["non_canonical"] = []
                    # Add counts of stateful agents
                    for component, count in condition.stateful_components:
                        condition_dict = {
                            "states": {},
                            "bonds": {},
                            "count": count
                        }
                        state_nodes = dict()
                        # state_nodes.update(agent_dict["stateful_sites"])
                        state_nodes.update(generic_stateful_sites)
                        skip = _retreive_states_and_bonds(
                            state_nodes, component, count, variant)
                        if not skip:
                            agent_dict["initial_conditions"][
                                "non_canonical"].append(condition_dict)

                    # Add bound initial conditions
                    for element in condition.bonds:
                        bnd_mechanism = None
                        try:
                            component, count, bnd_mechanism = element
                        except:
                            component, count = element

                        condition_dict = {
                            "bonds": {},
                            "count": count
                        }
                        skip = _retreive_bonds(
                            self.agents[protoform]["direct_bnd_sites"],
                            component, count,
                            bnd_mechanism)
                        if not skip:
                            agent_dict["initial_conditions"][
                                "non_canonical"].append(condition_dict)

    def generate(self, concentrations=None, default_concentration=100):
        """Generate a Kappa script.

        Parameters
        ----------
        concentrations : iterable of KappaInitialCondition
            Collection of initial conditions
        default_concentration : int
            Constant used as the default concentration

        Returns
        -------
        kappa : str
            Generated Kappa script

        """
        self.generate_agents()
        self.generate_rules()

        if concentrations is None:
            concentrations = []

        self.generate_initial_conditions(concentrations, default_concentration)

        header = "// Automatically generated from the KAMI {} '{}' {}\n\n".format(
            self.kb_type, self.kb._id,
            datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

        initial_conditions = ""
        signatures = "// Signatures\n\n"
        for agent_uniprot, agent_data in self.agents.items():
            agent_signature = []
            concentrations_str = []

            # Generate variant states
            if len(agent_data["variants"]) > 1:
                agent_signature.append("variant{{{}}}".format(
                    " ".join(v for v in agent_data["variants"].keys())))

            # Generate generic stateful sites
            if len(agent_data["stateful_sites"]) > 0:
                agent_signature.append(", ".join([
                    "{}{{off on}}".format(v)
                    for v in set(agent_data["stateful_sites"].values())
                ]))

            # Generate generic bnd sites
            all_sites = set(
                v for v in list(
                    agent_data["direct_bnd_sites"].values()) +
                list(agent_data["kami_bnd_sites"].values()) +
                list(agent_data["region_bnd_sites"].values())
            )

            # Generate varian-specific stateful and bnd sites
            for variant, variant_data in agent_data["variants"].items():
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
        if (self.default_bnd_rate or self.default_brk_rate or self.default_mod_rate):
            variables = "\n// variables \n\n"

        if self.default_bnd_rate:
            variables += "%var: 'default_bnd_rate' {}\n".format(
                self.default_bnd_rate)
        if self.default_brk_rate:
            variables += "%var: 'default_brk_rate' {}\n".format(
                self.default_brk_rate)
        if self.default_mod_rate:
            variables += "%var: 'default_mod_rate' {}\n".format(
                self.default_mod_rate)

        initial_conditions = (
            ("// Initial conditions\n\n" +
             initial_conditions)
            if len(initial_conditions) > 0
            else initial_conditions
        )
        result = header + signatures + rule_repr + variables + initial_conditions
        return result


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

    def _get_variants(self, nugget_identifier, agent_node,
                      agent_uniprotid, ag_node, ag_typing):
        return [self._get_variant_name(ag_node, agent_uniprotid)]

    def _get_variant_name(self, ag_node, uniprotid):
        for variant, variant_data in self.agents[
                uniprotid]["variants"].items():
            if "ref_node" in variant_data:
                if variant_data["ref_node"] == ag_node:
                    return variant

    def _generate_stateful_sites(self, protoform):
        variants = self.agents[protoform]["variants"]
        existing_stateful_sites =\
            self.agents[protoform]["stateful_sites"].values()
        if self.kb._component_equivalence:
            # Get all the states attached to all the variants
            all_states = set()
            for var_name, var_data in variants.items():
                states = self.identifier.get_attached_states(
                    var_data["ref_node"])
                all_states.update(states)
            # Find equivalence classes of states, these classes are used
            # as generic states for Kappa agents
            generic_states = dict()
            for state in all_states:
                if state in self.kb._component_equivalence:
                    original_state = self.kb._component_equivalence[state]
                    if original_state in generic_states:
                        generic_states[original_state].append(state)
                    else:
                        generic_states[original_state] = [state]

            if len(generic_states) == 0:
                # The states are not in the _component_equivalence
                # provided by the model we generate a site
                # per state node in the model
                for state in all_states:
                    self.agents[protoform][
                        "stateful_sites"][state] = self._generate_site_name(
                            state, "", existing_stateful_sites,
                            name_from_attrs=True,
                            attrs_key="name")
            else:
                # Generate a site per generic state
                for state, state_nodes in generic_states.items():
                    site_name = self._generate_site_name(
                        state_nodes[0], "", existing_stateful_sites,
                        name_from_attrs=True,
                        attrs_key="name")
                    for state_node in state_nodes:
                        self.agents[protoform][
                            "stateful_sites"][state_node] = site_name
        else:
            for var_name, var_data in variants.items():
                var_prefix = None
                if len(variants) > 1:
                    var_prefix = var_name
                states = self.identifier.get_attached_states(
                    var_data["ref_node"])
                for state in states:
                    self.agents[protoform]["stateful_sites"][
                        state] = self._generate_site_name(
                            state, "", existing_stateful_sites,
                            name_from_attrs=True,
                            attrs_key="name", variant_name=var_prefix)

    def _generate_kami_bnd_sites(self, protoform):
        """Generate binding sites for KAMI site nodes."""
        existing_elements = self.agents[protoform]["kami_bnd_sites"].values()
        if self.kb._component_equivalence:
            # Get all the sites attached to all the variants
            all_sites = set()
            for variant_name, variant_data in self.agents[protoform][
                    "variants"].items():
                sites = self.identifier.get_attached_sites(variant_data[
                    "ref_node"])
                all_sites.update(sites)

            # Find equivalence classes of sites, these classes are used
            # as generic sites for Kappa agents
            generic_sites = dict()
            for site in all_sites:
                if site in self.kb._component_equivalence:
                    original_site = self.kb._component_equivalence[site]
                    if original_site in generic_sites:
                        generic_sites[original_site].append(site)
                    else:
                        generic_sites[original_site] = [site]
            if len(generic_sites) == 0:
                # The sites are not in the _component_equivalence
                # provided by the model we generate a site
                # per site node in the model
                for s in all_sites:
                    bnds = self._generate_bnds(s)
                    site_name = self._generate_site_name(
                        s, "site", existing_elements,
                        True, "name")
                    new_sites = set()
                    for bnd in bnds:
                        name = generate_new_element_id(new_sites, site_name)
                        new_sites.add(name)
                        self.agents[protoform]["kami_bnd_sites"][
                            (s, bnd)] = name
            else:
                # Generate site per bnd action attached to generic site
                for site, site_nodes in generic_sites.items():
                    bnds = self._generate_bnds(site_nodes[0])
                    site_name = self._generate_site_name(
                        site_nodes[0], "site", existing_elements,
                        True, "name")
                    new_sites = set()
                    for bnd in bnds:
                        name = generate_new_element_id(new_sites, site_name)
                        new_sites.add(name)
                        for s in site_nodes:
                            self.agents[protoform]["kami_bnd_sites"][
                                (s, bnd)] = name
        else:
            for variant_name, variant_data in self.agents[protoform][
                    "variants"].items():
                sites = self.identifier.get_attached_sites(variant_data[
                    "ref_node"])

                for s in sites:
                    bnds = self._generate_bnds(s)
                    site_name = self._generate_site_name(
                        s, "site", existing_elements,
                        True, "name", variant_name)
                    new_sites = set()
                    for bnd in bnds:
                        name = generate_new_element_id(new_sites, site_name)
                        new_sites.add(name)
                        self.agents[protoform]["kami_bnd_sites"][
                            (s, bnd)] = name

    def _generate_region_bnd_sites(self, protoform):
        """Generate binding sites for region nodes attached to BND."""
        existing_elements = self.agents[
            protoform]["region_bnd_sites"].values()
        if self.kb._component_equivalence:
            # Get all the regions attached to all the variants
            all_regions = set()
            for variant_name, variant_data in self.agents[
                    protoform]["variants"].items():
                regions = self.identifier.get_attached_regions(variant_data[
                    "ref_node"])
                all_regions.update(regions)

            # Find equivalence classes of regions, these classes are used
            # as generic regions for Kappa agents
            generic_regions = dict()
            for region in all_regions:
                if region in self.kb._component_equivalence:
                    original_region = self.kb._component_equivalence[region]
                    if original_region in generic_regions:
                        generic_regions[original_region].append(region)
                    else:
                        generic_regions[original_region] = [region]
            # Generate site per bnd action attached to generic region
            if len(generic_regions) == 0:
                # The regions are not in the _component_equivalence
                # provided by the model we generate a site
                # per region node in the model
                for r in all_regions:
                    bnds = self._generate_bnds(r)
                    region_name = self._generate_site_name(
                        r, "region", existing_elements,
                        True, "name")
                    new_regions = set()
                    for bnd in bnds:
                        name = generate_new_element_id(new_regions, region_name)
                        new_regions.add(name)
                        self.agents[protoform]["region_bnd_sites"][
                            (r, bnd)] = name
            else:
                # Generate site per bnd action attached to generic region
                for region, region_nodes in generic_regions.items():
                    bnds = self._generate_bnds(region_nodes[0])
                    region_name = self._generate_site_name(
                        region_nodes[0], "region", existing_elements,
                        True, "name")
                    new_regions = set()
                    for bnd in bnds:
                        name = generate_new_element_id(new_regions, region_name)
                        new_regions.add(name)
                        for r in region_nodes:
                            self.agents[protoform]["region_bnd_sites"][
                                (r, bnd)] = name
        else:
            for variant_name, variant_data in self.agents[protoform][
                    "variants"].items():
                regions = self.identifier.get_attached_regions(variant_data[
                    "ref_node"])
                for r in regions:
                    bnds = self._generate_bnds(r)
                    region_name = self._generate_site_name(
                        r, "region", existing_elements,
                        True, "name", variant_name)
                    new_regions = set()
                    for bnd in bnds:
                        name = generate_new_element_id(new_regions, region_name)
                        new_regions.add(name)
                        self.agents[protoform]["region_bnd_sites"][
                            (r, bnd)] = name

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
    """Kappa generator from KAMI corpora and definitions.

    Attributes
    ----------
    instantiation_rules : iterable of tuples
        Collection of instantiation rules and their intances
        in the action graph of the underlying corpus

    """

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

    def _get_variants(self, nugget_identifier, agent_node,
                      agent_uniprotid, ag_node, ag_typing):
        return self._valid_agent_variants(
            nugget_identifier, agent_node,
            agent_uniprotid, ag_node, ag_typing)

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
                aa = list(res_attrs["aa"])[0]
                test = list(res_attrs["test"])[0]

                if test:
                    variants_with_aa =\
                        self._find_variants_with_key_residue(
                            rule, instance,
                            ag_node, agent_variants,
                            ag_typing[r], aa)
                    for v in agent_variants:
                        if v not in variants_with_aa:
                            invalid_variants.add(v)

        return agent_variants.difference(invalid_variants)

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
                "stateful_sites"].values()
            self.agents[protoform]["stateful_sites"][state] =\
                self._generate_site_name(
                    state, "", existing_elements, True, "name")

    def _generate_kami_bnd_sites(self, protoform):
        ref_node = self.agents[protoform]["ref_node"]
        sites = self.identifier.get_attached_sites(ref_node)

        for s in sites:
            existing_elements = self.agents[protoform][
                "kami_bnd_sites"].values()
            site_name = self._generate_site_name(
                s, "site", existing_elements, True, "name")
            bnds = self._generate_bnds(s)
            new_sites = set()
            for bnd in bnds:
                name = generate_new_element_id(new_sites, site_name)
                new_sites.add(name)
                self.agents[protoform]["kami_bnd_sites"][(s, bnd)] = name

    def _generate_region_bnd_sites(self, protoform):
        ref_node = self.agents[protoform]["ref_node"]
        regions = self.identifier.get_attached_regions(ref_node)
        existing_elements = self.agents[protoform][
            "region_bnd_sites"].values()
        for r in regions:
            site_name = self._generate_site_name(
                r, "region", existing_elements, True, "name")
            bnds = self._generate_bnds(r)
            new_sites = set()
            for bnd in bnds:
                name = generate_new_element_id(new_sites, site_name)
                new_sites.add(name)
                self.agents[protoform]["region_bnd_sites"][(r, bnd)] = name

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
