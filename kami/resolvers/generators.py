"""Collection of nugget generators."""

import collections
import copy
import warnings

import networkx as nx

from regraph.primitives import (add_edge,
                                add_node,
                                add_node_attrs,
                                remove_edge)

from kami.entities import (Gene, Region, RegionActor,
                           Residue, SiteActor, State
                           )
from kami.exceptions import (KamiError,
                             KamiWarning,
                             NuggetGenerationError,
                             )
from kami.utils.id_generators import (get_nugget_gene_id,
                                      get_nugget_region_id,
                                      get_nugget_residue_id,
                                      get_nugget_state_id,
                                      get_nugget_is_bnd_id,
                                      get_nugget_locus_id,
                                      get_nugget_bnd_id,
                                      get_nugget_site_id,
                                      generate_new_id)
from anatomizer.new_anatomizer import GeneAnatomy


class NuggetContainer:
    """Nugget container data structure.

    Contains the following fields:
    - `graph` - nugget graph;
    - `meta_typing` - typing of the nugget graph by the meta-model;
    - `ag_typing` - typing of the nugget graph by the action graph;
    - `template_rel` - relation of the nugget graph to the templates;
    - `semantic_rels` - relation of the nugget graph to the semantic nuggets;
    """

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
        """Initialize generator with a hierarchy."""
        self.hierarchy = hierarchy

    def _add_gene_to_ag(self, gene, anatomize=True):
        if anatomize is True:
            anatomy = None
            if gene.uniprotid is not None:
                anatomy = GeneAnatomy(
                    gene.uniprotid,
                    merge_features=True,
                    nest_features=False,
                    merge_overlap=0.05,
                    offline=True
                )
            elif gene.hgnc_symbol is not None:
                anatomy = GeneAnatomy(
                    gene.hgnc_symbol,
                    merge_features=True,
                    nest_features=False,
                    merge_overlap=0.05,
                    offline=True
                )
            elif gene.synonyms is not None and\
                    len(gene.synonyms) > 0:
                anatomy = GeneAnatomy(
                    gene.synonyms[0],
                    merge_features=True,
                    nest_features=False,
                    merge_overlap=0.05,
                    offline=True
                )

            if anatomy is not None:
                gene.hgnc_symbol = anatomy.hgnc_symbol
            gene_id = self.hierarchy.add_gene(gene)

            if anatomy is not None:
                for domain in anatomy.domains:
                    if domain.feature_type == "Domain":
                        region = Region(
                            domain.start,
                            domain.end,
                            " ".join(domain.short_names),
                            label=domain.prop_label)

                        semantics = domain.get_semantics()

                        region_id = self.hierarchy.find_region(
                            region, gene_id)
                        if not region_id:
                            region_id = self.hierarchy.add_region(
                                region,
                                gene_id,
                                semantics=semantics
                            )
                            if 'kinase' in semantics:
                                state = State("activity", True)
                                activity_id = self.hierarchy.add_state(
                                    state,
                                    region_id,
                                    semantics=["activity"]
                                )
                                add_edge(
                                    self.hierarchy.action_graph,
                                    activity_id,
                                    region_id
                                )
                        add_edge(self.hierarchy.action_graph,
                                 region_id, gene_id)
        else:
            gene_id = self.hierarchy.add_gene(gene)
        return gene_id

    def _add_region_to_ag(self, region, ref_agent, anatomize=True):
        region_id = self.hierarchy.add_region(region, ref_agent)
        return region_id

    def _add_site_to_ag(self, site, ref_agent, anatomize=True):
        site_id = self.hierarchy.add_site(site, ref_agent)
        return site_id

    def _add_residue_to_ag(self, residue, ref_agent):
        residue_id = self.hierarchy.add_residue(residue, ref_agent)
        return residue_id

    def _add_state_to_ag(self, state, ref_agent):
        state_id = self.hierarchy.add_state(state, ref_agent)
        return state_id

    def _identify_gene(self, gene, add_agents=True, anatomize=True):
        # try to identify an agent
        reference_id = self.hierarchy.find_gene(gene)
        if add_agents is True:
            if reference_id is not None:
                # add new xrefs to AG agent
                add_node_attrs(
                    self.hierarchy.action_graph,
                    reference_id,
                    gene.to_attrs()
                )
            # if not found
            else:
                reference_id = self._add_gene_to_ag(gene, anatomize)

        return reference_id

    def _identify_region(self, region, agent, add_agents=True, anatomize=True):
        """Identify a region in the action graph."""
        try:
            reference_id = self.hierarchy.find_region(region, agent)
        except Exception as e:
            print(e)
            if add_agents is False:
                return None
            else:
                raise NuggetGenerationError(
                    "Cannot map a region '%s' from the nugget "
                    "to a region from the action graph" %
                    str(region)
                )
        # if not found
        if add_agents is True:
            if reference_id is None:
                reference_id = self._add_region_to_ag(
                    region,
                    agent,
                    anatomize
                )
            else:
                add_node_attrs(
                    self.hierarchy.action_graph,
                    reference_id,
                    region.to_attrs()
                )

        return reference_id

    def _identify_site(self, site, agent, add_agents=True, anatomize=True):
        """Identify a site in the action graph."""
        # try:
        reference_id = self.hierarchy.find_site(site, agent)
        # except Exception as e:
        #     print(e)
        #     if add_agents is False:
        #         return None
        #     else:
        #         raise NuggetGenerationError(
        #             "Cannot map a site '%s' from the nugget "
        #             "to a site from the action graph" %
        #             str(site)
        #         )
        # if not found
        if add_agents is True:
            if reference_id is None:
                reference_id = self._add_site_to_ag(
                    site,
                    agent,
                    anatomize
                )
            else:
                add_node_attrs(
                    self.hierarchy.action_graph,
                    reference_id,
                    site.to_attrs()
                )

        return reference_id

    def _identify_residue(self, residue, agent, add_agents=True):
        # try to identify an agent
        try:
            reference_id = self.hierarchy.find_residue(
                residue, agent, add_agents
            )
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
                        merge_actions=True, apply_semantics=True):
        is_bnd_ids = []
        partner_ids = []
        for partner in partners:
            if isinstance(partner, Gene):
                partner_id = get_nugget_gene_id(nugget.graph, partner)
            elif isinstance(partner, RegionActor):
                partner_id = get_nugget_region_id(
                    nugget.graph, str(partner.region),
                    str(partner.gene)
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

            partner_locus_id = get_nugget_locus_id(
                nugget.graph, partner_id, is_bnd_id)
            # !TODO! add indentification in ag
            nugget.add_node(
                partner_locus_id,
                # meta_typing="locus"
            )

            if isinstance(partner, Gene):
                partner_id = self._generate_gene(
                    nugget, partner,
                    add_agents, anatomize, merge_actions,
                    apply_semantics
                )
            elif isinstance(partner, RegionActor):
                (_, partner_id) = self._generate_region_actor(
                    nugget, partner, add_agents, anatomize, merge_actions,
                    apply_semantics
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

    def _generate_site(self, nugget, site, father,
                       add_agents=True, anatomize=True):
        # 1. create region node
        prefix = father

        site_id = get_nugget_site_id(
            nugget.graph, str(site), prefix
        )

        action_graph_site = None
        if father in nugget.ag_typing.keys():
            action_graph_site = self._identify_site(
                site, nugget.ag_typing[father], add_agents, anatomize
            )

        nugget.add_node(
            site_id, site.to_attrs(),
            meta_typing="site",
            ag_typing=action_graph_site,
            # semantic_rels=semantic_rels
        )

        # create and attach residues
        for residue in site.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, site_id, add_agents
            )
            nugget.add_edge(residue_id, site_id)

        return site_id

    def _generate_region(self, nugget, region, father,
                         add_agents=True, anatomize=True,
                         merge_actions=True, apply_semantics=True):
        # 1. create region node
        prefix = father

        region_id = get_nugget_region_id(
            nugget.graph, str(region), prefix
        )

        # identify region
        action_graph_region = None
        if father in nugget.ag_typing.keys():
            action_graph_region = self._identify_region(
                region, nugget.ag_typing[father], add_agents, anatomize
            )

        # find semantic relations

        nugget.add_node(
            region_id, region.to_attrs(),
            meta_typing="region",
            ag_typing=action_graph_region,
            # semantic_rels=semantic_rels
        )

        # 2. create and attach sites
        for site in region.sites:
            site_id = self._generate_site(
                nugget, site, region_id, add_agents, anatomize,
            )
            nugget.add_edge(site_id, region_id)

        # 3. create and attach residues
        for residue in region.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, region_id, add_agents
            )
            nugget.add_edge(residue_id, region_id)

        # 4. create and attach states
        for state in region.states:
            state_id = self._generate_state(
                nugget, state, region_id, add_agents
            )
            nugget.add_edge(state_id, region_id)

        # 5. create and attach bounds
        for partners in region.bounds:
            bound_locus_id = self._generate_bound(
                nugget, partners, region_id, add_agents,
                anatomize, merge_actions, apply_semantics
            )
            nugget.add_edge(region_id, bound_locus_id)

        return region_id

    def _generate_gene(self, nugget, gene,
                       add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):
        """Generate agent group + indentify mapping."""
        # 1. create agent node
        agent_id = get_nugget_gene_id(nugget.graph, gene)

        # 2. identify agent (map to a node in the action graph)
        action_graph_agent = self._identify_gene(
            gene, add_agents, anatomize
        )

        nugget.add_node(
            agent_id,
            gene.to_attrs(),
            meta_typing="agent",
            ag_typing=action_graph_agent
        )
        # 2. create and attach regions
        for region in gene.regions:
            region_id = self._generate_region(
                nugget, region, agent_id, add_agents, anatomize,
                merge_actions, apply_semantics,
            )
            nugget.add_edge(region_id, agent_id)

        # 2. create and attach sites
        for site in gene.sites:
            site_id = self._generate_site(
                nugget, site, agent_id, add_agents, anatomize,
            )
            nugget.add_edge(site_id, agent_id)

        # 4. create and attach residues
        for residue in gene.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, agent_id, add_agents
            )
            nugget.add_edge(residue_id, agent_id)

        # 5. create and attach states
        for state in gene.states:
            state_id = self._generate_state(
                nugget, state, agent_id, add_agents
            )
            nugget.add_edge(state_id, agent_id)

        # 6. create and attach bounds
        for bnd in gene.bounds:
            bound_locus_id = self._generate_bound(
                nugget, bnd, agent_id, add_agents, anatomize,
                merge_actions, apply_semantics
            )
            nugget.add_edge(agent_id, bound_locus_id)

        return agent_id

    def _generate_region_actor(self, nugget, region_actor,
                               add_agents=True, anatomize=True,
                               merge_actions=True, apply_semantics=True):
        agent_id = self._generate_gene(
            nugget, region_actor.gene, add_agents, anatomize, merge_actions,
            apply_semantics
        )
        region_id = self._generate_region(
            nugget, region_actor.region, agent_id, add_agents, anatomize
        )
        nugget.add_edge(region_id, agent_id)
        return (agent_id, region_id)

    def _generate_site_actor(self, nugget, site_actor,
                             add_agents=True, anatomize=True,
                             merge_actions=True, apply_semantics=True):
        agent_id = self._generate_gene(
            nugget, site_actor.gene, add_agents, anatomize, merge_actions,
            apply_semantics
        )

        site_id = self._generate_site(
            nugget, site_actor.site, agent_id, add_agents, anatomize
        )
        nugget.add_edge(site_id, agent_id)

        if site_actor.region is not None:
            region_id = self._generate_region(
                nugget, site_actor.region, agent_id, add_agents, anatomize
            )
            nugget.add_edge(region_id, agent_id)
            nugget.add_edge(site_id, region_id)
            add_edge(
                self.hierarchy.action_graph,
                nugget.ag_typing[site_id],
                nugget.ag_typing[region_id])

        return (agent_id, site_id)

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
            self.hierarchy.add_template_rel(
                nugget_id, nugget.template_id, nugget.template_rel)

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
        """Create a mod nugget graph and find its typing."""
        nugget = NuggetContainer()
        nugget.template_id = "mod_template"
        # 1. Process enzyme
        if isinstance(mod.enzyme, Gene):
            enzyme = self._generate_gene(
                nugget, mod.enzyme, add_agents, anatomize
            )
            enzyme_region = None
        elif isinstance(mod.enzyme, RegionActor):
            (enzyme, enzyme_region) = self._generate_region_actor(
                nugget, mod.enzyme, add_agents, anatomize
            )
        elif isinstance(mod.enzyme, SiteActor):
            (enzyme, enzyme_region) = self._generate_site_actor(
                nugget, mod.enzyme, add_agents, anatomize
            )
        else:
            raise NuggetGenerationError(
                "Unkown type of an enzyme: '%s'" % type(mod.enzyme)
            )

        nugget.template_rel.add((enzyme, "enzyme"))
        if enzyme_region:
            nugget.template_rel.add((enzyme_region, "enzyme_region"))

        if isinstance(mod.substrate, Gene):
            substrate = self._generate_gene(
                nugget, mod.substrate, add_agents, anatomize
            )
            substrate_region = None
        elif isinstance(mod.substrate, RegionActor):
            (substrate, substrate_region) = self._generate_region_actor(
                nugget, mod.substrate, add_agents, anatomize
            )
        elif isinstance(mod.substrate, SiteActor):
            (substrate, substrate_region) = self._generate_site_actor(
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
        if substrate_region:
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
                        "with a single protein in the action graph: %s" %
                        (", ".join(kinase_regions), enzyme),
                        KamiWarning
                    )
                else:
                    warnings.warn(
                        "Cannot resolve phospho modification: "
                        "no protein kinase region is associated "
                        "with the protein in the action graph: %s" % enzyme,
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
                mods = self.hierarchy.ag_successors_of_type(ag_region, "mod")

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
                        "with a single protein kinase domain "
                        "in the action graph: %s" % region,
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
                    "phosphorylation_state"
                )

                if mod_residue_id:
                    nugget.semantic_rels["phosphorylation"].add(
                        (mod_residue_id, "target_residue")
                    )
                    self.hierarchy.add_ag_node_semantics(
                        nugget.ag_typing[mod_residue_id],
                        "phospho_target_residue"
                    )

        # 2. DEPHOSPHORYLATION

        return nugget


