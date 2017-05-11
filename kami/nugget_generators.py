"""Collection of nugget generators."""
import warnings
import networkx as nx

from regraph.primitives import (add_node,
                                add_edge,
                                remove_edge,
                                print_graph)

from kami.data_structures.entities import (State, Residue,
                                           PhysicalRegion,
                                           PhysicalAgent,
                                           PhysicalRegionAgent)

from kami.exceptions import KamiError, NuggetGenerationError

from kami.utils.id_generators import (get_nugget_agent_id,
                                      get_nugget_region_id,
                                      get_nugget_residue_id,
                                      get_nugget_state_id,
                                      get_nugget_is_bnd_id,
                                      get_nugget_locus_id,
                                      get_nugget_is_free_id,
                                      get_nugget_bnd_id)


class NuggetGenerator(object):
    """Abstract class for nugget generator."""

    def _check_existance(self, node_id):
        if node_id not in self.nugget.nodes():
            raise NuggetGenerationError(
                "Node with id '%s' does not exist in the nugget!" %
                node_id
            )

    def _check_node_type_memeber(self, node_id, type_list):
        if self.meta_typing[node_id] not in type_list:
            raise NuggetGenerationError(
                "Nugget modificaiton error: expected  node '%s' "
                "to be of types '[%s]', '%s' was provided!" %
                (node_id, ", ".join(type_list), self.meta_typing[node_id])
            )

    def _check_node_type(self, node_id, type_id):
        self._check_node_type_memeber(node_id, [type_id])

    def _generate_state(self, state, prefix=""):
        state_id = get_nugget_state_id(self.nugget, state, prefix)
        add_node(self.nugget, state_id, state.to_attrs())
        self.meta_typing[state_id] = "state"
        return state_id

    def _generate_residue(self, residue, prefix="", show_state=False):
        residue_id = get_nugget_residue_id(self.nugget, residue, prefix)
        add_node(self.nugget, residue_id, residue.to_attrs())
        self.meta_typing[residue_id] = "residue"

        state_id = None
        if residue.state:
            state_id = self._generate_state(residue.state, residue_id)
            add_edge(self.nugget, state_id, residue_id)

        return (residue_id, state_id)

    def _generate_bound(self, partners, prefix=""):
        is_bnd_ids = []
        partner_ids = []
        for partner in partners:
            if isinstance(partner, PhysicalAgent):
                partner_id = get_nugget_agent_id(self.nugget, partner.agent)
            elif isinstance(partner, PhysicalRegionAgent):
                partner_id = get_nugget_region_id(
                    self.nugget, str(partner.physical_region.region),
                    str(partner.physical_agent.agent)
                )

            partner_ids.append(partner_id)

            # print(partner_id)
            is_bnd_id = get_nugget_is_bnd_id(self.nugget, prefix, partner_id)
            add_node(
                self.nugget,
                is_bnd_id
            )
            self.meta_typing[is_bnd_id] = "is_bnd"
            is_bnd_ids.append(is_bnd_id)

            partner_locus_id = get_nugget_locus_id(self.nugget, partner_id, is_bnd_id)
            add_node(
                self.nugget,
                partner_locus_id
            )
            self.meta_typing[partner_locus_id] = "locus"

            if isinstance(partner, PhysicalAgent):
                partner_id = self._generate_agent_group(partner)
            elif isinstance(partner, PhysicalRegionAgent):
                (_, partner_id) = self._generate_agent_region_group(partner)
            else:
                raise NuggetGenerationError(
                    "Invalid type of binding partner: '%s'" % type(partner)
                )

            add_edge(self.nugget, partner_locus_id, is_bnd_id)
            add_edge(self.nugget, partner_id, partner_locus_id)

        bound_id = "%s_is_bnd_%s" % (prefix, "_".join(partner_ids))
        bound_locus_id = get_nugget_locus_id(self.nugget, prefix, bound_id)
        add_node(self.nugget, bound_locus_id)
        self.meta_typing[bound_locus_id] = "locus"
        for is_bnd_id in is_bnd_ids:
            add_edge(self.nugget, bound_locus_id, is_bnd_id)
        return bound_locus_id

    def _generate_region_group(self, region, prefix=""):
        # 1. create region node
        region_id = get_nugget_region_id(self.nugget, str(region.region), prefix)
        add_node(self.nugget, region_id, region.region.to_attrs())
        self.meta_typing[region_id] = "region"

        # 2. create and attach residues
        for residue in region.residues:
            (residue_id, _) = self._generate_residue(residue, region_id)
            add_edge(self.nugget, residue_id, region_id)

        # 3. create and attach states
        for state in region.states:
            state_id = self._generate_state(state, region_id)
            add_edge(self.nugget, state_id, region_id)

        # 4. create and attach bounds
        for partners in region.bounds:
            bound_locus_id = self._generate_bound(partners, region_id)
            add_edge(self.nugget, region_id, bound_locus_id)
        return region_id

    def _generate_agent_region_group(self, agent):
        agent_id = self._generate_agent_group(
            agent.physical_agent
        )
        region_id = self._generate_region_group(
            agent.physical_region, agent_id
        )
        add_edge(self.nugget, region_id, agent_id)
        return (agent_id, region_id)

    def _generate_agent_group(self, agent):
        # 1. create agent node
        agent_id = get_nugget_agent_id(self.nugget, agent.agent)
        add_node(
            self.nugget,
            agent_id,
            agent.agent.to_attrs()
        )
        self.meta_typing[agent_id] = "agent"
        # 2. create and attach regions
        for region in agent.regions:
            region_id = self._generate_region_group(region, agent_id)
            add_edge(self.nugget, region_id, agent_id)
        # 3. create and attach residues
        for residue in agent.residues:
            (residue_id, _) = self._generate_residue(residue, agent_id)
            add_edge(self.nugget, residue_id, agent_id)

        # 4. create and attach states
        for state in agent.states:
            state_id = self._generate_state(state, agent_id)
            add_edge(self.nugget, state_id, agent_id)

        # 5. create and attach bounds
        for bnd in agent.bounds:
            bound_locus_id = self._generate_bound(bnd, agent_id)
            add_edge(self.nugget, agent_id, bound_locus_id)

        return agent_id

    def add_residue_to_agent(self, agent_node_id, residue):
        """Add residue group to an agent in the nugget."""
        self._check_existance(agent_node_id)
        self._check_node_type(agent_node_id, "agent")

        res_id = get_nugget_residue_id(self.nugget, residue, agent_node_id)
        add_node(
            self.nugget,
            res_id,
            residue.to_attrs()
        )
        self.meta_typing[res_id] = "residue"

        add_edge(self.nugget, res_id, agent_node_id)

        state_id = None
        if residue.state:
            state_id = get_nugget_state_id(self.nugget, residue.state, res_id)
            add_node(
                self.nugget,
                state_id,
                residue.state.to_attrs()
            )
            self.meta_typing[state_id] = "state"
            add_edge(self.nugget, state_id, res_id)

        return (res_id, state_id)

    def add_state_to_agent(self, agent_node_id, state):
        """Add state to an agent in the nugget."""
        self._check_existance(agent_node_id)
        self._check_node_type(agent_node_id, "agent")

        state_id = get_nugget_state_id(self.nugget, state, agent_node_id)
        add_node(
            self.nugget,
            state_id,
            state.to_attrs()
        )
        self.meta_typing[state_id] = "state"
        add_edge(self.nugget, state_id, agent_node_id)
        return state_id

    def add_is_bnd_to_agent(self, agent_node_id, partner,
                            partner_res=None, partner_states=None):
        """Add is_bnd test to an agent."""
        self._check_existance(agent_node_id)
        self._check_node_type(agent_node_id, "agent")

        partner_id = get_nugget_agent_id(self.nugget, partner)
        add_node(
            self.nugget,
            partner_id,
            partner.to_attrs()
        )
        self.meta_typing[partner.uniprotid] = "agent"

        is_bnd_id = get_nugget_is_bnd_id(self.nugget, agent_node_id, partner_id)
        add_node(
            self.nugget,
            is_bnd_id
        )
        self.meta_typing[is_bnd_id] = "is_bnd"

        agent_locus_id = get_nugget_locus_id(self.nugget, agent_node_id, is_bnd_id)
        add_node(
            self.nugget,
            agent_locus_id
        )
        self.meta_typing[agent_locus_id] = "locus"

        partner_locus_id = get_nugget_locus_id(self.nugget, partner_id, is_bnd_id)
        add_node(
            self.nugget,
            partner_locus_id
        )
        self.meta_typing[partner_locus_id] = "locus"

        add_edge(self.nugget, agent_locus_id, is_bnd_id)
        add_edge(self.nugget, partner_locus_id, is_bnd_id)
        add_edge(self.nugget, agent_node_id, agent_locus_id)
        add_edge(self.nugget, partner_id, partner_locus_id)
        return (agent_locus_id, is_bnd_id, partner_locus_id, partner_id)

    def add_is_free_to_agent(self, agent_node_id, partner):
        """Add is_free test to an agent."""
        self._check_existance(agent_node_id)
        self._check_node_type(agent_node_id, "agent")

        partner_id = get_nugget_agent_id(self.nugget, partner)
        add_node(
            self.nugget,
            partner_id,
            partner.to_attrs()
        )
        self.meta_typing[partner_id] = "agent"

        is_free_id = get_nugget_is_free_id(self.nugget, agent_node_id, partner_id)
        add_node(
            self.nugget,
            is_free_id
        )
        self.meta_typing[is_free_id] = "is_free"

        agent_locus_id = get_nugget_locus_id(
            self.nugget,
            agent_node_id,
            is_free_id
        )
        add_node(self.nugget, agent_locus_id)
        self.meta_typing[agent_locus_id] = "locus"

        partner_locus_id = get_nugget_locus_id(
            self.nugget,
            partner_id,
            is_free_id
        )
        add_node(self.nugget, partner_locus_id)
        self.meta_typing[partner_locus_id] = "locus"

        add_edge(self.nugget, agent_locus_id, is_free_id)
        add_edge(self.nugget, partner_locus_id, is_free_id)
        add_edge(self.nugget, agent_node_id, agent_locus_id)
        add_edge(self.nugget, partner_id, partner_locus_id)
        return (agent_locus_id, is_free_id, partner_locus_id, partner_id)

    def add_region_to_agent(self, agent_node_id, region):
        """Add region to an agent node."""
        self._check_node_existance(agent_node_id)
        self._check_node_type(agent_node_id, "agent")

        region_id = get_nugget_region_id(
            self.nugget,
            region,
            agent_node_id
        )
        add_node(
            self.nugget,
            region_id,
            region.to_attrs()
        )
        self.meta_typing[region_id] = "region"
        self.add_edge(
            self.nugget,
            region_id,
            agent_node_id
        )
        return

    def insert_region(self, agent_id, element_id, region):
        """Insert region between agent and its structural elem."""
        self._check_existance(agent_id)
        self._check_existance(element_id)
        self._check_node_type(agent_id, "agent")
        self._check_node_type_memeber(element_id, ["residue", "state"])

        if (element_id, agent_id) not in self.nugget.edges():
            raise NuggetGenerationError(
                "Agent '%s' does not have structural element '%s'" %
                (agent_id, element_id)
            )
        remove_edge(self.nugget, element_id, agent_id)

        region_id = get_nugget_region_id(
            self.nugget,
            region,
            agent_id
        )
        add_node(
            self.nugget,
            region_id,
            region.to_attrs()
        )
        self.meta_typing[region_id] = "region"

        add_edge(self.nugget, element_id, region_id)
        add_edge(self.nugget, region_id, agent_id)

    def add_is_bnd_between(self, agent_1, agent_2):
        """Add is bnd condition between two nodes."""
        self._check_node_type_memeber(agent_1, ["agent", "region"])
        self._check_node_type_memeber(agent_2, ["agent", "region"])

        is_bnd_id = get_nugget_is_bnd_id(self.nugget, agent_1, agent_2)
        agent_1_locus = get_nugget_locus_id(self.nugget, agent_1, is_bnd_id)
        agent_2_locus = get_nugget_locus_id(self.nugget, agent_2, is_bnd_id)

        add_node(self.nugget, is_bnd_id)
        self.meta_typing[is_bnd_id] = "is_bnd"
        add_node(self.nugget, agent_1_locus)
        self.meta_typing[agent_1_locus] = "locus"
        add_node(self.nugget, agent_2_locus)
        self.meta_typing[agent_2_locus] = "locus"

        add_edge(self.nugget, agent_1_locus, is_bnd_id)
        add_edge(self.nugget, agent_2_locus, is_bnd_id)

        add_edge(self.nugget, agent_1, agent_1_locus)
        add_edge(self.nugget, agent_2, agent_2_locus)
        return


