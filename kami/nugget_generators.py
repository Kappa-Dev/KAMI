"""Collection of nugget generators."""
import warnings
import networkx as nx

from regraph.library.primitives import (add_node,
                                        add_edge,
                                        remove_edge)

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
                                      get_nugget_is_free_id)


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

            partner_id = self._generate_agent_group(partner)

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

    def _generate_agent_group(self, agent):
        # 1. create agent node

        if isinstance(agent, PhysicalAgent):
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

        elif isinstance(agent, PhysicalRegionAgent):
            super_agent_id = self._generate_agent_group(
                agent.physical_agent
            )
            agent_id = self._generate_region_group(
                agent.physical_region, super_agent_id
            )
            add_edge(self.nugget, agent_id, super_agent_id)
        else:
            raise NuggetGenerationError(
                "Agent group is generated from kami 'PhysicalAgent' or "
                "'PhysicalRegionAgent' objects, %s was provided!" %
                type(agent)
            )
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


class ModGenerator(NuggetGenerator):
    """Generator of modification nugget and its typing."""

    def __init__(self, enzyme, substrate, mod_target,
                 mod_value=True, annotation=None, direct=False):
        """Basic nugget construction."""
        self.nugget = nx.DiGraph()
        self.meta_typing = dict()

        enzyme_id = self._generate_agent_group(enzyme)
        self.enzyme_node = enzyme_id

        substrate_id = self._generate_agent_group(substrate)
        self.substrate_id = substrate_id

        # 2. create mod node
        mod_attrs = {
            "value": mod_value,
            "direct": direct
        }
        if annotation:
            mod_attrs.update(annotation.to_attrs())
        add_node(self.nugget, "mod", mod_attrs)
        self.meta_typing["mod"] = "mod"

        # 3. create state related nodes subject to modification
        if isinstance(mod_target, State):
            mod_target.name
            if mod_target.value == mod_value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(mod_target, self.substrate_id)
            add_edge(self.nugget, mod_state_id, self.substrate_id)

        elif isinstance(mod_target, Residue):
            if mod_target.state:
                if mod_target.state.value == mod_value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        UserWarning
                    )
                (residue_id, mod_state_id) = self._generate_residue(
                    mod_target,
                    self.substrate_id
                )
                add_edge(self.nugget, residue_id, self.substrate_id)
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

        add_edge(self.nugget, self.enzyme_node, "mod")
        add_edge(self.nugget, "mod", mod_state_id)
        return

    def add_enzyme_residue(self, residue):
        """Add residue mod conditions to enzyme."""
        self.add_residue_to_agent(self.enzyme_node, residue)
        return

    def add_enzyme_state(self, state):
        """Add state mod conditions to enzyme."""
        self.add_state_to_agent(self.enzyme_node, state)
        return

    def add_substrate_residue(self, residue):
        """Add residue mod conditions to enzyme."""
        self.add_residue_to_agent(self.substrate_node, residue)
        return

    def add_substrate_state(self, state):
        """Add state mod conditions to enzyme."""
        self.add_state_to_agent(self.substrate_node, state)
        return

    def add_enzyme_is_bnd(self, partner_agent):
        """Add binding mod conditions to enzyme."""
        self.add_is_bnd_to_agent(self.enzyme_node, partner_agent)
        return

    def add_enzyme_is_free(self, partner_agent):
        """Add free of binding mod conditions to enzyme."""
        self.add_is_free_to_agent(self.enzyme_node, partner_agent)
        return

    def add_substrate_is_bnd(self, partner_agent):
        """Add binding mod conditions to substrate."""
        self.add_is_bnd_to_agent(self.substrate_node, partner_agent)
        return

    def add_substrate_is_free(self, partner_agent):
        """Add free of binding mod conditions to enzyme."""
        self.add_is_free_to_agent(self.substrate_node, partner_agent)


class AutoModGenerator(ModGenerator):
    """Class for auto modification nuggets."""

    def __init__(self, enzyme_agent, mod_target, mod_value=True,
                 enz_region=None, sub_region=None, annotation=None,
                 direct=False):
        """Basic nugget construction."""

        if not isinstance(enzyme_agent, PhysicalAgent):
            raise NuggetGenerationError(
                "Automodification parameter 'enzyme_agent' "
                "should be an instance of 'PhysicalAgent', "
                "'%s' provided!" % type(enzyme_agent)
            )

        self.nugget = nx.DiGraph()
        self.meta_typing = dict()

        enzyme_id = self._generate_agent_group(enzyme_agent)
        self.enzyme_node = enzyme_id
        self.substrate_node = enzyme_id

        # 2. create enzymatic/substratic regions
        self.enz_region_id = None
        if enz_region:
            self.enz_region_id = self._generate_region_group(
                enz_region, self.enzyme_node
            )
            add_edge(self.nugget, self.enz_region_id, enzyme_id)

        self.sub_region_id = None
        if sub_region:
            self.sub_region_id = self._generate_region_group(
                sub_region, self.enzyme_node
            )
            add_edge(self.nugget, self.sub_region_id, enzyme_id)

        # 3. create mod node
        mod_attrs = {
            "value": mod_value,
            "direct": direct
        }
        if annotation:
            mod_attrs.update(annotation.to_attrs())
        add_node(self.nugget, "mod", mod_attrs)
        self.meta_typing["mod"] = "mod"

        if self.enz_region_id:
            add_edge(self.nugget, self.enz_region_id, "mod")
        else:
            add_edge(self.nugget, self.enzyme_node, "mod")

        # 4. create state related nodes subject to modification
        if isinstance(mod_target, State):
            mod_target.name
            if mod_target.value == mod_value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(mod_target, self.enzyme_node)
            if self.sub_region_id:
                add_edge(self.nugget, mod_state_id, self.sub_region_id)
            else:
                add_edge(self.nugget, mod_state_id, self.substrate_node)

        elif isinstance(mod_target, Residue):
            if mod_target.state:
                if mod_target.state.value == mod_value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        UserWarning
                    )
                (residue_id, mod_state_id) = self._generate_residue(
                    mod_target,
                    self.enzyme_node
                )
                if self.sub_region_id:
                    add_edge(self.nugget, residue_id, self.sub_region_id)
                else:
                    add_edge(self.nugget, residue_id, self.substrate_node)
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

    def __init__(self):
        pass


class BndGenerator(NuggetGenerator):

    def __init__(self, members, annotation=None):
        self.nugget = nx.DiGraph()
        self.meta_typing = dict()

        self.member_nodes = []

        for member in members:
            member_id = self._generate_agent_group(member)
            self.member_nodes.append(member_id)
