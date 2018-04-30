"""Collection of data structures for nugget generation."""
import copy
import warnings

import networkx as nx
import time

from regraph import (add_edge,
                     add_node)

from kami.entities import (Gene, RegionActor,
                           Residue, SiteActor, State
                           )
from kami.exceptions import (KamiError,
                             KamiWarning,
                             NuggetGenerationError)
from kami.utils.id_generators import (get_nugget_gene_id,
                                      get_nugget_region_id,
                                      get_nugget_residue_id,
                                      get_nugget_state_id,
                                      get_nugget_is_bnd_id,
                                      get_nugget_locus_id,
                                      get_nugget_site_id,
                                      get_nugget_bnd_id,)


class NuggetContainer:
    """Nugget container data structure.

    Attributes
    ----------
    graph : nx.(Di)Graph
        Nugget graph
    meta_typing : dict
        Typing of the nugget graph by the meta-model
    ag_typing : dict
        Typing of the nugget graph by the action graph
    template_rel : dict
        Relation of the nugget graph to the templates
    semantic_rels : dict
        Relation of the nugget graph to the semantic nuggets
    """

    def __init__(self, graph=None, meta_typing=None,
                 ag_typing=None, template_rel=None,
                 semantic_rels=None):
        """Initialize nugget container."""
        if graph:
            self.graph = copy.deepcopy(graph)
        else:
            self.graph = nx.DiGraph()

        self.node = self.graph.node
        self.edge = self.graph.edge

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
            self.template_rel = dict()
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
        self.template_rel[node_id] = set()
        if template_rel:
            for el in template_rel:
                self.template_rel[node_id].add(el)
        if semantic_rels:
            for key, value in semantic_rels.items():
                if key not in self.semantic_rels.keys():
                    self.semantic_rels[key] = dict()
                for v in value:
                    self.semantic_rels[key][node_id].add(v)
        return

    def add_edge(self, node_1, node_2, attrs=None):
        """Add edge between the nodes of a nugget."""
        add_edge(self.graph, node_1, node_2, attrs)
        return

    def nodes(self):
        """Return a list of nodes of the nugget graph."""
        return self.graph.nodes()

    def edges(self):
        """Return a list of edges of the nugget graph."""
        return self.graph.edges()


