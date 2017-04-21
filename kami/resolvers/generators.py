"""."""
import copy
import networkx as nx
import warnings

from regraph.primitives import (add_node,
                                add_edge,
                                remove_edge,
                                print_graph)

from kami.data_structures.entities import (State, Residue,
                                           PhysicalRegion,
                                           PhysicalAgent,
                                           PhysicalRegionAgent)
from kami.exceptions import KamiError, NuggetGenerationError
# from kami.resolvers.identifiers import (identify_agent,
#                                         identify_region,
#                                         identify_residue,
#                                         identify_mod,
#                                         add_action_graph_agent
#                                         )
from kami.utils.id_generators import (get_nugget_agent_id,
                                      get_nugget_region_id,
                                      get_nugget_residue_id,
                                      get_nugget_state_id,
                                      get_nugget_is_bnd_id,
                                      get_nugget_locus_id,
                                      get_nugget_is_free_id,
                                      get_nugget_bnd_id)


class NuggetContrainer:
    """Nugget container data structure."""

    def __init__(self, graph=None, meta_typing=None,
                 ag_typing=None, template_rel=None):
        """Initialize nugget container."""
        if graph:
            self.graph = copy.deepcopy(graph)
        else:
            self.graph = nx.DiGraph()
        if meta_typing:
            self.meta_typing = copy.deepcopy(meta_typing)
        else:
            self.meta_typing = dict()
        if ag_typing:
            self.ag_typing = copy.deepcopy(ag_typing)
        else:
            self.ag_typing = dict()
        if template_rel:
            self.template_rel = copy.deepcopy(template_rel)
        else:
            self.template_rel = set()
        return

    def add_node(self, node_id, attrs=None, meta_typing=None,
                 ag_typing=None, template_rel=None):
        """Add node + typings to a nugget."""
        add_node(self.graph, node_id, attrs)
        if meta_typing:
            self.meta_typing[node_id] = meta_typing
        if ag_typing:
            self.ag_typing[node_id] = ag_typing
        if template_rel:
            self.template_rel.add((node_id, template_rel))
        return

    def add_edge(self, node_1, node_2, attrs=None):
        """Add edge between the nodes of a nugget."""
        add_edge(self.graph, node_1, node_2, attrs)
        return