class ModGenerator(NuggetGenerator):
    """Generator class for modification nugget and its typing."""

    def __init__(self, enzyme, substrate, mod_target,
                 mod_value=True, annotation=None, direct=False):
        """Initialize generator object."""
        self.nugget = nx.DiGraph()
        self.meta_typing = dict()
        self.template_relation = set()

        if isinstance(enzyme, PhysicalAgent):
            self.enzyme = self._generate_agent_group(enzyme)
            self.enzyme_region = None
        elif isinstance(enzyme, PhysicalRegionAgent):
            (self.enzyme, self.enzyme_region) = self._generate_agent_region_group(
                enzyme
            )
        else:
            raise NuggetGenerationError(
                "Unkown type of an enzyme: '%s'" % type(enzyme)
            )

        self.template_relation.add((self.enzyme, "enzyme"))
        if self.enzyme_region:
            self.template_relation.add((self.enzyme_region, "enzyme_region"))

        if isinstance(substrate, PhysicalAgent):
            self.substrate = self._generate_agent_group(substrate)
            self.substrate_region = None
        elif isinstance(substrate, PhysicalRegionAgent):
            (self.substrate, self.substrate_region) = self._generate_agent_region_group(
                substrate
            )
        else:
            raise NuggetGenerationError(
                "Unkown type of a substrate: '%s'" % type(substrate)
            )

        self.template_relation.add((self.substrate, "substrate"))
        if self.substrate_region:
            self.template_relation.add((self.substrate_region, "substrate_region"))

        # 2. create mod node
        mod_attrs = {
            "value": mod_value,
            "direct": direct
        }
        if annotation:
            mod_attrs.update(annotation.to_attrs())
        add_node(self.nugget, "mod", mod_attrs)
        self.meta_typing["mod"] = "mod"
        self.template_relation.add(("mod", "mod"))

        # 3. create state related nodes subject to modification\
        if self.substrate_region:
            attached_to = self.substrate_region
        else:
            attached_to = self.substrate

        if isinstance(mod_target, State):
            mod_target.name
            if mod_target.value == mod_value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(mod_target, attached_to)
            add_edge(self.nugget, mod_state_id, attached_to)
            self.template_relation.add((mod_state_id, "mod_state"))
        elif isinstance(mod_target, Residue):
            if mod_target.state:
                if mod_target.state.value == mod_value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        UserWarning
                    )
                (residue_id, mod_state_id) = self._generate_residue(
                    mod_target,
                    attached_to
                )
                add_edge(self.nugget, residue_id, attached_to)
                self.template_relation.add((mod_state_id, "mod_state"))
                self.template_relation.add((residue_id, "mod_residue"))
            else:
                raise KamiError(
                    "Target of modification is required to be either "
                    "`State` or `Residue` with non-empty state: state "
                    "of residue is empty"
                )
        else:
            raise KamiError(
                "Target of modification is required to be either "
                "`State` or `Residue` with non-empty state: %s "
                "is provided" % type(mod_target)
            )

        add_edge(self.nugget, self.enzyme, "mod")
        add_edge(self.nugget, "mod", mod_state_id)
        return

    def add_enzyme_residue(self, residue):
        """Add residue mod conditions to enzyme."""
        self.add_residue_to_agent(self.enzyme, residue)
        return

    def add_enzyme_state(self, state):
        """Add state mod conditions to enzyme."""
        self.add_state_to_agent(self.enzyme, state)
        return

    def add_substrate_residue(self, residue):
        """Add residue mod conditions to enzyme."""
        self.add_residue_to_agent(self.substrate, residue)
        return

    def add_substrate_state(self, state):
        """Add state mod conditions to enzyme."""
        self.add_state_to_agent(self.substrate, state)
        return

    def add_enzyme_is_bnd(self, partner_agent):
        """Add binding mod conditions to enzyme."""
        self.add_is_bnd_to_agent(self.enzyme, partner_agent)
        return

    def add_enzyme_is_free(self, partner_agent):
        """Add free of binding mod conditions to enzyme."""
        self.add_is_free_to_agent(self.enzyme, partner_agent)
        return

    def add_substrate_is_bnd(self, partner_agent):
        """Add binding mod conditions to substrate."""
        self.add_is_bnd_to_agent(self.substrate, partner_agent)
        return

    def add_substrate_is_free(self, partner_agent):
        """Add free of binding mod conditions to enzyme."""
        self.add_is_free_to_agent(self.substrate, partner_agent)