class Generator(object):
    """Base class for nugget generators."""

    def __init__(self, hierarchy):
        """Initialize generator with a hierarchy."""
        self.hierarchy = hierarchy

    def generate(self, mod, add_agents=True, anatomize=True,
                 apply_semantics=True):
        """Generate a nuggert generation rule."""
        nugget, nugget_type = self._create_nugget(mod)
        nugget_id = self.hierarchy.add_nugget(
            nugget, nugget_type,
            add_agents=add_agents,
            anatomize=anatomize,
            apply_semantics=apply_semantics)
        print("Generated nugget '%s'..." % nugget_id)
        return nugget_id

    def _generate_state(self, nugget, state, father):
        prefix = father

        state_id = get_nugget_state_id(nugget.graph, state, prefix)

        action_graph_state = None
        if father in nugget.ag_typing.keys():
            action_graph_state = self.hierarchy.identify_state(
                state, nugget.ag_typing[father])

        nugget.add_node(
            state_id,
            state.to_attrs(),
            meta_typing="state",
            ag_typing=action_graph_state
        )
        return state_id

    def _generate_residue(self, nugget, residue, father, gene):
        prefix = father

        residue_id = get_nugget_residue_id(nugget.graph, residue, prefix)

        action_graph_residue = None
        if gene in nugget.ag_typing.keys():
            action_graph_residue = self.hierarchy.identify_residue(
                residue, nugget.ag_typing[gene])

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
                residue_id
            )
            nugget.add_edge(state_id, residue_id)

        return (residue_id, state_id)

    def _generate_bound(self, nugget, partners, father):
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
            elif isinstance(partner, SiteActor):
                partner_id = get_nugget_site_id(
                    nugget.graph, str(partner.site),
                    str(partner.gene)
                )
            else:
                raise KamiError(
                    "Invalid type of binding partner in bound conditions: "
                    "type '%s' is received ('Gene', "
                    "'RegionActor' or 'SiteActor' are expected)" %
                    (type(partner))
                )

            partner_ids.append(partner_id)

            # generate prefix for is_bnd_id
            prefix = father

            is_bnd_id = get_nugget_is_bnd_id(
                nugget.graph, prefix, partner_id)

            nugget.add_node(
                is_bnd_id,
                meta_typing="is_bnd"
            )
            is_bnd_ids.append(is_bnd_id)

            partner_locus_id = get_nugget_locus_id(
                nugget.graph, partner_id, is_bnd_id)
            nugget.add_node(
                partner_locus_id,
                meta_typing="locus"
            )

            if isinstance(partner, Gene):
                partner_id = self._generate_gene(
                    nugget, partner)
            elif isinstance(partner, RegionActor):
                (_, partner_id) = self._generate_region_actor(
                    nugget, partner)
            elif isinstance(partner, SiteActor):
                (_, partner_id, _) = self._generate_site_actor(
                    nugget, partner)
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

    def _generate_site(self, nugget, site, father, gene):
        # 1. create region node
        prefix = father
        site_id = get_nugget_site_id(
            nugget.graph, str(site), prefix
        )

        action_graph_site = None
        if father in nugget.ag_typing.keys():
            action_graph_site = self.hierarchy.identify_site(
                site, nugget.ag_typing[father])

        nugget.add_node(
            site_id, site.to_attrs(),
            meta_typing="site",
            ag_typing=action_graph_site
        )

        # create and attach residues
        for residue in site.residues:
            if residue.loc is not None and site.start is not None and\
               site.end is not None:
                if residue.loc < site.start or residue.loc > site.end:
                    raise KamiError(
                        "Residue '%s' of a site '%s' is not valid: "
                        "residue loc (%d) is out of the site range (%d-%d)" %
                        (str(residue), str(site),
                         residue.loc, site.start, site.end)
                    )
            (residue_id, _) = self._generate_residue(
                nugget, residue, site_id, gene)
            nugget.add_edge(residue_id, site_id)

        # create and attach states
        for state in site.states:
            state_id = self._generate_state(
                nugget, state, site_id)
            nugget.add_edge(state_id, site_id)

        # 5. create and attach bounds
        for partners in site.bound_to:
            bound_locus_id = self._generate_bound(
                nugget, partners, site_id)
            nugget.add_edge(site_id, bound_locus_id)

        return site_id

    def _generate_region(self, nugget, region, father):
        # 1. create region node
        prefix = father

        region_id = get_nugget_region_id(
            nugget.graph, str(region), prefix
        )

        # identify region
        action_graph_region = None
        if father in nugget.ag_typing.keys():
            action_graph_region = self.hierarchy.identify_region(
                region, nugget.ag_typing[father])

        nugget.add_node(
            region_id, region.to_attrs(),
            meta_typing="region",
            ag_typing=action_graph_region
        )

        # 2. create and attach residues
        for residue in region.residues:
            if residue.loc is not None and region.start is not None and\
               region.end is not None:
                if residue.loc < region.start or residue.loc > region.end:
                    raise KamiError(
                        "Residue '%s' of a region '%s' is not valid: "
                        "residue loc (%d) is out of the region range (%d-%d)" %
                        (str(residue), str(region),
                         residue.loc, region.start, region.end)
                    )
            (residue_id, _) = self._generate_residue(
                nugget, residue, region_id, father)
            nugget.add_edge(residue_id, region_id)

        # 3. create and attach sites
        for site in region.sites:
            if site.start is not None and site.end is not None and\
               region.start is not None and region.end is not None:
                if site.start < region.start or site.end > region.end:
                    raise KamiError(
                        "Site '%s' of a region '%s' is not valid: site "
                        "range (%d-%d) is out of the region range (%d-%d)" %
                        (str(site), str(region),
                         site.start, site.end, region.start, region.end)
                    )
            site_id = self._generate_site(
                nugget, site, region_id, father)
            nugget.add_edge(site_id, region_id)

        # 4. create and attach states
        for state in region.states:
            state_id = self._generate_state(
                nugget, state, region_id)
            nugget.add_edge(state_id, region_id)

        # 5. create and attach bounds
        for partners in region.bound_to:
            bound_locus_id = self._generate_bound(
                nugget, partners, region_id)
            nugget.add_edge(region_id, bound_locus_id)

        return region_id

    def _generate_gene(self, nugget, gene):
        """Generate agent group + indentify mapping."""
        # 1. create agent node
        agent_id = get_nugget_gene_id(nugget.graph, gene)

        # 2. identify agent (map to a node in the action graph)
        action_graph_agent = self.hierarchy.identify_gene(gene)

        nugget.add_node(
            agent_id,
            gene.to_attrs(),
            meta_typing="gene",
            ag_typing=action_graph_agent
        )

        # 2. create and attach residues
        for residue in gene.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, agent_id, agent_id)
            nugget.add_edge(residue_id, agent_id)

        # 3. create and attach states
        for state in gene.states:
            state_id = self._generate_state(
                nugget, state, agent_id)
            nugget.add_edge(state_id, agent_id)

        # 4. create and attach regions
        for region in gene.regions:
            region_id = self._generate_region(
                nugget, region, agent_id)
            nugget.add_edge(region_id, agent_id)

        # 5. create and attach sites
        for site in gene.sites:
            site_id = self._generate_site(
                nugget, site, agent_id, agent_id)
            nugget.add_edge(site_id, agent_id)

        # 6. create and attach bounds
        for bnd in gene.bound_to:
            bound_locus_id = self._generate_bound(
                nugget, bnd, agent_id)
            nugget.add_edge(agent_id, bound_locus_id)

        return agent_id

    def _generate_region_actor(self, nugget, region_actor):
        agent_id = self._generate_gene(
            nugget, region_actor.gene)
        region_id = self._generate_region(
            nugget, region_actor.region, agent_id)
        nugget.add_edge(region_id, agent_id)
        return (agent_id, region_id)

    def _generate_site_actor(self, nugget, site_actor):
        agent_id = self._generate_gene(
            nugget, site_actor.gene)

        site_id = self._generate_site(
            nugget, site_actor.site, agent_id, agent_id)
        region_id = None
        if site_actor.region is not None:
            region_id = self._generate_region(
                nugget, site_actor.region, agent_id)
            nugget.add_edge(region_id, agent_id)
            nugget.add_edge(site_id, region_id)
        else:
            nugget.add_edge(site_id, agent_id)

        return (agent_id, site_id, region_id)

    def _generate_actor(self, nugget, actor):
        actor_region = None
        actor_site = None
        if isinstance(actor, Gene):
            actor_gene = self._generate_gene(nugget, actor)
        elif isinstance(actor, RegionActor):
            (actor_gene, actor_region) = self._generate_region_actor(
                nugget, actor)
        elif isinstance(actor, SiteActor):
            (actor_gene, actor_site, actor_region) =\
                self._generate_site_actor(
                    nugget, actor)
        else:
            raise NuggetGenerationError(
                "Unkown type of a PPI actor: '%s'" % type(actor)
            )
        return actor_gene, actor_region, actor_site

    def _generate_mod_target(self, nugget, target, attached_to,
                             gene, mod_value=True):
        residue = None
        if isinstance(target, State):
            if target.value == mod_value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            state = self._generate_state(
                nugget, target, attached_to)
        elif isinstance(target, Residue):
            if target.state:
                if target.state.value == mod_value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        KamiWarning
                    )
                (residue, state) = self._generate_residue(
                    nugget, target, attached_to, gene)
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
                "is provided" % type(target)
            )

        if residue is not None:
            nugget.add_edge(residue, attached_to)
            nugget.template_rel[residue] = {"substrate_residue"}
        else:
            nugget.add_edge(state, attached_to)

        nugget.template_rel[state] = {"mod_state"}
        return residue, state