class Generator:
    """Base class for nugget generators."""

    def _add_agent_to_ag(self, agent, anatomize=True):
        agent_id = self.hierarchy.add_agent_to_ag(agent)
        return agent_id

    def _add_region_to_ag(self, region, ref_agent, anatomize=True):
        region_id = self.hierarchy.add_region_to_ag(region, ref_agent)
        return region_id

    def _add_residue_to_ag(self, residue, ref_agent):
        residue_id = self.hierarchy.add_residue_to_ag(residue, ref_agent)
        return residue_id

    def _add_state_to_ag(self, state, ref_agent):
        state_id = self.hierarchy.add_state_to_ag(state, ref_agent)
        return state_id

    def _identify_agent(self, agent, add_agents=True, anatomize=True):
        # try to identify an agent
        reference_id = self.hierarchy.find_agent(agent)

        # if not found
        if reference_id is None and add_agents is True:
            reference_id = self._add_agent_to_ag(agent, anatomize)

        return reference_id

    def _identify_region(self, region, agent, add_agents=True, anatomize=True):
        # try to identify an agent
        reference_id = self.hierarchy.find_region(region, agent)

        # if not found
        if reference_id is None and add_agents is True:
            reference_id = self._add_region_to_ag(region, agent, anatomize)

        return reference_id

    def _identify_residue(self, residue, agent, add_agents=True, anatomize=True):
        # try to identify an agent
        reference_id = self.hierarchy.find_residue(residue, agent)

        # if not found
        if reference_id is None and add_agents is True:
            reference_id = self._add_residue_to_ag(residue, agent)

        return reference_id

    def _generate_state(self, nugget, state, ref_agent,
                        add_agents=True, anatomize=True):
        prefix = str(ref_agent)
        state_id = get_nugget_state_id(nugget.graph, state, prefix)
        # !TODO! add identification
        nugget.add_node(
            state_id,
            state.to_attrs(),
            meta_typing="state",
            ag_typing=self._add_state_to_ag(state, ref_agent)
        )
        return state_id

    def _generate_residue(self, nugget, residue, ref_agent,
                          add_agents=True, anatomize=True):

        prefix = str(ref_agent)

        residue_id = get_nugget_residue_id(nugget.graph, residue, prefix)
        action_graph_residue = self._identify_residue(residue, ref_agent)
        if action_graph_residue is None and add_agents is True:
            action_graph_residue = self._add_residue_to_ag(residue, ref_agent)

        nugget.add_node(
            residue_id,
            residue.to_attrs(),
            meta_typing="residue",
            ag_typing=action_graph_residue
        )
        state_id = None
        if residue.state:
            state_id = self._generate_state(
                nugget,
                residue.state,
                action_graph_residue,
                add_agents,
                anatomize
            )
            nugget.add_edge(state_id, residue_id)

        return (residue_id, state_id)

    def _generate_bound(self, nugget, partners, prefix="",
                        add_agents=True, anatomize=True,
                        merge_actions=True, apply_sematics=True):
        is_bnd_ids = []
        partner_ids = []
        for partner in partners:
            if isinstance(partner, PhysicalAgent):
                partner_id = get_nugget_agent_id(nugget.graph, partner.agent)
            elif isinstance(partner, PhysicalRegionAgent):
                partner_id = get_nugget_region_id(
                    nugget.graph, str(partner.physical_region.region),
                    str(partner.physical_agent.agent)
                )

            partner_ids.append(partner_id)

            # print(partner_id)
            is_bnd_id = get_nugget_is_bnd_id(nugget.graph, prefix, partner_id)
            # !TODO! add identification in ag
            nugget.add_node(
                is_bnd_id,
                meta_typing="is_bnd"
            )
            is_bnd_ids.append(is_bnd_id)

            partner_locus_id = get_nugget_locus_id(nugget.graph, partner_id, is_bnd_id)
            # !TODO! add indentification in ag
            nugget.add_node(
                partner_locus_id,
                meta_typing="locus"
            )

            if isinstance(partner, PhysicalAgent):
                partner_id = self._generate_agent_group(
                    nugget, partner, add_agents, anatomize, merge_actions,
                    apply_sematics
                )
            elif isinstance(partner, PhysicalRegionAgent):
                (_, partner_id) = self._generate_agent_region_group(
                    nugget, partner, add_agents, anatomize, merge_actions,
                    apply_sematics
                )
            else:
                raise NuggetGenerationError(
                    "Invalid type of binding partner: '%s'" % type(partner)
                )

            nugget.add_edge(partner_locus_id, is_bnd_id)
            nugget.add_edge(partner_id, partner_locus_id)

        bound_id = "%s_is_bnd_%s" % (prefix, "_".join(partner_ids))
        bound_locus_id = get_nugget_locus_id(nugget.graph, prefix, bound_id)
        # !TODO! add id to ag
        nugget.add_node(
            bound_locus_id,
            meta_typing="locus"
        )
        for is_bnd_id in is_bnd_ids:
            nugget.add_edge(bound_locus_id, is_bnd_id)
        return bound_locus_id

    def _generate_region_group(self, nugget, region, ref_agent,
                               add_agents=True, anatomize=True,
                               merge_actions=True, apply_sematics=True):
        # 1. create region node
        prefix = str(ref_agent)

        region_id = get_nugget_region_id(nugget.graph, str(region.region), prefix)

        # identify region
        action_graph_region = self._identify_region(region, ref_agent)
        if action_graph_region is None and add_agents is True:
            action_graph_region = self._add_region_to_ag(
                region, ref_agent, anatomize
            )

        nugget.add_node(
            region_id, region.region.to_attrs(),
            meta_typing="region",
            ag_typing=action_graph_region
        )

        # 2. create and attach residues
        for residue in region.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, region_id, add_agents, anatomize
            )
            action_graph_residue = self._identify_residue(
                residue,
                ref_agent
            )
            if action_graph_residue is None and add_agents is True:
                action_graph_residue = self._add_region_residue_to_ag(
                    residue, action_graph_region, ref_agent
                )

            nugget.ag_typing[residue_id] = action_graph_residue
            nugget.add_edge(residue_id, region_id)

        # 3. create and attach states
        for state in region.states:
            state_id = self._generate_state(
                nugget, state, region_id, add_agents, anatomize
            )
            nugget.ag_typing[state_id] = self._add_state_to_ag(
                state, action_graph_region
            )
            nugget.add_edge(state_id, region_id)

        # 4. create and attach bounds
        for partners in region.bounds:
            bound_locus_id = self._generate_bound(
                nugget, partners, region_id, add_agents,
                anatomize, merge_actions, apply_sematics
            )
            nugget.add_edge(region_id, bound_locus_id)
        return region_id

    def _generate_agent_group(self, nugget, agent,
                              add_agents=True, anatomize=True,
                              merge_actions=True, apply_sematics=True):
        """Generate agent group + indentify mapping."""
        # 1. create agent node
        agent_id = get_nugget_agent_id(nugget.graph, agent.agent)

        # 2. identify agent (map to a node in the action graph)
        action_graph_agent = self._identify_agent(agent.agent)

        # if the node was not identified add new node
        if action_graph_agent is None:
            if add_agents is True:
                action_graph_agent = self._add_agent_to_ag(
                    agent.agent,
                    anatomize
                )

        nugget.add_node(
            agent_id,
            agent.agent.to_attrs(),
            meta_typing="agent",
            ag_typing=action_graph_agent
        )

        # 2. create and attach regions
        for region in agent.regions:
            region_id = self._generate_region_group(
                nugget, region, agent_id, add_agents, anatomize,
                merge_actions, apply_sematics,
            )

            # identify region (map to a node in the action graph)
            action_graph_region = self._identify_region(
                region,
                agent.agent
            )

            # if the node was not identified add new node
            if action_graph_region is None:
                if add_agents is True:
                    action_graph_region = self._add_region_to_ag(
                        region,
                        anatomize
                    )
                    add_edge(
                        self.hierarchy.action_graph,
                        action_graph_region,
                        action_graph_agent
                    )
            nugget.ag_typing[region_id] = action_graph_region
            nugget.add_edge(region_id, agent_id)

        # 3. create and attach residues
        for residue in agent.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, agent_id, add_agents, anatomize
            )
            # identify residue (map to a node in the action graph)
            action_graph_residue = self._identify_residue(
                residue,
                agent.agent
            )
            # if the node was not identified add new node
            if action_graph_residue is None:
                if add_agents is True:
                    action_graph_residue = self._add_residue_to_ag(
                        residue,
                        anatomize
                    )
                    add_edge(
                        self.hierarchy.action_graph,
                        action_graph_residue,
                        action_graph_agent
                    )
            nugget.ag_typing[residue_id] = action_graph_residue
            nugget.add_edge(residue_id, agent_id)

        # 4. create and attach states
        for state in agent.states:
            state_id = self._generate_state(
                nugget, state, agent_id, add_agents, anatomize
            )

            action_graph_state = self._add_state_to_ag(
                state,
                action_graph_agent
            )
            nugget.ag_typing[state_id] = action_graph_state

            nugget.add_edge(state_id, agent_id)

        # 5. create and attach bounds
        for bnd in agent.bounds:
            bound_locus_id = self._generate_bound(
                nugget, bnd, agent_id, add_agents, anatomize,
                merge_actions, apply_sematics
            )
            nugget.add_edge(agent_id, bound_locus_id)

        return agent_id

    def _generate_agent_region_group(self, nugget, agent,
                                     add_agents=True, anatomize=True,
                                     merge_actions=True, apply_sematics=True):
        agent_id = self._generate_agent_group(
            nugget, agent.physical_agent, add_agents, anatomize, merge_actions,
            apply_sematics
        )
        region_id = self._generate_region_group(
            nugget, agent.physical_region, agent_id, add_agents, anatomize
        )
        nugget.add_edge(region_id, agent_id)
        return (agent_id, region_id)