class AutoModGenerator(ModGenerator):
    """Generator class for automodification nuggets."""

    def __init__(self, enzyme_agent, mod_target, mod_value=True,
                 enz_region=None, sub_region=None, annotation=None,
                 direct=False):
        """Initialize generator object."""
        if not isinstance(enzyme_agent, PhysicalAgent):
            raise NuggetGenerationError(
                "Automodification parameter 'enzyme_agent' "
                "should be an instance of 'PhysicalAgent', "
                "'%s' provided!" % type(enzyme_agent)
            )

        self.nugget = nx.DiGraph()
        self.meta_typing = dict()
        self.template_relation = set()

        self.enzyme = self._generate_agent_group(enzyme_agent)

        self.template_relation.add((self.enzyme, "enzyme"))
        self.substrate = self.enzyme
        self.template_relation.add((self.enzyme, "substrate"))

        # 2. create enzymatic/substratic regions
        self.enzyme_region = None
        if enz_region:
            self.enzyme_region = self._generate_region_group(
                enz_region, self.enzyme
            )
            add_edge(self.nugget, self.enzyme_region, self.enzyme)
            self.template_relation.add((self.enzyme_region, "enzyme_region"))

        self.substrate_region = None
        if sub_region:
            self.substrate_region = self._generate_region_group(
                sub_region, self.enzyme
            )
            add_edge(self.nugget, self.substrate_region, self.enzyme)
            self.template_relation.add((self.substrate_region, "substrate_region"))

        # 3. create mod node
        mod_attrs = {
            "value": mod_value,
            "direct": direct
        }
        if annotation:
            mod_attrs.update(annotation.to_attrs())
        add_node(self.nugget, "mod", mod_attrs)
        self.meta_typing["mod"] = "mod"
        self.template_relation.add(("mod", "mod"))

        if self.enzyme_region:
            add_edge(self.nugget, self.enzyme_region, "mod")
        else:
            add_edge(self.nugget, self.enzyme, "mod")

        # 4. create state related nodes subject to modification
        if self.substrate_region:
            attached_to = self.substrate_region
        else:
            attached_to = self.substrate

        if isinstance(mod_target, State):
            mod_target.name
            if mod_target.value == mod_value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(mod_target, attached_to)
            self.template_relation.add((mod_state_id, "mod_state"))
            add_edge(self.nugget, mod_state_id, attached_to)

        elif isinstance(mod_target, Residue):
            if mod_target.state:
                if mod_target.state.value == mod_value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        UserWarning
                    )
                (residue_id, mod_state_id) = self._generate_residue(
                    mod_target,
                    attached_to
                )
                self.template_relation.add((mod_state_id, "mod_state"))
                self.template_relation.add((residue_id, "mod_residue"))
                add_edge(self.nugget, residue_id, attached_to)
            else:
                raise KamiError(
                    "Target of modification is required to be either "
                    "`State` or `Residue` with non-empty state: state "
                    "of residue is empty"
                )
        else:
            raise KamiError(
                "Target of modification is required to be either "
                "`State` or `Residue` with non-empty state: %s "
                "is provided" % type(mod_target)
            )
        add_edge(self.nugget, "mod", mod_state_id)
        return