class ModGenerator(Generator):
    """Modification nugget generator."""

    def _create_nugget(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = NuggetContainer()
        nugget.template_id = "mod_template"

        # 1. Process enzyme
        (enzyme, enzyme_region, enzyme_site) = self._generate_actor(
            nugget, mod.enzyme)
        nugget.template_rel[enzyme].add("enzyme")
        if enzyme_region:
            nugget.template_rel[enzyme_region] = {"enzyme_region"}
        if enzyme_site:
            nugget.template_rel[enzyme_site] = {"enzyme_site"}

        # Process substrate
        (substrate, substrate_region, substrate_site) = self._generate_actor(
            nugget, mod.substrate)
        nugget.template_rel[substrate].add("substrate")
        if substrate_region:
            nugget.template_rel[substrate_region] = {"substrate_region"}
        if substrate_site:
            nugget.template_rel[substrate_site] = {"substrate_site"}

        # 2. create mod node
        mod_attrs = mod.to_attrs()
        mod_attrs["value"] = mod.value

        nugget.add_node(
            "mod",
            mod_attrs,
            meta_typing="mod",
            template_rel=["mod"]
        )

        # 3. create state related nodes subject to modification
        if substrate_site:
            attached_to = substrate_site
        elif substrate_region:
            attached_to = substrate_region
        else:
            attached_to = substrate

        (mod_residue_id, mod_state_id) = self._generate_mod_target(
            nugget, mod.target, attached_to, substrate, mod.value)

        if enzyme_site:
            nugget.add_edge(enzyme_site, "mod")
        elif enzyme_region:
            nugget.add_edge(enzyme_region, "mod")
        else:
            nugget.add_edge(enzyme, "mod")
        nugget.add_edge("mod", mod_state_id)
        return nugget, "mod"


class BndGenerator(Generator):
    """Binding nugget generator."""

    def _create_nugget(self, bnd):

        nugget = NuggetContainer()
        nugget.template_id = "bnd_template"

        left = []
        right = []

        # 1. create bnd actors
        gene_id, region_id, site_id = self._generate_actor(nugget, bnd.left)
        nugget.template_rel[gene_id] = {"left_partner"}
        if site_id is not None:
            left.append(site_id)
            nugget.template_rel[site_id] = {"left_partner_site"}
        if region_id is not None:
            nugget.template_rel[region_id] = {"left_partner_region"}
            if site_id is None:
                left.append(region_id)
        if site_id is None and region_id is None:
            left.append(gene_id)

        gene_id, region_id, site_id = self._generate_actor(nugget, bnd.right)
        nugget.template_rel[gene_id] = {"right_partner"}
        if site_id is not None:
            right.append(site_id)
            nugget.template_rel[site_id] = {"right_partner_site"}
        if region_id is not None:
            nugget.template_rel[region_id] = {"right_partner_region"}
            if site_id is None:
                right.append(region_id)
        if site_id is None and region_id is None:
            right.append(gene_id)

        # 2. create binding action
        left_ids = "_".join(left)
        right_ids = "_".join(right)
        bnd_id = get_nugget_bnd_id(nugget.graph, left_ids, right_ids)

        bnd_attrs = bnd.to_attrs()

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
            template_rel=["left_partner_locus"]
        )
        nugget.add_edge(left_locus, bnd_id)

        right_locus = get_nugget_locus_id(
            nugget.graph, right_ids, bnd_id
        )
        nugget.add_node(
            right_locus,
            meta_typing="locus",
            template_rel=["right_partner_locus"]
        )
        nugget.add_edge(right_locus, bnd_id)

        # 4. connect left/right members to the respective loci
        for member in left:
            nugget.add_edge(member, left_locus)

        for member in right:
            nugget.add_edge(member, right_locus)

        return nugget, "bnd"