class AutoModGenerator(Generator):
    """Generator class for auto modification nugget."""

    def _create_nugget(self, mod, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):
        """Create mod nugget graph and find its typing."""
        nugget = NuggetContainer()
        nugget.template_id = "mod_template"

        if not isinstance(mod.enzyme, Gene):
            raise NuggetGenerationError(
                "Automodification parameter 'enzyme_agent' "
                "should be an instance of 'PhysicalAgent', "
                "'%s' provided!" % type(mod.enzyme)
            )

        enzyme = self._generate_gene(
            nugget, mod.enzyme, add_agents, anatomize,
            merge_actions, apply_semantics
        )

        nugget.template_rel.add((enzyme, "enzyme"))
        nugget.template_rel.add((enzyme, "substrate"))

        # 2. create enzymatic/substratic regions
        if mod.enz_region:
            enzyme_region = self._generate_region(
                nugget, mod.enz_region, add_agents,
                anatomize, merge_actions, apply_semantics
            )
            nugget.add_edge(enzyme_region, enzyme)
            nugget.template_rel.add((enzyme_region, "enzyme_region"))

        if mod.sub_region:
            substrate_region = self._generate_region(
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
        nugget.template_id = "mod_template"

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
        nugget = NuggetContainer()
        nugget.template_id = "mod_template"

        if isinstance(mod.substrate, Gene):
            substrate = self._generate_gene(
                nugget, mod.substrate, add_agents, anatomize,
                merge_actions, apply_semantics
            )
            substrate_region = None
            nugget.template_rel.add((substrate, "substrate"))

        elif isinstance(mod.substrate, RegionActor):
            (substrate, substrate_region) = self._generate_region_actor(
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

    def _autocomplete_sh2_partners(self, nugget, partner_ids, partner_locus):
        updated_partners = []
        for partner in partner_ids:
            py_motif = None
            ag_partner_ref = nugget.ag_typing[partner]

            # If a binding partner has been already recognized
            # (in rel to semantic AG) as a pY motif
            if self.hierarchy.action_graph_typing[ag_partner_ref] == 'region':
                if 'pY_motif' in self.hierarchy.ag_node_semantics(ag_partner_ref):
                    py_motif = partner
                else:
                    raise ValueError("Binding region of wrong semantics!")
            else:
                # Create pY motif node
                reg_obj = Region(name="pY_motif")
                # a) in AG
                ag_motif = self.hierarchy.add_region(
                    reg_obj,
                    partner,
                    semantics=["pY_motif"]
                )
                # b) in the nugget
                py_motif = generate_new_id('pY_motif')
                nugget.add_node(
                    py_motif,
                    reg_obj.to_attrs,
                    ag_typing=ag_motif,
                    template_rel=["partner_region"],
                    semantic_rels={
                        "sh2_pY_binding": ["pY_motif"]
                    }
                )

                # Create pY residue
                res_obj = Residue("Y")
                ag_py_residue = self.hierarchy.add_residue(
                    res_obj,
                    partner,
                    "pY_residue"
                )
                py_residue = generate_new_id('pY_residue')
                nugget.add_node(
                    py_residue,
                    res_obj.to_attrs(),
                    ag_typing=ag_py_residue,
                    semantic_rels={
                        "sh2_pY_binding": ["pY_residue"]
                    }
                )
                # Create phospho state
                state_obj = State("phosphorylation", True)
                ag_phospho = self.hierarchy.add_state(
                    state_obj,
                    ag_py_residue,
                    "phosphorylation"
                )
                py_state = generate_new_id('pY_phosporylation')
                nugget.add_node(
                    py_state,
                    state_obj.to_attrs,
                    ag_typing=ag_phospho,
                    semantic_rels={
                        "sh2_pY_binding": ["phosphorylation"]
                    }
                )

                # Add AG edges
                add_edge(
                    self.hierarchy.action_graph,
                    ag_motif,
                    nugget.ag_typing[partner]
                )
                add_edge(
                    self.hierarchy.action_graph,
                    ag_py_residue,
                    ag_motif
                )
                add_edge(
                    self.hierarchy.action_graph,
                    ag_phospho,
                    ag_py_residue
                )

                # Add nugget edges
                remove_edge(nugget.graph, partner, partner_locus)
                nugget.add_edge(py_motif, partner_locus)
                nugget.add_edge(py_motif, partner)
                nugget.add_edge(py_residue, py_motif)
                nugget.add_edge(py_state, py_residue)

            nugget.semantic_rels["sh2_pY_binding"].add(
                (py_motif, 'pY_motif')
            )
            updated_partners.append(py_motif)
            # Check if has phosphorylated Y, if not --
            # autocomplete
            py_residue = None
            nugget.semantic_rels["sh2_pY_binding"].add(
                (py_residue, 'pY_residue')
            )
            py_state = None
            nugget.semantic_rels["sh2_pY_binding"].add(
                (py_state, 'phosphorylation')
            )

        return updated_partners

    def _apply_sh2_semantics(self, nugget, sh2_region, sh2_locus,
                             bnd_action_id, partner_ids, partner_locus,
                             bnd_attrs):

        # 1. Find loci and bnd nodes associated with this sh2 region
        # in ag
        ag_loci = self.hierarchy.ag_successors_of_type(
            nugget.ag_typing[sh2_region],
            "locus"
        )
        if len(ag_loci) == 0:
            # 2. Create new locus and new bnd action

            ag_left_locus_id = self.hierarchy.add_locus(
                semantics=["sh2_locus"])
            ag_bnd_id = self.hierarchy.add_bnd(
                bnd_attrs,
                semantics=["sh2_pY_bnd"]
            )
            ag_right_locus_id = self.hierarchy.add_locus(
                semantics=["pY_locus"])

            add_edge(
                self.hierarchy.action_graph,
                nugget.ag_typing[sh2_region],
                ag_left_locus_id,
            )

            add_edge(
                self.hierarchy.action_graph,
                ag_left_locus_id,
                ag_bnd_id
            )

            add_edge(
                self.hierarchy.action_graph,
                ag_right_locus_id,
                ag_bnd_id
            )

            nugget.ag_typing[sh2_locus] = ag_left_locus_id
            nugget.ag_typing[bnd_action_id] = ag_bnd_id
            nugget.ag_typing[partner_locus] = ag_right_locus_id

            # 3. Add semantic relation to the nugget nodes
            nugget.semantic_rels["sh2_pY_binding"] = set()
            nugget.semantic_rels["sh2_pY_binding"].add(
                (sh2_region, 'sh2')
            )
            nugget.semantic_rels["sh2_pY_binding"].add(
                (sh2_locus, 'sh2_locus')
            )
            nugget.semantic_rels["sh2_pY_binding"].add(
                (bnd_action_id, 'sh2_pY_bnd')
            )

            # 4. Autocomplete partners to contain pY motifs
            # updated_partners = self._autocomplete_sh2_partners(
            #     nugget, partner_ids, partner_locus
            # )
            updated_partners = partner_ids
            for partner in updated_partners:
                add_edge(
                    self.hierarchy.action_graph,
                    nugget.ag_typing[partner],
                    ag_right_locus_id
                )

        elif len(ag_loci) == 1:
            ag_bnds = self.hierarchy.ag_successors_of_type(
                ag_loci[0], "bnd"
            )
            if len(ag_bnds) == 1:
                # Find partner opposite of SH2 loci in the action graph
                all_bnd_loci = self.hierarchy.ag_predecessors_of_type(
                    ag_bnds[0],
                    "locus"
                )
                opposite_loci = [l for l in all_bnd_loci if l != ag_loci[0]]
                if len(opposite_loci) == 1:
                    nugget.ag_typing[partner_locus] = opposite_loci[0]
                else:
                    # smth is not right
                    raise ValueError()

                nugget.ag_typing[sh2_locus] = ag_loci[0]
                nugget.ag_typing[bnd_action_id] = ag_bnds[0]

                # 2. Add semantic relation to the nugget nodes
                nugget.semantic_rels["sh2_pY_binding"] = set()
                nugget.semantic_rels["sh2_pY_binding"].add(
                    (sh2_region, 'sh2')
                )
                nugget.semantic_rels["sh2_pY_binding"].add(
                    (sh2_locus, 'sh2_locus')
                )
                nugget.semantic_rels["sh2_pY_binding"].add(
                    (bnd_action_id, 'sh2_pY_bnd')
                )

                # 3. Autocomplete partners to contain pY motifs
                # updated_partners = self._autocomplete_sh2_partners(
                #     nugget, partner_ids, partner_locus
                # )
                updated_partners = partner_ids
                for partner in updated_partners:
                    add_edge(
                        self.hierarchy.action_graph,
                        nugget.ag_typing[partner],
                        opposite_loci[0]
                    )

            else:
                warnings.warn(
                    "Cannot resolve SH2 binding: a loci node '%s' "
                    "has invalid number of 'bnd' nodes asociated "
                    "in the action graph" % ag_loci[0],
                    KamiWarning
                )

        else:
            warnings.warn(
                "Cannot resolve SH2 binding: multiple loci "
                "are associated with a single SH2 domain in "
                "the action graph: %s" % nugget.ag_typing[
                    sh2_region],
                KamiWarning
            )
        return

    def _create_nugget(self, bnd, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):

        nugget = NuggetContainer()
        nugget.template_id = "bnd_template"

        left = []
        right = []

        # 1. create physical agent nodes and conditions
        for member in bnd.left:
            if isinstance(member, Gene):
                member_id = self._generate_gene(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            elif isinstance(member, RegionActor):
                (_, member_id) = self._generate_region_actor(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            elif isinstance(member, SiteActor):
                (_, member_id) = self._generate_site_actor(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            else:
                raise NuggetGenerationError(
                    "Unkown type of an agent: '%s'" % type(member)
                )
            left.append(member_id)
            nugget.template_rel.add((member_id, "partner"))

        for member in bnd.right:
            if isinstance(member, Gene):
                member_id = member_id = self._generate_gene(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            elif isinstance(member, RegionActor):
                (_, member_id) = self._generate_region_actor(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            elif isinstance(member, SiteActor):
                (_, member_id) = self._generate_site_actor(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
            else:
                raise NuggetGenerationError(
                    "Unkown type of an agent: '%s'" % type(member)
                )
            right.append(member_id)
            nugget.template_rel.add((member_id, "partner"))

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
            template_rel=["partner_locus"]
        )
        nugget.add_edge(left_locus, bnd_id)

        # HEREEEEE

        right_locus = get_nugget_locus_id(
            nugget.graph, right_ids, bnd_id
        )
        nugget.add_node(
            right_locus,
            meta_typing="locus",
            template_rel=["partner_locus"]
        )
        nugget.add_edge(right_locus, bnd_id)

        # 4. connect left/right members to the respective loci
        for member in left:
            nugget.add_edge(member, left_locus)

        for member in right:
            nugget.add_edge(member, right_locus)

        # Attempt to autocomplete the nugget
        # using semantics
        # 1. SH2 - pY binding

        # a) Left partner is SH2
        if len(bnd.left) == 1:
            if isinstance(bnd.left[0], RegionActor):
                if "sh2" in self.hierarchy.ag_node_semantics(
                        nugget.ag_typing[left[0]]):
                    self._apply_sh2_semantics(
                        nugget, left[0], left_locus, bnd_id,
                        right, right_locus, bnd_attrs
                    )

        # b) Right partner is SH2
        if len(bnd.right) == 1:
            if isinstance(bnd.right[0], RegionActor):
                if "sh2" in self.hierarchy.ag_node_semantics(
                        nugget.ag_typing[right[0]]):
                    self._apply_sh2_semantics(
                        nugget, right[0], right_locus, bnd_id, left,
                        left_locus, bnd_attrs
                    )
        return nugget


class ComplexGenerator(Generator):
    """Generator class for complex nugget."""

    def _create_nugget(self, complex, add_agents=True, anatomize=True,
                       merge_actions=True, apply_semantics=True):

        nugget = NuggetContainer()

        members = []

        # create agents
        for member in complex.members:
            if isinstance(member, Gene):
                member_id = self._generate_gene(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
                members.append(member_id)
            elif isinstance(member, RegionActor):
                (member_id, region_id) = self._generate_region_actor(
                    nugget, member, add_agents, anatomize,
                    merge_actions, apply_semantics
                )
                members.append(region_id)
            elif isinstance(member, SiteActor):
                # TODO
                pass

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
