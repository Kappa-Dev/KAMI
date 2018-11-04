"""Collection of data structures for nugget generation."""
import copy
import warnings

import networkx as nx

from regraph import (add_edge,
                     add_node)

from kami.entities import (Gene, RegionActor,
                           Residue, SiteActor, State
                           )
from kami.interactions import (Modification, SelfModification,
                               AnonymousModification, LigandModification,
                               Binding, Unbinding)
from kami.exceptions import (KamiError,
                             KamiWarning,
                             NuggetGenerationError)
from kami.utils.id_generators import (get_nugget_gene_id,
                                      get_nugget_region_id,
                                      get_nugget_residue_id,
                                      get_nugget_state_id,
                                      get_nugget_is_bnd_id,
                                      get_nugget_site_id,
                                      get_nugget_bnd_id,)
from kami.aggregation.identifiers import (identify_gene, identify_region,
                                          identify_site, identify_residue,
                                          identify_state)


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
                 semantic_rels=None, desc=None):
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
        self.desc = desc
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

    def add_edge(self, s, t, attrs=None):
        """Add edge between the nodes of a nugget."""
        add_edge(self.graph, s, t, attrs)
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

    def _generate_state(self, nugget, state, father):
        prefix = father

        state_id = get_nugget_state_id(nugget.graph, state, prefix)

        action_graph_state = None
        if father in nugget.ag_typing.keys():
            action_graph_state = identify_state(
                self.hierarchy, state, nugget.ag_typing[father])

        nugget.add_node(
            state_id,
            state.meta_data(),
            meta_typing="state",
            ag_typing=action_graph_state
        )
        return state_id

    def _generate_residue(self, nugget, residue, father, gene):
        prefix = father

        residue_id = get_nugget_residue_id(nugget.graph, residue, prefix)

        action_graph_residue = None
        if gene in nugget.ag_typing.keys():
            action_graph_residue = identify_residue(
                self.hierarchy, residue, nugget.ag_typing[gene])

        nugget.add_node(
            residue_id,
            residue.meta_data(),
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

    def _generate_bound(self, nugget, partner, father, test=True):
        (partner_gene, partner_region, partner_site) = self._generate_actor(
            nugget, partner)

        # generate prefix for is_bnd_id
        prefix = father

        is_bnd_id = get_nugget_is_bnd_id(
            nugget.graph, prefix, partner_gene)

        nugget.add_node(
            is_bnd_id,
            attrs={"type": "be", "test": test},
            meta_typing="bnd"
        )
        if partner_site is not None:
            nugget.add_edge(partner_site, is_bnd_id)
        elif partner_region is not None:
            nugget.add_edge(partner_region, is_bnd_id)
        else:
            nugget.add_edge(partner_gene, is_bnd_id)
        return is_bnd_id

    def _generate_site(self, nugget, site, father, gene):
        # 1. create region node
        prefix = father
        site_id = get_nugget_site_id(
            nugget.graph, str(site), prefix
        )

        action_graph_site = None
        if father in nugget.ag_typing.keys():
            action_graph_site = identify_site(
                self.hierarchy, site, nugget.ag_typing[father])

        nugget.add_node(
            site_id, site.meta_data(),
            meta_typing="site",
            ag_typing=action_graph_site
        )

        # create and attach residues
        for residue in site.residues:
            if residue.loc is not None and site.start is not None and\
               site.end is not None:
                if residue.loc < int(site.start) or residue.loc > int(site.end):
                    raise KamiError(
                        "Residue '%s' of a site '%s' is not valid: "
                        "residue loc (%d) is out of the site range (%d-%d)" %
                        (str(residue), str(site),
                         residue.loc, site.start, site.end)
                    )
            (residue_id, _) = self._generate_residue(
                nugget, residue, site_id, gene)
            nugget.add_edge(residue_id, site_id, residue.location())

        # create and attach states
        for state in site.states:
            state_id = self._generate_state(
                nugget, state, site_id)
            nugget.add_edge(state_id, site_id)

        # 5. create and attach bounds
        for partner in site.bound_to:
            is_bnd_id = self._generate_bound(
                nugget, partner, site_id, test=True)
            nugget.add_edge(site_id, is_bnd_id)

        for partner in site.unbound_from:
            is_notbnd_id = self._generate_bound(
                nugget, partner, site_id, test=False)
            nugget.add_edge(site_id, is_notbnd_id)

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
            action_graph_region = identify_region(
                self.hierarchy, region, nugget.ag_typing[father])

        nugget.add_node(
            region_id, region.meta_data(),
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
            nugget.add_edge(residue_id, region_id, residue.location())

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
            nugget.add_edge(site_id, region_id, site.location())

        # 4. create and attach states
        for state in region.states:
            state_id = self._generate_state(
                nugget, state, region_id)
            nugget.add_edge(state_id, region_id)

        # 5. create and attach bounds
        for partners in region.bound_to:
            bound_locus_id = self._generate_bound(
                nugget, partners, region_id, test=True)
            nugget.add_edge(region_id, bound_locus_id)

        for partners in region.unbound_from:
            bound_locus_id = self._generate_bound(
                nugget, partners, region_id, test=False)
            nugget.add_edge(region_id, bound_locus_id)

        return region_id

    def _generate_gene(self, nugget, gene):
        """Generate agent group + indentify mapping."""
        # 1. create agent node
        agent_id = get_nugget_gene_id(nugget.graph, gene)

        # 2. identify agent (map to a node in the action graph)
        action_graph_agent = identify_gene(self.hierarchy, gene)

        nugget.add_node(
            agent_id,
            gene.meta_data(),
            meta_typing="gene",
            ag_typing=action_graph_agent
        )

        # 2. create and attach residues
        for residue in gene.residues:
            (residue_id, _) = self._generate_residue(
                nugget, residue, agent_id, agent_id)
            nugget.add_edge(residue_id, agent_id, residue.location())

        # 3. create and attach states
        for state in gene.states:
            state_id = self._generate_state(
                nugget, state, agent_id)
            nugget.add_edge(state_id, agent_id)

        # 4. create and attach regions
        for region in gene.regions:
            region_id = self._generate_region(
                nugget, region, agent_id)
            nugget.add_edge(region_id, agent_id, region.location())

        # 5. create and attach sites
        for site in gene.sites:
            site_id = self._generate_site(
                nugget, site, agent_id, agent_id)
            nugget.add_edge(site_id, agent_id, site.location())

        # 6. create and attach bounds
        for bnd in gene.bound_to:
            bound_locus_id = self._generate_bound(
                nugget, bnd, agent_id, test=True)
            nugget.add_edge(agent_id, bound_locus_id)

        for bnd in gene.unbound_from:
            bound_locus_id = self._generate_bound(
                nugget, bnd, agent_id, test=False)
            nugget.add_edge(agent_id, bound_locus_id)

        return agent_id

    def _generate_region_actor(self, nugget, region_actor):
        agent_id = self._generate_gene(
            nugget, region_actor.gene)
        region_id = self._generate_region(
            nugget, region_actor.region, agent_id)
        nugget.add_edge(region_id, agent_id, region_actor.region.location())
        return (agent_id, region_id)

    def _generate_site_actor(self, nugget, site_actor):
        agent_id = self._generate_gene(
            nugget, site_actor.gene)

        site_id = self._generate_site(
            nugget, site_actor.site, agent_id, agent_id)
        region_id = None
        if len(site_actor.region) > 0:
            for r in site_actor.region:
                region_id = self._generate_region(
                    nugget, r, agent_id)
                nugget.add_edge(region_id, agent_id, r.location())
                nugget.add_edge(site_id, region_id, site_actor.site.location())
        else:
            nugget.add_edge(site_id, agent_id, site_actor.site.location())

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
            if target.test == mod_value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            state = self._generate_state(
                nugget, target, attached_to)
        elif isinstance(target, Residue):
            if target.state:
                if target.state.test == mod_value:
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
            nugget.add_edge(residue, attached_to, target.location())
            nugget.template_rel[residue] = {"substrate_residue"}
        else:
            nugget.add_edge(state, attached_to)

        nugget.template_rel[state] = {"mod_state"}
        return residue, state


class ModGenerator(Generator):
    """Modification nugget generator."""

    def generate(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = NuggetContainer(desc=mod.desc)
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

    def generate(self, bnd):
        nugget = NuggetContainer(desc=bnd.desc)
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
        bnd_attrs["type"] = "do"
        if isinstance(bnd, Binding):
            bnd_attrs["test"] = True
        else:
            bnd_attrs["test"] = False

        nugget.add_node(
            bnd_id, bnd_attrs,
            meta_typing="bnd",
            template_rel=["bnd"]
        )

        # connect left/right members to the respective loci
        for member in left:
            nugget.add_edge(member, bnd_id)

        for member in right:
            nugget.add_edge(member, bnd_id)

        return nugget, "bnd"


class AnonymousModGenerator(Generator):
    """Anonymous nugget generator."""

    def generate(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = NuggetContainer(desc=mod.desc)
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

        nugget.add_edge("mod", mod_state_id)
        return nugget, "mod"


class SelfModGenerator(Generator):
    """Generator class for auto modification nugget."""

    def generate(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = NuggetContainer(desc=mod.desc)
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
            nugget.add_edge(
                substrate_region, enzyme, mod.substrate_region.location())
        if mod.substrate_site is not None:
            if substrate_region is not None:
                substrate_site = self._generate_site(
                    nugget, mod.substrate_site, substrate_region, enzyme)
                nugget.add_edge(
                    substrate_site, substrate_region,
                    mod.substrate_site.location())
            else:
                substrate_site = self._generate_site(
                    nugget, mod.substrate_site, enzyme, enzyme)
                nugget.add_edge(
                    substrate_site, enzyme,
                    mod.substrate_site.location())
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


class LigandModGenerator(Generator):
    """Generator class for transmodification nugget."""

    def generate(self, mod):
        """Create a mod nugget graph and find its typing."""

        nugget = NuggetContainer(desc=mod.desc)
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
        # 4.1 Validation checks
        if mod.enzyme_bnd_subactor == "gene":
            pass
        elif mod.enzyme_bnd_subactor == "region":
            if enzyme_region is None:
                raise KamiError(
                    "Cannot use region as an enzyme binding subactor: "
                    "no regions are included in the enzyme actor '{}'!".format(
                        mod.enzyme.__repr__()))
        elif mod.enzyme_bnd_subactor == "site":
            if enzyme_site is None:
                raise KamiError(
                    "Cannot use site as an enzyme binding subactor: "
                    "no sites are included in the enzyme actor '{}'!".format(
                        mod.enzyme.__repr__()))
        else:
            raise KamiError(
                "Invalid value of `enzyme_bnd_subactor` of LigandModification object:"
                "expected 'gene', 'site' or 'region', got '{}'".format(
                    mod.enzyme_bnd_subactor))

        if mod.substrate_bnd_subactor == "gene":
            pass
        elif mod.substrate_bnd_subactor == "region":
            if substrate_region is None:
                raise KamiError(
                    "Cannot use region as a substrate binding subactor: "
                    "no regions are included in the substrate actor '{}'!".format(
                        mod.substrate.__repr__()))
        elif mod.substrate_bnd_subactor == "site":
            if substrate_site is None:
                raise KamiError(
                    "Cannot use site as a substrate binding subactor: "
                    "no sites are included in the substrate actor '{}'!".format(
                        mod.substrate.__repr__()))
        else:
            raise KamiError(
                "Invalid value of `substrate_bnd_subactor` of LigandModification object:"
                "expected 'gene', 'site' or 'region', got '{}'".format(
                    mod.substrate_bnd_subactor))

        enzyme_bnd_region = None
        enzyme_bnd_site = None
        if mod.enzyme_bnd_region is not None:
            if mod.enzyme_bnd_subactor == "gene":
                enzyme_bnd_region = self._generate_region(
                    nugget, mod.enzyme_bnd_region, enzyme)
                nugget.add_edge(enzyme_bnd_region, enzyme,
                                mod.enzyme_bnd_region.location())
            else:
                raise KamiError(
                    "Cannot add enzyme binding region '{}' to ".format(
                        mod.enzyme_bnd_region.__repr__()) +
                    "the enzyme binding subactor: " +
                    "subactor is of type '{}'".format(
                        mod.enzyme_bnd_subactor))
        elif mod.enzyme_bnd_subactor == "region":
            enzyme_bnd_region = enzyme_region

        if mod.enzyme_bnd_site is not None:
            if mod.enzyme_bnd_subactor == "site":
                raise KamiError(
                    "Cannot add enzyme binding site '{}' to ".format(
                        mod.enzyme_bnd_site.__repr__()) +
                    "the enzyme binding subactor: " +
                    "subactor is of type 'site'")
            else:
                if enzyme_bnd_region is not None:
                    father = enzyme_bnd_region
                else:
                    father = enzyme
                enzyme_bnd_site = self._generate_site(
                    nugget, mod.enzyme_bnd_site, father, enzyme)
                if enzyme_bnd_region is not None:
                    nugget.add_edge(
                        enzyme_bnd_site, enzyme_bnd_region,
                        mod.enzyme_bnd_site.location())
                else:
                    nugget.add_edge(enzyme_bnd_site, enzyme,
                                    mod.enzyme_bnd_site.location())
        elif mod.enzyme_bnd_subactor == "site":
            enzyme_bnd_site = enzyme_site

        substrate_bnd_region = None
        substrate_bnd_site = None
        if mod.substrate_bnd_region is not None:
            if mod.substrate_bnd_subactor == "gene":
                substrate_bnd_region = self._generate_region(
                    nugget, mod.substrate_bnd_region, substrate)
                nugget.add_edge(substrate_bnd_region, substrate,
                                mod.substrate_bnd_region.location())
            else:
                raise KamiError(
                    "Cannot add substrate binding region '{}' to ".format(
                        mod.substrate_bnd_region.__repr__()) +
                    "the substrate binding subactor: " +
                    "subactor is of type '{}'".format(
                        mod.substrate_bnd_subactor))
        elif mod.substrate_bnd_subactor == "region":
            substrate_bnd_region = substrate_region

        if mod.substrate_bnd_site is not None:
            if mod.substrate_bnd_subactor == "site":
                raise KamiError(
                    "Cannot add substrate binding site '{}' to ".format(
                        mod.substrate_bnd_site.__repr__()) +
                    "the substrate binding subactor: " +
                    "subactor is of type 'site'")
            else:
                if substrate_bnd_region is not None:
                    father = substrate_bnd_region
                else:
                    father = substrate
                substrate_bnd_site = self._generate_site(
                    nugget, mod.substrate_bnd_site, father, substrate)
                if substrate_bnd_region is not None:
                    nugget.add_edge(
                        substrate_bnd_site, substrate_bnd_region,
                        mod.substrate_bnd_site.location())
                else:
                    nugget.add_edge(substrate_bnd_site, substrate,
                                    mod.substrate_bnd_site.location())
        elif mod.substrate_bnd_subactor == "site":
            substrate_bnd_site = substrate_site

        # if mod.substrate_bnd_region is not None:
        #     substrate_bnd_region = self._generate_region(
        #         nugget, mod.substrate_bnd_region, substrate)
        #     nugget.add_edge(substrate_bnd_region, substrate,
        #                     mod.substrate_bnd_region.location())
        # if mod.substrate_bnd_site is not None:
        #     if substrate_bnd_region is not None:
        #         father = substrate_bnd_region
        #     else:
        #         father = substrate
        #     substrate_bnd_site = self._generate_site(
        #         nugget, mod.substrate_bnd_site, father, substrate)
        #     if substrate_bnd_region is not None:
        #         nugget.add_edge(substrate_bnd_site, substrate_bnd_region,
        #                         mod.substrate_bnd_site.location())
        #     else:
        #         nugget.add_edge(substrate_bnd_site, substrate,
        #                         mod.substrate_bnd_site.location())

        nugget.add_node("is_bnd", attrs={"type": "be", "test": True},
                        meta_typing="bnd")

        if enzyme_bnd_site is not None:
            nugget.add_edge(enzyme_bnd_site, "is_bnd")
        elif enzyme_bnd_region is not None:
            nugget.add_edge(enzyme_bnd_region, "is_bnd")
        else:
            nugget.add_edge(enzyme, "is_bnd")

        if substrate_bnd_site is not None:
            nugget.add_edge(substrate_bnd_site, "is_bnd")
        elif substrate_bnd_region is not None:
            nugget.add_edge(substrate_bnd_region, "is_bnd")
        else:
            nugget.add_edge(substrate, "is_bnd")

        return nugget, "mod"


def generate_from_interaction(hierarchy, interaction):
    """Generate nugget from an interaction object."""
    if isinstance(interaction, Modification):
        gen = ModGenerator(hierarchy)
    elif isinstance(interaction, SelfModification):
        gen = SelfModGenerator(hierarchy)
    elif isinstance(interaction, AnonymousModification):
        gen = AnonymousModGenerator(hierarchy)
    elif isinstance(interaction, LigandModification):
        gen = LigandModGenerator(hierarchy)
    elif isinstance(interaction, Binding) or\
            isinstance(interaction, Unbinding):
        gen = BndGenerator(hierarchy)
    else:
        raise KamiError(
            "Unknown type of interaction '{}'".format(type(interaction))) 
    return gen.generate(interaction)