class TransModGenerator(ModGenerator):
    """Generator class for transmodification nugget."""

    def __init__(self, enzyme, substrate, mod_target, mod_value=True,
                 annotation=None, direct=False):
        """Initialize generator object."""
        ModGenerator.__init__(
            self, enzyme, substrate, mod_target, mod_value,
            annotation, direct
        )

        if self.enzyme_region:
            enzyme_actor = self.enzyme_region
        else:
            enzyme_actor = self.enzyme

        if self.substrate_region:
            substrate_actor = self.substrate_region
        else:
            substrate_actor = self.substrate

        self.add_is_bnd_between(enzyme_actor, substrate_actor)
        return


class AnonymousModGenerator(ModGenerator):
    """Generator class for anonymous modification nugget."""

    def __init__(self, substrate_agent, mod_target, mod_value,
                 annotation=None, direct=False):
        """Initialize generator object."""
        self.nugget = nx.DiGraph()
        self.meta_typing = dict()
        self.template_relation = set()

        if isinstance(substrate_agent, PhysicalAgent):
            self.substrate = self._generate_agent_group(substrate_agent)
            self.substrate_region = None
            self.template_relation.add((self.substrate, "substrate"))

        elif isinstance(substrate_agent, PhysicalRegionAgent):
            (self.substrate, self.substrate_region) = self._generate_agent_region_group(
                substrate_agent
            )
            self.template_relation.add((self.substrate, "substrate"))
            self.template_relation.add((self.substrate_region, "substrate_region"))

        else:
            raise NuggetGenerationError(
                "Unkown type of a substrate: '%s'" % type(substrate_agent)
            )

        self.enzyme = None
        self.enzyme_region = None

        # 3. create mod node
        mod_attrs = {
            "value": mod_value,
            "direct": direct
        }
        if annotation:
            mod_attrs.update(annotation.to_attrs())
        add_node(self.nugget, "mod", mod_attrs)
        self.meta_typing["mod"] = "mod"
        self.template_relation.add(("mod", "mod"))

        # 4. create state related nodes subject to modification
        if self.substrate_region:
            attached_to = self.substrate_region
        else:
            attached_to = self.substrate

        if isinstance(mod_target, State):
            mod_target.name
            if mod_target.value == mod_value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(mod_target, attached_to)
            self.template_relation.add((mod_state_id, "mod_state"))
            add_edge(self.nugget, mod_state_id, attached_to)

        elif isinstance(mod_target, Residue):
            if mod_target.state:
                if mod_target.state.value == mod_value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        UserWarning
                    )
                (residue_id, mod_state_id) = self._generate_residue(
                    mod_target,
                    attached_to
                )
                self.template_relation.add((mod_state_id, "mod_state"))
                self.template_relation.add((residue_id, "mod_residue"))
                add_edge(self.nugget, residue_id, attached_to)
            else:
                raise KamiError(
                    "Target of modification is required to be either "
                    "`State` or `Residue` with non-empty state: state "
                    "of residue is empty"
                )
        else:
            raise KamiError(
                "Target of modification is required to be either "
                "`State` or `Residue` with non-empty state: %s "
                "is provided" % type(mod_target)
            )
        add_edge(self.nugget, "mod", mod_state_id)
        return