class AnonymousModGenerator(Generator):
    """Anonymous nugget generator."""

    def _create_nugget(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = NuggetContainer()
        nugget.template_id = "mod_template"

        # Process substrate
        (substrate, substrate_region, substrate_site) = self._generate_actor(
            nugget, mod.substrate)
        nugget.template_rel[substrate].add("substrate")
        if substrate_region:
            nugget.template_rel[substrate_region] = {"substrate_region"}
        if substrate_site:
            nugget.template_rel[substrate_site] = {"substrate_site"}

        # 2. create mod node
        mod_attrs = mod.to_attrs()
        mod_attrs["value"] = mod.value,

        nugget.add_node(
            "mod",
            mod_attrs,
            meta_typing="mod",
            template_rel=["mod"]
        )

        # 3. create state related nodes subject to modification
        if substrate_site:
            attached_to = substrate_site
        elif substrate_region:
            attached_to = substrate_region
        else:
            attached_to = substrate

        (mod_residue_id, mod_state_id) = self._generate_mod_target(
            nugget, mod.target, attached_to, substrate, mod.value)

        nugget.add_edge("mod", mod_state_id)
        return nugget, "mod"


class AutoModGenerator(Generator):
    """Generator class for auto modification nugget."""

    def _create_nugget(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = NuggetContainer()
        nugget.template_id = "mod_template"

        # 1. Process enzyme
        (enzyme, enzyme_region, enzyme_site) = self._generate_actor(
            nugget, mod.enzyme)
        nugget.template_rel[enzyme].add("enzyme")
        nugget.template_rel[enzyme].add("substrate")
        if enzyme_region:
            nugget.template_rel[enzyme_region] = {"enzyme_region"}
        if enzyme_site:
            nugget.template_rel[enzyme_site] = {"enzyme_site"}

        # Process substrate components of the same gene
        substrate_region = None
        substrate_site = None
        if mod.substrate_region is not None:
            substrate_region = self._generate_region(
                nugget, mod.substrate_region, enzyme)
            nugget.template_rel[substrate_region] = {"substrate_region"}
            nugget.add_edge(substrate_region, enzyme)
        if mod.substrate_site is not None:
            if substrate_region is not None:
                substrate_site = self._generate_site(
                    nugget, mod.substrate_site, substrate_region, enzyme)
                nugget.add_edge(substrate_site, substrate_region)
            else:
                substrate_site = self._generate_site(
                    nugget, mod.substrate_site, enzyme, enzyme)
                nugget.add_edge(substrate_site, enzyme)
            nugget.template_rel[substrate_site] = {"substrate_site"}

        # 2. create mod node
        mod_attrs = mod.to_attrs()
        mod_attrs["value"] = mod.value

        nugget.add_node(
            "mod",
            mod_attrs,
            meta_typing="mod",
            template_rel=["mod"]
        )

        if substrate_site:
            attached_to = substrate_site
        elif substrate_region:
            attached_to = substrate_region
        else:
            attached_to = enzyme

        # 3. create state related nodes subject to modification
        (mod_residue_id, mod_state_id) = self._generate_mod_target(
            nugget, mod.target, attached_to, enzyme, mod.value)

        if enzyme_site:
            nugget.add_edge(enzyme_site, "mod")
        elif enzyme_region:
            nugget.add_edge(enzyme_region, "mod")
        else:
            nugget.add_edge(enzyme, "mod")
        nugget.add_edge("mod", mod_state_id)
        return nugget, "mod"


class TransModGenerator(Generator):
    """Generator class for transmodification nugget."""

    def _create_nugget(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = NuggetContainer()
        nugget.template_id = "mod_template"

        # 1. Process enzyme
        (enzyme, enzyme_region, enzyme_site) = self._generate_actor(
            nugget, mod.enzyme)
        nugget.template_rel[enzyme].add("enzyme")
        if enzyme_region:
            nugget.template_rel[enzyme_region] = {"enzyme_region"}
        if enzyme_site:
            nugget.template_rel[enzyme_site] = {"enzyme_site"}

        # Process substrate
        (substrate, substrate_region, substrate_site) = self._generate_actor(
            nugget, mod.substrate)
        nugget.template_rel[substrate].add("substrate")
        if substrate_region:
            nugget.template_rel[substrate_region] = {"substrate_region"}
        if substrate_site:
            nugget.template_rel[substrate_site] = {"substrate_site"}

        # 2. create mod node
        mod_attrs = mod.to_attrs()
        mod_attrs["value"] = mod.value

        nugget.add_node(
            "mod",
            mod_attrs,
            meta_typing="mod",
            template_rel=["mod"]
        )

        # 3. create state related nodes subject to modification
        if substrate_site:
            attached_to = substrate_site
        elif substrate_region:
            attached_to = substrate_region
        else:
            attached_to = substrate

        (mod_residue_id, mod_state_id) = self._generate_mod_target(
            nugget, mod.target, attached_to, substrate, mod.value)

        if enzyme_site:
            nugget.add_edge(enzyme_site, "mod")
        elif enzyme_region:
            nugget.add_edge(enzyme_region, "mod")
        else:
            nugget.add_edge(enzyme, "mod")
        nugget.add_edge("mod", mod_state_id)

        # 4. Process enzyme/substrate binding conditions
        enzyme_bnd_region = None
        enzyme_bnd_site = None
        if mod.enzyme_bnd_region is not None:
            enzyme_bnd_region = self._generate_region(
                nugget, mod.enzyme_bnd_region, enzyme)
            nugget.add_edge(enzyme_bnd_region, enzyme)
        if mod.enzyme_bnd_site is not None:
            if enzyme_bnd_region is not None:
                father = enzyme_bnd_region
            else:
                father = enzyme
            enzyme_bnd_site = self._generate_site(
                nugget, mod.enzyme_bnd_site, father, enzyme)
            if enzyme_bnd_region is not None:
                nugget.add_edge(enzyme_bnd_site, enzyme_bnd_region)
            else:
                nugget.add_edge(enzyme_bnd_site, enzyme)

        substrate_bnd_region = None
        substrate_bnd_site = None
        if mod.substrate_bnd_region is not None:
            substrate_bnd_region = self._generate_region(
                nugget, mod.substrate_bnd_region, substrate)
            nugget.add_edge(substrate_bnd_region, substrate)
        if mod.substrate_bnd_site is not None:
            if substrate_bnd_region is not None:
                father = substrate_bnd_region
            else:
                father = substrate
            substrate_bnd_site = self._generate_site(
                nugget, mod.substrate_bnd_site, father, substrate)
            if substrate_bnd_site is not None:
                nugget.add_edge(substrate_bnd_site, substrate_bnd_region)
            else:
                nugget.add_edge(substrate_bnd_site, substrate)

        nugget.add_node("is_bnd", meta_typing="is_bnd")
        enzyme_locus_id = get_nugget_locus_id(
            nugget.graph, enzyme, "is_bnd")
        nugget.add_node(
            enzyme_locus_id,
            meta_typing="locus"
        )
        substrate_locus_id = get_nugget_locus_id(
            nugget.graph, substrate, "is_bnd")
        nugget.add_node(
            substrate_locus_id,
            meta_typing="locus"
        )
        nugget.add_edge(enzyme_locus_id, "is_bnd")
        nugget.add_edge(substrate_locus_id, "is_bnd")

        if enzyme_bnd_site is not None:
            nugget.add_edge(enzyme_bnd_site, enzyme_locus_id)
        elif enzyme_bnd_region is not None:
            nugget.add_edge(enzyme_bnd_region, enzyme_locus_id)
        else:
            nugget.add_edge(enzyme, enzyme_locus_id)

        if substrate_bnd_site is not None:
            nugget.add_edge(substrate_bnd_site, substrate_locus_id)
        elif substrate_bnd_region is not None:
            nugget.add_edge(substrate_bnd_region, substrate_locus_id)
        else:
            nugget.add_edge(substrate, substrate_locus_id)

        return nugget, "mod"
