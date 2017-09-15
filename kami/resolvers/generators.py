"""Collection of nugget generators."""
import collections
import copy
import networkx as nx
import warnings

from regraph.primitives import (add_node,
                                add_edge,
                                remove_edge,
                                print_graph,
                                add_node_attrs)

from kami.data_structures.entities import (Region, State, Residue,
                                           PhysicalRegion,
                                           PhysicalAgent,
                                           PhysicalRegionAgent)
from kami.exceptions import (KamiError,
                             NuggetGenerationError,
                             KamiHierarchyError,
                             KamiWarning)
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
from anatomizer.new_anatomizer import (GeneAnatomy, AnatomizerError)


class NuggetContrainer:
    """Nugget container data structure."""

    def __init__(self, graph=None, meta_typing=None,
                 ag_typing=None, template_rel=None,
                 semantic_rels=None):
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
            if isinstance(template_rel, collections.Iterable):
                self.template_rel = copy.deepcopy(template_rel)
            else:
                self.template_rel = set([template_rel])
        else:
            self.template_rel = set()
        if semantic_rels:
            self.semantic_rels = copy.deepcopy(semantic_rels)
        else:
            self.semantic_rels = dict()
        return

    def add_node(self, node_id, attrs=None, meta_typing=None,
                 ag_typing=None, template_rel=None, semantic_rels=None):
        """Add node + typings to a nugget."""
        add_node(self.graph, node_id, attrs)
        if meta_typing:
            self.meta_typing[node_id] = meta_typing
        if ag_typing:
            self.ag_typing[node_id] = ag_typing
        if template_rel:
            for el in template_rel:
                self.template_rel.add((node_id, el))
        if semantic_rels:
            for key, value in semantic_rels.items():
                if key not in self.semantic_rels.keys():
                    self.semantic_rels[key] = set()
                for v in value:
                    self.semantic_rels[key].add((node_id, v))
        return

    def add_edge(self, node_1, node_2, attrs=None):
        """Add edge between the nodes of a nugget."""
        add_edge(self.graph, node_1, node_2, attrs)
        return