class BinaryBndGenerator(NuggetGenerator):
    """Generator class for generic binary binding nugget."""

    def __init__(self, left_members, right_members,
                 annotation=None, direct=False):
        """Initialize generator object."""
        self.nugget = nx.DiGraph()
        self.meta_typing = dict()

        self.left_nodes = []
        self.right_nodes = []

        # 1. create physical agent nodes and conditions
        for member in left_members:
            if isinstance(member, PhysicalAgent):
                member_id = self._generate_agent_group(member)
            elif isinstance(member, PhysicalRegionAgent):
                (_, member_id) = self._generate_agent_region_group(member)
            else:
                raise NuggetGenerationError(
                    "Unkown type of an agent: '%s'" % type(member)
                )
            self.left_nodes.append(member_id)

        for member in right_members:
            if isinstance(member, PhysicalAgent):
                member_id = self._generate_agent_group(member)
            elif isinstance(member, PhysicalRegionAgent):
                (_, member_id) = self._generate_agent_region_group(member)
            else:
                raise NuggetGenerationError(
                    "Unkown type of an agent: '%s'" % type(member)
                )
            self.right_nodes.append(member_id)

        # 2. create binding action
        left_ids = "_".join(self.left_nodes)
        right_ids = "_".join(self.right_nodes)
        bnd_id = get_nugget_bnd_id(self.nugget, left_ids, right_ids)

        bnd_attrs = {
            "direct": direct
        }
        if annotation:
            bnd_attrs.update(annotation.to_attrs())

        add_node(self.nugget, bnd_id, bnd_attrs)
        self.meta_typing[bnd_id] = "bnd"

        # 3. create loci
        left_locus = get_nugget_locus_id(self.nugget, left_ids, bnd_id)
        add_node(self.nugget, left_locus)
        self.meta_typing[left_locus] = "locus"
        add_edge(self.nugget, left_locus, bnd_id)

        right_locus = get_nugget_locus_id(self.nugget, right_ids, bnd_id)
        add_node(self.nugget, right_locus)
        self.meta_typing[right_locus] = "locus"
        add_edge(self.nugget, right_locus, bnd_id)

        # 4. connect left/right members to the respective loci
        for member in self.left_nodes:
            add_edge(self.nugget, member, left_locus)

        for member in self.right_nodes:
            add_edge(self.nugget, member, right_locus)
        return