class ModGenerator(Generator):
    """Modification nugget generator."""

    def _create_nugget(self, mod, add_agents=True, anatomize=True,
                       merge_actions=True, apply_sematics=True):
        """Create mod nugget graph and find its typing."""
        nugget = NuggetContrainer()

        if isinstance(mod.enzyme, PhysicalAgent):
            enzyme = self._generate_agent_group(
                nugget, mod.enzyme, add_agents, anatomize
            )
            enzyme_region = None
        elif isinstance(mod.enzyme, PhysicalRegionAgent):
            (enzyme, enzyme_region) = self._generate_agent_region_group(
                nugget, mod.enzyme, add_agents, anatomize
            )
        else:
            raise NuggetGenerationError(
                "Unkown type of an enzyme: '%s'" % type(mod.enzyme)
            )

        nugget.template_rel.add((enzyme, "enzyme"))
        if enzyme_region:
            nugget.template_rel.add((enzyme_region, "enzyme_region"))

        if isinstance(mod.substrate, PhysicalAgent):
            substrate = self._generate_agent_group(
                nugget, mod.substrate, add_agents, anatomize
            )
            substrate_region = None
        elif isinstance(substrate, PhysicalRegionAgent):
            (substrate, substrate_region) = self._generate_agent_region_group(
                nugget, mod.substrate, add_agents, anatomize
            )
        else:
            raise NuggetGenerationError(
                "Unkown type of a substrate: '%s'" % type(mod.substrate)
            )

        nugget.template_rel.add((substrate, "substrate"))
        if substrate_region:
            nugget.template_rel.add((substrate_region, "substrate_region"))

        # 2. create mod node
        mod_attrs = {
            "value": mod.value,
            "direct": mod.direct
        }
        if mod.annotation:
            mod_attrs.update(mod.annotation.to_attrs())

        # !TODO! add identification to ag
        nugget.add_node("mod", mod_attrs, meta_typing="mod", template_rel="mod")

        # 3. create state related nodes subject to modification\
        if substrate_region:
            attached_to = substrate_region
        else:
            attached_to = substrate

        if isinstance(mod.target, State):
            mod.target.name
            if mod.target.value == mod.value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(
                nugget, mod.target, attached_to, add_agents, anatomize
            )
            nugget.add_edge(mod_state_id, attached_to)
            nugget.template_rel.add((mod_state_id, "mod_state"))
        elif isinstance(mod.target, Residue):
            if mod.target.state:
                if mod.target.state.value == mod.value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        UserWarning
                    )
                (residue_id, mod_state_id) = self._generate_residue(
                    nugget,
                    mod.target,
                    attached_to,
                    add_agents,
                    anatomize
                )
                nugget.add_edge(residue_id, attached_to)
                nugget.template_rel.add((mod_state_id, "mod_state"))
                nugget.template_rel.add((residue_id, "mod_residue"))
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
                "is provided" % type(mod.target)
            )
        if enzyme_region:
            nugget.add_edge(enzyme_region, "mod")
        else:
            nugget.add_edge(enzyme, "mod")
        nugget.add_edge("mod", mod_state_id)

        return nugget

    def __init__(self, hierarchy):
        """Initializer generator with a hierarchy."""
        self.hierarchy = hierarchy
        return

    def generate(self, mod, add_agents=True, anatomize=True,
                 merge_actions=True, apply_sematics=True):
        """Generate modification nugget."""
        # 1. Create a nugget graph and make respective changes to the AG
        nugget = self._create_nugget(
            mod, add_agents, anatomize, merge_actions, apply_sematics
        )
        print_graph(nugget.graph)
        print(nugget.meta_typing)
        print(nugget.ag_typing)
        print(nugget.template_rel)

        # 1. Add nugget to the hierarchy
        # nugget_id = self.hierarchy.add_nugget(nugget.graph)
        # self.hierarchy.type_nugget_by_ag(nugget_id, nugget.ag_typing)
        # self.hierarchy.type_nugget_by_meta(nugget_id, nugget.meta_typing)
        # self.hierarchy.add_nugget_template(nugget_id, nugget.template_rel)

        # 2. Add negative conditions to the nugget
        # if negative:
        #     negative_id = self.hierarchy.add_negative_cond(
        #         negative, nugget_id
        #     )
        #     self.hierarchy.type_nugget_by_ag(
        #         negative_id, negative_ag_typing
        #     )
        #     self.hierarchy.type_nugget_by_meta(
        #         negative_id, negative_meta_typing
        #     )
        #     self.hierarchy.add_nugget_template(
        #         negative_id, negative_template_rel
        #     )
        # return nugget_id