class Generator:
    """Base class for nugget generators."""

    def __init__(self, hierarchy):
        """Initializer generator with a hierarchy."""
        self.hierarchy = hierarchy
        return

    def _add_agent_to_ag(self, agent, anatomize=True):
        if anatomize is True:
            anatomy = GeneAnatomy(
                agent.uniprotid,
                merge_features=True,
                nest_features=False,
                merge_overlap=0.05,
                offline=True
            )
            agent.names = {anatomy.hgnc_symbol}
            agent_id = self.hierarchy.add_agent(agent)
            for domain in anatomy.domains:
                region = Region(domain.start, domain.end, ", ".join(domain.short_names))
                kinase = False
                if domain.is_protein_kinase():
                    kinase = True
                region_id = self.hierarchy.find_region(region, agent_id)
                if not region_id:
                    region_id = self.hierarchy.add_region(region, agent_id, kinase=kinase)
                add_edge(self.hierarchy.action_graph, region_id, agent_id)
        else:
            agent_id = self.hierarchy.add_agent(agent)
        return agent_id

    def _add_region_to_ag(self, region, ref_agent, anatomize=True):
        region_id = self.hierarchy.add_region(region, ref_agent)
        return region_id

    def _add_residue_to_ag(self, residue, ref_agent):
        residue_id = self.hierarchy.add_residue(residue, ref_agent)
        return residue_id

    def _add_state_to_ag(self, state, ref_agent):
        state_id = self.hierarchy.add_state(state, ref_agent)
        return state_id

    def _identify_agent(self, agent, add_agents=True, anatomize=True):
        # try to identify an agent
        reference_id = self.hierarchy.find_agent(agent)

        if add_agents is True:
            if reference_id is not None:
                # add new names to AG agent
                # if not set(agent.names).issubset(
                #    self.hierarchy.action_graph.node[reference_id]["names"]):
                #     add_node_attrs(
                #         self.hierarchy.action_graph,
                #         reference_id,
                #         {"names": agent.names}
                #     )
                # add new xrefs to AG agent
                add_node_attrs(
                    self.hierarchy.action_graph,
                    reference_id,
                    agent.to_attrs()
                )
            # if not found
            else:
                reference_id = self._add_agent_to_ag(agent, anatomize)

        return reference_id

    def _identify_region(self, region, agent, add_agents=True, anatomize=True):
        # try to identify an agent
        try:
            reference_id = self.hierarchy.find_region(region.region, agent)
        except Exception as e:
            if add_agents is False:
                return None
            else:
                raise NuggetGenerationError(
                    "Cannot map a region '%s' from nugget "
                    "to a region from action graph" %
                    str(region.region)
                )
        # if not found
        if reference_id is None and add_agents is True:
            reference_id = self._add_region_to_ag(
                region.region,
                agent,
                anatomize
            )

        return reference_id

    def _identify_residue(self, residue, agent, add_agents=True):
        # try to identify an agent
        try:
            reference_id = self.hierarchy.find_residue(residue, agent)
        except:
            if add_agents is False:
                return None
            else:
                raise NuggetGenerationError(
                    "Cannot map a residue '%s' from nugget to a residue "
                    "from action graph (unkown reference agent '%s')" %
                    (str(residue), str(agent))
                )
        # if not found
        if reference_id is None and add_agents is True:
            reference_id = self._add_residue_to_ag(residue, agent)
        return reference_id

    def _identify_state(self, state, agent, add_agents=True):
        try:
            reference_id = self.hierarchy.find_state(state, agent)
        except:
            if add_agents is False:
                return None
            else:
                raise NuggetGenerationError(
                    "Cannot map a state '%s' from nugget to a state "
                    "from action graph (unkown reference agent '%s')" %
                    (str(state), str(agent))
                )
        # if not found
        if reference_id is None and add_agents is True:
            reference_id = self._add_state_to_ag(state, agent)

        return reference_id

    def _generate_state(self, nugget, state, father,
                        add_agents=True):
        prefix = father

        state_id = get_nugget_state_id(nugget.graph, state, prefix)

        action_graph_state = None
        if father in nugget.ag_typing.keys():
            action_graph_state = self._identify_state(
                state, nugget.ag_typing[father], add_agents
            )

        nugget.add_node(
            state_id,
            state.to_attrs(),
            meta_typing="state",
            ag_typing=action_graph_state
        )
        return state_id

    def _generate_residue(self, nugget, residue, father,
                          add_agents=True):
        prefix = father

        residue_id = get_nugget_residue_id(nugget.graph, residue, prefix)

        action_graph_residue = None
        if father in nugget.ag_typing.keys():
            action_graph_residue = self._identify_residue(
                residue,
                nugget.ag_typing[father],
                add_agents
            )
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
                residue_id,
                add_agents
            )
            nugget.add_edge(state_id, residue_id)

        return (residue_id, state_id)

    def _generate_bound(self, nugget, partners, father,
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

            # generate prefix for is_bnd_id
            prefix = ""
            if nugget.meta_typing[father] == "agent":
                prefix = father
            elif nugget.meta_typing[father] == "region":
                for succ in nugget.graph.successors(father):
                    if nugget.meta_typing[succ] == "agent":
                        prefix += succ
                prefix += "_" + father

            is_bnd_id = get_nugget_is_bnd_id(nugget.graph, prefix, partner_id)
            # !TODO! add identification in ag
            nugget.add_node(
                is_bnd_id,
                # meta_typing="is_bnd"
            )
            is_bnd_ids.append(is_bnd_id)

            partner_locus_id = get_nugget_locus_id(nugget.graph, partner_id, is_bnd_id)
            # !TODO! add indentification in ag
            nugget.add_node(
                partner_locus_id,
                # meta_typing="locus"
            )

            if isinstance(partner, PhysicalAgent):
                partner_id = self._generate_agent_group(
                    nugget, partner,
                    add_agents, anatomize, merge_actions,
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
            # meta_typing="locus"
        )
        for is_bnd_id in is_bnd_ids:
            nugget.add_edge(bound_locus_id, is_bnd_id)
        return bound_locus_id

    def _generate_region_group(self, nugget, region, father,
                               add_agents=True, anatomize=True,
                               merge_actions=True, apply_sematics=True):
        # 1. create region node
        prefix = father

        region_id = get_nugget_region_id(
            nugget.graph, str(region.region), prefix
        )

        # identify region
        action_graph_region = None
        if father in nugget.ag_typing.keys():
            action_graph_region = self._identify_region(
                region, nugget.ag_typing[father], add_agents, anatomize
            )

        nugget.add_node(
            region_id, region.region.to_attrs(),
            meta_typing="region",
            ag_typing=action_graph_region,
            # semantic_rels=semantic_rels
        )

        # 2. create and attach residues
        for residue in region.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, region_id, add_agents
            )
            nugget.add_edge(residue_id, region_id)

        # 3. create and attach states
        for state in region.states:
            state_id = self._generate_state(
                nugget, state, region_id, add_agents
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
        action_graph_agent = self._identify_agent(
            agent.agent, add_agents, anatomize
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
            nugget.add_edge(region_id, agent_id)

        # 3. create and attach residues
        for residue in agent.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, agent_id, add_agents
            )
            nugget.add_edge(residue_id, agent_id)

        # 4. create and attach states
        for state in agent.states:
            state_id = self._generate_state(
                nugget, state, agent_id, add_agents
            )
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

    def generate(self, mod, add_agents=True, anatomize=True,
                 merge_actions=True, apply_semantics=True):
        """Generate modification nugget."""
        # 1. Create a nugget graph and make respective changes to the AG
        # try:
        if True:
            nugget = self._create_nugget(
                mod, add_agents, anatomize, merge_actions, apply_semantics
            )

            nugget_id = self.hierarchy.add_nugget(nugget.graph)
            # print("Nugget '%s' added..." % nugget_id)
            # print(
            #     "# nodes in the action graph: %d" %
            #     len(self.hierarchy.action_graph.nodes())
            # )
            self.hierarchy.type_nugget_by_ag(nugget_id, nugget.ag_typing)
            # self.hierarchy.type_nugget_by_meta(nugget_id, nugget.meta_typing)
            self.hierarchy.add_mod_template_rel(nugget_id, nugget.template_rel)

            # add semantic relations found for the nugget
            for semantic_nugget, rel in nugget.semantic_rels.items():
                self.hierarchy.add_semantic_nugget_rel(
                    nugget_id, semantic_nugget, rel
                )

        # except Exception as e:
        #     warnings.warn(
        #         "No nugget created: error received: %s" % str(e),
        #         KamiWarning
        #     )

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


class ModGenerator(Generator):
    """Modification nugget generator."""

    def _create_nugget(self, mod, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):
        """Create mod nugget graph and find its typing."""
        nugget = NuggetContrainer()
        # 1. Process enzyme
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

        nugget.add_node(
            "mod",
            mod_attrs,
            # meta_typing="mod",
            template_rel=["mod"]
        )

        # 3. create state related nodes subject to modification
        if substrate_region and substrate_region in self:
            attached_to = substrate_region
        else:
            attached_to = substrate

        mod_residue_id = None
        if isinstance(mod.target, State):
            mod.target.name
            if mod.target.value == mod.value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(
                nugget, mod.target, attached_to, add_agents
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
                (mod_residue_id, mod_state_id) = self._generate_residue(
                    nugget,
                    mod.target,
                    attached_to,
                    add_agents
                )
                nugget.add_edge(mod_residue_id, attached_to)
                nugget.template_rel.add((mod_state_id, "mod_state"))
                nugget.template_rel.add((mod_residue_id, "substrate_residue"))
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

        # Attempt to autocomplete the nugget
        # using semantics
        # 1. PHOSPHORYLATION

        phospho = False
        if isinstance(mod.target, State):
            if mod.target.name == "phosphorylation":
                phospho = True
        else:
            if mod.target.state and mod.target.state.name == "phosphorylation":
                phospho = True

        if phospho:
            kinase_region = None
            if enzyme_region:
                ag_region = nugget.ag_typing[enzyme_region]
                if 'kinase' in self.hierarchy.ag_node_semantics(ag_region):
                    kinase_region = enzyme_region
                else:
                    warnings.warn(
                        "Cannot resolve phospho modification: "
                        "action graph region `%s` corresponding to "
                        "enzyme region `%s` is not a protein kinase. " %
                        (ag_region, enzyme_region),
                        KamiWarning
                    )
            else:
                # Find the unique kinase region
                ag_node = nugget.ag_typing[enzyme]
                regions = self.hierarchy.get_regions_of_agent(ag_node)
                kinase_regions = set()
                for region in regions:
                    if 'kinase' in self.hierarchy.ag_node_semantics(region):
                        kinase_regions.add(region)

                # if there is only one kinase region
                if len(kinase_regions) == 1:
                    kinase_region = list(kinase_regions)[0]
                elif len(kinase_regions) > 1:
                    warnings.warn(
                        "Cannot resolve phospho modification: "
                        "multiple protein kinase regions (%s) are associated "
                        "with a single protein: %s" %
                        (", ".join(kinase_regions), enzyme),
                        KamiWarning
                    )
                else:
                    warnings.warn(
                        "Cannot resolve phospho modification: "
                        "no protein kinase region is associated "
                        "with the protein: %s" % enzyme,
                        KamiWarning
                    )
            if kinase_region:

                # if kinase_region was not in the nugget
                if kinase_region not in nugget.graph.nodes():
                    # autocomplete nugget by inserting kinase region
                    nugget.add_node(
                        kinase_region,
                        self.hierarchy.action_graph.node[kinase_region],
                        meta_typing="region",
                        ag_typing=kinase_region,
                        semantic_rels={
                            "phosphorylation": ['kinase']
                        }
                    )
                    remove_edge(nugget.graph, enzyme, "mod")
                    nugget.add_edge(kinase_region, "mod")
                    nugget.add_edge(kinase_region, enzyme)
                else:
                    nugget.semantic_rels["phosphorylation"] = set()
                    nugget.semantic_rels["phosphorylation"].add(
                        (kinase_region, 'kinase')
                    )

                ag_region = nugget.ag_typing[kinase_region]
                mods = self.hierarchy.get_mods_of_region(ag_region)

                # if mod associated with
                # protein kinase region already exists
                if len(mods) == 1:
                    nugget.ag_typing["mod"] = mods[0]
                    add_node_attrs(
                        self.hierarchy.action_graph,
                        mods[0],
                        mod_attrs
                    )
                    if (mods[0], nugget.ag_typing[mod_state_id]) not \
                       in self.hierarchy.action_graph.edges():
                        add_edge(
                            self.hierarchy.action_graph, mods[0],
                            nugget.ag_typing[mod_state_id]
                        )

                # if no mod associated with protein kinase exists
                elif len(mods) == 0:
                    # add new mod and associated with phospho
                    mod_id = self.hierarchy.add_mod(
                        mod_attrs,
                        semantics=["phospho"]
                    )

                    nugget.ag_typing["mod"] = mod_id

                    # add edge `kinase -> mod` and `mod -> mod_state`
                    add_edge(
                        self.hierarchy.action_graph,
                        kinase_region,
                        mod_id
                    )
                    add_edge(
                        self.hierarchy.action_graph,
                        mod_id,
                        nugget.ag_typing[mod_state_id]
                    )
                else:
                    warnings.warn(
                        "Cannot resolve phospho modification: "
                        "multiple modifications are associated "
                        "with a single protein kinase domain: %s" % region,
                        KamiWarning
                    )
                nugget.semantic_rels["phosphorylation"].add(
                    ("mod", "phospho")
                )
                nugget.semantic_rels["phosphorylation"].add(
                    (mod_state_id, "target_state")
                )

                self.hierarchy.add_ag_node_semantics(
                    nugget.ag_typing[mod_state_id],
                    "target_state"
                )

                if mod_residue_id:
                    nugget.semantic_rels["phosphorylation"].add(
                        (mod_residue_id, "target_residue")
                    )
                    self.hierarchy.add_ag_node_semantics(
                        nugget.ag_typing[mod_residue_id],
                        "target_residue"
                    )
        return nugget


class AutoModGenerator(Generator):
    """Generator class for auto modification nugget."""

    def _create_nugget(self, mod, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):
        """Create mod nugget graph and find its typing."""
        nugget = NuggetContrainer()

        if not isinstance(mod.enzyme, PhysicalAgent):
            raise NuggetGenerationError(
                "Automodification parameter 'enzyme_agent' "
                "should be an instance of 'PhysicalAgent', "
                "'%s' provided!" % type(mod.enzyme)
            )

        enzyme = self._generate_agent_group(
            nugget, mod.enzyme, add_agents, anatomize, merge_actions, apply_sematics
        )

        nugget.template_rel.add((enzyme, "enzyme"))
        nugget.template_rel.add((enzyme, "substrate"))

        # 2. create enzymatic/substratic regions
        if mod.enz_region:
            enzyme_region = self._generate_region_group(
                nugget, mod.enz_region, add_agents,
                anatomize, merge_actions, apply_semantics
            )
            nugget.add_edge(enzyme_region, enzyme)
            nugget.template_rel.add((enzyme_region, "enzyme_region"))

        if mod.sub_region:
            substrate_region = self._generate_region_group(
                nugget, mod.sub_region, add_agents,
                anatomize, merge_actions, apply_semantics
            )
            nugget.add_edge(substrate_region, enzyme)
            nugget.template_rel.add((substrate_region, "substrate_region"))

        # 3. create mod node
        mod_attrs = {
            "value": mod.value,
            "direct": mod.direct
        }
        if mod.annotation:
            mod_attrs.update(mod.annotation.to_attrs())
        nugget.add_node(
            "mod", mod_attrs,
            meta_typing="mod",
            template_rel=["mod"]
        )

        if enzyme_region:
            nugget.add_edge(enzyme_region, "mod")
        else:
            nugget.add_edge(enzyme, "mod")

        # 4. create state related nodes subject to modification
        if substrate_region:
            attached_to = substrate_region
        else:
            attached_to = enzyme

        if isinstance(mod.target, State):
            if mod.target.value == mod.value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(
                nugget, mod.target, attached_to, add_agents
            )
            nugget.template_rel.add((mod_state_id, "mod_state"))
            nugget.add_edge(mod_state_id, attached_to)

        elif isinstance(mod.target, Residue):
            if mod.target.state:
                if mod.target.state.value == mod.value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        UserWarning
                    )
                (residue_id, mod_state_id) = self._generate_residue(
                    mod.target,
                    attached_to,
                    add_agents
                )
                nugget.template_rel.add((mod_state_id, "mod_state"))
                nugget.template_rel.add((residue_id, "mod_residue"))
                nugget.add_edge(residue_id, attached_to)
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
        nugget.add_edge("mod", mod_state_id)

        return nugget


class TransModGenerator(ModGenerator):
    """Generator class for trans modification nugget."""

    def _add_is_bnd(self, nugget, agent_1, agent_2,
                    merge_actions=True, apply_semantics=True):
        is_bnd_id = get_nugget_is_bnd_id(
            nugget.graph, agent_1, agent_2
        )
        agent_1_locus = get_nugget_locus_id(
            nugget.graph, agent_1, is_bnd_id
        )
        agent_2_locus = get_nugget_locus_id(
            nugget.graph, agent_2, is_bnd_id
        )
        # !TODO! add action identification
        nugget.add_node(
            is_bnd_id,
            meta_typing="is_bnd",
        )

        nugget.add_node(
            agent_1_locus,
            meta_typing="locus"
        )

        nugget.add_node(
            agent_2_locus,
            meta_typing="locus"
        )

        nugget.add_edge(agent_1_locus, is_bnd_id)
        nugget.add_edge(agent_2_locus, is_bnd_id)

        nugget.add_edge(agent_1, agent_1_locus)
        nugget.add_edge(agent_2, agent_2_locus)
        return

    def _create_nugget(self, mod, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):
        nugget = ModGenerator._create_nugget(
            mod, add_agents=True, anatomize=True,
            merge_actions=True, apply_semantics=True
        )

        # find enzyme and substrate node ids
        enzyme_id = None
        substrate_id = None
        for (node, role) in nugget.template_rel:
            if role == "enzyme":
                enzyme_id = node
            elif role == "substrate":
                substrate_id = node

        self._add_is_bnd(
            nugget, enzyme_id, substrate_id, merge_actions, apply_semantics
        )

        return nugget


class AnonymousModGenerator(Generator):
    """Generator class for anonymous modification nugget."""

    def _create_nugget(self, mod, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):
        nugget = NuggetContrainer()

        if isinstance(mod.substrate, PhysicalAgent):
            substrate = self._generate_agent_group(
                nugget, mod.substrate, add_agents, anatomize,
                merge_actions, apply_semantics
            )
            substrate_region = None
            nugget.template_rel.add((substrate, "substrate"))

        elif isinstance(mod.substrate, PhysicalRegionAgent):
            (substrate, substrate_region) = self._generate_agent_region_group(
                nugget, mod.substrate, add_agents, anatomize,
                merge_actions, apply_semantics
            )
            nugget.template_rel.add((substrate, "substrate"))
            nugget.template_rel.add((substrate_region, "substrate_region"))

        else:
            raise NuggetGenerationError(
                "Unkown type of a substrate: '%s'" % type(mod.substrate)
            )

        # 3. create mod node
        mod_attrs = {
            "value": mod.value,
            "direct": mod.direct
        }
        if mod.annotation:
            mod_attrs.update(mod.annotation.to_attrs())
        nugget.add_node(
            "mod", mod_attrs,
            meta_typing="mod",
            template_rel=["mod"]
        )

        # 4. create state related nodes subject to modification
        if substrate_region:
            attached_to = substrate_region
        else:
            attached_to = substrate

        if isinstance(mod.target, State):
            if mod.target.value == mod.value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            mod_state_id = self._generate_state(
                nugget, mod.target, attached_to, add_agents
            )
            nugget.template_rel.add((mod_state_id, "mod_state"))
            nugget.add_edge(mod_state_id, attached_to)

        elif isinstance(mod.target, Residue):
            if mod.target.state:
                if mod.target.state.value == mod.value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        UserWarning
                    )
                (residue_id, mod_state_id) = self._generate_residue(
                    nugget, mod.target, attached_to, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
                nugget.template_rel.add((mod_state_id, "mod_state"))
                nugget.template_rel.add((residue_id, "mod_residue"))
                nugget.add_edge(residue_id, attached_to)
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
        nugget.add_edge("mod", mod_state_id)

        return nugget


class BinaryBndGenerator(Generator):
    """Generator class for binary binding nugget."""

    def _create_nugget(self, bnd, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):

        nugget = NuggetContrainer()
        left = []
        right = []

        # 1. create physical agent nodes and conditions
        for member in bnd.left:
            if isinstance(member, PhysicalAgent):
                member_id = self._generate_agent_group(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            elif isinstance(member, PhysicalRegionAgent):
                (_, member_id) = self._generate_agent_region_group(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            else:
                raise NuggetGenerationError(
                    "Unkown type of an agent: '%s'" % type(member)
                )
            left.append(member_id)
            nugget.template_rel.add((member_id, "left"))

        for member in bnd.right:
            if isinstance(member, PhysicalAgent):
                member_id = member_id = self._generate_agent_group(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            elif isinstance(member, PhysicalRegionAgent):
                (_, member_id) = self._generate_agent_region_group(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            else:
                raise NuggetGenerationError(
                    "Unkown type of an agent: '%s'" % type(member)
                )
            right.append(member_id)
            nugget.template_rel.add((member_id, "right"))

        # 2. create binding action
        left_ids = "_".join(left)
        right_ids = "_".join(right)
        bnd_id = get_nugget_bnd_id(nugget.graph, left_ids, right_ids)

        bnd_attrs = {
            "direct": bnd.direct
        }
        if bnd.annotation:
            bnd_attrs.update(bnd.annotation.to_attrs())

        nugget.add_node(
            bnd_id, bnd_attrs,
            meta_typing="bnd",
            template_rel=["bnd"]
        )

        # 3. create loci
        left_locus = get_nugget_locus_id(nugget.graph, left_ids, bnd_id)
        nugget.add_node(
            left_locus,
            meta_typing="locus",
            template_rel=["left_locus"]
        )
        nugget.add_edge(left_locus, bnd_id)

        # HEREEEEE

        right_locus = get_nugget_locus_id(
            nugget.graph, right_ids, bnd_id
        )
        nugget.add_node(
            right_locus,
            meta_typing="locus"
        )
        nugget.add_edge(right_locus, bnd_id)

        # 4. connect left/right members to the respective loci
        for member in left:
            nugget.add_edge(member, left_locus)

        for member in right:
            nugget.add_edge(member, right_locus)

        return nugget


class ComplexGenerator(Generator):
    """Generator class for complex nugget."""

    def _create_nugget(self, complex, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):

        nugget = NuggetContrainer()

        members = []

        # create agents
        for member in complex.members:
            if isinstance(member, PhysicalAgent):
                member_id = self._generate_agent_group(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
                members.append(member_id)
            elif isinstance(member, PhysicalRegionAgent):
                (member_id, region_id) = self._generate_agent_region_group(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
                members.append(region_id)

        visited = set()

        for member in members:
            for partner in members:
                if member != partner and partner not in visited:
                    bnd_id = get_nugget_bnd_id(nugget.graph, member, partner)
                    nugget.add_node(
                        bnd_id,
                        {"direct": False},
                        meta_typing="bnd"
                    )

                    member_locus_id = get_nugget_locus_id(
                        nugget.graph, member, bnd_id
                    )
                    nugget.add_node(
                        member_locus_id,
                        meta_typing="locus"
                    )

                    partner_locus_id = get_nugget_locus_id(
                        nugget.graph, partner, bnd_id
                    )
                    nugget.add_node(
                        partner_locus_id,
                        meta_typing="locus"
                    )

                    nugget.add_edge(member_locus_id, bnd_id)
                    nugget.add_edge(partner_locus_id, bnd_id)

                    nugget.add_edge(member, member_locus_id)
                    nugget.add_edge(partner, partner_locus_id)

            visited.add(member)

        return nugget