class ComplexGenerator(NuggetGenerator):
    """."""

    def __init__(self, members, annotation=None):
        """."""
        self.nugget = nx.DiGraph()
        self.meta_typing = dict()
        self.template_relation = dict()

        self.members = list()

        # create agents
        for member in members:
            if isinstance(member, PhysicalAgent):
                member_id = self._generate_agent_group(member)
                self.members.append(member_id)
            elif isinstance(member, PhysicalRegionAgent):
                (member_id, region_id) = self._generate_agent_region_group(member)
                self.members.append(region_id)

        visited = set()

        for member in self.members:
            for partner in self.members:
                if member != partner and partner not in visited:
                    bnd_id = get_nugget_bnd_id(self.nugget, member, partner)
                    add_node(self.nugget, bnd_id, {"direct": False})
                    self.meta_typing[bnd_id] = "bnd"

                    member_locus_id = get_nugget_locus_id(self.nugget, member, bnd_id)
                    add_node(self.nugget, member_locus_id)
                    self.meta_typing[member_locus_id] = "locus"

                    partner_locus_id = get_nugget_locus_id(self.nugget, partner, bnd_id)
                    add_node(self.nugget, partner_locus_id)
                    self.meta_typing[partner_locus_id] = "locus"

                    add_edge(self.nugget, member_locus_id, bnd_id)
                    add_edge(self.nugget, partner_locus_id, bnd_id)

                    add_edge(self.nugget, member, member_locus_id)
                    add_edge(self.nugget, partner, partner_locus_id)

            visited.add(member)

        return
